import database as db
import re

USER_INFO = {
    "Role" : "",
    "User_Name" : "",
    "ID" : -1
}

MENU = ""
USER_ACTIONS = []

def startup_menu():
    while True:
        print("=====================================")
        print("         WELCOME TO QA SYSTEM        ")
        print("=====================================")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        print("=====================================")

        choice = input("Select an option (1-3): ")

        if choice == "1":
            return login()
        elif choice == "2":
            return "register"
        elif choice == "3":
            print("Exiting program...")
            return "exit"

def login():
    print("=====================================")
    print("               LOGIN                 ")
    print("=====================================")

    while True:
        username = input("Enter Username: ")
        if username.strip().lower() == "back":
            return ()
        
        password = input("Enter Password: ")
        if password.strip().lower() == "back":
            return ()

        print("\nAttempting login...\n")
        result = db.check_login(username.strip(), password.strip())
        if result:
            return result

def register():
    print("=====================================")
    print("              REGISTER               ")
    print("=====================================")

    while True:
        while True:
            user_name = input("Username (max: 20 characters): ")

            if not user_name:
                print("Field cannot be empty. Try again.")
            elif user_name.strip().lower() == "back":
                return
            elif len(user_name) > 20:
                print("Username too long.")
            else:
                break
        
        email_pattern =  r"^[^@]+@[^@]+\.[^@]+$"
        while True:
            email = input("Email: ")

            if not email:
                print("Field cannot be empty. Try again.")

            elif email.strip().lower() == "back":
                return

            elif not re.match(email_pattern, email):
                print("Invalid email.")

            elif len(email) > 30:
                print("Email too long.")

            else:
                break

        while True:
            password = input("Password: ")

            if not password:
                print("Field cannot be empty. Try again.")
            elif password.strip().lower() == "back":
                return
            elif len(password) > 15:
                print("Password too long.")
            else:
                break

        if db.add_user(user_name.strip(), email.strip(), password.strip(), "EndUser"):
            return
        

def query():
    global USER_INFO
    print("=====================================")
    print("                QUERY                ")
    print("=====================================")

    while True:
        query_text = input("Query (Enter \"back\" to return): ")

        if not query_text:
            print("Field cannot be empty. Try again.")
        elif query_text.strip().lower() == "back":
            return
        else:
            break
    
    while True:
        k = input("Retrieve Top # (Enter \"back\" to return): ")

        if not k:
            print("Field cannot be empty. Try again.")
        elif k.strip().lower() == "back":
            return
        else:
            try:
                k = int(k)
                break           
            except ValueError:
                print("Please enter a valid number.")

    print("=====================================")
    print(f"           TOP {k} RESULTS          ")
    print("=====================================")
    retrieved_docs, retrieved_chunks = db.make_query(USER_INFO["ID"], query_text, k)
    
    for i, (doc, chunk) in enumerate(zip(retrieved_docs, retrieved_chunks), start=1):
        print(f"{i}. {doc}\n\t{chunk}\n")

    print("=====================================")

def logout():
    db.close_db()
    print("Logging out....")
    exit(1)

def upload():
    global USER_INFO
    print("=====================================")
    print("               UPLOAD                ")
    print("=====================================")

    while True:
        while True:
            file_path = input("Enter the path to the document (Enter \"back\" to return):")

            if not file_path:
                print("Field cannot be empty. Try again.")
            elif file_path.strip().lower() == "back":
                return
            else:
                file_path = file_path.strip()
                break

        if db.add_document(USER_INFO["ID"], file_path):
            return

def get_documents():
    print("=====================================")
    print("               DOCUMENTS             ")
    print("=====================================")

    results = db.retrieve_all_documents()

    for i, (title, doc_type, added_by) in enumerate(results, start=1):
        print(f"{i}.\n - Title: {title}\n - Type: {doc_type}\n - Added By: {added_by}\n")

def get_own_documents():
    global USER_INFO
    print("=====================================")
    print("            YOUR DOCUMENTS           ")
    print("=====================================")

    results = db.retrieve_user_documents(USER_INFO["ID"])

    for i, (title, doc_type) in enumerate(results, start=1):
        print(f"{i}.\n - Title: {title}\n - Type: {doc_type}\n")

def remove():
    global USER_INFO
    print("=====================================")
    print("               REMOVE                ")
    print("=====================================")

    if USER_INFO["Role"] == "Curator":
        print("Your Documents:")
        docs = db.retrieve_user_documents(USER_INFO["ID"])

        for i, (title, doc_type) in enumerate(docs, start=1):
            print(f"{i}.\n - Title: {title}\n - Type: {doc_type}\n")
    elif USER_INFO["Role"] == "Admin":
        print("All Documents:")
        docs = db.retrieve_all_documents()

        for i, (title, doc_type, added_by) in enumerate(docs, start=1):
            print(f"{i}.\n - Title: {title}\n - Type: {doc_type}\n - Added By: {added_by}\n")

    while True:
        while True:
            choice = input(f"Pick Document to Remove (1 - {len(docs)}) (Enter \"back\" to return): ")

            if not choice:
                print("Field cannot be empty. Try again.")
            elif choice.strip().lower() == "back":
                return
            else:
                try:
                    choice = int(choice)

                    if choice < 1 or choice > len(docs):
                        print("Invalid option. Try again.")
                        continue

                    break   

                except ValueError:
                    print("Please enter a valid number.")

        if db.remove_document(USER_INFO["ID"], choice):
            return

def get_users():
    global USER_INFO
    print("=====================================")
    print("              ALL USERS              ")
    print("=====================================")

    users = db.get_all_users(USER_INFO["ID"])

    for (id, user_role, user_name, email, user_password) in users:
        print(f"Username: {user_name}\n - User ID: {id}\n - Email: {email}\n - Password: {user_password}\n - Role: {user_role}")
        print("-------------------------------")

def define_menu():
    global USER_INFO
    global MENU

    match USER_INFO["Role"]:
        case "EndUser":
            MENU = "1. Make Query\n2. Get All Documents\n3. Logout"
        case "Curator":
            MENU = "1. Upload Document\n2. Get All Documents\n3. Get Self-Uploaded Documents\n4. Delete Document\n5. Logout"
        case "Admin":
            MENU = "1. Get All Users\n2. Edit User\n3. Delete User\n4. Logout"

def menu():
    global MENU
    global USER_ACTIONS
    print("=====================================")
    print("                MENU                 ")
    print("=====================================")
    print(MENU)

    while True:
        choice = input(f"Action (1 - {len(USER_ACTIONS)}): ")

        if choice < 1 or choice > len(USER_ACTIONS):
            print("Invalid option. Try again.")
        else:
            return USER_ACTIONS[choice - 1]()