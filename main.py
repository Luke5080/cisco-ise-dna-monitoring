'''
Script for connectivity debugging for environments
using Cisco ISE and DNAC. Script flow works as follows:
1. First obtain SSO for user with connectivity issues
2. Then check ISE for all active sessions with the SSO
3. Extract all MACs from ISE with the associated SSO
4. Look through data and look for possible issues
5. If possible issue is found -> reference the failure DB and return
code, cause, resolution
6. If user connection is wireless -> check possible issues on DNAC
Author: Luke Marshall
'''
import sys
import re
import os
import sqlite3
import asyncio
import json
import time
import string
import ast
import random
from datetime import datetime
import aiohttp
import requests
from requests.auth import HTTPBasicAuth
import xmltodict
import macaddress
from cryptography.fernet import Fernet

working_dir = os.getcwd()
config_file = f"{working_dir}/env_config.txt"

# Check if env_config.txt file exists.. if it doesn't
# exit the script and prompt user to rebuild env

check_config_exists = os.path.exists(config_file)

if not check_config_exists:
    print("ERROR: env_config.txt file not found.")
    print("Please run builder.py -c to create a new environment")
    sys.exit()

# Open the mykey.key file and hold the encryption key
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

configured_ise_url = decrypted_data[0]
configured_ise_user = decrypted_data[1]
configured_ise_pwd = decrypted_data[2]

configured_dna_url = decrypted_data[3]
configured_dna_user = decrypted_data[4]
configured_dna_pwd = decrypted_data[5]

# Suppress warnings spat back by requests package
requests.packages.urllib3.disable_warnings()

DNAC_BASE = configured_dna_url

ISE_BASE = f"{configured_ise_url}/admin/API/mnt"

DB_PATH = f"{working_dir}/failure_db"

