# retrieval/embedding.py
"""
Embed user query using Groq embedder.
"""
from groq_embedder import Embedder

def embed_query(text):
    """
    Convert a query text into an embedding vector.
    
    Args:
        text (str): Input query.
    
    Returns:
        list: Embedding vector.
    """
    return Embedder.embed_query(text)
