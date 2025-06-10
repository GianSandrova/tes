import json
import re
import os
import sys

# Tambahkan path proyek ke sys.path agar bisa mengimpor dari package 'retrieval'
# Asumsi skrip ini dijalankan dari root direktori proyek
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# ==============================================================================
# == BAGIAN 1: IMPORT DARI SISTEM RETRIEVAL ANDA                            ==
# ==============================================================================
# Impor fungsi-fungsi yang dibutuhkan dari kode Anda.
# Pastikan semua dependensi seperti 'config.py' (untuk driver db) sudah benar.
from retrieval.parser import parse_hadith_query
from retrieval.retrieval import keyword_search_hadith_by_number, vector_search_chunks_generator
from retrieval.traversal import get_full_context_from_info, find_info_chunk_id
from retrieval.context_builder import build_chunk_context_interleaved

# Catatan: Karena kode Anda menggunakan Streamlit (st), kita perlu membuat objek tiruan
# agar tidak error saat dijalankan di luar Streamlit.
class MockStreamlit:
    def __init__(self):
        self.session_state = {}

st = MockStreamlit()

# ==============================================================================
# == BAGIAN 2: FUNGSI HELPER DAN FUNGSI RETRIEVAL UTAMA                       ==
# ==============================================================================

def get_source_from_context_string(context_part: str) -> str | None:
    """
    Mengekstrak ID Sumber dari satu blok konteks yang dihasilkan sistem Anda.
    Contoh input: "📘 Hadis Shahih Bukhari No. 4721\nKitab: Nikah | Bab: ... \nSkor Similarity:..."
    """
    # Mengambil baris yang dimulai dengan emoji buku sampai sebelum "Skor Similarity"
    match = re.search(r"^(📖.*?|📘.*?)(?=\nSkor Similarity:)", context_part, re.DOTALL)
    if match:
        # Membersihkan spasi berlebih dan mengganti newline dengan format yang konsisten
        return ' '.join(match.group(1).strip().split())
    return None

def run_retrieval_for_query(query: str, history: list = []) -> list[str]:
    """
    Menjalankan alur retrieval sistem Anda untuk satu query dan mengembalikan
    daftar ID sumber yang terurut.
    """
    print(f"\n---> Menjalankan retrieval untuk query: '{query}'")
    
    # Meniru fungsi build_semantic_query dari query_processor.py
    combined_query = ""
    for q, a in history:
        combined_query += f"User: {q}\nAssistant: {a}\n"
    combined_query += f"User: {query}"

    # Cek keyword search dulu, meniru logika process_user_query
    hadith_request = parse_hadith_query(query)
    context_str = ""
    if hadith_request:
        info_id = keyword_search_hadith_by_number(hadith_request["number"])
        if info_id:
            row = get_full_context_from_info(info_id)
            if row:
                sumber = (f"📘 Hadis {row.get('source_name')} No. {row.get('hadith_number')} "
                          f"| Kitab: {row.get('kitab_name', '-')} | Bab: {row.get('bab_name', '-')}")
                # Langsung kembalikan karena ini Exact Match
                return [sumber]

    # Jika tidak ada keyword match, fallback ke vector search
    # Panggil fungsi inti Anda untuk mendapatkan konteks
    context_str = build_chunk_context_interleaved(combined_query, top_k=5, min_score=0.6)

    if not context_str:
        return []

    # Pisahkan konteks menjadi beberapa bagian per dokumen (dipisahkan oleh '---')
    context_parts = context_str.strip().split('---')
    
    retrieved_ids = []
    for part in context_parts:
        if part.strip():
            source_id = get_source_from_context_string(part)
            if source_id:
                retrieved_ids.append(source_id)
            
    return retrieved_ids

# ==============================================================================
# == BAGIAN 3: KALKULASI MRR                                                  ==
# ==============================================================================

def calculate_mrr(ground_truth_data: list[dict]):
    """
    Menghitung Mean Reciprocal Rank (MRR) dari serangkaian query.
    """
    reciprocal_ranks = []
    
    for item in ground_truth_data:
        query = item.get("query")
        queries = item.get("queries") # Untuk multiturn
        expected_id = item["expected_id"]
        
        retrieved_ids = []
        if query: # Single-turn query
            retrieved_ids = run_retrieval_for_query(query)
        elif queries: # Multi-turn query
            print(f"\n---> Menjalankan retrieval MULTITURN")
            chat_history = []
            # Untuk evaluasi, kita hanya peduli hasil retrieval dari pertanyaan TERAKHIR
            for i, q in enumerate(queries):
                if i < len(queries) - 1:
                     # Untuk simplicitas, kita anggap jawaban dummy untuk membentuk history
                    chat_history.append((q, "jawaban dummy"))
                else: # Pertanyaan terakhir
                    retrieved_ids = run_retrieval_for_query(q, history=chat_history)

        print(f"Hasil retrieval: {retrieved_ids}")
        print(f"Jawaban diharapkan: {expected_id}")
        
        rank = 0
        try:
            rank = retrieved_ids.index(expected_id) + 1
        except ValueError:
            rank = 0
            
        reciprocal_rank = 1 / rank if rank > 0 else 0
        reciprocal_ranks.append(reciprocal_rank)
        
        print(f"Rank ditemukan: {rank}")
        print(f"Reciprocal Rank (RR) untuk query ini: {reciprocal_rank:.4f}")
        print("-" * 40)

    mrr_score = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0
    return mrr_score

if __name__ == "__main__":
    print("==============================================")
    print("== Memulai Evaluasi Sistem Retrieval (MRR) ==")
    print("==============================================")
    
    try:
        with open('ground_truth.json', 'r', encoding='utf-8') as f:
            ground_truth = json.load(f)
    except FileNotFoundError:
        print("❌ ERROR: File 'ground_truth.json' tidak ditemukan. Pastikan file ada di direktori yang sama.")
        sys.exit(1)
        
    mrr_value = calculate_mrr(ground_truth)
    
    print("\n==============================================")
    print("== HASIL AKHIR EVALUASI ==")
    print(f"== Jumlah Query      : {len(ground_truth)}")
    print(f"== Skor MRR Total    : {mrr_value:.4f}")
    print("==============================================")
    print("\nInterpretasi Skor MRR:")
    print("  - Skor mendekati 1.0: Sangat Baik. Jawaban benar hampir selalu di posisi pertama.")
    print("  - Skor di atas 0.8: Baik. Jawaban benar seringkali di posisi teratas.")
    print("  - Skor sekitar 0.5: Cukup. Jawaban benar rata-rata ada di posisi kedua.")
    print("  - Skor di bawah 0.3: Perlu Peningkatan. Jawaban benar seringkali tidak ditemukan atau berada di peringkat bawah.")