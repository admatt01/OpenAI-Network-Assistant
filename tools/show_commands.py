import os
import paramiko
import json
import logging
import boto3
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_secret(secret_name, region_name=os.environ.get('AWS_REGION_NAME')):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        # Retrieve the secret
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

def show_commands(command, routers):
    try:
        logger.info(f"Received command: {command}")
        logger.info(f"Routers to connect to: {routers}")

        # Validate required parameters
        if not command:
            raise ValueError('Missing required parameter: command')
        if not routers:
            raise ValueError('Missing required parameter: routers')

        # Fetch the username and password from AWS Secrets Manager
        secret_name = os.environ.get('AWS_SECRETS_NAME')
        credentials = get_secret(secret_name)
        if not credentials:
            raise ValueError('Could not retrieve credentials from AWS Secrets Manager')
        
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            raise ValueError('Missing username or password in the retrieved credentials')

        # Load all router IP addresses from file
        all_routers = load_router_ips('devices/routers.json')
        if not all_routers:
            raise ValueError('Could not load router IPs from file')

        # Filter the routers to connect to
        routers_to_connect = {router_name: all_routers[router_name] for router_name in routers if router_name in all_routers}
        if not routers_to_connect:
            raise ValueError('None of the specified routers found in the loaded IPs')

        # Define function to execute command on a single router
        def execute_command(router_name, router_info):
            try:
                management_ip = router_info.get('management_ip')

                if not management_ip:
                    raise ValueError(f'Missing management_ip for router: {router_name}')

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(management_ip, username=username, password=password)

                stdin, stdout, stderr = ssh.exec_command(command)
                command_output = stdout.read().decode('utf-8')
                ssh.close()
                logger.info(f"Command output for router {management_ip}: {command_output}")
                return {router_name: command_output}
            except Exception as e:
                logger.error(f"Error executing command on router {management_ip}: {str(e)}")
                return {router_name: f"Error: {str(e)}"}

        # Execute command on routers concurrently
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(execute_command, router_name, router_info) for router_name, router_info in routers_to_connect.items()]
            results = [future.result() for future in futures]

        # Combine results into a single dictionary
        combined_results = {}
        for result in results:
            combined_results.update(result)

        return {
            "status": "success",
            "command": command,
            "routers": list(routers_to_connect.keys()),
            "results": combined_results
        }
    except Exception as e:
        logger.error(f"Error in show_commands: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "command": command,
            "routers": routers
        }
