# retrieval/retrieval.py
"""
Perform vector similarity search over Chunk embeddings in Neo4j.
"""
import traceback
from config import driver
from retrieval.embedding import embed_query

def vector_search_chunks(query_text, top_k=5, min_score=0.6):
    """
    Perform vector similarity search against chunk_embeddings index.

    Args:
        query_text (str): The user query text.
        top_k (int): Number of top results to return.
        min_score (float): Minimum score threshold.

    Returns:
        list: Filtered matching chunks with metadata.
    """
    try:
        vector = embed_query(query_text)

        result = driver.execute_query(
            """
            CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $query_vector)
            YIELD node, score
            RETURN node.text AS chunk_text,
                   node.source AS source,
                   node.ayat_number AS ayat_number,
                   node.surah_name AS surah,
                   score
            ORDER BY score DESC
            """,
            {"query_vector": vector, "top_k": top_k}
        )

        records = result.records if result.records else []
        filtered = [r for r in records if r["score"] >= min_score]

        if not filtered:
            print("⚠️ Tidak ada chunk yang melewati ambang skor minimal.")
        else:
            print("📦 Chunk relevan ditemukan:")
            for r in filtered:
                print(f"- ({r['surah']}:{r['ayat_number']}) [{r['source']}] | score={r['score']:.4f}")

        return filtered

    except Exception as e:
        print(f"❌ Vector search chunk error: {traceback.format_exc()}")
        return []

def build_chunk_context(records):
    """
    Format retrieved chunk records into a readable context for LLM input.

    Args:
        records (list): List of chunk metadata records.

    Returns:
        str: Formatted context string.
    """
    context = ""
    for r in records:
        context += f"""
📖 Surah: {r.get('surah')}
Ayat {r.get('ayat_number')} | Sumber: {r.get('source')}
➷ \"{r.get('chunk_text')}\"
"""
    return context