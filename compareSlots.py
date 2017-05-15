import sys
import subprocess
import toml
import argparse


# Select library Menu
def selectLibraryMenu(libraries):
    while True:
        counter = 1
        for library in libraries:
            if library:
                print("%s: %s " % (counter, library))
                counter += 1
        print("{}: Exit ".format(len(libraries) + 1))
        try:
            userInput = int(input("Enter number: "))
            if (userInput > len(libraries) or userInput == 0):
                if (userInput == len(libraries) + 1):
                    sys.exit()
                else:
                    print("Try again...")
            else:
                return libraries[userInput - 1]
                break
        except ValueError:
            print("You didn't enter a number")


# Get Available libraries from given TSM server
def getLibraries(tsmName):
    try:
        return subprocess.check_output(tsmCmd +
                                       " -dataonly=yes " +
                                       "'select LIBRARY_NAME " +
                                       "from libraries' " +
                                       "| sed '/^$/d'",
                                       shell=True).decode("utf-8")

    except subprocess.CalledProcessError as tsmexec:
        print("TSM get libraries command failed with return code:",
              tsmexec.returncode)
        sys.exit(tsmexec.returncode)


# Get Library's Inventory
def getLibraryInventory(ip, username, password, device):
    try:
        sshOutput = subprocess.check_output(["sshpass -p %s ssh -q %s@%s "
                                             "tapeutil -f %s inventory" %
                                             (password, username, ip, device)],
                                            shell=True,
                                            stderr=subprocess.PIPE)

        slotMap = dict()
        slot = None
        volume = None

        for line in sshOutput.decode("utf-8").split("\n"):
            if "Slot Address" in line:
                slot = line.strip().split()[-1]
            if "Volume Tag" in line:
                volume = line.strip().split()[-1]
                if "....." in volume:
                    volume = "Empty..."

            # Populate dictionary
            if slot:
                slotMap[slot] = volume

        return slotMap

    except subprocess.CalledProcessError as sshexec:
        print("SSH command failed with return code:", sshexec.returncode)
        sys.exit(sshexec.returncode)


# Get list of libvolumes with element number.
def getLibVolumes(library):
    try:
        tsmOutput = subprocess.check_output(tsmCmd +
                                            " -dataonly=yes -tab " +
                                            "select VOLUME_NAME," +
                                            "HOME_ELEMENT " +
                                            "from libvolumes " +
                                            "where library_name=\\'" +
                                            library + "\\' ORDER BY 2",
                                            shell=True)

        libvolsMap = dict()
        for volumeElement in tsmOutput.decode("utf-8").split('\n'):
            if volumeElement:
                libvolsMap[volumeElement.split(
                    '\t')[1]] = volumeElement.split('\t')[0]

        return libvolsMap
    except subprocess.CalledProcessError as tsmexec:
        print("TSM get libvolumes command failed with return code:",
              tsmexec.returncode)
        sys.exit(tsmexec.returncode)


# Get device of the library.
# This is needed to pass it to -f of tapeutil command.
def getDevice(library):
    try:
        return subprocess.check_output(tsmCmd +
                                       " -dataonly=yes " +
                                       "select device from paths " +
                                       "where DESTINATION_TYPE=" +
                                       "\\'LIBRARY\\' " +
                                       "and DESTINATION_NAME=\\'" +
                                       str(library) + "\\'",
                                       shell=True).decode("utf-8")
    except subprocess.CalledProcessError as tsmexec:
        print("TSM get device command failed with return code:",
              tsmexec.returncode)
        sys.exit(tsmexec.returncode)


# List of volumes that are currently mounted in TSM server.and
# This is important because the slot in the physical library will be empty,
# because the volume it will be in a drive's slot.
def getMountedVolumes(library):
    try:
        return subprocess.check_output(tsmCmd +
                                       " -dataonly=yes " +
                                       "select volume_name from drives " +
                                       "where DRIVE_STATE=\\'LOADED\\' " +
                                       "and LIBRARY_NAME=\\'" +
                                       library + "\\'",
                                       shell=True,
                                       ).decode("utf-8")

    except subprocess.CalledProcessError as tsmexec:
        if tsmexec.returncode == 11:
            print("No mounted volumes found in the library.Continue..\n")
        else:
            print("TSM get mounted volumes command failed with return code:",
                  tsmexec.returncode)
            sys.exit(tsmexec.returncode)


# Get dictonary from Toml file.
def getInfoFromToml(tomlFile):
    with open(tomlFile) as conffile:
        return toml.loads(conffile.read())


