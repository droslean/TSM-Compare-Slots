# Compare Slot Script

The purpose of this bash script is to compare the slots of a TSM server 
with the slots of the Physical library.

TSM libvolumes generated with TSM commands and the Physical Library Inventory 
is generated with tapeutil or itdt command.

# Requirements

TSM client 5.x, 6.x, 7.x or 8.x is required because the script is using dsmadmc command to 
connect to TSM server. 
The TSM information in the tsmlist.conf file must exist in dsm.sys of the TSM client.

# TOML Configuration File 

Example:<br />
[TSM_SERVERS.TSM01]<br />
	tsmName = "TSM01"<br />
	tsmUser = "tsmUser"<br />
	tsmPass = "tsmPass"<br />
	tsmIp   = "192.168.1.101"<br />
	username = "hostUser"<br />
	password = "hostPass"<br />
<br />
1 - Name of the TSM server ( this must exist in dsm.sys file with all the STANZA information.)<br />
2 - Username to connect to the TSM server.<br />
3 - Password to connect to the TSM server.<br />
4 - Hostname of the server that TSM is hosted.<br />
5 - Username to login to the server that TSM is hosted.<br />
6 - Password to login to the server that TSM is hosted.<br />
<br />

# Arguments

usage: compareSlots.py [-h] -t TSM [-o {ALL,KO}] [-v VOLUME] [-c CONFIG]<br />

optional arguments:<br />
  -h, --help            show this help message and exit<br />
  -t TSM, --tsm TSM     TSM server name.<br />
  -o {ALL,KO}, --outmode {ALL,KO}<br />
                        Output mode. ALL to see all the comparison and KO to see only errors<br />
  -v VOLUME, --volume VOLUME<br />
                        Volume name. If you wish to compare slots for only one volume<br />
  -c CONFIG, --config CONFIG<br />
                        TOML configuration file.<br />


# Example Output

Select Library :<br />
1 : LIBRARY1<br />
2 : LIBRARY2<br />
3 : LIBRARY3<br />
4 : Exit<br />
Enter Number: 1<br />
Library Selected is LIBRARY1 and device is /dev/smc0<br />
 <br />                                                      
|&emsp;&emsp;Slot Number&emsp;&emsp;|&emsp;&emsp;TSM Entry&emsp;&emsp;|&emsp;&emsp;Physical Entry&emsp;&emsp;|&emsp;&emsp;Result&emsp;&emsp;|<br />
<br />
|&emsp;&emsp;1027&emsp;&emsp;|&emsp;&emsp;VOL1LT4&emsp;&emsp;|&emsp;&emsp;VOL1LT4&emsp;&emsp;|&emsp;&emsp;OK&emsp;&emsp;&emsp;&emsp;|<br />
|&emsp;&emsp;1028&emsp;&emsp;|&emsp;&emsp;VOL2LT4&emsp;&emsp;|&emsp;&emsp;VOL2LT4&emsp;&emsp;|&emsp;&emsp;OK&emsp;&emsp;&emsp;&emsp;|<br />
|&emsp;&emsp;1029&emsp;&emsp;|&emsp;&emsp;VOL3LT4&emsp;&emsp;|&emsp;&emsp;VOL3LT4&emsp;&emsp;|&emsp;&emsp;OK&emsp;&emsp;&emsp;&emsp;|<br />
|&emsp;&emsp;1030&emsp;&emsp;|&emsp;&emsp;VOL4LT4&emsp;&emsp;|&emsp;&emsp;VOL4LT4&emsp;&emsp;|&emsp;&emsp;OK&emsp;&emsp;&emsp;&emsp;|<br />
|&emsp;&emsp;1031&emsp;&emsp;|&emsp;&emsp;VOL5LT4&emsp;&emsp;|&emsp;&emsp; EMPTY  &emsp;&emsp;|&emsp;&emsp;KO&emsp;&emsp;&emsp;&emsp;|<br />
|&emsp;&emsp;1032&emsp;&emsp;|&emsp;&emsp;VOL6LT4&emsp;&emsp;|&emsp;&emsp; EMPTY  &emsp;&emsp;|&emsp;&emsp;KO&emsp;&emsp;&emsp;&emsp;|<br />
|&emsp;&emsp;1033&emsp;&emsp;|&emsp;&emsp;VOL7LT4&emsp;&emsp;|&emsp;&emsp;VOL7LT4&emsp;&emsp;|&emsp;&emsp;OK&emsp;&emsp;&emsp;&emsp;|<br />
|&emsp;&emsp;1034&emsp;&emsp;|&emsp;&emsp;VOL8LT4&emsp;&emsp;|&emsp;&emsp; EMPTY  &emsp;&emsp;|&emsp;&emsp;MOUNTED&emsp;&emsp;|<br />
|&emsp;&emsp;1035&emsp;&emsp;|&emsp;&emsp;VOL9LT4&emsp;&emsp;|&emsp;&emsp;VOL9LT4&emsp;&emsp;|&emsp;&emsp;OK&emsp;&emsp;&emsp;&emsp;|<br />


# Required Modules

sys<br />
subprocess<br />
toml<br />
argparse<br />

Install toml module from pip with command: pip install toml<br />
or<br />
git clone https://github.com/toml-lang/toml.git<br />
and, python setup.py install<br />

# Licence

 GNU GENERAL PUBLIC LICENSE<br />
 Version 3, 29 June 2007<br />


