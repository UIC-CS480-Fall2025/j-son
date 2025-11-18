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

model = SentenceTransformer("all-MiniLM-L6-v2")

BATCH_SIZE = 100

with conn.cursor() as cur:

    cur.execute("SELECT id, text FROM chunks WHERE embedding IS NULL order by id")
    rows = cur.fetchall()

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i+BATCH_SIZE]
        ids = [r[0] for r in batch]
        texts = [r[1] for r in batch]

        embeddings = model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True
        )

        for chunk_id, emb in zip(ids, embeddings):
            cur.execute(
                "UPDATE chunks SET embedding = %s WHERE id = %s",
                (emb.tolist(), chunk_id)
            )

        conn.commit()
        print(f"Processed batch {i}-{i+len(batch)}")

conn.close()
print("Done embedding all chunks")