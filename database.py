import psycopg2
from dotenv import load_dotenv
import os
import chunk
import embedding

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
                Create Table If Not Exists Users (
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
                Create Table If Not Exists Document (
                    ID Serial Not NULL Primary Key,
                    Title varchar(80) Not NULL,
                    Doc_Type varchar(20) Not NULL,
                    Added_Time Timestamp Default now() Not NULL,
                    Processed Boolean Default False Not NULL, 
                    Added_By Int Not NULL,

                    Foreign Key (Added_By) References Users(ID)
                );
            """)

            cur.execute("""
                Create Table If Not Exists QueryLog (
                    User_ID Int Not NULL,
                    Query_Time Timestamp Default Now() Not NULL,
                    Query_Text Text Not NULL,

                    Foreign Key (User_ID) References Users(ID),
                    Primary Key(User_ID, Query_Time)
                );
            """)

            cur.execute("""
                Create Table If Not Exists Retrieved_Docs (
                    User_ID Int Not NULL,
                    Query_Time Timestamp Not NULL,
                    Doc_ID Int Not NULL,
                    
                    Foreign Key (User_ID, Query_Time) References QueryLog(User_ID, Query_Time),
                    Foreign Key (Doc_ID) References Document(ID),
                    Primary Key(User_ID, Query_Time, Doc_ID)
                );
            """)

            cur.execute("""
                Create Table If Not Exists Chunk_Embeddings (
                    ID Serial Primary Key,
                    Document_ID Int Not NULL,
                    text Text NOT NULL,
                    embedding_mini vector(384),
                    embedding_qa vector(384),
                    embedding_mpnet vector(768),

                    Foreign Key (Document_ID) References Document(ID)
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
            SELECT User_Role, User_Name FROM Users
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
                SELECT User_Role from Users WHERE User_Name = %s;
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
                SELECT User_Role from Users WHERE User_Name = %s;
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
                SELECT User_Role from Users WHERE User_Name = %s;
            """, [curator])


            role = cur.fetchone()
            if role[0] != "Curator":
                print("You do not have permission to perform this action.")
                return False

            file_type = os.path.splitext(document_name)[1].lower()
            if file_type == ".jsonl":
                chunks = chunk.load_jsonl_file(document_name)
                pass
            elif file_type == ".txt":
                chunks = chunk.load_txt_file(document_name)
                pass
            else:
                print("Unsupported document type (jsonl, txt only). Please try again.")
                return
            
            embeddings = embedding.create_embedding(chunks)
            
            cur.execute("""
                INSERT INTO Document (Title, Doc_Type, Source, Added_By) 
                VALUES (%s, %s, %s, %s);
            """, [document_name, file_type[1:], ])
            return True

        except Exception as e:
            return False
        

        