class IseApiController:
    """Class to create an ISE object and to call functions on that object"""

    def __init__(self, iseuser, isepass):
        self.iseuser = iseuser
        self.isepass = isepass
    
    async def get_active_sessions(self) -> dict:
        """Function to grab all active sessions on Ise"""

        api_url = f"{ISE_BASE}/Session/ActiveList"
        api_headers = {
            "accept":"application/xml"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=api_headers, auth=aiohttp.BasicAuth(self.iseuser, self.isepass), ssl=False) as response:

                try:
                    response.raise_for_status()

                    content = await response.text()

                except aiohttp.ClientResponseError as err:
                    sys.exit("Could not fulfill request. Error Code 200")
            
                dict_data = xmltodict.parse(content)

                json_format = json.dumps(dict_data)

                res = json.loads(json_format)

        return res

    async def check_macs_in_session(self, all_session: dict, sso: str) -> list:
        """Function to grab MACs associated with SSO given"""

        mac_list = []

        for element in all_session["activeList"]["activeSession"]:
            for key, value in element.items():
                if key == 'user_name' and value == sso:
                    mac_list.append(element["calling_station_id"])

        ## calling-station-id is not always a MAC address, handle it here
        ## and remove it from mac_list before being processed further
        for mac in mac_list:
            try:
                macaddress.MAC(mac)

            except ValueError:
                mac_list.remove(mac)

        
        return mac_list 

    async def get_session_info(self, mac:str, session) -> dict:
        """
        Function to grab session info for each mac associated with the given SSO
        Checks if there is failures for each record for the MAC
        if yes, query failure_db for code, cause, resolution
        also extract important info such as timestamp for each session, posture,
        connection type, authentication method, authorisation policy, authentication_policy,
        endpoint profile. Each session for a given MAC is indexed in the dictionary with 
        the last 4 characters of the timestamp as a session id.
        """

        api_url = f"{ISE_BASE}/AuthStatus/MACAddress/{mac}/86400/0/All"

        api_headers = {
            'accept':'application/xml'
        }

        data_found = {}
        
        async with session.get(api_url, headers=api_headers, auth=aiohttp.BasicAuth(self.iseuser, self.isepass), ssl=False) as query_resp:

            try:
                query_resp.raise_for_status()
                content = await query_resp.text()

            except aiohttp.ClientResponse as err:
                print("Could not fulfill request. Error Code 100")
                return data_found
            
        dict_data = xmltodict.parse(content)

        json_format = json.dumps(dict_data)

        res = json.loads(json_format)
        
        if res["authStatusOutputList"]["authStatusList"]["authStatusElements"]:
            
            for element in res["authStatusOutputList"]["authStatusList"]["authStatusElements"]:
                
                failure_list = []

                try:
                    post_status = element["posture_status"]

                except KeyError:
                    post_status = "null"

                except TypeError:
                    post_status = "null"

                try:
                    identity_group = element["identity_group"]

                except KeyError:
                    identity_group = "null"
                
                except TypeError:
                    identity_group = "null"

                try:
                    auth_method = element["authentication_method"]

                except KeyError:
                    auth_method = "null"

                except TypeError:
                    auth_method = "null"

                try:
                    timestamp_one = element["acs_timestamp"]

                except KeyError:
                    timestamp_one = "null"

                except TypeError:
                    timestamp_one = "null"

                if timestamp_one != "null":
                    timestamp_two = timestamp_one.replace("T","  ")

                try:
                    nac_compliance = element["nac_policy_compliance"]
                
                except KeyError:
                    nac_compliance = "null"

                except TypeError:
                    nac_compliance = "null"

                try:
                    other_attr = element["other_attr_string"]

                except TypeError:
                    other_attr = "null"

                if other_attr != "null":
                    other_attr = other_attr.replace("=",":")

                    other_attr = other_attr.split(":!:")
                
                    for info in other_attr:
                        chk_that = "AuthorizationPolicyMatchedRule:"

                        chk_that_also = "ISEPolicySetName:"

                        if chk_that in info:
                            risation_policy = info.lstrip(chk_that)

                        if chk_that_also in info:
                            tication_policy = info.lstrip(chk_that_also)
                try:
                    fail_check = element["failed"]["#text"]

                except TypeError:
                    fail_check = "null"

                if fail_check == "true":
                    try:
                        fail_details = element["failure_reason"]
                    
                    except KeyError:
                        fail_details = "null"

                    if fail_details != "null":  

                        ## All failure IDs are 5-6 digits long
                        find_id = r'^(\d{5,6})'
                    
                        failure_id = str(re.findall(find_id, fail_details)).strip("[").strip("]").strip("'")

                        conn = sqlite3.connect(DB_PATH)

                        c = conn.cursor()

                        c.execute(f"SELECT code, cause, resolution from failures where id = {failure_id}")

                        for info in c.fetchall():
                            failure_list.append(info)

                        c.close()
                        conn.close()

                if timestamp_one != "null":
                    dict_key = timestamp_one[-4:]

                else:
                    letters = string.ascii_letters

                    digits = string.digits

                    char_set = letters + digits

                    dict_key = ''.join(random.choice(char_set) for i in range(4))
                
                data_found[dict_key] = {}

                if timestamp_one != "null":
                    data_found[dict_key]["timestamp"] = timestamp_two
                else:
                    data_found[dict_key]["timestamp"] = timestamp_one

                data_found[dict_key]["authentication_method"] = auth_method
                data_found[dict_key]["posture_status"] = post_status
                data_found[dict_key]["failures"] = failure_list
                data_found[dict_key]["identity_group"] =  identity_group

                if other_attr != "null":
                    data_found[dict_key]["authorisation_policy"] = risation_policy
                    data_found[dict_key]["authentication_policy"] = tication_policy
                else:
                    data_found[dict_key]["authorisation_policy"] = "null"
                    data_found[dict_key]["authentication_policy"] = "null"

                data_found[dict_key]["nac_compliance"] = nac_compliance

            return data_found

        else:
            pass
        
