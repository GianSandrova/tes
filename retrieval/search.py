# === retrieval/search.py ===
import re
from collections import Counter
from retrieval.retrieval import vector_search_chunks, build_chunk_context
from generation import generate_answer
from retrieval.topic_detector import is_topic_changed
import streamlit as st


def build_semantic_query(query_text, history):
    """
    Gabungkan pertanyaan sekarang dengan riwayat sebelumnya untuk query vector search.
    """
    combined = ""
    for q, a in history:
        combined += f"{q}\n{a}\n"
    combined += query_text
    return combined

def process_query(query_text):
    print(f"\n💬 Query: '{query_text}'")

    if st.session_state.get("history"):
        last_query = st.session_state.history[-1][0]
        if is_topic_changed(query_text, last_query):
            print("📉 Topik baru terdeteksi. Riwayat direset.")
            st.session_state.history.clear()

    semantic_query = build_semantic_query(query_text, st.session_state.history)
    records = vector_search_chunks(semantic_query, top_k=10, min_score=0.6)
    if not records:
        return "❌ Maaf, saya tidak menemukan potongan yang relevan untuk menjawab pertanyaan ini."

    context = build_chunk_context(records)
    return generate_answer(query_text, context, history=st.session_state.history)
