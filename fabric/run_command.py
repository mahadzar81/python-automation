import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from fabric import Connection
from invoke.exceptions import UnexpectedExit

def print_help():
    print("""Usage instructions and JSON format help here...""")

def get_args():
    parser = argparse.ArgumentParser(description=print_help())
    parser.add_argument("-f", "--file", required=True, help='Path to JSON configuration file')
    return parser.parse_args()

def load_config(json_file):
    with open(json_file) as f:
        configs = json.load(f)
    return {
        'user': configs[0]['env.user'],
        'password': configs[0]['env.password'],
        'hosts_file': configs[0]['filepath'],
        'log_file': configs[0]['log_file'],
        'command_file': configs[0]['command_file']
    }

def read_hosts(hosts_file):
    with open(hosts_file) as f:
        return [line.strip() for line in f if line.strip()]

def read_commands(command_file):
    with open(command_file) as f:
        return [line.strip() for line in f if line.strip()]

def execute_commands(host, user, password, commands):
    """Execute commands on a single host using Fabric 2 Connection"""
    try:
        conn = Connection(
            host=host,
            user=user,
            connect_kwargs={'password': password}
        )
        
        logging.info(f"Starting execution on {host}")
        
        for cmd in commands:
            try:
                result = conn.sudo(cmd, warn=True, hide=True)
                if result.failed:
                    error_msg = f"Command failed on {host}: {cmd}\nError: {result.stderr}"
                    logging.error(error_msg)
                    print(f"ERROR {host}: {cmd} failed")
                else:
                    logging.info(f"Success on {host}: {cmd}")
                    print(f"OK {host}: {cmd} executed")
                    
            except UnexpectedExit as e:
                error_msg = f"Unexpected error on {host}: {str(e)}"
                logging.error(error_msg)
                print(f"ERROR {host}: {e}")
                
        conn.close()
    except Exception as e:
        error_msg = f"Connection failed to {host}: {str(e)}"
        logging.error(error_msg)
        print(f"CONNECTION ERROR {host}: {e}")

def main():
    args = get_args()
    config = load_config(args.file)
    
    # Configure logging
    logging.basicConfig(
        filename=config['log_file'],
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    hosts = read_hosts(config['hosts_file'])
    commands = read_commands(config['command_file'])
    
    print(f"Starting execution on {len(hosts)} hosts with {len(commands)} commands")
    
    # Execute commands in parallel with thread pool
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = []
        for host in hosts:
            futures.append(
                executor.submit(
                    execute_commands,
                    host,
                    config['user'],
                    config['password'],
                    commands
                )
            )
        
        # Wait for all tasks to complete
        for future in futures:
            future.result()

if __name__ == '__main__':
    main()