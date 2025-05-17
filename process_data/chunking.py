# process_data/chunking.py
"""
Module for processing Surah and Ayat nodes,
including chunking text and inserting chunk embeddings into Neo4j.
"""

from uuid import uuid4
from process_data.embedding import embed_chunk

def chunk_text(text, max_tokens=8192, overlap=128):
    """
    Split long text into smaller overlapping chunks for embedding.

    Args:
        text (str): The text to be chunked.
        max_tokens (int): Maximum tokens per chunk.
        overlap (int): Overlap tokens between chunks.

    Returns:
        list: List of chunked text segments.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + max_tokens, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += max_tokens - overlap

    return chunks

def extract_ayah_number(ayah_key: str) -> int:
    """
    Extract numeric part from ayah key string (e.g., 'Ayat 2').

    Args:
        ayah_key (str): Key string to extract number from.

    Returns:
        int: Ayah number.

    Raises:
        ValueError: If parsing fails.
    """
    try:
        return int(''.join(filter(str.isdigit, ayah_key)))
    except Exception:
        raise ValueError(f"❌ Gagal parsing ayat: {ayah_key}")

def extract_hadith_number(nomor_string):
    """
    Extract nomor angka dari string seperti 'Shahih Bukhari : 1'
    """
    try:
        return int(''.join(filter(str.isdigit, nomor_string)))
    except:
        return None

def process_hadith_chunks(hadith_item, session):
    from uuid import uuid4
    from process_data.embedding import embed_chunk

    hadith_number_str = hadith_item.get("nomor", "")
    hadith_number = extract_hadith_number(hadith_number_str)
    if hadith_number is None:
        print(f"❌ Gagal parsing nomor hadis: {hadith_number_str}")
        return

    arabic_text = hadith_item.get("arab", "")
    translation_text = hadith_item.get("terjemahan", "")

    # Node: HadithNumber
    session.run("""
        MATCH (h:Hadith {name: 'Shahih Bukhari'})
        CREATE (n:HadithNumber {
            number: $number,
            label: $label
        })
        CREATE (h)-[:HAS_NUMBER]->(n)
    """, {
        "number": hadith_number,
        "label": hadith_number_str
    })

    # === 1. Chunk Info ===
    info_text = f"[INFO Bukhari:{hadith_number}] Hadis Shahih Bukhari nomor {hadith_number}"
    info_embedding = embed_chunk(info_text)
    info_id = str(uuid4())

    session.run("""
        MATCH (n:HadithNumber {number: $number})
        CREATE (c_info:Chunk {
            id: $id,
            text: $text,
            embedding: $embedding,
            source: 'info',
            hadith_number: $number,
            label: $label
        })
        CREATE (n)-[:HAS_CHUNK]->(c_info)
    """, {
        "id": info_id,
        "text": info_text,
        "embedding": info_embedding,
        "number": hadith_number,
        "label": hadith_number_str
    })

    # === 2. Chunk Text (Arabic)
    for chunk in chunk_text(arabic_text):
        chunk_arab = f"[text Shahih Bukhari:{hadith_number}] {chunk}"
        embedding_arab = embed_chunk(chunk_arab)
        arab_id = str(uuid4())

        session.run("""
            MATCH (c_info:Chunk {id: $parent_id})
            CREATE (c_arab:Chunk {
                id: $id,
                text: $text,
                embedding: $embedding,
                source: 'text',
                hadith_number: $number,
                label: $label
            })
            CREATE (c_info)-[:HAS_CHUNK]->(c_arab)
        """, {
            "id": arab_id,
            "parent_id": info_id,
            "text": chunk_arab,
            "embedding": embedding_arab,
            "number": hadith_number,
            "label": hadith_number_str
        })

        # === 3. Chunk Translation
        if translation_text:
            for t_chunk in chunk_text(translation_text):
                chunk_trans = f"[translation Shahih Bukhari:{hadith_number}] {t_chunk}"
                embedding_trans = embed_chunk(chunk_trans)
                trans_id = str(uuid4())

                session.run("""
                    MATCH (c_arab:Chunk {id: $parent_id})
                    CREATE (c_trans:Chunk {
                        id: $id,
                        text: $text,
                        embedding: $embedding,
                        source: 'translation',
                        hadith_number: $number,
                        label: $label
                    })
                    CREATE (c_arab)-[:HAS_CHUNK]->(c_trans)
                """, {
                    "id": trans_id,
                    "parent_id": arab_id,
                    "text": chunk_trans,
                    "embedding": embedding_trans,
                    "number": hadith_number,
                    "label": hadith_number_str
                })



def process_surah_chunks(surah, session):
    from uuid import uuid4
    from process_data.embedding import embed_chunk

    surah_id = int(surah["number"])
    surah_name = surah["name"]
    surah_name_latin = surah["name_latin"]
    number_of_ayah = int(surah["number_of_ayah"])

    # Insert Surah node
    session.run(
        """
        MATCH (q:Quran {name: 'Al-Quran'})
        CREATE (s:Surah {
            number: $number,
            name: $name,
            name_latin: $name_latin,
            number_of_ayah: $number_of_ayah
        })
        CREATE (q)-[:HAS_SURAH]->(s)
        """, {
            "number": surah_id,
            "name": surah_name,
            "name_latin": surah_name_latin,
            "number_of_ayah": number_of_ayah
        }
    )

    for ayah_key, ayah_text in surah["text"].items():
        try:
            ayah_num = extract_ayah_number(ayah_key)
        except ValueError as e:
            print(str(e))
            continue

        translation = surah.get("translations", {}).get("id", {}).get("text", {}).get(ayah_key, "")
        tafsir = surah.get("tafsir", {}).get("id", {}).get("kemenag", {}).get("text", {}).get(ayah_key, "")

        # Insert Ayat node
        session.run(
            """
            MATCH (s:Surah {number: $surah_number})
            CREATE (a:Ayat {
                number: $number,
                text: $text,
                translation: $translation,
                tafsir: $tafsir
            })
            CREATE (s)-[:HAS_AYAT]->(a)
            """, {
                "surah_number": surah_id,
                "number": ayah_num,
                "text": ayah_text,
                "translation": translation,
                "tafsir": tafsir
            }
        )

        # === 1. Chunk Info Surah ===
        info_text = f"[INFO {surah_name_latin}:{ayah_num}] Surah {surah_name_latin} Ayat {ayah_num}"
        info_embedding = embed_chunk(info_text)
        info_id = str(uuid4())

        session.run(
            """
            MATCH (s:Surah {number: $surah_number})-[:HAS_AYAT]->(a:Ayat {number: $ayat_number})
            CREATE (c_info:Chunk {
                id: $id,
                text: $text,
                embedding: $embedding,
                source: 'info',
                ayat_number: $ayat_number,
                surah_name: $surah_name,
                surah_number: $surah_number
            })
            CREATE (a)-[:HAS_CHUNK]->(c_info)
            """, {
                "id": info_id,
                "text": info_text,
                "embedding": info_embedding,
                "ayat_number": ayah_num,
                "surah_name": surah_name_latin,
                "surah_number": surah_id
            }
        )

        # === 2. Chunk Text ===
        if ayah_text.strip():
            for chunk in chunk_text(ayah_text):
                chunk_text_full = f"[text {surah_name_latin}:{ayah_num}] {chunk}"
                text_embedding = embed_chunk(chunk_text_full)
                text_id = str(uuid4())

                session.run(
                    """
                    MATCH (c_info:Chunk {id: $parent_id})
                    CREATE (c_text:Chunk {
                        id: $id,
                        text: $text,
                        embedding: $embedding,
                        source: 'text',
                        ayat_number: $ayat_number,
                        surah_name: $surah_name,
                        surah_number: $surah_number
                    })
                    CREATE (c_info)-[:HAS_CHUNK]->(c_text)
                    """, {
                        "id": text_id,
                        "parent_id": info_id,
                        "text": chunk_text_full,
                        "embedding": text_embedding,
                        "ayat_number": ayah_num,
                        "surah_name": surah_name_latin,
                        "surah_number": surah_id
                    }
                )

                # === 3. Chunk Translation ===
                if translation.strip():
                    for t_chunk in chunk_text(translation):
                        chunk_trans_full = f"[translation {surah_name_latin}:{ayah_num}] {t_chunk}"
                        trans_embedding = embed_chunk(chunk_trans_full)
                        trans_id = str(uuid4())

                        session.run(
                            """
                            MATCH (c_text:Chunk {id: $parent_id})
                            CREATE (c_trans:Chunk {
                                id: $id,
                                text: $text,
                                embedding: $embedding,
                                source: 'translation',
                                ayat_number: $ayat_number,
                                surah_name: $surah_name,
                                surah_number: $surah_number
                            })
                            CREATE (c_text)-[:HAS_CHUNK]->(c_trans)
                            """, {
                                "id": trans_id,
                                "parent_id": text_id,
                                "text": chunk_trans_full,
                                "embedding": trans_embedding,
                                "ayat_number": ayah_num,
                                "surah_name": surah_name_latin,
                                "surah_number": surah_id
                            }
                        )

                        # === 4. Chunk Tafsir ===
                        if tafsir.strip():
                            for taf_chunk in chunk_text(tafsir):
                                chunk_taf_full = f"[tafsir {surah_name_latin}:{ayah_num}] {taf_chunk}"
                                taf_embedding = embed_chunk(chunk_taf_full)
                                taf_id = str(uuid4())

                                session.run(
                                    """
                                    MATCH (c_trans:Chunk {id: $parent_id})
                                    CREATE (c_tafsir:Chunk {
                                        id: $id,
                                        text: $text,
                                        embedding: $embedding,
                                        source: 'tafsir',
                                        ayat_number: $ayat_number,
                                        surah_name: $surah_name,
                                        surah_number: $surah_number
                                    })
                                    CREATE (c_trans)-[:HAS_CHUNK]->(c_tafsir)
                                    """, {
                                        "id": taf_id,
                                        "parent_id": trans_id,
                                        "text": chunk_taf_full,
                                        "embedding": taf_embedding,
                                        "ayat_number": ayah_num,
                                        "surah_name": surah_name_latin,
                                        "surah_number": surah_id
                                    }
                                )
