# retrieval/query_processor.py

import streamlit as st
from retrieval.input_validation import validate_input
from retrieval.topic_detector import is_topic_changed, get_last_question
from retrieval.context_builder import build_chunk_context_interleaved
from generation import generate_answer
from retrieval.parser import parse_hadith_query
from retrieval.retrieval import keyword_search_hadith_by_number
# FIX: Import the correct universal function name
from retrieval.traversal import get_full_context_from_info

def send_jawaban_to_user(jawaban_hasil_generate):
    """Sends the generated answer to the user."""
    return jawaban_hasil_generate

def update_chat_history(teks_pertanyaan, jawaban, status_topik):
    """Updates the chat history in the session state."""
    new_history_item = (teks_pertanyaan, jawaban)
    if status_topik == "berubah":
        st.session_state.history = [new_history_item]
    else:
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.append(new_history_item)
    return st.session_state.history

def process_user_query(teks_pertanyaan):
    """Processes the user's query from input to final answer."""
    print(f"Processing user query: {teks_pertanyaan}")
    riwayat_chat = st.session_state.get("history", [])
    valid, message = validate_input(teks_pertanyaan, riwayat_chat)

    if not valid:
        return message

    last_question = get_last_question(riwayat_chat)
    if last_question and is_topic_changed(teks_pertanyaan, last_question):
        print("Topic has changed, clearing chat history.")
        riwayat_chat = []
        st.session_state.history = []

    context = ""
    hadith_request = parse_hadith_query(teks_pertanyaan)
    
    if hadith_request:
        info_id = keyword_search_hadith_by_number(hadith_request["number"])
        if info_id:
            print(f"Keyword match. Traversing from info_id: {info_id}")
            # Use the correct universal traversal function
            row = get_full_context_from_info(info_id)
            if row:
                sumber = (f"📘 Hadis {row.get('source_name')} No. {row.get('hadith_number')}\n"
                          f"Kitab: {row.get('kitab_name', '-')} | Bab: {row.get('bab_name', '-')}")

                context = f"""
{sumber}
Skor Similarity: 1.00 (Exact Match)

➤ Info:
{row.get('info_text') or '-'}

➤ Teks Arab:
{row.get('text_text') or '-'}

➤ Terjemahan:
{row.get('translation_text') or '-'}
---
"""

    if not context:
        print("Fallback to vector search.")
        combined_query = build_semantic_query(teks_pertanyaan, riwayat_chat)
        context = build_chunk_context_interleaved(combined_query, top_k=5, min_score=0.6)

    if not context:
        return "❌ Maaf, saya tidak dapat menemukan informasi yang relevan."

    answer = generate_answer(teks_pertanyaan, context, history=st.session_state.get("history", []))
    send_jawaban_to_user(answer)
    status_topik = "berubah" if is_topic_changed(teks_pertanyaan, last_question) else "sama"
    update_chat_history(teks_pertanyaan, answer, status_topik)
    return answer

def build_semantic_query(teks_pertanyaan, history):
    """Builds a context-rich query including chat history for embedding."""
    combined = ""
    for q, a in history:
        combined += f"User: {q}\nAssistant: {a}\n"
    combined += f"User: {teks_pertanyaan}"
    return combined