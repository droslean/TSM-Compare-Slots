import sys
import subprocess
import toml
import argparse
from tabulate import tabulate


# Select library Menu
def select_library_menu(libraries):
    while True:
        counter = 1
        for library in libraries:
            if library:
                print("%s: %s " % (counter, library))
                counter += 1
        print("{}: Exit ".format(len(libraries) + 1))
        try:
            user_input = int(input("Enter number: "))
            if (user_input > len(libraries) or user_input == 0):
                if (user_input == len(libraries) + 1):
                    sys.exit()
                else:
                    print("Try again...")
            else:
                return libraries[user_input - 1]
                break
        except ValueError:
            print("You didn't enter a number")

        except KeyboardInterrupt:
            print("\nCTRL+C detected. Program is exiting...\n")
            sys.exit()


# Get Available libraries from given TSM server


def get_libraries(tsm_name):
    try:
        libraries = subprocess.check_output(tsm_command +
                                            " -dataonly=yes " +
                                            "'select LIBRARY_NAME " +
                                            "from libraries' " +
                                            "| sed '/^$/d'",
                                            shell=True).decode("utf-8")

        if "ANS1017E" in libraries:
            print("Session rejected: TCP/IP connection failure.")
            sys.exit()

        return libraries

    except subprocess.CalledProcessError as tsm_exec:
        print("TSM get libraries command failed with return code:",
              tsm_exec.returncode)
        sys.exit(tsm_exec.returncode)
    except KeyboardInterrupt:
        print("\nCTRL+C detected. Program is exiting...\n")
        sys.exit()


# Get Library's Inventory
def get_library_inventory(ip, username, password, device):
    try:
        ssh_output = subprocess.check_output(["sshpass -p %s ssh -q %s@%s "
                                              "tapeutil -f %s inventory" %
                                              (password, username,
                                               ip, device)],
                                             shell=True,
                                             stderr=subprocess.PIPE)

        slot_dict = dict()
        slot = None
        volume = None

        for line in ssh_output.decode("utf-8").split("\n"):
            if "Slot Address" in line:
                slot = line.strip().split()[-1]
            if "Volume Tag" in line:
                volume = line.strip().split()[-1]
                if "....." in volume:
                    volume = "Empty..."

            # Populate dictionary
            if slot:
                slot_dict[slot] = volume

        return slot_dict

    except subprocess.CalledProcessError as ssh_exec:
        print("SSH command failed with return code:", ssh_exec.returncode)
        sys.exit(ssh_exec.returncode)
    except KeyboardInterrupt:
        print("\nCTRL+C detected. Program is exiting...\n")
        sys.exit()


# Get list of libvolumes with element number.
def get_libvolumes(library):
    try:
        tsm_output = subprocess.check_output(tsm_command +
                                             " -dataonly=yes -tab " +
                                             "select VOLUME_NAME," +
                                             "HOME_ELEMENT " +
                                             "from libvolumes " +
                                             "where library_name=\\'" +
                                             library + "\\' ORDER BY 2",
                                             shell=True)

        libvolumes_dict = dict()
        for volume_element in tsm_output.decode("utf-8").split('\n'):
            if volume_element:
                libvolumes_dict[volume_element.split(
                    '\t')[1]] = volume_element.split('\t')[0]

        return libvolumes_dict
    except subprocess.CalledProcessError as tsm_exec:
        print("TSM get libvolumes command failed with return code:",
              tsm_exec.returncode)
        sys.exit(tsm_exec.returncode)
    except KeyboardInterrupt:
        print("\nCTRL+C detected. Program is exiting...\n")
        sys.exit()


# Get device of the library.
# This is needed to pass it to -f of tapeutil command.
def get_device(library):
    try:
        return subprocess.check_output(tsm_command +
                                       " -dataonly=yes " +
                                       "select device from paths " +
                                       "where DESTINATION_TYPE=" +
                                       "\\'LIBRARY\\' " +
                                       "and DESTINATION_NAME=\\'" +
                                       str(library) + "\\'",
                                       shell=True).decode(
            "utf-8").replace("\n", "")

    except subprocess.CalledProcessError as tsm_exec:
        print("TSM get device command failed with return code:",
              tsm_exec.returncode)
        sys.exit(tsm_exec.returncode)
    except KeyboardInterrupt:
        print("\nCTRL+C detected. Program is exiting...\n")
        sys.exit()


# List of volumes that are currently mounted in TSM server.and
# This is important because the slot in the physical library will be empty,
# because the volume it will be in a drive's slot.
def get_mounted_volumes(library):
    try:
        return subprocess.check_output(tsm_command +
                                       " -dataonly=yes " +
                                       "select volume_name from drives " +
                                       "where DRIVE_STATE=\\'LOADED\\' " +
                                       "and LIBRARY_NAME=\\'" +
                                       library + "\\'",
                                       shell=True,
                                       ).decode("utf-8")

    except subprocess.CalledProcessError as tsm_exec:
        if tsm_exec.returncode == 11:
            print("No mounted volumes found in the library.Continue..\n")
        else:
            print("TSM get mounted volumes command failed with return code:",
                  tsm_exec.returncode)
            sys.exit(tsm_exec.returncode)
    except KeyboardInterrupt:
        print("\nCTRL+C detected. Program is exiting...\n")
        sys.exit()


# Get dictonary from Toml file.
def get_info_from_toml(tomlFile):
    with open(tomlFile) as conffile:
        return toml.loads(conffile.read())


