from config import driver

def find_info_chunk_id(chunk_id):
    result = driver.execute_query(
        """
        MATCH (c:Chunk)
        WHERE elementId(c) = $cid
        MATCH (c)<-[:HAS_CHUNK*0..3]-(info:Chunk {source: 'info'})
        RETURN elementId(info) AS info_id
        LIMIT 1
        """, {"cid": chunk_id}
    )
    return result.records[0]["info_id"] if result.records else None

def traverse_from_info(info_id):
    traversal = driver.execute_query(
        """
        MATCH (info:Chunk {source: 'info'})
        WHERE elementId(info) = $info_id
        OPTIONAL MATCH (info)-[:HAS_CHUNK]->(text:Chunk {source: 'text'})
        OPTIONAL MATCH (text)-[:HAS_CHUNK]->(translation:Chunk {source: 'translation'})
        OPTIONAL MATCH (translation)-[:HAS_CHUNK]->(tafsir:Chunk {source: 'tafsir'})
        RETURN 
            info.surah_name AS surah,
            info.ayat_number AS ayat_number,
            info.hadith_number AS hadith_number,
            info.label AS label,
            info.text AS info_text,
            text.text AS text_text,
            translation.text AS translation_text,
            tafsir.text AS tafsir_text
        LIMIT 1
        """, {"info_id": info_id}
    )
    return traversal.records[0] if traversal.records else None