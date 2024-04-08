'''
Script to gather infomration to be used in the mainscript
Information gathered from user from this script is the ISE\DNA
URL, and the system user accounts/passwords needed to make the 
API calls
'''

import os
import getpass
import sys
import validators

working_dir = os.getcwd()

def config_env() -> list:
    """Function to gather information for environment configuration"""
    
    if os.path.isfile("env_config.txt"):
        print("Environment already configured")
        print("Would you like to create a new environment? (doing so will remove current environment) ")

        while True:
            try:
                create_new_env = input(">>> (y/n) ")

                if create_new_env.lower() == "y" or create_new_env.lower() == "n":
                    break
                else:
                    print("Please enter a valid choice")

            except ValueError:
                print("Please enter a valid choice")
                

        if create_new_env.lower() == "y":
            current_config = f"{working_dir}/env_config.txt"
            current_key = f"{working_dir}/mykey.key"
            os.remove(current_config)
            os.remove(current_key)
        
        else:
            sys.exit()

    print("="*23, "\nConfiguring Environment")

    print("Step 1: Configuring ISE Environment")

    print("\nWhat is the URL to the primary ISE node to which the script will retrieve data from?")

    while True:
        ise_url = str(input(">>> "))
        ise_valid = validators.url(ise_url)

        if ise_valid:
            break
        else:
            print("URL INVALID.")
    try:
        ise_url = ise_url.split("/admin")

        ise_url.pop(1)

        ise_url = ise_url[0]

    except IndexError:
        pass

    if ise_url.endswith("/"):
        ise_url = ise_url.rstrip("/")
    
    print("Which ISE system account will we be using to make API calls to ISE?")
    
    ise_acc_uname = str(input("Enter account username: "))

    ise_acc_pwd = getpass.getpass("Enter account password: ")
   
    print("Step 2: Configuring DNA Center Environment")
    print("\nWhat is the URL to the Cisco DNA Center to which the script will retrieve data from?")

    while True:
        dnac_url = str(input(">>> "))
        dnac_valid = validators.url(dnac_url)

        if dnac_valid:
            break
        else:
            print("URL INVALID.")

    if dnac_url.endswith("/"):
        dnac_url = dnac_url.rstrip("/")
    
    print("Which DNA system account will we be using to make API calls to DNA?")
    
    dna_acc_uname = str(input("Enter account username: "))

    dna_acc_pwd = getpass.getpass("Enter account password: ")

    info_list = [ise_url, ise_acc_uname, ise_acc_pwd, dnac_url, dna_acc_uname, dna_acc_pwd]

    info_desc = [
        "ISE URL", 
        "ISE Account Username", 
        "ISE Account Password", 
        "DNAC URL",
        "DNA Account Username", 
        "DNA Account Password"]
    
    while True:
        print("\nVALIDATE INFORMATION BEFORE CONTINUING:")

        print(f"ISE URL: {info_list[0]}\nISE ACCOUNT: {info_list[1]}\nISE PASSWORD: {info_list[2]}")
        print(f"DNAC URL: {info_list[3]}\nDNA ACCOUNT: {info_list[4]}\nDNA PASSWORD: {info_list[5]}")

        print("\nEdit info?")

        while True:
            try:
                edit_choice = input(">>> (enter y/n) ")

                if edit_choice.lower() == "y" or edit_choice.lower() == "n":
                    break
                else:
                    print("Please enter a valid option")

            except ValueError:
                print("Please enter a valid option")

        if edit_choice == "y":
            print("Which section of information would you like to edit?")

            for value, desc in enumerate(info_desc):
                print(f"{value+1}: {desc}")
            
            while True:
                choice_options = list(range(0,7))

                try:
                    edit_choice = int(input(">>> (enter option 1-6 or 0 to discontinue) "))

                    if edit_choice not in choice_options:
                        print("Invalid Choice")

                    elif edit_choice in choice_options:
                        break

                except ValueError:
                    print("Invalid Choice")
                
            match edit_choice:

                case 0:
                    print("Finsihed Configuring Environment")

                case 1:
                    print("\nWhat is the URL to the primary ISE node to which the script will retrieve data from?")

                    while True:
                        new_ise_url = input(">>> ")
                        new_ise_valid = validators.url(new_ise_url)

                        if new_ise_valid:
                            break
                        else:
                            print("URL INVALID.")
                        try:
                            ise_url = ise_url.split("/admin")

                            ise_url.pop(1)

                            ise_url = ise_url[0]

                        except IndexError:
                            pass

                        if ise_url.endswith("/"):
                            ise_url = ise_url.rstrip("/")

                    info_list[0] = new_ise_url
                
                case 2:
                    print("Which ISE system account will we be using to make API calls to ISE?")
                    new_ise_uname = str(input("Enter account username: "))

                    info_list[1] = new_ise_uname

                case 3:
                    print("What is the password for the ISE system account?")
                    new_ise_pwd = getpass.getpass("Enter account password: ")

                    info_list[2] = new_ise_pwd

                case 4:
                    print("\nWhat is the URL to the Cisco DNA Center to which the script will retrieve data from?")

                    while True:
                        new_dna_url = input(">>> ")
                        new_dna_valid = validators.url(new_dna_url)

                        if new_dna_valid:
                            break
                        else:
                            print("URL INVALID")
                            
                    if dnac_url.endswith("/"):
                        dnac_url = dnac_url.rstrip("/")

                    info_list[3] = new_dna_url

                case 5:
                    print("Which DNA system account will we be using to make API calls to DNA?")
                    new_dnac_uname = str(input("Enter account username: "))

                    info_list[4] = new_dnac_uname

                case 6:
                    print("What is the password for the DNA Account")
                    new_dnac_pwd = getpass.getpass("Enter account password: ")

                    info_list[5] = new_dnac_pwd
                
                case _:
                    print("Invalid option")

        else:
            print("Finished Configuring Environment")
            break

    return info_list





