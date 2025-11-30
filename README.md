# Fandom Page Searcher

This is a Query Answering System that takes textual content from documents and embeds them as vectors. These vectors are then stored inside of a PostgreSQL vector database for future querying.

The system itself is a CLI program where users login to make queries and upload documents to the database. Two types of documents are supported by the system: `jsonl` and `txt` files. Each `json` object in `jsonl` documents should have a `text` field that contains the textual content.

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
6. Clone this repository and navigate to its directory
    - Alongside with the code, this repository also includes a sample of the data inside of `archive/` for demoing purposes
7. Install the necessary dependencies with `pip install -r requirements.txt`
8. Inside of the repo directory, create a `.env` file to store your postgres password formatted as such:
    `DB_PASSWORD = <password>`

## Running the Project

Simply run the `main.py` file.
You will be greeted with a start up menu where you can login or register a new user.
By default, there will be an user `admin` in the system. To login to that account, both
the username and password are `admin`.

Otherwise, register a new End User to login.

There are 3 types of Users:

- End Users: Able to make queries. All registered users start off as an End User
- Curators: Special End Users that are able to upload documents and remove self uploaded documents
- Admins: Users with the highest level of access. Able to edit all other user information.

Once logged in, you will be able to perform certain actions according to your user role.

As a note, the system will start off with no documents stored. A curator or admin must add at least one document first before querying can provide any results.
