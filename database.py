import psycopg2
from dotenv import load_dotenv
import os
import chunk
import embedding
from itertools import chain
from psycopg2.extras import execute_values

load_dotenv()

conn = psycopg2.connect(
    dbname = "text_embeddings",
    user = "postgres",
    password = os.getenv("DB_PASSWORD"),
    host = "localhost",
    port = 55432
)

def initialize_db():

    with conn.cursor() as cur:

        try:
            cur.execute("""
                CREATE SCHEMA IF NOT EXISTS public;
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.Users (
                    ID SERIAL NOT NULL PRIMARY KEY,
                    User_Role varchar(10) NOT NULL,
                    User_Name varchar(20) Unique NOT NULL,
                    Email varchar(30) Unique NOT NULL,
                    User_Password varchar(15) NOT NULL,

                    Check(Email like '_%@_%._%'),
                    Check(User_Role in ('Admin', 'Curator', 'EndUser'))
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXIST public.Document (
                    ID SERIAL NOT NULL PRIMARY KEY,
                    Title varchar(80) NOT NULL,
                    Doc_Type varchar(20) NOT NULL,
                    Added_Time Timestamp Default now() NOT NULL,
                    Processed BOOLEAN DEFAULT False NOT NULL, 
                    Added_By INT NOT NULL,

                    Foreign Key (Added_By) REFERENCES Users(ID) ON DELETE CASCADE
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXIST public.QueryLog (
                    User_ID INT NOT NULL,
                    Query_Time TIMESTAMP DEFAULT Now() NOT NULL,
                    Query_Text TEXT NOT NULL,

                    FOREGIN KEY (User_ID) REFERENCES Users(ID) ON DELETE CASCADE,
                    PRIMARY KEY(User_ID, Query_Time)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXIST public.Retrieved_Docs (
                    User_ID INT NOT NULL,
                    Query_Time TIMESTAMP NOT NULL,
                    Doc_ID INT NOT NULL,
                    
                    FOREIGN KEY (User_ID, Query_Time) REFERENCES QueryLog(User_ID, Query_Time) ON DELETE CASCADE,
                    FOREIGN KEY (Doc_ID) REFERENCES Document(ID) ON DELETE CASCADE, 
                    PRIMARY KEY(User_ID, Query_Time, Doc_ID)
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXIST public.Chunk_Embeddings (
                    ID SERIAL PRIMARY KEY,
                    Document_ID INT NOT NULL,
                    Chunk_Text TEXT NOT NULL,
                    Embedding_Mini vector(384),
                    Embedding_QA vector(384),
                    Embedding_MPNET vector(768),

                    FOREIGN KEY (Document_ID) REFERENCES Document(ID) ON DELETE CASCADE
                );
            """)

            conn.commit()

            return True
        
        except Exception as e:
            print("Database initialization went wrong. " + str(e) + "\n Please restart.")
            return False

def add_user(user_name, email, pwd, role):

    with conn.cursor() as cur:

        try:
            cur.execute("""
                INSERT INTO Users(User_Role, User_Name, Email, User_Password)
                VALUES(%s, %s, %s, %s);
            """, [role, user_name, email, pwd])

            conn.commit()

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            print("A user with this username or email already exists. Please try again.")
            return False
        except psycopg2.errors.CheckViolation as e:
            print("Invalid email: " + e.pgerror + "\nPlease try again.")
            return False
        except psycopg2.errors.StringDataRightTruncation as e:
            conn.rollback()
            print("Field too long. " + e.pgerror + "\nPlease try again.")
            return False
        except Exception as e:
            conn.rollback()
            print("Unable to add create new user. " + str(e))
            return False
        
    print("User: " + user_name + " created.")
    return True

def check_login(user_name, pwd):

    with conn.cursor() as cur:

        cur.execute("""
            SELECT User_Role, User_Name, ID FROM Users
            WHERE User_Name = %s and User_Password = %s;
        """, [user_name, pwd])

        result = cur.fetchone()

        if not result:
            print("Invalid user name or password. Please try again")
            return ()
        
        return result
    
