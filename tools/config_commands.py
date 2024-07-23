import paramiko
import json
import logging
import boto3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secret(secret_name, region_name="us-east-1"):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = response['SecretString']
        return json.loads(secret)
    except NoCredentialsError:
        logger.error("Credentials not available")
    except PartialCredentialsError:
        logger.error("Incomplete credentials provided")
    except Exception as e:
        logger.error(f"Error retrieving secret: {e}")
        return None

def load_router_ips(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data["routers"]
    except Exception as e:
        logger.error(f"Error loading router IPs: {e}")
        return {}

def execute_commands(router_name, router_info, commands, username, password):
    try:
        management_ip = router_info.get('management_ip')

        if not management_ip:
            raise ValueError(f'Missing management_ip for router: {router_info}')

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(management_ip, username=username, password=password, timeout=10)

        # Start an interactive shell
        shell = ssh.invoke_shell()
        shell.settimeout(30)  # Set a timeout for operations

        output = ""
        # Send all commands in the same session
        for command in commands:
            shell.send(command + '\n')
            time.sleep(2)  # Wait 2 seconds between commands

            # Wait for and capture the output
            while shell.recv_ready():
                output += shell.recv(65535).decode('utf-8')
                time.sleep(0.5)

        # Close the SSH connection
        ssh.close()

        return {
            "status": "success",
            "router": router_name,
            "management_ip": management_ip,
            "output": output
        }

    except Exception as e:
        logger.error(f"Error executing commands on router {router_name}: {str(e)}")
        return {
            "status": "error",
            "router": router_name,
            "management_ip": management_ip,
            "error": str(e)
        }

def config_commands(commands, target_routers):
    if not target_routers:
        raise ValueError('No target routers specified. Please provide a list of router names to configure.')

    try:
        # Fetch the username and password from AWS Secrets Manager
        secret_name = "routers"
        credentials = get_secret(secret_name)
        if not credentials:
            raise ValueError('Could not retrieve credentials from AWS Secrets Manager')
        
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            raise ValueError('Missing username or password in the retrieved credentials')

        # Load router IP addresses from file
        all_routers = load_router_ips('devices/routers.json')
        if not all_routers:
            raise ValueError('Could not load router IPs from file')

        # Filter routers based on target_routers
        routers = {k: v for k, v in all_routers.items() if k in target_routers}

        if not routers:
            raise ValueError('None of the specified target routers were found in the router configuration file')

        results = []
        with ThreadPoolExecutor(max_workers=len(routers)) as executor:
            future_to_router = {executor.submit(execute_commands, router_name, router_info, commands, username, password): router_name for router_name, router_info in routers.items()}
            for future in as_completed(future_to_router):
                results.append(future.result())

        # Prepare response
        response_data = {
            "status": "success",
            "message": f"Configuration commands executed on {len(results)} routers",
            "results": results
        }

        logger.info(f"Configuration commands executed on {len(results)} routers")
        return response_data

    except Exception as e:
        # Handle any errors and return appropriate response
        error_response = {
            "status": "error",
            "message": str(e)
        }
        logger.error("Error in config_commands: %s", str(e))
        return error_response

# Example usage
if __name__ == "__main__":
    commands_to_execute = [
        "configure terminal",
        "interface Ethernet0/0",
        "description Configured by AI Agent",
        "exit",
        "exit"
    ]
    
    # Specify target routers
    target_routers = ["router1", "router2"]
    
    result = config_commands(commands_to_execute, target_routers)
    print(result)
    