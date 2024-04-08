# Cisco ISE and DNA Monitoring  [Unstable/ Still Testing]
![banner](https://shoppaulzizkaphoto.com/cdn/shop/products/Desktop-1.jpg?v=1523412172 "banner")  
### A simple and effective tool to help debug end user connectivity using logs from Cisco ISE and Cisco DNA Center. Currently still testing - not stable. Feel free to experiment with this repository regardless.  

## Installation
1. First, install all necessary package dependencies for the project to run by reading the `requirements.txt` file:  

    `pip3 install -r requirements.txt`  

2. Next, set up your environment for the script to here. In order to do this, you will need the following pieces of information:  
- URL of the Cisco ISE node which the data will be extracted from  
**NOTE: You DO NOT need to appened /admin/API/mnt to the URL**  

- Username of a system account on Cisco ISE (API calls will we be made from this account)    
- Password of the provided Cisco ISE system account  
- URL of your Cisco DNA Center Domain  
- Username of a system account on Cisco DNA (API calls will be made from this account)  
- Password of the provided Cisco DNA system account  

Run the `builder.py` script with the `-c` flag and follow the interactive environment setup:  

`python3 builder.py -c`  

This information will be stored and encrypted in a file called `env_config.txt`.  

At any moment, you can edit the configurations of your environment by running the `builder.py` script with the `-e` flag. Here, you can edit the information you configured in the inital set up with `python3 builder.py -c`. To edit the environment, run:  

`python3 builder.py -e`  
  
3. Next, create the database where all failure ID's, codes, causes and resolutions will be held. Run the `constuct_db.py` script:  

`python3 construct_db.py`

This will have created an SQLite3 database file named `failure_db` which is now present in the repository folder. This will be referenced when `main.py` run and finds a log of a specific user where a failure occurred. The script will refer to `failure_db` to retrieve the code, cause and resolutionof the failure.    

4. Next, run the `main.py` script with a user SSO as an argument to retrieve all logs of a specific user from the past 24 hours. The script first retrieves all active sessions registered on your primary Cisco ISE node, and then finds all mac addresses correlated to the SSO. From there, the script retrieves all logs from the past 24 hours for each mac address related to the given SSO, and outputs this information to the user. If a log for a mac address is found to have a wireless connection type, it will be held, and information regarding that MAC, as well as possible issues found, is pulled from Cisco DNA. Run the `main.py` script as follows:  
`python3 main.py <user sso>`  

For logs found on Cisco ISE, the script will output the information as such:  
```
<MAC ADDRESS>
=============
Timestamp:
Authentication Method:
Posture Status:
Failures: <failure code>
          <failure cause>
          <failure resolution>
Connection Type:
Identity Group:
Authorisation Policy:
Authentication Policy:
NAC Compliance
```
