import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    dbname = "text_embeddings",
    user = "postgres",
    password = os.getenv("DB_PASSWORD"),
    host = "localhost",
    port = 55432
)

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
                # parse and chunk json file like chunk.py
                pass
            elif file_type == ".txt":
                # chunk regular text file
                pass

            return True

        except Exception as e:
            return False
        

        