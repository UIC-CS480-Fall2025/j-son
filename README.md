# Fandom Page Searcher

This is a Query Answering System that takes webpages scraped from several popular Fandom wikis, chunk each page's textual content and embeds them as vectors. These vectors are then stored inside of a PostgreSQL vector database for future querying.

## Data Source

This data was sourced from <https://www.kaggle.com/datasets/jonathanluo101/fandom-wiki-page-content>.

## Installation Guide

1. First install the latest versions of Python, Docker, and PostgreSQL.
2. Using Docker, install the vector extension for PostgreSQL, pgvector
    - `docker pull pgvector/pgvector:pg18-trixie`
3. Create a Docker container to set up a PostgreSQL server
    - `docker run -d --name <container_name> -e POSTGRES_PASSWORD=<postgres_password> -e POSTGRES_DB=text_embeddings -p 55432:5432 ankane/pgvector:latest`
    - Input your own container name, i.e. cs480-project, and postgres password
    - Verify the container has been created with `docker ps`
4. Start the newly created container and enter into psql via the container.
    - `docker start cs480-project` or the name you chose for the container
    - `docker exec -it cs480-project psql -U postgres -d text_embeddings`
    - This will create an interactive psql shell connected to a database called `text_embeddings`
5. Add the vector extension to the database: `CREATE EXTENSION IF NOT EXISTS vector;`
    - Verify with `\dx`, vector should be listed
6. Create a table `chunks` to store the chunked text
    - `CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                embedding VECTOR(384)
        );`
7. Clone this repository and navigate to its directory
    - Alongside with the code, this repository also includes a sample of the data inside of `archive/` for demoing purposes
8. Install the necessary dependencies with `pip install -r requirements.txt`
9. Inside of the repo directory, create a `.env` file to store your postgres password formatted as such:
    `DB_PASSWORD = <password>`

## Running the Project

1. First chunk the data by executing `chunk.py` with `python chunk.py`
    - All of the chunks should now be stored inside of the `chunks` table within the database
2. Then, embed all of the chunks by executing `embedding.py` with `python embedding.py`
    - After execution, all of the embeddings should be stored inside of the `chunks` table, under the column `embedding`, with their corresponding text chunk.
    - This process might take a long time due to the sheer quantity of chunks. If the purpose is to quickly demo the project, remove all but a few of the jsonl files from `archive/`, ideally the keeping the smaller files.
3. To finally begin querying, simply run `query.py` with `python query.py`
