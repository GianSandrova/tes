from neo4j import GraphDatabase

# Konfigurasi Neo4j
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "12345678")

# Konfigurasi index embedding
INDEX_NAME = "ayat_embeddings"  # Nama indeks di Neo4j
DIMENSION = 3584  # Disesuaikan dengan model embedding yang digunakan
LABEL = "Tafsir"  # Label node di Neo4j
EMBEDDING_PROPERTY = "embedding"  # Properti yang menyimpan embedding

# Koneksi ke Neo4j
driver = GraphDatabase.driver(URI, auth=AUTH)

DIMENSION_STRUCTURAL = 128
GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"  # Pastikan model ini benar