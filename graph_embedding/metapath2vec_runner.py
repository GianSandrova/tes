
"""
graph_embedding/metapath2vec_runner.py
Module for generating metapath2vec structural embeddings from the Neo4j graph.
"""

import torch
import numpy as np
from neo4j import GraphDatabase
from torch_geometric.data import HeteroData
from torch_geometric.nn import MetaPath2Vec
from config import URI, AUTH, DIMENSION_STRUCTURAL


def create_graph_from_neo4j():
    """
    Extract graph structure from Neo4j database.
    
    Returns:
        tuple: (node_map, edge_type_lists)
            - node_map: Dict mapping node type to list of node IDs
            - edge_type_lists: Dict mapping edge types to lists of (source_idx, target_idx)
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    try:
        with driver.session() as session:
            # Get all nodes with their types - use elementId instead of id
            node_results = session.run("""
                MATCH (n) 
                RETURN DISTINCT elementId(n) AS node_id, labels(n)[0] AS node_type
            """)
            
            # Get all relationships (edges) - use elementId instead of id
            edge_results = session.run("""
                MATCH (a)-[r]->(b) 
                RETURN elementId(a) AS source_id, labels(a)[0] AS source_type, 
                       type(r) AS rel_type, 
                       elementId(b) AS target_id, labels(b)[0] AS target_type
            """)
            
            # Process nodes
            node_map = {}  # Type -> list of node IDs
            node_id_to_idx = {}  # Global node ID -> (type, local_idx) mapping
            
            for record in node_results:
                node_id = record["node_id"]
                node_type = record["node_type"]
                
                if node_type not in node_map:
                    node_map[node_type] = []
                
                # Store type-specific index
                local_idx = len(node_map[node_type])
                node_map[node_type].append(node_id)
                node_id_to_idx[node_id] = (node_type, local_idx)
            
            # Process edges
            edge_type_lists = {}  # (source_type, rel_type, target_type) -> [(src_idx, tgt_idx), ...]
            
            for record in edge_results:
                source_id = record["source_id"]
                target_id = record["target_id"]
                source_type = record["source_type"]
                target_type = record["target_type"]
                rel_type = record["rel_type"]
                
                edge_type = (source_type, rel_type, target_type)
                
                if edge_type not in edge_type_lists:
                    edge_type_lists[edge_type] = []
                
                source_idx = node_id_to_idx[source_id][1]
                target_idx = node_id_to_idx[target_id][1]
                
                edge_type_lists[edge_type].append((source_idx, target_idx))
    
    finally:
        driver.close()
        
    return node_map, edge_type_lists


def build_hetero_data(node_map, edge_type_lists):
    """
    Convert extracted graph data to PyTorch Geometric HeteroData format.
    
    Args:
        node_map: Dict mapping node type to list of node IDs
        edge_type_lists: Dict mapping edge types to lists of (source_idx, target_idx)
        
    Returns:
        HeteroData: PyTorch Geometric heterogeneous graph data object
    """
    data = HeteroData()
    
    # Add nodes with basic features (identity matrix)
    for node_type, node_ids in node_map.items():
        num_nodes = len(node_ids)
        data[node_type].x = torch.eye(num_nodes)
        data[node_type].node_ids = node_ids  # Store original Neo4j IDs
    
    # Add edges
    for edge_type, edge_list in edge_type_lists.items():
        source_type, rel_type, target_type = edge_type
        
        if not edge_list:
            continue
            
        edge_tensor = torch.tensor(edge_list, dtype=torch.long).t()
        data[edge_type].edge_index = edge_tensor
    
    # Create reverse edges for metapath2vec
    added_reverse_edges = 0
    for edge_type, edge_list in edge_type_lists.items():
        if not edge_list:
            continue
            
        source_type, rel_type, target_type = edge_type
        reverse_edge_type = (target_type, f"REVERSE_{rel_type}", source_type)
        
        # Create reverse edges by flipping source and target indices
        reverse_edge_list = [(target_idx, source_idx) for source_idx, target_idx in edge_list]
        reverse_edge_tensor = torch.tensor(reverse_edge_list, dtype=torch.long).t()
        data[reverse_edge_type].edge_index = reverse_edge_tensor
        added_reverse_edges += len(reverse_edge_list)
    
    print(f"✅ Built hetero graph with {sum(len(ids) for ids in node_map.values())} nodes, "
          f"{sum(len(edges) for edges in edge_type_lists.values())} original edges, and "
          f"{added_reverse_edges} added reverse edges")
    
    return data


def train_metapath2vec(hetero_data):
    """
    Train a MetaPath2Vec model on the heterogeneous graph.
    
    Args:
        hetero_data (HeteroData): PyTorch Geometric heterogeneous graph
        
    Returns:
        dict: Mapping node IDs to embeddings
    """
    # Define meaningful metapaths for Quran domain
    metapaths = [
        # Quran -> Surah -> Ayat -> Chunk (sequence of content)
        [('Quran', 'HAS_SURAH', 'Surah'), 
         ('Surah', 'HAS_AYAT', 'Ayat'),
         ('Ayat', 'HAS_CHUNK', 'Chunk')],
        
        # Alternate shorter paths
        [('Surah', 'HAS_AYAT', 'Ayat'), 
         ('Ayat', 'HAS_CHUNK', 'Chunk')]
    ]
    
    node_embeddings = {}
    
    for metapath_idx, metapath in enumerate(metapaths):
        print(f"Training on metapath {metapath_idx+1}/{len(metapaths)}: {metapath}")
        
        # Create a cycle from the metapath for MetaPath2Vec requirements
        cycle_metapath = []
        # Forward path
        for edge in metapath:
            cycle_metapath.append(edge)
        # Backward path (to create a cycle)
        for edge in reversed(metapath):
            source, rel, target = edge
            cycle_metapath.append((target, f"REVERSE_{rel}", source))
            
        # Check if we have the necessary edges in the graph
        missing_edges = False
        for edge_type in cycle_metapath:
            if edge_type not in hetero_data.edge_types:
                print(f"⚠️ Missing edge type in graph: {edge_type}")
                if edge_type[0] not in hetero_data.node_types:
                    print(f"   - Missing node type: {edge_type[0]}")
                if edge_type[2] not in hetero_data.node_types:
                    print(f"   - Missing node type: {edge_type[2]}")
                missing_edges = True
        
        if missing_edges:
            print("⚠️ Skipping this metapath due to missing edges")
            continue
            
        # Use appropriate walk length that's a multiple of the cycle
        walk_length = len(cycle_metapath) * 2
        
        try:
            # Create the model with updated API parameters
            model = MetaPath2Vec(
                edge_index_dict=hetero_data.edge_index_dict,
                embedding_dim=DIMENSION_STRUCTURAL,
                metapath=cycle_metapath,
                walk_length=walk_length,
                context_size=5,
                walks_per_node=5,
                num_negative_samples=5,
                sparse=True  # Memory efficient
            )
            
            print(f"👟 Starting training with walk_length={walk_length}, context_size=5")
            
            # Train the model
            model.train()
            optimizer = torch.optim.SparseAdam(list(model.parameters()), lr=0.01)
            
            # Train for a reasonable number of epochs
            num_epochs = 50
            batch_size = 128
            
            # Check how the MetaPath2Vec loader should be used based on the implementation
            try:
                loader = model.loader(batch_size=batch_size, shuffle=True)
                use_loader = True
                print("Using MetaPath2Vec loader API")
            except (AttributeError, TypeError):
                use_loader = False
                print("Using direct sampling API")
            
            for epoch in range(num_epochs):
                optimizer.zero_grad()
                
                # Different sampling approaches based on API availability
                if use_loader:
                    for pos_rw, neg_rw in loader:
                        optimizer.zero_grad()
                        loss = model.loss(pos_rw, neg_rw)
                        loss.backward()
                        optimizer.step()
                else:
                    # Use direct sampling without batch_size parameter
                    pos_rw = model._pos_sample()
                    neg_rw = model._neg_sample()
                    loss = model.loss(pos_rw, neg_rw)
                    loss.backward()
                    optimizer.step()
                
                if epoch % 10 == 0:
                    print(f"Epoch {epoch}/{num_epochs}: Loss = {loss.item():.4f}")
            
            print(f"✅ Finished training metapath {metapath_idx+1}")
            
            # Extract embeddings for each node type
            for node_type in hetero_data.node_types:
                # Get the original Neo4j IDs for this node type
                node_ids = hetero_data[node_type].node_ids
                
                # For each node, get its embedding
                for idx, node_id in enumerate(node_ids):
                    try:
                        # Different approaches to get embeddings based on API availability
                        try:
                            # Try newer API first if available
                            if hasattr(model, 'get_embedding_idx'):
                                node_idx = model.get_embedding_idx(node_type, idx)
                                if node_idx is not None:
                                    emb = model.embedding.weight[node_idx].detach().cpu().numpy().tolist()
                            else:
                                # Try direct embedding lookup (newer versions might have this approach)
                                emb = model.embedding(node_type, torch.tensor([idx])).detach().cpu().numpy()[0].tolist()
                        except (AttributeError, TypeError, ValueError):
                            try:
                                # Last resort: try to get embeddings directly if the structure allows
                                # This assumes the embedding table has nodes ordered by type and index
                                offset = 0
                                for nt in sorted(hetero_data.node_types):
                                    if nt == node_type:
                                        if idx < len(hetero_data[nt].x):
                                            node_idx = offset + idx
                                            emb = model.embedding.weight[node_idx].detach().cpu().numpy().tolist()
                                            break
                                    offset += len(hetero_data[nt].x)
                                else:
                                    # If we get here, we couldn't find the embedding
                                    print(f"⚠️ Could not find embedding for {node_type}[{idx}]")
                                    continue
                            except Exception as e2:
                                print(f"⚠️ Could not extract embedding for {node_type}[{idx}]: {str(e2)}")
                                continue
                        
                        # Store or update embedding
                        if 'emb' in locals():  # Check if we successfully got an embedding
                            if node_id not in node_embeddings:
                                node_embeddings[node_id] = emb
                            else:
                                # Average with existing embedding from other metapaths
                                existing = np.array(node_embeddings[node_id])
                                new = np.array(emb)
                                avg = ((existing + new) / 2).tolist()
                                node_embeddings[node_id] = avg
                    except Exception as e:
                        print(f"⚠️ Error getting embedding for {node_type}[{idx}]: {str(e)}")
                        continue
        
        except Exception as e:
            print(f"⚠️ Error training on metapath {metapath_idx+1}: {str(e)}")
            print("Continuing to next metapath...")
            import traceback
            traceback.print_exc()
            continue
    
    return node_embeddings


def update_node_embeddings(node_embeddings):
    """
    Update Neo4j nodes with metapath2vec embeddings.
    
    Args:
        node_embeddings (dict): Dict mapping node IDs to embeddings
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    try:
        with driver.session() as session:
            print(f"💾 Updating {len(node_embeddings)} nodes with structural embeddings...")
            
            # Update in batches for efficiency
            batch_size = 100
            node_items = list(node_embeddings.items())
            
            for i in range(0, len(node_items), batch_size):
                batch = node_items[i:i+batch_size]
                
                # Update each node individually
                for node_id, embedding in batch:
                    session.run(
                        """
                        MATCH (n) WHERE elementId(n) = $node_id
                        SET n.embedding_struct = $embedding
                        """,
                        {"node_id": node_id, "embedding": embedding}
                    )
                
                print(f"Updated {i+len(batch)}/{len(node_embeddings)} nodes")
    
    finally:
        driver.close()
    
    print("✅ All nodes updated with structural embeddings")


def generate_metapath2vec_embeddings():
    """
    Main function to generate and save metapath2vec embeddings.
    """
    print("🔄 Starting MetaPath2Vec embedding generation...")
    print("🔄 Extracting graph structure from Neo4j...")
    node_map, edge_type_lists = create_graph_from_neo4j()
    
    print("🔄 Building heterogeneous graph data...")
    hetero_data = build_hetero_data(node_map, edge_type_lists)
    
    print("🔄 Training MetaPath2Vec model...")
    node_embeddings = train_metapath2vec(hetero_data)
    
    print("🔄 Updating Neo4j nodes with structural embeddings...")
    update_node_embeddings(node_embeddings)
    
    print("✅ MetaPath2Vec embeddings generation complete")
    return node_embeddings

if __name__ == "__main__":
    node_embeddings = generate_metapath2vec_embeddings()
    print("✅ MetaPath2Vec embeddings successfully generated and stored in Neo4j")