# Compares the slots of TSM and Physical libraries, and print the results.
def compare_all_and_print(library_inventory_dict, tsm_libvolumes_dict,
                          mounted_volumes):

    title = ["SLOT", "TSM ENTRY", "Physical Entry", "Result"]
    list_to_print = list()

    maximum = max(library_inventory_dict.keys(), key=int)
    mininum = min(library_inventory_dict.keys(), key=int)

    for x in range(int(mininum), int(maximum) + 1):

        # Check for empty slots.
        if str(x) not in library_inventory_dict:
            libinv_vol = "Empty..."
        else:
            libinv_vol = library_inventory_dict[str(x)]

        if str(x) not in tsm_libvolumes_dict:
            tsmlib_vol = "Empty..."
        else:
            tsmlib_vol = tsm_libvolumes_dict[str(x)]

        # Check Generate results.
        if libinv_vol == tsmlib_vol:
            result = "\033[92mOK\033[97m"
            if args.outmode == "ALL":
                list_to_print.append([x, tsmlib_vol, libinv_vol, result])

        else:
            if mounted_volumes and tsmlib_vol in mounted_volumes:
                result = "\033[44mMOUNTED\033[49m"
                if args.outmode == "ALL":
                    list_to_print.append([x, tsmlib_vol, libinv_vol, result])
            else:
                result = "\033[41mKO\033[49m"
                list_to_print.append([x, tsmlib_vol, libinv_vol, result])

    # Print the table
    print(tabulate(list_to_print, title, tablefmt="orgtbl"))


def compare_tape_and_print(library_inventory_dict, tsm_libvolumes_dict,
                           mounted_volumes, volume_name):
    print("Compare Slots for", volume_name)
    in_tsm = False
    in_physical = False
    try:
        tsm_slot = list(tsm_libvolumes_dict.keys())[list(
            tsm_libvolumes_dict.values()).index(volume_name)]

        print("TSM entry: ", tsm_slot)
        in_tsm = True
    except ValueError:
        print("Volume not found in TSM library")

    try:
        physical_slot = list(library_inventory_dict.keys())[list(
            library_inventory_dict.values())
            .index(volume_name)]

        print("Physical Library entry: ", physical_slot)
        in_physical = True
    except ValueError:
        print("Volume not found in Physical library")

    if not in_tsm:
        tsm_slot = "Not found!"

    if not in_physical:
        physical_slot = "Not found!"

    if not in_tsm and not in_physical:
        print("Volume {} couldn't be found in TSM and Physical Library."
              .format(volume_name))
        sys.exit()

    if tsm_slot == physical_slot:
        result = "\033[92mOK\033[97m"
    else:
        if mounted_volumes and volume_name in mounted_volumes:
            result = "\033[44mMOUNTED\033[49m"
        else:
            result = "\033[41mKO\033[49m"

    print("Result:", result)


def parse_toml_conf(config_info, tsm_name):
    try:
        config_info = get_info_from_toml(args.config)
    except FileNotFoundError as error:
        print("File not found.\n", error)
        sys.exit()

    # Check if TSM exists in the configuration file.
    if tsm_name not in config_info['TSM_SERVERS']:
        print("TSM {} not found in the configuration file.".format(tsm_name))
        sys.exit()

    tsmDetails = config_info['TSM_SERVERS'][tsm_name]
    # Return all information needed to connect
    # to TSM server and the host server.
    return tsmDetails['tsmUser'], \
        tsmDetails['tsmPass'], \
        tsmDetails['tsmIp'], \
        tsmDetails['username'], \
        tsmDetails['password']

    # Main Part
if __name__ == '__main__':
    # Set white color
    print("\033[97m")

    # Manage arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tsm", required=True, help="TSM server name.")
    parser.add_argument("-o", "--outmode", default="ALL",
                        choices=['ALL', 'KO'],
                        help="Output mode. \
                        ALL to see all the comparison\
                         and KO to see only errors")
    parser.add_argument("-v", "--volume",
                        help="Volume name. If you wish to compare slots\
                         for only one volume")
    parser.add_argument("-c", "--config",
                        default="tsmlist.toml",
                        help="TOML configuration file.")

    args = parser.parse_args()

    # Define important information from the configuration file
    tsmUsername, tsmPassword, tsmIp,\
        username, password = parse_toml_conf(args.config, args.tsm)

    global tsm_command
    tsm_command = "dsmadmc -se={} -id={} -pa={}" \
        .format(args.tsm, tsmUsername, tsmPassword)
    libraries = get_libraries(args.tsm)

    # Get library from user's selection menu.
    selected_library = select_library_menu(libraries.split())
    print("Library Selected is", selected_library, end="")

    # Get library's device from TSM server.
    device = get_device(selected_library)
    print(" and device is", device)

    # Create a dictonary with which volumes are in which slots,
    # in Physical library
    library_inventory_dict = get_library_inventory(
        tsmIp, username, password, device)

    # Get libvolumes and element information from TSM server library.
    tsm_libvolumes_dict = get_libvolumes(selected_library)

    # Get volumes that are currently mounted in TSM server.
    # This is to ignore error, because the slot in the physical library
    # will be empty, since the volume is mounted on a disk slot.
    mounted_volumes = get_mounted_volumes(selected_library)

    if args.volume:
        compare_tape_and_print(library_inventory_dict, tsm_libvolumes_dict,
                               mounted_volumes, args.volume)
    else:
        # Finally compare everything and print output.
        compare_all_and_print(library_inventory_dict,
                              tsm_libvolumes_dict, mounted_volumes)

    # Clear colors.
    print("\033[0m")
