import errno
import requests
import json
import getopt
import yaml
from datetime import date
import time
import os
import logging
import sys
from requests.auth import HTTPBasicAuth

# Used for creating logs
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(filename='logs/appd.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


# Opens yml file
config_file='appd.yml'
log_level=logging.INFO

# Get full command-line arguments
full_cmd_arguments = sys.argv

# Keep all but the first
argument_list = full_cmd_arguments[1:]
short_options = "hc:v"
long_options = ["help", "config=","logPath=", "verbose"]
try:
    arguments, values = getopt.getopt(argument_list, short_options, long_options)
except getopt.error as err:
    # Output error, and return with an error code
    logging.error(str(err))
    pass

log_filename='logs/appd.log'
log_level=logging.INFO

for current_argument, current_value in arguments:
    if current_argument in "--logPath":
        logging.info("Setting log path to " + current_value)
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        if not os.path.exists(os.path.dirname(current_value)):
            try:
                os.makedirs(os.path.dirname(current_value))
            except OSError as exc:
                print("Attempted to create log directory failed for dir "+str(os.path.dirname(current_value)))
                print("Validate Permissions and reattempt")
        log_filename = current_value
        logging.basicConfig(filename=log_filename, format='%(asctime)s - %(levelname)s - %(message)s', level=log_level)
        logging.info("Changed log location to " + log_filename)

for current_argument, current_value in arguments:
    if current_argument in ("-v", "--verbose"):
        logging.info("Setting log level to DEBUG")
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        logging.basicConfig(filename=log_filename, format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    elif current_argument in ("-h", "--help"):
        print ("Displaying help")
    elif current_argument in ("-c", "--config"):
        config_file=current_value
        logging.info("Config file location changed to "+config_file)



logging.info("Started AppDynamics")
test_fields = []
metric_fields = []
appd_config = []
testIds = []
office365_config = []
#extension_schema={}
# Create Client
client = requests.session()

# Creates schema
def appdynamics_create_schema(schema):
    
    logging.info("Creating Script for Analytics Schema Creation......")
    command = "curl -X POST \"${events_service}:${port}/events/schema/$schemaName\" -H\"X-Events-API-AccountName:${accountName}\" -H\"X-Events-API-Key:${apiKey}\" -H\"Content-type: application/vnd.appd.events+json;v=2\" -d '{\"schema\":" + json.dumps(
        schema) + "}'"
    with open('createSchema.sh', 'w') as rsh:
        rsh.write('''\
    #!/bin/bash
    schemaName=
    accountName=
    apiKey=
    events_service=
    port=

    while test $# -gt 0; do
        case $1 in
          -h|--help)
             echo "AppDynamics Analytics Schema Creation"
             echo " "
             echo "-------------------------------------"
             echo " "
             echo "options:"
             echo "-h,  --help                show brief help"
             echo "-sc, --schema              AppDynamics Schema Name specify an action to use"
             echo "-ac, --accountname         AppDynamics Global Account Name"
             echo "-k , --key                 AppDynamics Analytics API Key"
             echo "-es                        AppDynamics events service host name, inc protocol Example: https://analytics.api.appdynamics.com"
             echo "-port                      AppDynamics events service port"
             exit 0
         ;;
            -sc | --schema )        shift
                                    schemaName="$1"
                                    ;;
            -ac | --accountname )   shift
                                    accountName="$1"
                                    ;;
            -k | --key )            shift
                                    apiKey="$1"
                                    ;;
            -es)                    shift
                                    events_service="$1"
                                    ;;
            -port)                  shift
                                    port=$1
                                    ;;
            * )                     usage
                                    exit 1
         esac
         shift
     done
    ''')
        rsh.write(command)
        rsh.close()
        logging.info("Custom schema creation has been created. Please navigate to: "+os.getcwd())
        logging.info("Change permissions to createSchema.sh chmod +x createSchema.sh")
        logging.info("execute createSchema.sh in order to create the AppDynamics Analytics schema")
        sys.exit()

# Parses config file
try:
    logging.info("Opening configuration file " + config_file)
    with open(config_file) as f:
        data = yaml.safe_load(f)
        logging.debug("Full Config Loaded from file: "+str(data))
        # Create the schema creation command
        extension_dict={}
        #te_account_group=''
        #extension_host=''
        try:
            extension_host=data['Optimiz']['AppDynamics']['hostname']
        except Exception as error:
            logging.warning("Failed to extract hostname")
        #extension_schema.update({'AccountGroup': te_account_group} if te_account_group is not None else {})
        #extension_schema.update({'extensionHost': extension_host} if extension_host is not None else {})

        schema_dict = {"tenantId": "string",
                        "serverName": "string",
                        "status": "string",
                        "location": "string",
                        "destination": "string",
                        "senderEmail": "string",
                        "time_to_auth": "string",
                        "time_to_send": "string"
        }
        if not os.path.exists("./createSchema.sh"):
            appdynamics_create_schema(schema_dict)
        appd_config = data['Optimiz']['AppDynamics']
        office365_config = data['Optimiz']['Office365']
        tls_certificate= data['Optimiz']['TLSCertificate']
except Exception as err:
    logging.error("Failed to parse appd.yml in the following directory " + os.getcwd())
    logging.error(err)

# Checks to make sure the tls is present
def get_verification(tls_certificate):
    if(tls_certificate):
        logging.info("Certificate has been changed using configuration yaml")
        logging.debug("New certificate path is "+ str(tls_certificate['certificateBundlePath']))
        return tls_certificate['certificateBundlePath']
    else:
        logging.info("Certificate has not been set defaults to verification False")
        return False

certificate_bundle=get_verification(tls_certificate)

# Gets the schema
def get_appdynamics_schema():
    events_service_url = appd_config['appdEventsService']
    schema_name = appd_config['schemaName']
    retrieve_schema_url = events_service_url + "/events/schema/" + schema_name
    api_key = appd_config['analyticsApiKey']
    account_name = appd_config['globalAccountName']
    headers = {
        'X-Events-API-AccountName': account_name,
        'X-Events-API-Key': api_key,
        'Content-type': 'application/vnd.appd.events+json;v=2'
    }
    schema = {}

    try:
        response = requests.request("GET", retrieve_schema_url, headers=headers, verify=certificate_bundle)
        schema = response.json()
        if(response.status_code==404):
            logging.error("Cannot retrieve Analytics Schema")
            logging.error("Run createSchema.sh and validate the schema has been created in AppDynamics")
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logging.error("Failed to collect information on the AppDynamics analytics schema")
        logging.error(e)
        raise SystemExit(e)
    return schema


# Updates schema
def update_appdynamics_schema():
    schema_old={}
    try:
        schema_old = get_appdynamics_schema()['schema']
    except(KeyError):
        logging.error("Cannot retrieve Analytics Schema")
        logging.error("Run createSchema.sh and validate the schema has been created in AppDynamics")
        sys.exit()
    set_1 = set(schema_old.items())
    set_2 = set(schema_dict.items())
    difference = dict(set_2 - set_1)
    if (difference):
        diff_payload = {}
        diff_payload.update({'add': difference})
        events_service_url = appd_config['appdEventsService']
        schema_name = appd_config['schemaName']
        events_service_url = events_service_url + "/events/schema/" + schema_name
        api_key = appd_config['analyticsApiKey']
        account_name = appd_config['globalAccountName']
        headers = {
            'X-Events-API-AccountName': account_name,
            'X-Events-API-Key': api_key,
            'Content-type': 'application/vnd.appd.events+json;v=2',
            'Accept-type': 'Accept: application/vnd.appd.events+json;v=2'
        }
        payload = "[" + json.dumps(diff_payload) + "]"
        try:
            logging.info("Updating custom schema fields: " + payload)
            response = requests.patch(events_service_url, headers=headers, data=payload , verify=certificate_bundle)
        except requests.exceptions.RequestException as e:  # This is the correct syntax
            logging.error("Failed to update Appdynamics Custom Schema")
            logging.error(e.message)
            raise SystemExit(e)


# Publishes new data to appd
def post_appdynamics_data(data):
    events_service_url = appd_config['appdEventsService']
    schema_name = appd_config['schemaName']
    events_service_url = events_service_url + "/events/publish/" + schema_name

    api_key = appd_config['analyticsApiKey']
    account_name = appd_config['globalAccountName']
    headers = {
        'X-Events-API-AccountName': account_name,
        'X-Events-API-Key': api_key,
        'Content-type': 'application/vnd.appd.events+json;v=2'
    }
    schema = json.dumps(data)
    schema = "[" + schema + "]"
    
    try:
        logging.info("Pushing data into AppDynamics schema"+events_service_url)
        logging.debug("Pushing data into AppDynamics schema: "+events_service_url)
        response = requests.request("POST", events_service_url, headers=headers, data=schema , verify=certificate_bundle)
        if(response.status_code>204):
            logging.warning("POST data to AppDynamics failed with code: "+str(response.status_code))
            logging.debug("POST data to AppDynamics failed with response: "+response.text)
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logging.error("Failed to POST data to the AppDynamics analytics schema")
        logging.error(e)
        raise SystemExit(e)


def get_o365_data():
    from O365 import Account
    import socket
    import time

    try:
        start_time = time.time()
        cred = (office365_config["client_id"], office365_config["client_secret"])
        account = Account(cred, auth_flow_type='credentials', tenant_id=office365_config["tenant_id"])
        if account.authenticate():
            auth_time = time.time() - start_time

            m = account.new_message(resource=office365_config["sender"])
            m.to.add(office365_config["email"])
            m.subject = office365_config["subject"]
            m.body = office365_config["body"]
            m.send()

            send_time = time.time() - start_time

            data = {'status': 'Success',
                    'tenantId': str(office365_config["tenant_id"]),
                    'serverName': socket.gethostname(),
                    'location': str(office365_config["location"]),
                    'destination': str(office365_config["email"]),
                    'senderEmail': str(office365_config["sender"]),
                    'time_to_auth': auth_time,
                    'time_to_send': send_time
            }
            post_appdynamics_data(data)
        else: 
            logging.error("Authenticatio to mail server failed")
            data = {'status': 'Failed',
                    'tenantId': str(office365_config["tenant_id"]),
                    'serverName': socket.gethostname(),
                    'location': str(office365_config["location"]),
                    'destination': str(office365_config["email"]),
                    'senderEmail': str(office365_config["sender"]),
                    'time_to_auth': 0,
                    'time_to_send': 0
            }
            post_appdynamics_data(data)
    except:
        print("failed")
        data = {'status': 'Failed',
                    'tenantId': str(office365_config["tenant_id"]),
                    'serverName': socket.gethostname(),
                    'location': str(office365_config["location"]),
                    'destination': str(office365_config["email"]),
                    'senderEmail': str(office365_config["sender"]),
                    'time_to_auth': 0,
                    'time_to_send': 0
            }
        post_appdynamics_data(data)

def delete_schema(schema):
    events_service_url = appd_config['appdEventsService']
    api_key = appd_config['analyticsApiKey']
    account_name = appd_config['globalAccountName']

    headers = {
        'X-Events-API-AccountName': account_name,
        'X-Events-API-Key': api_key,
        'Content-type': 'application/vnd.appd.events+json;v=2'
    }
    
    requests.delete(events_service_url + "/events/schema/" + schema, headers=headers)

#delete_schema("office365")
get_o365_data()