class DnaApiController():
    """Class to make API calls to DNAC"""

    def __init__(self, d_uname, d_pass):
        self.d_uname = d_uname
        self.d_pass = d_pass
    
    async def get_token(self) -> str:
        """ Function: Get token to be used for DNAC API Calls"""
        
        api = '/dna/system/api/v1/auth/token'

        token = requests.post(
            DNAC_BASE + api,
            auth=HTTPBasicAuth(
            username = self.d_uname,
            password = self.d_pass
            ),
            headers={'content-type': 'application/json'},
            verify=False,
        )

        dna_token = token.json()

        return dna_token["Token"]

    async def client_details(self, token:str, sso:str) -> list:
        """Initial Function to obtain MAC address of device connected to wireless"""

        api = "/dna/intent/api/v1/user-enrichment-details"

        api_url = DNAC_BASE + api

        api_headers = {
            'X-Auth-Token': token,
            'content-type': 'application/json',
            'accept': 'application/json',
            'entity_type': 'network_user_id',
            'entity_value': sso
        }

        wireless_macs = []

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=api_headers, ssl=False) as response:

                try:
                    response.raise_for_status()
                    info_back = await response.json()

                except aiohttp.ClientResponse as err:
                    return wireless_macs
                
        try:
            wireless_mac = info_back[0]["userDetails"]["hostMac"]
            wireless_macs.append(wireless_mac)

        except KeyError:
            pass

        return wireless_macs

    async def client_health(self, token:str, mac:str, session) -> dict:
        """
        Function: API call to get general user info from inputted MAC
        """

        api = '/dna/intent/api/v1/client-detail'
        url = DNAC_BASE + api
        api_headers = {
            'X-Auth-Token': token,
            'content-type': 'application/json',
            'accept': 'application/json'
        }

        async with session.get(url, params={"macAddress": mac}, headers=api_headers, ssl=False) as response:
            try:
                response.raise_for_status()
                info_back = await response.json()

            except aiohttp.ClientResponse as err:
                info_back = ""

        return info_back


    async def client_issues(self, token:str, mac:str, session) -> dict:
        """
        Function: API call to retrieve client issues found on DNAC and return it
        """

        api = "/dna/intent/api/v1/issues"
        
        url = DNAC_BASE + api
        api_headers = {
            'X-Auth-Token': token,
            'content-type': 'application/json',
            'accept': 'application/json'
        }

        async with session.get(url, params={"macAddress":mac}, headers=api_headers, ssl=False) as response:

            try:
                response.raise_for_status()

                content = await response.json()

            except aiohttp.ClientResponseError:
                content = ""

        return content

async def process_ise_data(info_gathered: dict) -> None:
    """Function to process ise data and display
    to end user"""

    for key in info_gathered:
        print(key,"\n","="*20,"\n")

        if len(info_gathered[key]) == 0:
            print("No data found")
            
        else:
            for element in info_gathered[key]:
                
                log_time = info_gathered[key][element]["timestamp"]
                post_stat = info_gathered[key][element]["posture_status"]
                id_group = info_gathered[key][element]["identity_group"]
                ris_policy = info_gathered[key][element]["authorisation_policy"]
                cation_policy = info_gathered[key][element]["authentication_policy"]
                nac_comply = info_gathered[key][element]["nac_compliance"]
            
                if len(info_gathered[key][element]["failures"]) != 0:

                    grab_fail_details = info_gathered[key][element]["failures"][0]

                    grab_details = grab_fail_details[0]
                    
                    print(f"Time: {log_time}")
                    print(f"Posture Status: {post_stat}")
                    print(f"Identity Group: {id_group}")
                    print(f"Authorisation Policy: {ris_policy}")
                    print(f"Authentication Policy: {cation_policy}")
                    print(f"NAC Compliance: {nac_comply}")
                    print(f"Failure code: {grab_details[0]}")
                    print(f"Cause: {grab_details[1]}")
                    print(f"Resolution {grab_details[2]}, \n")
                           
                else:  
                    print(f"Time: {log_time}")
                    print(f"Posture Status: {post_stat}")
                    print(f"Identity Group: {id_group}")
                    print(f"Authorisation Policy: {ris_policy}")
                    print(f"Authentication Policy: {cation_policy}")
                    print(f"NAC Compliance: {nac_comply}")
                    print("No failures found", "\n")

