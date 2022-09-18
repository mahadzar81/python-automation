#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import print_function
import re
from datetime import datetime
import csv
import argparse
import time
import os
import json

try:
  import boto3
  # import botocore
except ImportError as e:
  print('This script require Boto3 to be installed and configured.')
  exit()

from botocore.exceptions import ClientError


def get_args():
  parser = argparse.ArgumentParser(description='''
                      # example : python3 ec2_inventory.py             
              ''')
  # parser.add_argument("-r",
  #                     "--region",
  #                     required=False,
  #                     action='store',
  #                     help='selected region',
  #                     )
  parser.add_argument('--list', action='store_true')
  parser.add_argument('--host', action='store')
  args = parser.parse_args()
  return args

def get_account_details():
  # generate a list of AWS accounts based on the credentials file
  local_account_list = []

  try:
    credentials = open(os.path.expanduser('~/.aws/credentials'), 'r')
    for line in credentials:
      account = re.search('\[([\w\d\-\_\.]*)\]', line)
      if account is not None:
        local_account_list.insert(0, account.group(1))
  except:
    print("Script expects ~/.aws/credentials. Make sure this file exists")
    exit()

  return local_account_list

args = get_args()
# selected_region = args.region

def get_client(account, local_region):
  # Sets up a boto3 session
  local_profile = account
  try:
    current_session = boto3.Session(profile_name = local_profile, region_name=local_region)
    local_client = current_session.client("ec2")
    return local_client
  except:
    print('\'{}\' is not a configured account.'.format(account))
    exit()

def get_regions(lcl_account):
  #get the current list of regions to iterate through
  lcl_region = "ap-southeast-1"
  client = get_client(lcl_account, lcl_region)
  aws_region_data = client.describe_regions()
  aws_regions = aws_region_data['Regions']
  lcl_regions = [region['RegionName'] for region in aws_regions]
  
  return lcl_regions

def ansible_fix_inventory():

  return {
      'group': {
          'hosts': '',
          'vars': {
              'ansible_ssh_user': 'admin',
              'ansible_ssh_private_key_file':
                  '~/.ssh/id_rsa',
          }
      }
  }

def example_inventory():
  return {
      'group': {
          'hosts': ['192.168.28.71', '192.168.28.72'],
          'vars': {
              'ansible_ssh_user': 'vagrant',
              'ansible_ssh_private_key_file':
                  '~/.vagrant.d/insecure_private_key',
              'example_variable': 'value'
          }
      },
      '_meta': {
          'hostvars': {
              '192.168.28.71': {
                  'host_specific_var': 'foo'
              },
              '192.168.28.72': {
                  'host_specific_var': 'bar'
              }
          }
      }
  }

def validate_credentials(accounts_dictionary, accounts_credentials, *profile):
  # validate that the local credentials file has an entry for each account in scope and use only
  # the credentials for the accounts in scope.
  in_scope_acct_alias_list = []
  for acct in accounts_credentials:
    if (acct in accounts_dictionary.values()):
      in_scope_acct_alias_list.append(acct)
    else:
      print("****INFORMATION: %s was not found in list of accounts in scope." % acct)
  for key, value in accounts_dictionary.items():
    if value not in in_scope_acct_alias_list:
      print("****WARNING: %s does not have a corresponding entry in the local credentials file." % value)
      print("****WARNING: The %s account will not be audited" % value)
  return in_scope_acct_alias_list

def main():
  ec2_public_ip = []
  account_list = get_account_details()
  regions = get_regions(account_list[0])

  for region in regions:
    client = get_client(account_list[0],  region)
    response = client.describe_instances()

    for key, value in response.items():
      if key == "Reservations":
        for object_items1 in value:
          for key1, value1 in object_items1.items():
            if key1 == "OwnerId":
              owner_id = value1

            if key1 == "Instances":
              instances = value1
              for object_items2 in instances:
                for key2, value2 in object_items2.items():

                  if key2 == "NetworkInterfaces":
                    network_interfaces = str(len(value2))

                  if key2 == "PrivateIpAddress":
                    private_ip = value2

                  if key2 == "PublicIpAddress":
                    public_ip = value2
                    ec2_public_ip.append(public_ip)

  if ec2_public_ip:
    fix_inventory = ansible_fix_inventory()
    fix_inventory['group']['hosts'] = ec2_public_ip
    print(json.dumps(fix_inventory))

if __name__ == '__main__':
  main()




