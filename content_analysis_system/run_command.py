#!/usr/bin/python
import paramiko
import sys
import socket
import time
import logging
import threading
import Queue
import argparse
import json

#Number of threads
n_thread = 15
#Create queue
queue = Queue.Queue()

def get_args():
  parser = argparse.ArgumentParser(description='''
                        # example : python run_command.py --file info.json\
                        Sample of info.json file entries as below:
                        [
                            {
                              "username":"<username>",
                              "credential":"<credential>",
                              "_comment": "filepath is list of CAS IP address seperated by each line",
                              "filepath":"/tmp/list_nodes.txt",
                              "log_file":"/tmp/run_command.log",
                              "_comment": "command file is list of command to run",
                              "command_file":"/tmp/list_command.txt"
                            }
                        ]
            ''')
  parser.add_argument("-f",
                      "--file",
                      required=True,
                      action='store',
                      help='source json files',
                      )
  args = parser.parse_args()
  return args

def get_json_info(json_file):

  with open(json_file) as data_file:  
    data = json.load(data_file)
    for x in data:
      username = x["username"]
      credential = x["credential"]
      filepath = x["filepath"]
      log_file = x["log_file"]
      command_file = x["command_file"]

  return {
  'username':username, 'credential':credential, 'filepath':filepath, 
  'log_file':log_file, 'command_file':command_file
  } 

args = get_args()
json_file=args.file
result = get_json_info(json_file)
username = result['username']
credential = result['credential']
filepath = result['filepath']    
log_file = result['log_file']  
command_file = result["command_file"] 

logging.basicConfig(format='%(asctime)s %(message)s', filename='{0}' .format(log_file),level=logging.ERROR)
#-------------------------------------------------------------------------------
# simple Thread class
#-------------------------------------------------------------------------------

class ThreadClass(threading.Thread):
  def __init__(self, queue):
    threading.Thread.__init__(self)
    self.queue = queue

  def run(self):
    while True:
      try:
        host = self.queue.get()
        print self.getName() + ":" + host
        run_command(host)
        self.queue.task_done()
      except:
        pass
#-------------------------------------------------------------------------------
# Main Thread
#-------------------------------------------------------------------------------

for i in range(n_thread):
  t = ThreadClass(queue)
  t.setDaemon(True)
  #Start thread
  t.start()


#-------------------------------------------------------------------------------
# Other function
#-------------------------------------------------------------------------------

def disable_paging(remote_conn):
  remote_conn.send("terminal length 0\n")
  time.sleep(1)
  output = remote_conn.recv(1000)
  return output

def run_command(host):
    
  username = username
  cas_ip = host.strip()
  password = credential
  try:
    remote_conn_pre = paramiko.SSHClient()
    remote_conn_pre.set_missing_host_key_policy(
    paramiko.AutoAddPolicy())
    remote_conn_pre.connect(host, username=username, password=password, look_for_keys=False, allow_agent=False, timeout=10)
    print "SSH connection established to %s" % host
    remote_conn = remote_conn_pre.invoke_shell()
    print "SSH session established"
    output = remote_conn.recv(100000)
    print output
    disable_paging(remote_conn)

    remote_conn.send("en\n")
    remote_conn.send("%s\n" % password)
    with open(command_file, "r") as conf_file:
      conf_list = conf_file.readlines()
      for command in conf_list:
        remote_conn.send("%s\n" % command)
        buff = ''
        while not buff.endswith('# '):
          output_command = remote_conn.recv(1000000)
          buff += output_command
          print buff
          print "closing ssh connection"

  except (paramiko.SSHException, socket.error) as error:
    print "%s on %s"  % (error,host)
    logging.error('%s on %s' % (error,host))

def main():
  with open(filepath, "r") as conf_file:
    conf_list = conf_file.readlines()
    x = len(conf_list)

    threads = []
    for host in conf_list:
      queue.put(host)
      queue.join()    

if __name__ == "__main__":
  main()

 