def get_user(admin, target_user):
    with conn.cursor() as cur:

        try:
            cur.execute("""
                SELECT User_Role FROM Users WHERE ID = %s;
            """, [admin])

            role = cur.fetchone()

            if role[0] != "Admin":
                print("You do not have permission to perform this action.")
                return []
            
            cur.execute("""
                SELECT * FROM Users
                WHERE ID = %s;
            """, [target_user])

            result = cur.fetchone()

            if not result:
                print("User with not found.")
                return ()
            
            return result
            
        except Exception as e:
            print("Something went wrong.\n" + str(e) + "\nPlease try again.")
            return ()

def get_all_users(admin):

    with conn.cursor() as cur:

        try:
            cur.execute("""
                SELECT User_Role FROM Users WHERE ID = %s;
            """, [admin])

            role = cur.fetchone()

            if role[0] != "Admin":
                print("You do not have permission to perform this action.")
                return []
            
            cur.execute("""
                SELECT * FROM Users;
            """)

            users = cur.fetchall()
            return users
        
        except Exception as e:
            print("Something went wrong.\n" + str(e) + "\nPlease try again.")
            return []

def edit_user(admin, new_info):

    with conn.cursor() as cur:

        try:
            cur.execute("""
                SELECT User_Role FROM Users WHERE ID = %s;
            """, [admin])

            role = cur.fetchone()

            if role[0] != "Admin":
                print("You do not have permission to perform this action.")
                return False
            
            id = new_info["ID"]

            cur.execute("""
                UPDATE Users
                SET User_Role = %s,
                    User_Name = %s,
                    Email = %s,
                    User_Password = %s
                WHERE ID = %s;
            """, [new_info["User_Role"], new_info["User_Name"], new_info["Email"], new_info["User_Password"], id])

            conn.commit()
            return True
        
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            print("A user with this username or email already exists. Please try again.")
            return False
        except psycopg2.errors.CheckViolation as e:
            conn.rollback()
            print("Invalid password or email: " + e.pgerror + "\nPlease try again.")
            return False
        except psycopg2.errors.StringDataRightTruncation as e:
            conn.rollback()
            print("Field too long. " + e.pgerror + "\nPlease try again.")
            return False
        except Exception as e:
            conn.rollback()
            print("Something went wrong.\n" + str(e) + "\nPlease try again.")
            return False

def delete_user(admin, target_user):

    with conn.cursor() as cur:

        try:
            cur.execute("""
                SELECT User_Role FROM Users WHERE ID = %s;
            """, [admin])

            role = cur.fetchone()

            cur.execute("""
                SELECT User_Name FROM Users WHERE ID = %s;
            """, [target_user])

            target_info = cur.fetchone()

            if role[0] != "Admin":
                print("You do not have permission to perform this action.")
                return False
            elif not target_info:
                print("User not found.")
                return False
            
            cur.execute("""
                DELETE FROM Users WHERE ID = %s;
            """, [target_user])

            conn.commit()

            print("User " + target_info[0] + " and all their related information deleted.")
            return True
        
        except Exception as e:
            conn.rollback()
            print("Something went wrong.\n" + str(e) + "\nPlease try again.")
            return False

