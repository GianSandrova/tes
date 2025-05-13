# process_data/insert_data.py
"""
Script to insert Quran, Surah, Ayat, and Chunk embeddings into Neo4j.
"""
import os
import sys

# Determine the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from process_data.data_loader import load_quran_data
from process_data.chunking import process_surah_chunks
from config import driver
from tqdm import tqdm

def insert_quran_chunks():
    """
    Load Quran JSON data and insert all nodes and relationships into Neo4j,
    including chunked embeddings of verses, translations, and tafsir.
    """
    # Use an absolute path to the quran.json file
    quran_json_path = os.path.join(project_root, 'quran.json')
    
    try:
        # Load Quran data
        quran_data = load_quran_data(quran_json_path)

        with driver.session() as session:
            # Reset all existing data
            session.run("MATCH (n) DETACH DELETE n")
            session.run("CREATE (:Quran {name: 'Al-Quran'})")

            total_ayat = sum(len(surah["text"]) for surah in quran_data)
            progress = tqdm(total=total_ayat, desc="Memproses Ayat")

            for surah in quran_data:
                process_surah_chunks(surah, session)
                progress.update(len(surah["text"]))

            progress.close()
            print("\n✅ Semua data Al-Quran dan chunk embedding berhasil dimasukkan ke Neo4j.")

    except FileNotFoundError:
        print(f"❌ File quran.json tidak ditemukan di {quran_json_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error saat insert: {str(e)}")
        sys.exit(1)
    finally:
        driver.close()

if __name__ == "__main__":
    insert_quran_chunks()