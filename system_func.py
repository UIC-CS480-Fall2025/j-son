import database as db
import re

USER_INFO = {}
MENU = ""
USER_ACTIONS = []

def startup_menu():
    if not db.initialize_db():
        exit(1)

    global USER_INFO
    
    while True:
        print("=====================================")
        print("       WELCOME TO FANDOM SEARCH      ")
        print("=====================================")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        print("=====================================")
        choice = input("Select an option (1 - 3): ")

        if choice == "1":
            result = login()

            if not result:
                return {}
            
            USER_INFO["Role"] = result[0]
            USER_INFO["User_Name"] = result[1]
            USER_INFO["ID"] = result[2]

            return USER_ACTIONS

        elif choice == "2":
            register()
        elif choice == "3":
            print("Exiting program...")
            exit(1)
        else:
            print("Invalid option. Please try again.")

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
            print("=====================================")
            print(f"           WELCOME {username.strip()} ")
            print("=====================================")
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
                return None
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
                return None

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
                return None
            elif len(password) > 15:
                print("Password too long.")
            else:
                break

        if db.add_user(user_name.strip(), email.strip(), password.strip(), "EndUser"):
            return None
        
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
            file_path = input("Enter the path to the document\n(Enter \"back\" to return): ")

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

    for i, (_, title, doc_type, added_by) in enumerate(results, start=1):
        print(f"{i}.\n - Title: {title}\n - Type: {doc_type}\n - Added By: {added_by}\n")

def get_own_documents():
    global USER_INFO
    print("=====================================")
    print("            YOUR DOCUMENTS           ")
    print("=====================================")

    results = db.retrieve_user_documents(USER_INFO["ID"])
    for i, (_, title, doc_type) in enumerate(results, start=1):
        print(f"{i}.\n - Title: {title}\n - Type: {doc_type}\n")

def remove():
    global USER_INFO
    print("=====================================")
    print("               REMOVE                ")
    print("=====================================")

    if USER_INFO["Role"] == "Curator":
        print("Your Documents:")
        docs = db.retrieve_user_documents(USER_INFO["ID"])

        for i, (_, title, doc_type) in enumerate(docs, start=1):
            print(f"{i}.\n - Title: {title}\n - Type: {doc_type}\n")
    elif USER_INFO["Role"] == "Admin":
        print("All Documents:")
        docs = db.retrieve_all_documents()

        for i, (_, title, doc_type, added_by) in enumerate(docs, start=1):
            print(f"{i}.\n - Title: {title}\n - Type: {doc_type}\n - Added By: {added_by}\n")

    while True:
        while True:
            choice = input(f"Pick Document to Remove (1 - {len(docs)})\n(Enter \"back\" to return): ")

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
                    
                    target_id = docs[choice - 1][0]
                    break   

                except ValueError:
                    print("Please enter a valid number.")

        if db.remove_document(USER_INFO["ID"], target_id):
            return

def get_users():
    global USER_INFO
    print("=====================================")
    print("              ALL USERS              ")
    print("=====================================")

    users = db.get_all_users(USER_INFO["ID"])

    for i, (id, user_role, user_name, email, user_password) in enumerate(users, start=1):
        print(f"{i}.\n - Username: {user_name}\n - User ID: {id}\n - Email: {email}\n - Password: {user_password}\n - Role: {user_role}")
        print("-------------------------------")

