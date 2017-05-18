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

        except KeyboardInterrupt as rc:
            print("\nCTRL+C detected. Program is exiting...\n")
            exit_program(rc)
        except EOFError as rc:
            print("\nCTRL+D detected. Program is exiting...\n")
            exit_program(rc)


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
        exit_program(tsm_exec.returncode)
    except KeyboardInterrupt as rc:
        print("\nCTRL+C detected. Program is exiting...\n")
        exit_program(rc)
    except EOFError as rc:
        print("\nCTRL+D detected. Program is exiting...\n")
        exit_program(rc)


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
        exit_program(ssh_exec.returncode)
    except KeyboardInterrupt as rc:
        print("\nCTRL+C detected. Program is exiting...\n")
        exit_program(rc)
    except EOFError as rc:
        print("\nCTRL+D detected. Program is exiting...\n")
        exit_program(rc)


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
        exit_program(tsm_exec.returncode)
    except KeyboardInterrupt as rc:
        print("\nCTRL+C detected. Program is exiting...\n")
        exit_program(rc)
    except EOFError as rc:
        print("\nCTRL+D detected. Program is exiting...\n")
        exit_program(rc)


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
        exit_program(tsm_exec.returncode)
    except KeyboardInterrupt as rc:
        print("\nCTRL+C detected. Program is exiting...\n")
        exit_program(rc)
    except EOFError as rc:
        print("\nCTRL+D detected. Program is exiting...\n")
        exit_program(rc)


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
            exit_program(tsm_exec.returncode)
    except KeyboardInterrupt as rc:
        print("\nCTRL+C detected. Program is exiting...\n")
        exit_program(rc)
    except EOFError as rc:
        print("\nCTRL+D detected. Program is exiting...\n")
        exit_program(rc)


# Compares all slots of TSM and Physical libraries, and print the results.
def compare_all_and_print(library_inventory_dict, tsm_libvolumes_dict,
                          mounted_volumes, output_mode):

    title = ["SLOT", "TSM ENTRY", "Physical Entry", "Result"]
    list_to_print = list()
    KO_dict = dict()
    counter_OK = 0
    counter_KO = 0
    counter_MOUNTED = 0

    maximum = max(library_inventory_dict.keys(), key=int)
    mininum = min(library_inventory_dict.keys(), key=int)
    for x in range(int(mininum), int(maximum) + 1):
        libinv_vol = library_inventory_dict[str(x)]

        # Check for empty slots in TSM library.
        if str(x) not in tsm_libvolumes_dict:
            tsmlib_vol = "Empty..."
        else:
            tsmlib_vol = tsm_libvolumes_dict[str(x)]

        # Check Generate results.
        if libinv_vol == tsmlib_vol:
            result = "\033[92mOK\033[97m"
            counter_OK += 1
            if output_mode == "ALL":
                list_to_print.append([x, tsmlib_vol, libinv_vol, result])

        else:
            if mounted_volumes and tsmlib_vol in mounted_volumes:
                counter_MOUNTED += 1
                result = "\033[44mMOUNTED\033[49m"
                if output_mode == "ALL":
                    list_to_print.append([x, tsmlib_vol, libinv_vol, result])
            else:
                counter_KO += 1
                result = "\033[41mKO\033[49m"
                list_to_print.append([x, tsmlib_vol, libinv_vol, result])
                # Populate KO dictonary {VOLUME_NAME:[TSM_SLOT,PHYSICAL_SLOT]}
                # in case in --sync argument, to fix them.
                if tsmlib_vol != "Empty...":
                    for slot, volume in library_inventory_dict.items():
                        if volume == tsmlib_vol:
                            KO_dict[tsmlib_vol] = [str(x), str(slot)]

    # Print the table
    print(tabulate(list_to_print, title, tablefmt="orgtbl"))

    print("\n\nOK: {}\nMOUNTED: {}\nKO: {}\nTOTAL: {}\n".format(
        counter_OK, counter_MOUNTED, counter_KO,
         (counter_OK + counter_KO + counter_MOUNTED)))
    return KO_dict


