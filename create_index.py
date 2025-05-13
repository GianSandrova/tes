# create_index.py
from neo4j import GraphDatabase
from config import driver, DIMENSION
import sys

def create_indices():
    try:
        with driver.session() as session:
            # Index untuk embedding Chunk (menggunakan VECTOR INDEX)
            session.run("""
                CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
                FOR (c:Chunk) 
                ON (c.embedding)
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: $dim,
                        `vector.similarity_function`: 'cosine'
                    }
                }
            """, dim=DIMENSION)

            # Verifikasi indeks yang berhasil dibuat
            check = session.run("""
                SHOW INDEXES 
                WHERE name = 'chunk_embeddings' 
                AND type = 'VECTOR'
            """)

            created_indexes = [record["name"] for record in check]

            if "chunk_embeddings" in created_indexes:
                print("✅ Index vektor berhasil dibuat:")
                print(f"- Nama: chunk_embeddings (Chunk)")
                print(f"- Dimensi: {DIMENSION}")
                print(f"- Similarity Function: cosine")
            else:
                print("❌ Gagal membuat indeks chunk_embeddings!")
                sys.exit(1)

    except Exception as e:
        print(f"❌ Error saat membuat indeks: {str(e)}")
        sys.exit(1)
    finally:
        driver.close()

if __name__ == "__main__":
    create_indices()
