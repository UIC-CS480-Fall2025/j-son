import json
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(
    dbname = "text_embeddings",
    user = "postgres",
    password = os.getenv("DB_PASSWORD"),
    host = "localhost",
    port = 55432
)

def load_jsonl_files(folder_path):

    jsonl_files = os.listdir(folder_path)

    for file in jsonl_files:
        file_path = os.path.join(folder_path, file)

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

def chunk_text(text, size=400, overlap=50):
    
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + size
        chunk = words[start:end]
        chunks.append(" ".join(chunk))
        start += size - overlap

    return chunks

def chunk_dataset(folder_path, size=150, overlap=50):
    
    all_chunks = []
    for item in load_jsonl_files(folder_path):
        url = item.get("url", "")
        text = item.get("text", "")
        if not text:
            continue
        
        local_chunks = chunk_text(text, size, overlap)
        for i, chunk in enumerate(local_chunks):

            if not chunk.strip():
                continue

            all_chunks.append({
                "url": url,
                "chunk_index": i,
                "text": chunk
            })

    return all_chunks

if __name__ == "__main__":
    
    chunked_dataset = chunk_dataset("archive")

    with conn.cursor() as cur:
        for c in chunked_dataset:
            cur.execute(
                "INSERT INTO Chunk_Embeddings (url, chunk_index, text) VALUES (%s, %s, %s)",
                (c["url"], c["chunk_index"], c["text"])
            )

    print("All files in archive/ are processsed and stored.")
    conn.commit()
    conn.close()