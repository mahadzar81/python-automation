# Creating custom dynamic AWS inventories for Ansible

A simple script that uses uses theAWS Boto3 python module to generate AWS EC2 Instances inventories for Ansible.

Ansible will call it with the argument --list when you run

P/S : Credit to Jeff Geerling for guidelines -> https://www.jeffgeerling.com/blog/creating-custom-dynamic-inventories-ansible

## Prerequisites
Use git clone to download this repository to the system that will run the script. Boto3 python module is required.

Make this script executables
```
chmod +x ec2_inventory.py

```
## Description
This script will iterate all EC2 instances for all AWS regions and creating custom dynamic inventories for Ansible

## (Example using the script)
```
ansible all -i ec2_inventory.py -m ping

```

