import system_func

if __name__  == "__main__":

    while True:
        system_func.startup_menu()
        system_func.define_menu()

        while system_func.USER_INFO:
            system_func.menu()