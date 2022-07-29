# This is using python script to run multiple ssh command on multiple nodes on Content Analysis System Appliance

## (Example content of info.json )
```
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

```
## (Example content of list_command.txt) 
```
configure
ictm seconds 30
ictm drop threshold 30
ictm drop enable-alerts true
ictm warning threshold 20
```

## Example to run the script
```
$ python run_command.py
usage: run_command.py [-h] -f FILE
run_command.py: error: argument -f/--file is required

```