# Compares single volume's slot of TSM and Physical libraries,
# and print the results.
def compare_tape_and_print(library_inventory_dict, tsm_libvolumes_dict,
                           mounted_volumes, volume_name):
    print("\nCompare Slots for", volume_name)
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


# Get dictonary from Toml file.
def get_info_from_toml(tomlFile):
    try:
        with open(tomlFile) as conffile:
            return toml.loads(conffile.read())
    except OSError as error:
        print("Couldn't open configuration file!")
        exit_program(error)


# Parse the configuration file and return all the important information
def parse_toml_conf(config_file, tsm_name):
    config_info = get_info_from_toml(config_file)

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


# Clear colors and exit program with the given RC code.
def exit_program(rc):
    print("\033[0m")
    sys.exit(rc)


# Parse arguments given from the user and return them with variables
def parse_arguments():
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

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--sync", action="store_true",
                       help="Try to synchronize the KO slots")
    args = parser.parse_args()
    return args.tsm, args.outmode, args.volume, args.config, args.sync


# Check if the specified tape can be moved to the slot
# that TSM thinks the tape is.
def can_move(slot, library_inventory_dict):
    if library_inventory_dict[str(slot)] == "Empty...":
        return True


# Move the tape from slot to slot
def move_tape(ip, username, password, device, from_slot, to_slot):
    try:
        return subprocess.check_output(["sshpass -p %s ssh -q %s@%s "
                                        "tapeutil -f %s move %s %s " %
                                        (password, username,
                                         ip, device,
                                         from_slot, to_slot)],
                                       shell=True,
                                       stderr=subprocess.PIPE).decode("utf-8")

    except subprocess.CalledProcessError as ssh_exec:
        print("Move tape command failed with return code:", ssh_exec.returncode)
    except KeyboardInterrupt as rc:
        print("\nCTRL+C detected. Program is exiting...\n")
        exit_program(rc)
    except EOFError as rc:
        print("\nCTRL+D detected. Program is exiting...\n")
        exit_program(rc)


# Try to fix all the KO slots. This function will try to move
# the tape to the slot that TSM server thinks that the tape exist.
# For example:
#   |   SLOT | TSM ENTRY   | Physical Entry   | Result   |
#   |   1010 | VOL01L4     | Empty...         | KO       |
#   |   1020 | Empty...    | VOL01L4          | KO       |
#
#   In this case the tape will be moved from 1020 to 1010
#   The function can_move() will check if the 1010 is empty
#   in the physical library.
def fix_tapes(ip, username, password, device, KO_dict, library_inventory_dict):
    for volume, slot_list in KO_dict.items():
        if can_move(str(slot_list[0]), library_inventory_dict):
            print("Moving volume {} from {} to {}".format(
                  volume, str(slot_list[1]), str(slot_list[0])))
            print(move_tape(ip, username, password, device,
                            str(slot_list[1]), str(slot_list[0])))


# Main Part
if __name__ == '__main__':
    # Set white color
    print("\033[97m")

    # Parse Arguments
    tsm_name, output_mode, \
        volume_name, config_file, sync = parse_arguments()

    # Define important information from the configuration file
    tsmUsername, tsmPassword, tsmIp,\
        username, password = parse_toml_conf(config_file, tsm_name)

    global tsm_command
    tsm_command = "dsmadmc -se={} -id={} -pa={}" \
        .format(tsm_name, tsmUsername, tsmPassword)
    libraries = get_libraries(tsm_name)

    # Get library from user's selection menu.
    selected_library = select_library_menu(libraries.split())
    print("Library Selected is", selected_library, end="")

    # Get library's device from TSM server.
    device = get_device(selected_library)
    print(" and device is", device, "\n")

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

    if volume_name:
        compare_tape_and_print(library_inventory_dict, tsm_libvolumes_dict,
                               mounted_volumes, volume_name)
    else:
        KO_dict = dict()
        # Finally compare everything and print output.
        KO_dict = compare_all_and_print(library_inventory_dict,
                                        tsm_libvolumes_dict,
                                        mounted_volumes, output_mode)

        if sync and KO_dict:
            print("Trying to synchronize KO slots.")
            fix_tapes(tsmIp, username, password,
                      device, KO_dict, library_inventory_dict)

    # Clear colors.
    print("\033[0m")
