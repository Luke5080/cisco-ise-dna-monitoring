'''
Script to create SQLite DB
Uses ISE FailureReasons API to grab all failure IDs, codes, causes, resolutions
and populates DB with them for future reference by main script
'''

import sqlite3
import json
import ast
import os
from sqlite3 import Error
import requests
import xmltodict
from cryptography.fernet import Fernet


WORKING_DIR = os.getcwd()

requests.packages.urllib3.disable_warnings()

def decrypt_ise() -> str:
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

    # Hold appropiate info in variables
    configured_ise_url = decrypted_data[0]
    configured_ise_user = decrypted_data[1]
    configured_ise_pwd = decrypted_data[2]


    return configured_ise_url, configured_ise_user, configured_ise_pwd

def db_setup(db_file: str):
    """function to set up sqlite3 db"""
    try:
        #Establish connection to DB
        conn = sqlite3.connect(db_file)

        #Create cursor    
        c = conn.cursor()

        #Create table
        c.execute(""" CREATE TABLE IF NOT EXISTS failures(id integer NOT NULL, code text DEFAULT 'empty', cause text DEFAULT 'empty', resolution text DEFAULT 'empty')""")

        #Enter sample data
        c.execute(""" INSERT INTO failures(id,code,cause,resolution) VALUES(1, 'test', 'test', 'test')""")

        #Commit change
        conn.commit()

        # View results from select all 
        c.execute("SELECT * FROM failures")

        check_works = c.fetchall()

        print(check_works)

        # Close connecion + cursor
        c.close()
        conn.close()

        print("\nDatabase Connection + Table created succesfully")

    except Error as e:
        print(e)
    
def resolve(url: str, uname: str, pwd:str) -> list:
    """function making FailureReasons API"""
    all_failures = []

    api_url = f"{url}/admin/API/mnt/FailureReasons"

    api_headers = {
        'accept':'application/xml'
    }

    query_resp = requests.get(api_url, headers=api_headers, auth=(uname,pwd), verify=False)

    dict_data = xmltodict.parse(query_resp.content)

    json_format = json.dumps(dict_data, indent=4)

    res = json.loads(json_format)
    
    all_ids = res["failureReasonList"]["failureReason"]

    attributes = ["@id", "code", "cause", "resolution"]

    for key in all_ids:
        att = []
        for attribute in attributes:
            try:
                att.append(key[attribute])
            except KeyError:
                pass
        all_failures.append(att)

    return all_failures

def db_populate(db_file: str, data: list, short_data:list):
    """function to populate DB with data extracted from FailureReasons API"""

    conn = sqlite3.connect(db_file)

    c = conn.cursor()

    c.executemany('''INSERT INTO failures(id,code,cause,resolution) VALUES (?, ?, ?, ?)''', data)

    c.executemany('''INSERT INTO failures(id,code,cause) VALUES (?, ?, ?)''', short_data)

    conn.commit()

    c.close()
    conn.close()

def main():
    """main func"""
    db_location  = f"{WORKING_DIR}/failure_db"

    url, uname, pwd = decrypt_ise()
    
    datalist = resolve(url, uname,pwd)
    
    data = [tuple(value) for value in datalist]

    short_data = [value for value in data if len(value) == 3]

    data = [value for value in data if len(value) != 3]
    
    db_setup(db_location)

    db_populate(db_location, data, short_data)

    conn = sqlite3.connect(db_location)

    #Create cursor    
    c = conn.cursor()
    c.execute("SELECT * FROM failures")

    check_works = c.fetchall()

    print(check_works)

    # Close connecion + cursor
    c.close()
    conn.close()
    print("DATA ENTRIES IN FAILURE_DB")

main()