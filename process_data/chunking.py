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

def process_surah_chunks(surah, session):
    """
    Insert Surah, Ayat, and related Chunk embeddings into Neo4j.

    Args:
        surah (dict): Surah data from loaded JSON.
        session (neo4j.Session): Active Neo4j session.
    """
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

        # Insert Chunk nodes with embeddings
        for source, content in {
            "text": ayah_text,
            "translation": translation,
            "tafsir": tafsir
        }.items():
            if content.strip():
                chunks = chunk_text(content)
                for chunk in chunks:
                    prefixed_chunk = f"[{source} {surah_name_latin}:{ayah_num}] {chunk}"
                    embedding = embed_chunk(prefixed_chunk)
                    session.run(
                        """
                        MATCH (s:Surah {number: $surah_number})-[:HAS_AYAT]->(a:Ayat {number: $ayat_number})
                        CREATE (c:Chunk {
                            id: $id,
                            text: $chunk_text,
                            embedding: $embedding,
                            source: $source,
                            ayat_number: $ayat_number,
                            surah_name: $surah_name,
                            surah_number: $surah_number
                        })
                        CREATE (a)-[:HAS_CHUNK]->(c)
                        """, {
                            "id": str(uuid4()),
                            "chunk_text": prefixed_chunk,
                            "embedding": embedding,
                            "source": source,
                            "ayat_number": ayah_num,
                            "surah_name": surah_name_latin,
                            "surah_number": surah_id
                        }
                    )
