from sentence_transformers import SentenceTransformer

models = {
    "mini": SentenceTransformer("all-MiniLM-L6-v2"),
    "qa": SentenceTransformer("multi-qa-MiniLM-L6-cos-v1"),
    "mpnet" : SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
}

def create_embedding(text):

    embeddings = {
        name: model.encode(
                [text],
                convert_to_numpy=True,
                normalize_embeddings=True
            )[0].tolist()
            for name, model in models.items()
    }

    return embeddings