def add_document(curator, file_path):

    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT User_Role FROM Users WHERE ID = %s;
            """, [curator])

            curator_info = cur.fetchone()

            if curator_info[0] == "EndUser":
                print("You do not have permission to perform this action.")
                return False

            file_type = os.path.splitext(file_path)[1].lower()
            if file_type == ".jsonl":
                chunks = chunk.chunk_jsonl_file(file_path)
            elif file_type == ".txt":
                chunks = chunk.chunk_txt_file(file_path)
            else:
                print("Unsupported document type (jsonl, txt only). Please try again.")
                return
            
            first_chunk = next(chunks)
            chunks = chain([first_chunk], chunks)
            
            file_name = os.path.basename(file_path)
            cur.execute("""
                INSERT INTO Document (Title, Doc_Type, Added_By) 
                VALUES (%s, %s, %s)
                RETURNING ID;
            """, [file_name, file_type[1:], curator])
            new_id = cur.fetchone()[0]

            for c in chunks:
                e = embedding.create_embedding(c)
                cur.execute("""
                    INSERT INTO Chunk_Embeddings (Document_ID, Chunk_Text, Embedding_Mini, Embedding_QA, Embedding_MPNET)
                    VALUES (%s, %s, %s, %s, %s);
                """, [new_id, c, e["mini"], e["qa"], e["mpnet"]])

            cur.execute("""
                UPDATE Document
                SET Processed = True
                WHERE ID = %s;
            """, [new_id])

            conn.commit()
            print("Added " + file_name + " to database.")
            return True
        
        except StopIteration:
            print("Empty file. Document not added.")
            return False
        except Exception as e:
            conn.rollback()
            print("Something went wrong. " + str(e))
            return False

def retrieve_all_documents():
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT Document.ID, Title, Doc_Type, User_Name
                FROM Document JOIN Users ON Added_By = Users.ID
                ORDER BY Document.ID;
            """)

            docs = cur.fetchall()
            return docs

        except Exception as e:
            conn.rollback()
            print("Something went wrong. " + str(e))
            return None
        
def retrieve_user_documents(user):

    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT ID, Title, Doc_Type
                FROM Document 
                WHERE Added_By = %s
                ORDER BY ID;
            """, [user])

            return cur.fetchall()
        
        except Exception as e:
            conn.rollback()
            print("Something went wrong. " + str(e))
            return None

def remove_document(curator, target_doc):
    
    with conn.cursor() as cur:

        try:
            cur.execute("""
                SELECT User_Role FROM Users WHERE ID = %s;
            """, [curator])

            curator_info = cur.fetchone()

            cur.execute("""
                SELECT Added_By FROM Document WHERE ID = %s;
            """, [target_doc])

            doc_info = cur.fetchone()

            if curator_info[0] == "EndUser":
                print("You do not have permission to perform this action.")
                return False
            
            elif not doc_info:
                print("Document not found.")
                return False
            
            elif doc_info[0] != curator and curator_info[0] != "Admin":
                print("You do not have permission to delete this document.")
                return False
            
            cur.execute("""
                DELETE FROM Document
                WHERE ID = %s;
            """, [target_doc])

            conn.commit()
            return True
        
        except Exception:
            conn.rollback()
            print("Something went wrong. Please try again.")
            return False

def make_query(user, query, k):
    
    with conn.cursor() as cur:
        try:
            cur.execute("""
                INSERT INTO QueryLog (User_ID, Query_Text)
                VALUES (%s, %s)
                RETURNING Query_Time;
            """, [user, query])

            query_time = cur.fetchone()[0]

            query_embeddings = embedding.create_embedding(query)

            cur.execute("""
                SELECT Document_ID, Title, Chunk_Text, 
                    (0.2 * (Embedding_Mini <=> %s::vector) +
                    0.5 * (Embedding_QA <=> %s::vector) +
                    0.3 * (Embedding_MPNET <=> %s::vector)
                    ) AS Distance 
                FROM Chunk_Embeddings
                JOIN Document ON Document.ID = Chunk_Embeddings.Document_ID
                ORDER BY Distance
                LIMIT %s;
            """, [query_embeddings["mini"], query_embeddings["qa"], query_embeddings["mpnet"], k])

            top_k = cur.fetchall()

            retrieved_docs_ids = set()
            retrieved_doc_titles = []
            retrieved_chunks = []
            for r in top_k:
                retrieved_docs_ids.add(r[0])
                retrieved_doc_titles.append(r[1])
                retrieved_chunks.append(r[2])

            values = [(user, query_time, doc_id) for doc_id in retrieved_docs_ids]
            execute_values(cur, """
                INSERT INTO Retrieved_Docs (User_ID, Query_Time, Doc_ID)
                VALUES %s;
            """, values)
            
            conn.commit()
            return retrieved_doc_titles, retrieved_chunks
        
        except Exception as e:
            conn.rollback()
            print("Something went wrong. " + str(e) + "\n Please try again.")
            return [], []
    
def close_db():
    conn.commit()
    conn.close()