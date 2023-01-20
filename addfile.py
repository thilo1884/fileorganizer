import fileinput
import csv
import json
import re
import os
import shutil
import ntpath
import filecmp
import argparse

# dictionary that maps the file-extensions and the folder where the file needs to be stored to
dicOfExtFile = {"docs": ["txt", "odt"], 
                "audio": ["mp3"],
                "image": ["png", "jpg", "jpeg"]
               }

class dataFile(object):
    def __init__(self, name, type, size): 
        self.name = name 
        self.type = type
        self.size = size

    def show(self):
        print(self.name, self.type, self.size)

class fileCSV(object):
    def __init__(self, path): 
        self.namefile = os.path.basename(path)
        self.path = path

    def updateListDataInCsv(self, item):
        with fileinput.input(files=(self.path), inplace=True, mode='r') as f:
            reader = csv.DictReader(f)
            print(",".join(reader.fieldnames))  # print back the headers
            for row in reader:
                if row["name"] == item.name and row["type"] == item.type:
                    row["size(B)"] = str(item.size)
                print(",".join([row["name"], row["type"], row["size(B)"]]))

    def appendDataItem(self, item):
        fields=[item.name, item.type, str(item.size)]
        # fields=['first','second','third']
        with open(self.path, 'a',  newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fields)

    def createNewCSV(self):
        headerList = ['name', 'type', 'size(B)']
        # open CSV file and assign header
        with open(self.path, 'w', newline='') as file:
            dw = csv.DictWriter(file, delimiter=',', 
                                fieldnames=headerList)
            dw.writeheader()

class FileOrganizer(object):
    def __init__(self, mainfolder, csvname): 
        self.mainfolder = mainfolder
        self.csvFile = fileCSV(csvname)
        # create a new file only if it's not present already
        pwd = os.path.abspath(os.getcwd())
        pathToCSVFile = os.path.join(pwd, csvname)
        if os.path.exists(pathToCSVFile) == False:
            self.csvFile.createNewCSV()    
             
    # create the folder in the current path
    def createFolder(self, folderName):
        # get the current path 
        pwd = os.path.abspath(os.getcwd())
        pathToFolder = os.path.join(pwd, self.mainfolder, folderName)
        # create the folder (if it is not there yet)
        try:
            res = os.mkdir(pathToFolder) 
        except FileExistsError:
            res = ""

    def moveFileInFolder(self, folderName, nameFile):
        pwd = os.path.abspath(os.getcwd())
        pathToOriginFile = os.path.join(pwd, self.mainfolder, nameFile)
        pathToDestinationFile = os.path.join(pwd, "files", folderName, nameFile)
        # Check the following scenarios:
        # if the file already exists and is the same: remove the file and do nothing with csv
        # if the file already exists and is different (e.g. different size): overwrite the file
        #                                                                    and update csv
        # if the file does not exist: move it and update csv
        if os.path.exists(pathToDestinationFile):
            if filecmp.cmp(pathToDestinationFile, pathToOriginFile):
                os.remove(pathToDestinationFile) # ?necessary?
            else:
                shutil.move(pathToOriginFile, pathToDestinationFile)
                data = self.printHandleFile(pathToDestinationFile)
                # in this case update the entry file in csv
                self.csvFile.updateListDataInCsv(data)

        else:
            shutil.move(pathToOriginFile, pathToDestinationFile)
            data = self.printHandleFile(pathToDestinationFile)
            # in this case append the entry file in csv
            self.csvFile.appendDataItem(data)

    # get the folder name that needs to be created based on the extension file based on map dicOfExtFile
    def getKey(self, fileExt):
        test = fileExt
        key = [dictionary for dictionary, listOfExts in dicOfExtFile.items() if test in listOfExts]
        if key:
            # convert the extracted key in string and trimmer/clean the key (e.g. from ['audio'] to audio)
            keyString = json.dumps(key)
            keyString = re.sub(r'[^a-zA-Z0-9 ]',r'',keyString)
            return keyString
        else:
            #key not found
            return


    def loopFilesFolder(self):
        pwd = os.path.abspath(os.getcwd())
        pathToFiles =  os.path.join(pwd, self.mainfolder)
        for filename in os.listdir(pathToFiles):
            f = os.path.join(pathToFiles, filename)
            # checking if it is a file
            self.handleFile(f)  

    def handleFile(self, pathToNewFile):
        if os.path.isfile(pathToNewFile):
            filename = ntpath.basename(pathToNewFile)
            # get the extension file and remove the . (e.g. '.jpg')
            ext = os.path.splitext(filename)[1][1:]
            folderName = self.getKey(ext)
            # check folderName is not empty
            if folderName:
                self.createFolder(folderName)
                self.moveFileInFolder(folderName, filename)

    def printHandleFile(self, pathToNewFile):
        filename = ntpath.basename(pathToNewFile)
        name, ext = os.path.splitext(filename)
        ext = ext[1:]
        type = self.getKey(ext)
        file_stats = os.stat(pathToNewFile)
        print("{} type:{} size{}B".format(name,type, file_stats.st_size))
        d = dataFile(name, type, file_stats.st_size)
        return d


def getFileName(filename):
    return os.path.join("files", filename)

# here the script starts
fileOrganizer = FileOrganizer("files", "files\\recap.csv")   

# get input argument
parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Name of the file that will be organized")
args = parser.parse_args()

# chech if the user file in args exists
pwd = os.path.abspath(os.getcwd())
pathToInputfile = os.path.join(pwd, fileOrganizer.mainfolder,args.filename)
if os.path.exists(pathToInputfile):
    fileOrganizer.handleFile(getFileName(args.filename))
else:    
     print("The 'new' file {} does not exists in folder {}".format(args.filename, os.path.join(pwd, fileOrganizer.mainfolder)))
