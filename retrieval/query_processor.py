# retrieval/query_processor.py

from retrieval.input_validation import validate_input
from retrieval.topic_detector import is_topic_changed, get_last_question
from retrieval.embedding import embed_combined
from retrieval.retrieval import vector_search_chunks_generator
from retrieval.context_builder import build_chunk_context_interleaved
from generation import generate_answer
import streamlit as st

# Fungsi untuk mengirimkan jawaban ke pengguna (Modul CD-015)
def send_jawaban_to_user(jawaban_hasil_generate):
    return jawaban_hasil_generate

# Fungsi untuk memperbarui riwayat chat (Modul CD-016)
def update_chat_history(teks_pertanyaan, jawaban, status_topik):
    if status_topik == "berubah":
        st.session_state.history = [{"user": teks_pertanyaan, "bot": jawaban}]
    else:
        if "history" not in st.session_state:
            st.session_state.history = []  # Jika belum ada riwayat, buat baru
        st.session_state.history.append({"user": teks_pertanyaan, "bot": jawaban})

    return st.session_state.history

# Fungsi utama untuk memproses pertanyaan pengguna
def process_user_query(teks_pertanyaan):
    print(f"Processing user query: {teks_pertanyaan}")
    riwayat_chat = st.session_state.get("history", [])
    valid, message = validate_input(teks_pertanyaan, riwayat_chat)

    if not valid:
        return message

    last_question = get_last_question(riwayat_chat)

    if last_question and is_topic_changed(teks_pertanyaan, last_question):
        print("Topik telah berubah, menghapus riwayat chat.")
        st.session_state.history.clear()

    combined_query = build_semantic_query(teks_pertanyaan, st.session_state.history)
    results = vector_search_chunks_generator(combined_query, top_k=20, min_score=0.6)

    if not results:
        return "❌ Maaf, saya tidak menemukan potongan yang relevan untuk menjawab pertanyaan ini."

    context = build_chunk_context_interleaved(combined_query, top_k=20, min_score=0.6)
    answer = generate_answer(teks_pertanyaan, context, history=st.session_state.history)

    # Kirim jawaban ke pengguna
    send_jawaban_to_user(answer)

    # Tentukan apakah topik berubah
    status_topik = "berubah" if is_topic_changed(teks_pertanyaan, last_question) else "sama"

    # Simpan riwayat chat
    update_chat_history(teks_pertanyaan, answer, status_topik)

    return answer

def build_semantic_query(teks_pertanyaan, history):
    combined = ""
    for q, a in history:
        combined += f"{q}\n{a}\n"
    combined += teks_pertanyaan
    return combined
