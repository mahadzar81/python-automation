import os
import sys
import platform
import paramiko
import socket
import time
import logging
import json
import argparse
from subprocess import call
from fabric import tasks
from fabric.api import *
from getpass import getpass
from fabric.contrib.files import exists, upload_template, sed, cd
from fabric.exceptions import NetworkError
from os.path import expanduser
from fabric.network import disconnect_all

def print_argument():
	print """# you need to install fabric by running apt-get install fabric on local machines

        # example : python run_command.py --file info.json
	Sample of info.json file entries as below:
		[
  			{
  				"env.user":"<username>",
  				"env.password":"<password>",
  				"_comment": "filepath is list of ops IP address seperated by each line",
  				"filepath":"/tmp/list_nodes.txt",
  				"log_file":"/tmp/run_command.log",
  				"_comment": "command file is list of command to run",
  				"command_file":"/tmp/list_command.txt"
  			}
		]

	"""
def get_args():

	parser = argparse.ArgumentParser(description=print_argument())
	parser.add_argument("-f", "--file",required=True,action='store',help='source json files')
	args = parser.parse_args()
	return args

def get_json_info(json_file):
	""" get json properties """
	with open(json_file) as data_file:
		data = json.load(data_file)
		for x in data:
			env.user = x["env.user"]
			env.password = x["env.password"]
			filepath = x["filepath"]
			log_file = x["log_file"]
			command_file = x["command_file"]

	return {
           'env.user':env.user, 'env.password':env.password , 'filepath':filepath, 'log_file':log_file,'command_file':command_file
            } 

# global variables
env.warn_only=True
env.connection_attempts = 3
home = expanduser("~")
args = get_args()
json_file=args.file
result = get_json_info(json_file)
env.user = result['env.user']
env.password = result['env.password']
filepath = result['filepath']    
log_file = result['log_file']  
command_file = result["command_file"] 
env.hosts = open(filepath, 'r').readlines()
logging.basicConfig(format='%(asctime)s %(message)s', filename='{0}' .format(log_file),level=logging.ERROR)

@parallel(pool_size=15)
def run_command():
	""" run command """
	with open(command_file, "r") as conf_file:
		conf_list = conf_file.readlines()
		for command in conf_list:
			try:
				run_command = sudo("{0}".format(command))
				if run_command.return_code !=0:
					print "run %s issue on %s" % (run_command, env.host_string)
					logging.error('run command issue on %s' % env.host_string)

			except NetworkError as error:
				print error
				logging.error(error) 



def main():
	
	uts_dict = tasks.execute(run_command)
	disconnect_all()

if __name__ == '__main__':
	main()




