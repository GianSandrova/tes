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

def keyword_search_hadith_by_number(hadith_number: int):
    """
    Mencari hadis berdasarkan nomor secara langsung pada struktur data Anda.
    Fungsi ini secara spesifik mencari node :Chunk dengan source: 'info'
    yang memiliki properti hadith_number yang cocok.
    
    Mengembalikan element_id dari 'info' node agar bisa digunakan
    oleh fungsi traversal Anda yang sudah ada di traversal.py.
    """
    print(f"Executing keyword search for Hadith Bukhari No. {hadith_number}")
    
    # Query ini DIBUAT KHUSUS untuk skema Anda:
    # Ia menargetkan properti 'hadith_number' (yang bertipe integer)
    # di dalam node :Chunk yang berasal dari 'info'.
    result = driver.execute_query(
        """
        MATCH (info_chunk:Chunk {source: 'info', hadith_number: $nomor_hadis})
        RETURN elementId(info_chunk) AS info_id
        LIMIT 1
        """,
        {"nomor_hadis": hadith_number}
    )
    
    record = result.records[0] if result.records else None
    if record and record["info_id"]:
        info_id = record["info_id"]
        print(f"✅ Keyword search found a matching info_chunk. Element ID: {info_id}")
        return info_id
    
    print(f"❌ Keyword search did not find a match for Hadith Bukhari No. {hadith_number}")
    return None
