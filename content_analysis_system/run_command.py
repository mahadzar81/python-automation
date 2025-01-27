#!/usr/bin/env python3
import paramiko
import sys
import socket
import time
import logging
import threading
import queue  # Use queue.Queue for Python 3
import argparse
import json
from dataclasses import dataclass
from typing import List

# Constants
DEFAULT_NUM_THREADS = 15

@dataclass
class SSHConfig:
    username: str
    credential: str
    hosts_file: str
    log_file: str
    commands_file: str

class SSHThread(threading.Thread):
    def __init__(self, task_queue, config, commands):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.config = config
        self.commands = commands

    def run(self):
        while True:
            try:
                host = self.task_queue.get()
                self.process_host(host.strip())
                self.task_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logging.error(f"Thread error: {str(e)}")

    def process_host(self, host):
        try:
            with paramiko.SSHClient() as client:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=host,
                    username=self.config.username,
                    password=self.config.credential,
                    look_for_keys=False,
                    allow_agent=False,
                    timeout=10
                )
                logging.info(f"SSH connection established to {host}")
                
                with client.invoke_shell() as shell:
                    self.disable_paging(shell)
                    self.execute_commands(shell, host)

        except (paramiko.SSHException, socket.error) as e:
            logging.error(f"Connection failed to {host}: {str(e)}")

    def disable_paging(self, shell):
        shell.send("terminal length 0\n")
        time.sleep(0.5)
        self._read_output(shell)

    def execute_commands(self, shell, host):
        shell.send("en\n")
        shell.send(f"{self.config.credential}\n")
        time.sleep(1)  # Wait for enable prompt
        
        for cmd in self.commands:
            shell.send(f"{cmd}\n")
            output = self._read_output(shell)
            logging.info(f"Output from {host} for '{cmd.strip()}':\n{output}")

    def _read_output(self, shell, timeout=2):
        output = ""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if shell.recv_ready():
                output += shell.recv(4096).decode('utf-8')
            else:
                time.sleep(0.1)
        return output

def parse_args():
    parser = argparse.ArgumentParser(
        description='Execute commands on multiple network devices',
        epilog='Example JSON config: [{"username":"user", "credential":"pass", "filepath":"hosts.txt", "log_file":"output.log", "command_file":"commands.txt"}]'
    )
    parser.add_argument("-f", "--file", required=True, help="JSON configuration file")
    return parser.parse_args()

def load_config(json_file) -> SSHConfig:
    with open(json_file) as f:
        configs = json.load(f)
        if len(configs) != 1:
            raise ValueError("JSON config must contain exactly one configuration object")
        conf = configs[0]
        return SSHConfig(
            username=conf["username"],
            credential=conf["credential"],
            hosts_file=conf["filepath"],
            log_file=conf["log_file"],
            commands_file=conf["command_file"]
        )

def read_lines(file_path) -> List[str]:
    with open(file_path) as f:
        return [line.strip() for line in f if line.strip()]

def main():
    args = parse_args()
    config = load_config(args.file)
    
    # Setup logging
    logging.basicConfig(
        filename=config.log_file,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Read configuration files
    hosts = read_lines(config.hosts_file)
    commands = read_lines(config.commands_file)

    # Create and populate task queue
    task_queue = queue.Queue()
    for host in hosts:
        task_queue.put(host)

    # Create and start threads
    threads = []
    for _ in range(DEFAULT_NUM_THREADS):
        thread = SSHThread(task_queue, config, commands)
        thread.start()
        threads.append(thread)

    # Wait for all tasks to complete
    task_queue.join()

    # Clean up threads
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()