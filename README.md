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

Example:
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
| Slot Number | TSM Entry 	| Physical Entry 	| Result 	|<br />
<br />
|	 1027 	    | VOL1LT4 	  | VOL1LT4 		    |  OK  		|<br />
|	 1028 	    | VOL2LT4 	  | VOL2LT4 		    |  OK  		|<br />
|	 1029 	    | VOL3LT4 	  | VOL3LT4 		    |  OK  		|<br />
|	 1030 	    | VOL4LT4 	  | VOL4LT4 		    |  OK  		|<br />
|	 1031 	    | VOL5LT4 	  | EMPTY   		    |  KO  		|<br />
|	 1032 	    | VOL6LT4 	  | EMPTY    		    |  KO  		|<br />
|	 1033 	    | VOL7LT4 	  | VOL7LT4 		    |  OK  		|<br />
|	 1034 	    | VOL8LT4 	  | EMPTY   		    |  MOUNTED  	|<br />
|	 1035 	    | VOL9LT4 	  | VOL9LT4 		    |  OK  		|<br />


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


