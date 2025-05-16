"""
graph_embedding/generate_metapath2vec.py
Script to run the MetaPath2Vec embedding generation process.
"""

import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from graph_embedding.metapath2vec_runner import generate_metapath2vec_embeddings
from config import driver

def update_embeddings():
    """
    Run the complete process to generate and store MetaPath2Vec embeddings.
    """
    try:
        print("🔄 Starting MetaPath2Vec embedding generation...")
        generate_metapath2vec_embeddings()
        print("✅ MetaPath2Vec embeddings successfully generated and stored in Neo4j")
        
    except Exception as e:
        print(f"❌ Error generating MetaPath2Vec embeddings: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()

if __name__ == "__main__":
    update_embeddings()