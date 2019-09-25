
"""This is the core module to manipulate Comae Snapshots files
__version__ = '0.1'
__author__ = 'Comae Technologies'
"""

import json
import os

__version__ = '0.1'
__author__ = 'Comae Technologies'

def getFilesFromDirectory(dir):
    files = []
    for r, d, f in os.walk(dir):
        for file in f:
            if '.json' in file:
                files.append(file)
    return files

class ComaeSnapshot:
    def __init__(self, snapshorDir):
        self.snapshorDir = snapshorDir

        self.processes = getFilesFromDirectory(snapshorDir + "/Processes/")
        self.drivers = getFilesFromDirectory(snapshorDir + "/Drivers/")

        if 'Info.json' in self.processes:
            self.processes.remove('Info.json')
        if 'Info.json' in self.drivers:
            self.drivers.remove('Info.json')

    def getProcessById(self, pid):
        base = self.snapshorDir + "/Processes/"

        for process in self.processes:
            with open(base + process, "r") as f:
                data = json.load(f)
                # print("%s (%d)" % (data['processObject']['imageFileName'], data['processObject']['processId']))
                if data['processObject']['processId'] == pid:
                    return data

        return False

    def getProcess(self, process):
        base = self.snapshorDir + "/Processes/"
        with open(base + process, "r") as f:
            data = json.load(f)
            # print("%s (%d)" % (data['processObject']['imageFileName'], data['processObject']['processId']))
            return data
        return False

######################################################################################################

snapshot = ComaeSnapshot("MACHINE12345-20190922-071725")

print("[Test 1] Query existing process")
data = snapshot.getProcessById(6872)
if data:
    print("%s process found." % (data['processObject']['imageFileName']))
else: 
    print("Process not found. 6872")

print("[Test 2] Query non existing process")
data = snapshot.getProcessById(1337)
if data:
    print("%s process found." % (data['processObject']['imageFileName']))
else: 
    print("Process not found. 1337")

print("[Test 3] Listing processes")
for process in snapshot.processes:
    data = snapshot.getProcess(process)
    if data:
        print("%s (%d)" % (data['processObject']['imageFileName'], data['processObject']['processId']))