import psycopg2
from dotenv import load_dotenv
import os
import chunk
import embedding
from itertools import chain

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
                Create Table If Not Exists public.Users (
                    ID Serial Not NULL Primary Key,
                    User_Role varchar(10) Not NULL,
                    User_Name varchar(20) Unique Not NULL,
                    Email varchar(30) Unique Not NULL,
                    User_Password varchar(15) Not NULL,

                    Check(Email like '_%@_%._%'),
                    Check(User_Role in ('Admin', 'Curator', 'EndUser'))
                );
            """)

            cur.execute("""
                Create Table If Not Exists public.Document (
                    ID Serial Not NULL Primary Key,
                    Title varchar(80) Not NULL,
                    Doc_Type varchar(20) Not NULL,
                    Added_Time Timestamp Default now() Not NULL,
                    Processed Boolean Default False Not NULL, 
                    Added_By Int Not NULL,

                    Foreign Key (Added_By) References Users(ID) ON DELETE CASCADE
                );
            """)

            cur.execute("""
                Create Table If Not Exists public.QueryLog (
                    User_ID Int Not NULL,
                    Query_Time Timestamp Default Now() Not NULL,
                    Query_Text Text Not NULL,

                    Foreign Key (User_ID) References Users(ID) ON DELETE CASCADE,
                    Primary Key(User_ID, Query_Time)
                );
            """)

            cur.execute("""
                Create Table If Not Exists public.Retrieved_Docs (
                    User_ID Int Not NULL,
                    Query_Time Timestamp Not NULL,
                    Doc_ID Int Not NULL,
                    
                    Foreign Key (User_ID, Query_Time) References QueryLog(User_ID, Query_Time),
                    Foreign Key (Doc_ID) References Document(ID),
                    Primary Key(User_ID, Query_Time, Doc_ID)
                );
            """)

            cur.execute("""
                Create Table If Not Exists public.Chunk_Embeddings (
                    ID Serial Primary Key,
                    Document_ID Int Not NULL,
                    text Text NOT NULL,
                    embedding_mini vector(384),
                    embedding_qa vector(384),
                    embedding_mpnet vector(768),

                    Foreign Key (Document_ID) References Document(ID) ON DELETE CASCADE
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
            print("Invalid password or email: " + e.pgerror + "\nPlease try again.")
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
            return ("", "")
        
        return result
    
def get_users(admin):

    with conn.cursor() as cur:

        try:
            cur.execute("""
                SELECT User_Role FROM Users WHERE User_Name = %s;
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
        
def add_document(curator, document_name):

    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT User_Role FROM Users WHERE ID = %s;
            """, [curator])

            curator_info = cur.fetchone()

            if curator_info[0] != "Curator":
                print("You do not have permission to perform this action.")
                return False

            file_type = os.path.splitext(document_name)[1].lower()
            if file_type == ".jsonl":
                chunks = chunk.load_jsonl_file(document_name)
            elif file_type == ".txt":
                chunks = chunk.load_txt_file(document_name)
            else:
                print("Unsupported document type (jsonl, txt only). Please try again.")
                return
            
            first_chunk = next(chunks)
            chunks = chain([first_chunk], chunks)
            
            cur.execute("""
                INSERT INTO Document (Title, Doc_Type, Source, Added_By) 
                VALUES (%s, %s, %s, %s)
                RETURNING ID;
            """, [document_name, file_type[1:], "user", curator])

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
                SELECT Title, Doc_Type, Added_By 
                FROM Document 
                ORDER BY ID;
            """)

            docs = cur.fetchall()
            return docs

        except Exception as e:
            conn.rollback()
            print("Something went wrong. " + str(e))
            return None
        
def retrieve_own_documents(user):

    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT Title, Doc_Type, Added_By 
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

            if curator_info[0] != "Curator":
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
            print("Something went wrong. Please try again.")
            return False

