# Compare Slot Script

The purpose of this python program is to compare the slots of a TSM server 
with the slots of the Physical library.

TSM libvolumes generated with TSM commands and the Physical Library Inventory 
is generated with tapeutil or itdt command.

# Requirements

TSM client 5.x, 6.x, 7.x or 8.x is required because the script is using dsmadmc command to 
connect to TSM server. 
The TSM information in the tsmlist.conf file must exist in dsm.sys of the TSM client.

# Configuration Example File
```toml
[TSM_SERVERS.TSM01]
# Name of the TSM server ( this must exist in dsm.sys file with all the STANZA information.)
tsmName = "TSM01"
# Username to connect to the TSM server.
tsmUser = "tsmUser"
# Password to connect to the TSM server.
tsmPass = "tsmPass"
# IP of the server that TSM is hosted.
tsmIp   = "192.168.1.101"
# Username to login to the server that TSM is hosted.
username = "hostUser"
# Password to login to the server that TSM is hosted.
password = "hostPass"
```

# Arguments
```
usage: compareSlots.py [-h] -t TSM [-o {ALL,KO}] [-v VOLUME] [-c CONFIG]

optional arguments:
  -h, --help                       show this help message and exit
  -t TSM, --tsm TSM                TSM server name.
  -o {ALL,KO}, --outmode {ALL,KO}  Output mode. ALL to see all the comparison and KO to see only errors
  -v VOLUME, --volume VOLUME       Volume name. If you wish to compare slots for only one volume
  -c CONFIG, --config CONFIG       TOML configuration file.
```

# Example Output
```
Select Library :
1 : LIBRARY1
2 : LIBRARY2
3 : LIBRARY3
4 : Exit
Enter Number: 1
Library Selected is LIBRARY1 and device is /dev/smc0

|   SLOT | TSM ENTRY   | Physical Entry   | Result   |
|--------+-------------+------------------+----------|
|   1030 | VOL01LT4    | VOL01LT4         | OK       |
|   1031 | VOL02LT4    | Empty...         | MOUNTED  |
|   1032 | VOL03LT4    | Empty...         | KO       |
|   1033 | VOL04LT4    | VOL04LT4         | OK       |
|   1034 | VOL05LT4    | VOL05LT4         | OK       |
|   1035 | Empty...    | VOL06LT4         | KO       |
|   1036 | VOL07LT4    | Empty...         | MOUNTED  |
|   1037 | VOL08LT4    | VOL08LT4         | OK       |
|   1038 | VOL09LT4    | VOL09LT4         | OK       |
|   1039 | VOL06LT4    | Empty...         | KO       |

```

# Required Modules
```
sys
subprocess
toml
argparse
tabulate

Install toml module from pip with command: pip install toml
or
git clone https://github.com/toml-lang/toml.git
and, python setup.py install

Install tabulate module from pip with command: pip install tabulate
or
Download [source code](https://pypi.python.org/pypi/tabulate/#downloads)
and, python setup.py install

```
# Licence
```
 GNU GENERAL PUBLIC LICENSE
 Version 3, 29 June 2007
```