async def process_dna_data(dna_info: dict, issue_desc: dict) -> None:
    """Function to process dna data an display it 
    to end user"""

    dnac_info = {}
    print("INFO GATHERED ON DNAC:")
    for entry, value in dna_info.items():

        print(f"{entry}\n","="*20, "\n")

        if len(dna_info[entry]) == 0:
            dnac_info[entry] = "No data found"
    
        else:
            dna_id = value['detail']['id']
            con_status = value["detail"]["connectionStatus"]
            host_type = value["detail"]["hostType"]
            uid = value["detail"]["userId"]
            dnac_identifier = value["detail"]["identifier"]
            dna_hostname = value["detail"]["hostName"]
            host_os = value["detail"]["hostOs"]
            host_os_ver = value["detail"]["hostVersion"]
            host_stype = value["detail"]["subType"]
            firm_version = value["detail"]["firmwareVersion"]
            dev_vendor = value["detail"]["deviceVendor"]

            last_update = value["detail"]["lastUpdated"]

            last_update = last_update / 1000
            last_update = datetime.fromtimestamp(last_update)

            last_update = str(last_update)

            health_info = value["detail"]["healthScore"]
            host_mac = value["detail"]["hostMac"]
            host_ipv4 = value["detail"]["hostIpV4"]
            auth_type = value["detail"]["authType"]
            ssid = value["detail"]["ssid"]
            region = value["detail"]["location"]
            client_conn_device = value["detail"]["clientConnection"]
            issues_user = value["detail"]["issueCount"]
            try:
                auth_done_time = value["detail"]["authDoneTime"]

            except KeyError:
                auth_done_time = "null"

            onboard_time = value["detail"]["onboardingTime"]

            onboard_time = onboard_time / 1000

            onboard_time =  datetime.fromtimestamp(onboard_time)

            onboard_time = str(onboard_time)

            try:
                con_info = value["detail"]["connectionInfo"]
            except KeyError:
                con_info = "null"
   
            print(f"Identifier on DNA: {dna_id}")
            print(f"Connection Status: {con_status}")
            print(f"Host Type: {host_type}")
            print(f"User ID: {uid}")
            print(f"Identifier: {dnac_identifier}")
            print(f"Device Hostname: {dna_hostname}")
            print("Device Details:\n","="*10)
            print(f"Host OS: {host_os}, Version: {host_os_ver}")
            print(f"Host SubType: {host_stype}, Firmware Version: {firm_version}")
            print(f"Device Vendor: {dev_vendor}\n","="*10)
            print(f"Last Updated: {last_update}")

            print("Health Info:\n", "="*10)
            for info in health_info:
                for key, value in info.items():
                    print(f"{key}: {value}")
            print("="*10)

            print(f"Host MAC Address: {host_mac}")
            print(f"Host IPv4 Address: {host_ipv4}")
            print(f"Authentication Type: {auth_type}")
            print(f"SSID: {ssid}")
            print(f"Region: {region}")
            print(f"Client Connected Device: {client_conn_device}")
            print(f"Detected Issues: {issues_user}")
            print(f"Authentication Done Time: {auth_done_time}")
            print(f"Onboarding Time: {onboard_time}")
            print(f"Connection Info: {con_info}\n")
            
    print("Issues found on DNAC:")
    for key, value in issue_desc.items():
        print(f"{key}\n","="*20, "\n")

        if len(issue_desc[key]) != 0:

            version = value["version"]
            total_c = value["totalCount"]
            resp = value["response"]

            if len(resp) != 0:
                resp = str(resp)

                resp = resp.split(",")
                
                for index, val in enumerate(resp):
                    if val.startswith(" 'last_occurence_time'"):

                        last_occ = val

                        last_occ_index = index

                last_occ = last_occ.lstrip(" 'last_occurence_time':")

                last_occ = last_occ.strip("}").strip("]").strip("}")

                last_occ = int(last_occ)

                last_occ = last_occ / 1000

                last_occ_utc = datetime.fromtimestamp(last_occ)

                last_occ_utc = str(last_occ_utc)

                resp.pop(last_occ_index)
                
                resp.append(f"last_occurence_time: {last_occ_utc}")

                resp.pop(3)

            print(f"Version: {version}")
            print(f"Total Count: {total_c}")
            print("Details:")
    

            for item in resp:
                if type(item) == str:
                    item = item.strip(" ").strip("[").strip("{")
                print(item)

