import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv

load_dotenv()

from os import getenv
conn = psycopg2.connect(
    dbname = "text_embeddings",
    user = "postgres",
    password = getenv("DB_PASSWORD"),
    host = "localhost",
    port = 55432 
)

conn.autocommit = False

models = {
    "mini": SentenceTransformer("all-MiniLM-L6-v2"),
    "qa": SentenceTransformer("multi-qa-MiniLM-L6-cos-v1"),
    "mpnet" : SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
}

BATCH_SIZE = 100

with conn.cursor() as cur:

    cur.execute("SELECT id, text FROM chunks WHERE embedding_mini IS NULL order by id")
    rows = cur.fetchall()

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i+BATCH_SIZE]
        ids = [r[0] for r in batch]
        texts = [r[1] for r in batch]

        embedding_mini = models["mini"].encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        embedding_qa = models["qa"].encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        embedding_mpnet = models["mpnet"].encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        for idx, chunk_id in enumerate(ids):
            emb_mini = embedding_mini[idx].tolist()
            emb_qa = embedding_qa[idx].tolist()
            emb_bge = embedding_bge[idx].tolist()
            emb_mpnet = embedding_mpnet[idx].tolist()

            cur.execute("""
                UPDATE chunks
                SET embedding_mini = %s,
                    embedding_qa = %s,
                    embedding_mpnet = %s
                WHERE id = %s
            """, (emb_mini, emb_qa, emb_mpnet, chunk_id))

        conn.commit()
        print(f"Processed batch {i}-{i+len(batch)}")

conn.close()
print("Done embedding all chunks")