def edit_user():
    global USER_INFO
    print("=====================================")
    print("              EDIT USER              ")
    print("=====================================")

    all_users = db.get_all_users(USER_INFO["ID"])

    for i, (id, user_role, user_name, email, user_password) in enumerate(all_users, start=1):
        print(f"{i}.\n - Username: {user_name}\n - User ID: {id}\n - Email: {email}\n - Password: {user_password}\n - Role: {user_role}")
        print("-------------------------------")

    while True:

        target_user = input(f"Pick a User to edit (1 - {len(all_users)})\n(Enter \"back\" to return): ")

        if not target_user:
            print("Field cannot be empty. Please try again.")
        elif target_user.strip().lower() == "back":
                return
        else:
            try:
                target_user = int(target_user)

                if target_user < 1 or target_user > len(all_users):
                    print("Invalid option. Try again.")
                    continue
                
                target_user_info = {
                    "ID" : all_users[target_user - 1][0],
                    "User_Role" : all_users[target_user - 1][1],
                    "User_Name" : all_users[target_user - 1][2],
                    "Email" : all_users[target_user - 1][3],
                    "User_Password" : all_users[target_user - 1][4]
                }

                break   

            except ValueError:
                print("Please enter a valid number.")
    
    print("-------------------------------------")
    print("               EDITING               ")
    print("-------------------------------------")
    print(f"Username: {target_user_info['User_Name']}\n - User ID: {target_user_info['ID']}\n - Email: {target_user_info['Email']}\n - Password: {target_user_info['User_Password']}\n - Role: {target_user_info['User_Role']}")
    print("-------------------------------")
    print("1. Username\n2. Email\n3. Password\n4. Role")

    to_print = ["Username", "Email", "Password", "Role"]
    options = ["User_Name", "Email", "User_Password", "User_Role"]
    while True:

        to_edit = input("Pick one of the above to edit (1 - 4)\n(Enter \"back\" to return): ")
        
        if not to_edit:
            print("Field cannot be empty. Please try again.")
        elif to_edit.strip().lower() == "back":
            return
        else:
            try:
                to_edit = int(to_edit)

                if to_edit < 1 or to_edit > 4:
                    print("Invalid option. Try again.")
                    continue

                to_edit -= 1
                break
            except ValueError:
                print("Please enter a valid number.")

    while True:
        while True:
            new_info = input(f"Enter a new {to_print[to_edit]}\n(Enter \"back\" to return): ")
            
            if not new_info:
                print("Field cannot be empty. Please try again.")
            elif new_info.strip().lower() == "back":
                return
            else:
                target_user_info[options[to_edit]] = new_info
                break

        if db.edit_user(USER_INFO["ID"], target_user_info):
            print(f"{to_print[to_edit]} successfully changed.")
            return

def delete_user():
    global USER_INFO
    print("=====================================")
    print("             DELETE USER             ")
    print("=====================================")

    all_users = db.get_all_users(USER_INFO["ID"])

    for i, (id, user_role, user_name, email, _) in enumerate(all_users, start=1):
        print(f"{i}.\n - Username: {user_name}\n - User ID: {id}\n - Email: {email}\n - Role: {user_role}")
        print("-------------------------------")

    while True:
        while True:
            to_delete = input(f"Pick a user to delete (1 - {len(all_users)})\n(Enter \"back\" to return): ")

            if not to_delete:
                print("Field cannot be empty. Please try again.")
            elif to_delete.strip().lower() == "back":
                return
            else:
                try:
                    to_delete = int(to_delete)

                    if to_delete < 1 or to_delete > len(all_users):
                        print("Invalid option. Try again.")
                        continue

                    target_user = all_users[to_delete - 1][0]
                    break
                except ValueError:
                    print("Please enter a valid number.")

        if db.delete_user(USER_INFO["ID"], target_user):
            return

def define_menu():
    global USER_INFO
    global MENU
    global USER_ACTIONS

    match USER_INFO["Role"]:
        case "EndUser":
            MENU = "1. Make Query\n2. Get All Documents\n3. Logout"
            USER_ACTIONS = [query, get_documents, logout]
        case "Curator":
            MENU = "1. Make Query\n2. Upload Document\n3. Get All Documents\n4. Get Self-Uploaded Documents\n5. Delete Document\n6. Logout"
            USER_ACTIONS = [query, upload, get_documents, get_own_documents, remove, logout]
        case "Admin":
            MENU = "1. Make Query\n2. Upload Document\n3. Get All Documents\n4. Get Self-Uploaded Documents\n5. Delete Document\n6. Get All Users\n7. Edit User\n8. Delete User\n9. Logout"
            USER_ACTIONS = [query, upload, get_documents, get_own_documents, remove, get_users, edit_user, delete_user, logout]

def menu():
    global MENU
    global USER_ACTIONS
    print("=====================================")
    print("                MENU                 ")
    print("=====================================")
    print(MENU)

    while True:
        try:
            choice = int(input(f"Action (1 - {len(USER_ACTIONS)}): "))

            if choice < 1 or choice > len(USER_ACTIONS):
                print("Invalid option. Try again.")
            else:
                return USER_ACTIONS[choice - 1]()
        except ValueError:
            print("Please enter a valid number.")