# Compares the slots of TSM and Physical libraries, and print the results.
def compareAllAndPrint(libraryInventoryMap, libVolumesMap, mountedVols):

    print("\n|\tSLOT\t|\tTSM ENTRY\t|\tPhysical Entry\t|\tResult\t|\n")

    maximum = max(libraryInventoryMap.keys(), key=int)
    mininum = min(libraryInventoryMap.keys(), key=int)

    for x in range(int(mininum), int(maximum) + 1):

        if str(x) not in libraryInventoryMap:
            libInvVol = "Empty..."
        else:
            libInvVol = libraryInventoryMap[str(x)]

        if str(x) not in libVolumesMap:
            tsmLibVol = "Empty..."
        else:
            tsmLibVol = libVolumesMap[str(x)]

        if libInvVol == tsmLibVol:
            result = "\033[92mOK\033[97m"
            if args.outmode == "ALL":
                print("|\t{}\t|\t{}\t|\t{}\t|\t{}\t|"
                      .format(x, tsmLibVol, libInvVol, result))
        else:
            if mountedVols and tsmLibVol in mountedVols:
                result = "\033[44mMOUNTED\033[49m"
                if args.outmode == "ALL":
                    print("|\t{}\t|\t{}\t|\t{}\t|\t{}\t|"
                          .format(x, tsmLibVol, libInvVol, result))
            else:
                result = "\033[41mKO\033[49m"
                print("|\t{}\t|\t{}\t|\t{}\t|\t{}\t|"
                      .format(x, tsmLibVol, libInvVol, result))


def compareTapeAndPrint(libraryInventoryMap, libVolumesMap,
                        mountedVols, volumeName):
    print("Compare Slots for", volumeName)
    isInTSM = False
    isInPhysical = False
    try:
        tsmSlot = list(libVolumesMap.keys())[list(libVolumesMap.values())
                                             .index(volumeName)]

        print("TSM entry: ", tsmSlot)
        isInTSM = True
    except ValueError:
        print("Volume not found in TSM library")

    try:
        physicalSlot = list(libraryInventoryMap.keys())[list(
            libraryInventoryMap.values())
            .index(volumeName)]

        print("Physical Library entry: ", physicalSlot)
        isInPhysical = True
    except ValueError:
        print("Volume not found in Physical library")

    if not isInTSM:
        tsmSlot = "Not found!"

    if not isInPhysical:
        physicalSlot = "Not found!"

    if not isInTSM and not isInPhysical:
        print("Volume {} couldn't be found in TSM and Physical Library."
              .format(volumeName))
        sys.exit()

    if tsmSlot == physicalSlot:
        result = "\033[92mOK\033[97m"
    else:
        if mountedVols and volumeName in mountedVols:
            result = "\033[44mMOUNTED\033[49m"
        else:
            result = "\033[41mKO\033[49m"

    print("Result:", result)

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
    tsmName = args.tsm
    try:
        configInfo = getInfoFromToml(args.config)
    except FileNotFoundError as error:
        print("File not found.\n", error)
        sys.exit()

    # Check if TSM exists in the configuration file.
    if tsmName not in configInfo['TSM_SERVERS']:
        print("TSM {} not found in the configuration file.".format(tsmName))
        sys.exit()

    # Set all information needed to connect to TSM server and the host server.
    tsmDetails = configInfo['TSM_SERVERS'][tsmName]
    tsmUsername = tsmDetails['tsmUser']
    tsmPassword = tsmDetails['tsmPass']
    tsmIp = tsmDetails['tsmIp']
    username = tsmDetails['username']
    password = tsmDetails['password']

    global tsmCmd
    tsmCmd = "dsmadmc -se={} -id={} -pa={}" \
        .format(tsmName, tsmUsername, tsmPassword)
    libraries = getLibraries(tsmName)

    if "ANS1017E" in libraries:
        print("Session rejected: TCP/IP connection failure.")
        sys.exit()
    # Get library from user's selection menu.
    selectedLibrary = selectLibraryMenu(libraries.split())
    print("Library Selected is", selectedLibrary, end="")

    # Get library's device from TSM server.
    device = getDevice(selectedLibrary).replace("\n", "")
    print(" and device is", device)

    # Create a dictonary with which volumes are in which slots,
    # in Physical library
    libraryInventoryMap = getLibraryInventory(
        tsmIp, username, password, device)

    # Get libvolumes and element information from TSM server library.
    libVolumesMap = getLibVolumes(selectedLibrary)

    # Get volumes that are currently mounted in TSM server.
    # This is to ignore error, because the slot in the physical library
    # will be empty, since the volume is mounted on a disk slot.
    mountedVols = getMountedVolumes(selectedLibrary)

    if args.volume:
        compareTapeAndPrint(libraryInventoryMap,
                            libVolumesMap, mountedVols, args.volume)
    else:
        # Finally compare everything and print output.
        compareAllAndPrint(libraryInventoryMap, libVolumesMap, mountedVols)

    # Clear colors.
    print("\033[0m")
