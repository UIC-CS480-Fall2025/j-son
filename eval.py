import psycopg2
from sentence_transformers import SentenceTransformer

# -----------------------------
# Load models
# -----------------------------
models = {
    # "mini": SentenceTransformer("all-MiniLM-L6-v2"),
    # "qa": SentenceTransformer("multi-qa-MiniLM-L6-cos-v1"),
    # "bge": SentenceTransformer("BAAI/bge-small-en"),
    "mpnet" : SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
}

# Optional weights for combining embeddings
weights = {"mini": 0.3, "qa": 0.5, "bge": 0.2}

# -----------------------------
# Connect to database
# -----------------------------
conn = psycopg2.connect(
    dbname="text_embeddings",
    user="postgres",
    password="jason",
    host="localhost",
    port=55432
)

# -----------------------------
# Helper functions
# -----------------------------
def search_single_model(query, model_name, k=5):
    """Return top-k results for a single model."""
    query_emb = models[model_name].encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].tolist()
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT id, url, chunk_index, text,
                embedding_{model_name} <=> %s::vector AS distance
            FROM chunks
            ORDER BY distance
            LIMIT %s;
        """, (query_emb, k))
        return cur.fetchall()

def search_combined(query, k=5):
    """Return top-k results using weighted combination of all embeddings."""
    query_embeds = {
        name: model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].tolist()
        for name, model in models.items()
    }
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT id, url, chunk_index, text,
                ({weights['mini']} * (embedding_mini <=> %s::vector) +
                 {weights['qa']}   * (embedding_qa   <=> %s::vector) +
                 {weights['bge']}  * (embedding_bge  <=> %s::vector)
                ) AS distance
            FROM chunks
            ORDER BY distance
            LIMIT %s;
        """, (query_embeds['mini'], query_embeds['qa'], query_embeds['bge'], k))
        return cur.fetchall()

# -----------------------------
# Test queries (manual evaluation)
# -----------------------------
test_queries = [
    "Who is Mai Sakurajima?",
    "What is Adolescence Syndrome?",
    "Who is Azusagawa Sakuta?",
    "Describe Sakuta's school life",
    "What happened on May 6th?"
]

for query in test_queries:
    print("\n" + "="*50)
    print(f"Query: {query}\n")
    
    # Individual models
    for model_name in models:
        results = search_single_model(query, model_name, k=5)
        print(f"--- Top results from {model_name} ---")
        for r in results:
            print(f"ID: {r[0]} | URL: {r[1]} | Chunk: {r[2]} | Distance: {r[4]:.4f}")
            print(f"Text: {r[3]}\n")  # truncate for readability
    input()

    # Combined
    # results_combined = search_combined(query, k=5)
    # print("--- Top results from combined embeddings ---")
    # for r in results_combined:
    #     print(f"ID: {r[0]} | URL: {r[1]} | Chunk: {r[2]} | Distance: {r[4]:.4f}")
    #     print(f"Text: {r[3]}\n")