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

models = {
    "mini": SentenceTransformer("all-MiniLM-L6-v2"),
    "qa": SentenceTransformer("multi-qa-MiniLM-L6-cos-v1"),
    "mpnet" : SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
}

def search(query, k=5):

    embedding_mini = models["mini"].encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0].tolist()

    embedding_qa = models["qa"].encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0].tolist()

    embedding_mpnet = models["mpnet"].encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0].tolist()

    with conn.cursor() as cur:

        cur.execute("""
            SELECT 
                id, url, chunk_index, text,
                (0.2 * (embedding_mini <=> %s::vector) +
                 0.5 * (embedding_qa   <=> %s::vector) +
                 0.3 * (embedding_mpnet  <=> %s::vector)
                ) AS distance
            FROM Chunk_Embeddings
            ORDER BY distance
            LIMIT %s;
        """, 
        (embedding_mini, embedding_qa, embedding_mpnet, k))

        results = cur.fetchall()

    return results

if __name__ == "__main__":
    query = input("Query: ")

    while query:
        results = search(query, 5)

        for r in results:
            print("----")
            print("URL:", r[1])
            print("Chunk:", r[2])
            print("Distance:", r[4])
            print("Text:", r[3])
            
        print()
        query = input("Query: ")