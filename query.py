import psycopg2
from sentence_transformers import SentenceTransformer
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

model = SentenceTransformer("all-MiniLM-L6-v2")

def search(query, k=5):

    query_embedding = model.encode([query], convert_to_numpy=True)[0].tolist()

    with conn.cursor() as cur:

        cur.execute("""
            SELECT 
                id, url, chunk_index, text,
                embedding <=> %s::vector AS distance
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """, 
        (query_embedding, query_embedding, k))

        results = cur.fetchall()

    return results

results = search(input("Query: "), 5)

for r in results:
    print("----")
    print("URL:", r[1])
    print("Chunk:", r[2])
    print("Distance:", r[4])
    print("Text:", r[3])