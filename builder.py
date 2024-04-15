'''
Script to build the user environment using data gathered from 
config_env function
'''

import sys
import ast
import os
import getpass
import validators
from cryptography.fernet import Fernet
from config import config_env

def help_user() -> None:
    """Function to notify user how to use this script"""

    print("BUILDER.PY")
    print("This is used as a first point of call to configure your environment")
    print("Use the -c flag to configure your environment")
    print("Use the -e flag to edit an existing environment")


def main_build() -> list:
    """Main function to handle environment configuration"""

    if len(sys.argv) == 1:
        help_user()

    else:
        intial_user_choice = sys.argv[1]

        match intial_user_choice:
            
            case "-c":
                user_data = config_env()

                # Convert user data list to string and write to env_config.txt
                user_data = str(user_data)

                with open("env_config.txt", "w") as f:
                    f.write(user_data)

                # Generate a new key
                key = Fernet.generate_key()

                # Write new key to file mykey.key
                with open("mykey.key", "wb") as mykey:
                    mykey.write(key)

                # Open the mykey.key file and hold the encryption key
                with open("mykey.key", "rb") as used_key:
                    inv_key = used_key.read()

                f = Fernet(inv_key)

                # Open env_config.txt and load the data in a variable
                with open("env_config.txt", "rb") as unencrypt_config:
                    data = unencrypt_config.read()

                # Encrypt the data with the key
                encrypted_data = f.encrypt(data)

                # Overwrite env_config.txt with encrypted data
                with open("env_config.txt", "wb") as encrypted_config:
                    encrypted_config.write(encrypted_data)

            case "-e":
                current_dir = os.getcwd()

                config_path = f"{current_dir}/env_config.txt"

                config_file_exists = os.path.isfile(config_path)

                if not config_file_exists:
                    print("No environment configuration file available to edit.")
                    print("Please run builder.py -c to create one")
                    sys.exit()

                print("Edit Environment Information:")

                with open("mykey.key", "rb") as used_key:
                    inv_key = used_key.read()

                f = Fernet(inv_key)

                # Open env_config.txt and load the data in a variable
                with open("env_config.txt", "rb") as encrypt_config:
                    encrypted_data = encrypt_config.read()

                # Decrypt the data with the key and hold it as a list
                decrypted_data = f.decrypt(encrypted_data)

                decrypted_data = decrypted_data.decode('utf-8')

                decrypted_data = ast.literal_eval(decrypted_data)

                print(f"ISE URL: {decrypted_data[0]}\nISE ACCOUNT: {decrypted_data[1]}\nISE PASSWORD: {decrypted_data[2]}")
                print(f"DNAC URL: {decrypted_data[3]}\nDNA ACCOUNT: {decrypted_data[4]}\nDNA PASSWORD: {decrypted_data[5]}")

                info_desc = [
                    "ISE URL", 
                    "ISE Account Username", 
                    "ISE Account Password", 
                    "DNAC URL",
                    "DNA Account Username", 
                    "DNA Account Password"]
                
                print("Which section of information would you like to edit?\n")

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
                        print("Finished Configuring Environment")

                    case 1:
                        print("\nWhat is the URL to the primary ISE node to which the script will retrieve data from?")
                        print("NOTE: YOU ONLY NEED TO PROVIDE THE URL. DO NOT APPEND /ADMIN/API/MNT ETC.")
                        
                        while True:
                            new_ise_url = input(">>> ")
                            new_ise_valid = validators.url(new_ise_url)

                            if new_ise_valid:
                                break
                            else:
                                print("URL INVALID.")

                        decrypted_data[0] = new_ise_url
                    
                    case 2:
                        print("Which ISE system account will we be using to make API calls to ISE?")
                        new_ise_uname = str(input("Enter account username: "))

                        decrypted_data[1] = new_ise_uname

                    case 3:
                        print("What is the password for the ISE system account?")
                        new_ise_pwd = getpass.getpass("Enter account password: ")

                        decrypted_data[2] = new_ise_pwd

                    case 4:
                        print("\nWhat is the URL to the Cisco DNA Center to which the script will retrieve data from?")

                        while True:
                            new_dna_url = input(">>> ")
                            new_dna_valid = validators.url(new_dna_url)

                            if new_dna_valid:
                                break
                            else:
                                print("URL INVALID")

                        decrypted_data[3] = new_dna_url

                    case 5:
                        print("Which DNA system account will we be using to make API calls to DNA?")
                        new_dnac_uname = str(input("Enter account username: "))

                        decrypted_data[4] = new_dnac_uname

                    case 6:
                        print("What is the password for the DNA Account")
                        new_dnac_pwd = getpass.getpass("Enter account password: ")

                        decrypted_data[5] = new_dnac_pwd
                    
                    case _:
                        print("Invalid option")

                if edit_choice != 0:
                    decrypted_data = str(decrypted_data)

                    decrypted_data = decrypted_data.encode('utf-8')

                    encrypted_data_edited = f.encrypt(decrypted_data)

                    with open("env_config.txt","wb") as file:
                        file.write(encrypted_data_edited)
                    
            case "-h":
                help_user()

            case _:
                help_user()

main_build()