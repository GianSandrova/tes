# === generation/prompt_builder.py ===
def build_prompt(query_text, context, history=[]):
    """
    Build instruction-based prompt from context and query with optional chat history.
    """
    history_text = ""
    if history:
        for idx, (q, a) in enumerate(history, 1):
            history_text += f"[{idx}] ❓ {q}\n[{idx}] 💡 {a}\n"

    return f"""
**Instruksi Sistem**
Gunakan riwayat jika relevan. Berikut tanya jawab sebelumnya:
{history_text}

Berikan penjelasan tafsir berdasarkan potongan konten berikut:
{context}

**Pertanyaan Baru**:
{query_text}

Jika potongan konten tidak relevan, mohon jawab bahwa Anda tidak bisa menjawab.
"""