def help_user() -> None:
    banner = "HOW TO USE THIS SCRIPT"
    print(banner)
    print("="*len(banner))
    print("Please input a username as an argument to the script.")
    print("e.g. python3 main.py foobar")

async def main():
    """main function"""

    start = time.time()

    if len(sys.argv) == 1:
        help_user()
        sys.exit()

    else:
        user_sso = sys.argv[1]

    # Create ISE object
    ise_api = IseApiController(configured_ise_user, configured_ise_pwd)

    # Create DNA object
    dna_api_ob = DnaApiController(configured_dna_user, configured_dna_pwd)

    t1 = asyncio.create_task(ise_api.get_active_sessions())
    t2 = asyncio.create_task(dna_api_ob.get_token())

    await asyncio.gather(t1, t2)

    active_list = await t1
    token_dna = await t2
    
    # Retrieve all macs related to SSO
    t3 = asyncio.create_task(ise_api.check_macs_in_session(active_list, user_sso))
    t4 = asyncio.create_task(dna_api_ob.client_details(token_dna, user_sso))

    await asyncio.gather(t3, t4)

    macs_to_check = await t3
    wireless_mac_check = await t4

    data_gathered = {}

    ## Check each MACs for failures, retrieve posture status of each, etc

    async with aiohttp.ClientSession() as session:
        tasks = []
        for mac in macs_to_check:
            task = asyncio.create_task(ise_api.get_session_info(mac, session))
            tasks.append(task)

        data = await asyncio.gather(*tasks)

    for i, mac in enumerate(macs_to_check):
        data_gathered[mac] = data[i]

    if len(wireless_mac_check) != 0:

        t4 = asyncio.create_task(process_ise_data(data_gathered))

        async with aiohttp.ClientSession() as session:
            tasks = []

            for mac in wireless_mac_check:
                task = asyncio.create_task(dna_api_ob.client_health(token_dna, mac, session))
                tasks.append(task)

            dna_data = await asyncio.gather(*tasks)

        dna_health = {}

        for i, mac in enumerate(wireless_mac_check):
            dna_health[mac] = dna_data[i]

        async with aiohttp.ClientSession() as session:
            tasks = []

            for mac in wireless_mac_check:
                task = asyncio.create_task(dna_api_ob.client_issues(token_dna, mac, session))
                tasks.append(task)

            dna_issues_data = await asyncio.gather(*tasks)

        dna_issues = {}

        for i, mac in enumerate(wireless_mac_check):
            dna_issues[mac] = dna_issues_data[i]
    
        t7 = asyncio.create_task(process_dna_data(dna_health, dna_issues))

        dnac_back = await t7

        api_out = {}
        
        api_out["ise_information"] = data_gathered

        api_out["dnac_information"] = dnac_back
    
    else:
        t4 = asyncio.create_task(process_ise_data(data_gathered))

        await asyncio.gather(t4)
        
        api_out = {}
        
        api_out["ise_information"] = data_gathered

    api_out = json.dumps(api_out, indent=4)

    end = time.time()
    total = end - start
    print(f"Total time taken: {total:.2f}")
    
    ## api_out can be used as an API response for whatever purpose
    ## e.g. Flask application
    return api_out

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
