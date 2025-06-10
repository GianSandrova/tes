# retrieval/context_builder.py

from retrieval.retrieval import vector_search_chunks_generator
from retrieval.traversal import find_info_chunk_id, get_full_context_from_info

def build_chunk_context_interleaved(query_text, top_k=5, min_score=0.6):
    context = ""
    visited_info_ids = set()

    for record in vector_search_chunks_generator(query_text, top_k=top_k*3, min_score=min_score):
        try:
            chunk_id = record["node"].element_id
            similarity = record["score"]
        except Exception as e:
            print(f"❌ Gagal mengambil element_id: {e}")
            continue

        info_id = find_info_chunk_id(chunk_id)
        if not info_id:
            print(f"⚠️ Tidak ditemukan info chunk untuk chunk ID={chunk_id}")
            continue
        if info_id in visited_info_ids:
            continue
        
        visited_info_ids.add(info_id)

        # Gunakan fungsi traversal universal yang baru
        row = get_full_context_from_info(info_id)
        if not row:
            continue

        # Tentukan sumber secara dinamis berdasarkan data yang ada di 'row'
        sumber = "❓ Sumber tidak diketahui"
        if row.get("surah_name") and row.get("ayat_number"):
            sumber = f"📖 Surah: {row.get('surah_name')} | Ayat: {row.get('ayat_number')}"
        elif row.get("source_name") and row.get("hadith_number"):
            sumber = (f"📘 Hadis {row.get('source_name')} No. {row.get('hadith_number')}\n"
                      f"Kitab: {row.get('kitab_name', '-')} | Bab: {row.get('bab_name', '-')}")

        print(f"🔍 Konteks dibangun dari info ID={info_id} | Skor: {similarity:.4f}")
        print(f"   📚 Sumber: {sumber.replace('\n', ' ')}")

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
---
"""
        if len(visited_info_ids) >= top_k:
            break

    return context