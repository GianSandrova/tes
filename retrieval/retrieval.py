# retrieval/retrieval.py
from config import driver
from retrieval.embedding import embed_query

def vector_search_chunks_generator(query_text, top_k=10, min_score=0.6):
    vector = embed_query(query_text)

    result = driver.execute_query(
        """
        CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $query_vector)
        YIELD node, score
        RETURN node,
               node.text AS chunk_text,
               node.source AS source,
               node.ayat_number AS ayat_number,
               node.surah_name AS surah,
               node.hadith_number AS hadith_number,
               node.label AS label,
               score
        ORDER BY score DESC
        """,
        {"query_vector": vector, "top_k": top_k}
    )

    for record in result.records:
        if record["score"] >= min_score:
            yield record

