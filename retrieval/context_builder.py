from retrieval.retrieval import vector_search_chunks_generator
from retrieval.traversal import find_info_chunk_id, traverse_from_info

def build_chunk_context_interleaved(query_text, top_k=20, min_score=0.6):
    context = ""
    visited_info_ids = set()

    for record in vector_search_chunks_generator(query_text, top_k=top_k, min_score=min_score):
        try:
            chunk_id = record["node"].element_id
            similarity = record["score"]
        except Exception as e:
            print(f"❌ Gagal mengambil element_id: {e}")
            continue

        # Temukan node info terdekat
        info_id = find_info_chunk_id(chunk_id)
        if not info_id:
            print(f"⚠️ Tidak ditemukan info chunk untuk chunk ID={chunk_id}")
            continue
        if info_id in visited_info_ids:
            print(f"🔁 Info ID {info_id} sudah diproses, dilewati.")
            continue
        visited_info_ids.add(info_id)

        # Ambil struktur penuh dari node info
        row = traverse_from_info(info_id)
        if not row:
            continue

        # Tentukan sumber otomatis (Qur’an atau Hadis)
        if row.get("surah"):
            sumber = f"📖 Surah: {row.get('surah')}\nAyat: {row.get('ayat_number')}"
        elif row.get("hadith_number"):
            sumber = f"📘 Hadis Bukhari No. {row.get('hadith_number')} ({row.get('label')})"
        else:
            sumber = "❓ Sumber tidak diketahui"

        # Debug (opsional)
        print(f"🔍 [HYBRID] Traversal dari chunk ID={chunk_id} → info ID={info_id}")
        print(f"    🔢 Skor similarity: {similarity:.4f}")
        print(f"    📚 Sumber: {sumber}")
        print(f"    🧩 Info       : {(row.get('info_text') or '-')[:60]}...")
        print(f"    🧩 Teks       : {(row.get('text_text') or '-')[:60]}...")
        print(f"    🧩 Terjemahan : {(row.get('translation_text') or '-')[:60]}...")
        print(f"    🧩 Tafsir     : {(row.get('tafsir_text') or '-')[:60]}...\n")

        # Bentuk blok konteks
        context += f"""
{sumber}
Skor Similarity: {similarity:.4f}

➤ Info:
{row.get('info_text') or '-'}

➤ Teks Arab:
{row.get('text_text') or '-'}

➤ Terjemahan:
{row.get('translation_text') or '-'}

➤ Tafsir:
{row.get('tafsir_text') or '-'}
"""

        if len(visited_info_ids) >= top_k:
            break

    return context
