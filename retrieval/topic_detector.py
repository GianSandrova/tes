# === topic_detector.py ===
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generation.groq_client import call_groq_api

def is_topic_changed(new_query, last_query):
    """
    Gunakan LLM (Groq) untuk mendeteksi apakah topik dua pertanyaan berbeda.
    """
    prompt = f"""
Tentukan apakah dua pertanyaan berikut memiliki topik yang sama atau berbeda.
Jika topik berbeda, jawab hanya: "berbeda".
Jika topik masih sama atau lanjutan, jawab hanya: "sama".

Pertanyaan lama:
"{last_query}"

Pertanyaan baru:
"{new_query}"
"""
    try:
        response = call_groq_api(prompt).strip().lower()
        return "berbeda" in response
    except:
        return False  # fallback aman