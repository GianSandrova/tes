from groq_embedder import Embedder
embedding = Embedder.embed_text("Bismillah")
print(f"Panjang embedding: {len(embedding)}")
