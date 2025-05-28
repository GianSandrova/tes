# retrieval/query_processor.py

from retrieval.input_validation import validate_input
from retrieval.topic_detector import is_topic_changed, get_last_question
from retrieval.embedding import embed_combined
from retrieval.retrieval import vector_search_chunks_generator
from retrieval.context_builder import build_chunk_context_interleaved
from generation import generate_answer
from retrieval.parser import parse_hadith_query
from retrieval.retrieval import keyword_search_hadith_by_number
from retrieval.traversal import traverse_from_info
import streamlit as st

# Fungsi untuk mengirimkan jawaban ke pengguna (Modul CD-015)
def send_jawaban_to_user(jawaban_hasil_generate):
    return jawaban_hasil_generate

# Fungsi untuk memperbarui riwayat chat (Modul CD-016)
def update_chat_history(teks_pertanyaan, jawaban, status_topik):
    """
    FIX: Menyimpan history secara konsisten sebagai list of TUPLES.
    """
    # Menggunakan format (pertanyaan, jawaban)
    new_history_item = (teks_pertanyaan, jawaban)

    if status_topik == "berubah":
        st.session_state.history = [new_history_item]
    else:
        if "history" not in st.session_state:
            st.session_state.history = []
        st.session_state.history.append(new_history_item)
    
    # Anda bisa hapus baris 'return' jika tidak digunakan di tempat lain
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
        riwayat_chat = [] 

    context = ""
    # === LOGIKA HYBRID SEARCH ===
    
    hadith_request = parse_hadith_query(teks_pertanyaan)
    
    if hadith_request:
        info_id = keyword_search_hadith_by_number(hadith_request["number"])
        if info_id:
            print(f"Building context directly from keyword search. Traversing from info_id: {info_id}")
            row = traverse_from_info(info_id)
            if row:
                sumber = f"📘 Hadis Bukhari No. {row.get('hadith_number')} ({row.get('label')})"
                context = f"""
{sumber}
Skor Similarity: 1.00 (Exact Match)
➤ Info:
{row.get('info_text') or '-'}
➤ Teks Arab:
{row.get('text_text') or '-'}
➤ Terjemahan:
{row.get('translation_text') or '-'}
➤ Tafsir:
{row.get('tafsir_text') or '-'}
"""

    if not context:
        print("Keyword search failed or not applicable. Falling back to vector search.")
        
        # 1. Bangun query yang kaya konteks dengan riwayat chat
        combined_query = build_semantic_query(teks_pertanyaan, riwayat_chat)
        
        # 2. Gunakan combined_query dan NAIKKAN min_score
        #    Ini adalah kunci untuk memfilter hasil yang tidak relevan pada pertanyaan lanjutan.
        #    Nilai 0.88 adalah titik awal yang baik, Anda bisa menyesuaikannya.
        context = build_chunk_context_interleaved(combined_query, top_k=5, min_score=0.6)

    # === SELESAI ===

    if not context:
        return "❌ Maaf, saya tidak dapat menemukan informasi yang relevan dalam sumber yang tersedia untuk menjawab pertanyaan tersebut."

    answer = generate_answer(teks_pertanyaan, context, history=st.session_state.get("history", []))

    send_jawaban_to_user(answer)
    status_topik = "berubah" if is_topic_changed(teks_pertanyaan, last_question) else "sama"
    update_chat_history(teks_pertanyaan, answer, status_topik)

    return answer

def build_semantic_query(teks_pertanyaan, history):
    """
    FIX: Memproses history secara konsisten sebagai list of TUPLES.
    """
    combined = ""
    # Membongkar tuple menjadi q (question) dan a (answer)
    for q, a in history:
        combined += f"User: {q}\nAssistant: {a}\n"
    combined += f"User: {teks_pertanyaan}"
    # print(f"Combined query for embedding:\n---\n{combined}\n---")
    return combined


