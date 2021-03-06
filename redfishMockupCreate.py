# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Mockup-Creator/LICENSE.md

# redfishMockupCreate:  ver 0.9.1
#
# contains:
#
import os
import sys
import getopt
import re
import json
from redfishtoollib  import RfTransport
# uses same transport that is used by redfishtool.
# only the program name, date, and version is changed
import errno
import datetime



# rootservice navigation properties
rootLinks=["Systems","Chassis", "Managers", "SessionService", "AccountService", "Registries", "JsonSchemas", "Tasks" ]
# list of navigation properties for each root service nav props
resourceLinks={
        # rootResource: [list of sub-resources],
        "Systems": [ "Processors", "SimpleStorage", "EthernetInterfaces", "LogServices", "Memory"],
        "Chassis": ["Power", "Thermal", "LogServices"],
        "Managers": ["NetworkProtocol", "EthernetInterfaces", "SerialInterfaces", "LogServices"],
        "SessionService": ["Sessions"],
        "AccountService": ["Accounts", "Roles"],
        "Registries": [],
        "JsonSchemas": [],
        "Tasks": ["Tasks"]
}



def displayUsage(rft,*argv,**kwargs):
        rft.printErr("  Usage:",noprog=True)
        rft.printErr("   {} [-VhvqS] -u<user> -p<passwd> -r<rhost[<port>] [-A <auth>] [-D <dir>]",prepend="  ")
        rft.printErr("   where -S is https",     prepend="  ")
              
def displayOptions(rft):
        print("")
        print("  Common OPTIONS:")
        print("   -V,          --version           -- show {} version, and exit".format(rft.program))
        print("   -h,          --help              -- show Usage, Options".format(rft.program))
        print("   -v,          --verbose           -- verbose level, can repeat up to 4 times for more verbose output")
        print("                                       -v ")
        print("   -q,          --quiet             -- quiet mode. no progress messages are displayed")
        print("   -S,          --Secure            -- use HTTPS for all gets.   otherwise HTTP is used")
        print("   -u <user>,   --user=<usernm>     -- username used for remote redfish authentication")
        print("   -p <passwd>, --password=<passwd> -- password used for remote redfish authentication")
        print("   -r <rhost>,  --rhost=<rhost>     -- remote redfish service hostname or IP:port")
        print("   -A <Auth>,   --Auth=<auth>       -- auth method ot use: None, Basic(dflt), Session ")
        print("   -D <directory>,--Dir=<directory> -- output mockup to directory path <directory>")
        print("   -d <description> --description=<d> -- text description that is put in README. ex: -d \"mockup of Contoso 1U\" ")
        print("")




def main(argv):
    # Resource, links used to drive the mockup creation
    # in future, mockupCreate could follow schemas, but initial 1.0 uses these


    # program flow:
    #
    # parse main options
    # write README file to top of mockup directory
    # create /redfish, /redfish/v1, /redfish/v1/odata, and /redfish/v1/$metadata folders/files
    # create folders/files for apis under root
    #  for res in rootLinks:  (eg Systems, AccountService)
    #    mkdir ./res
    #    CreateIndexFile(./res/index.json)     --- read,write to index.json
    #    if(type is collection)  (eg Systems, Chassis)
    #      for each member,
    #        mkdir, create index.json
    #        subLinks=resourceLinks[res]  
    #        for res2 in sublinks:    (eg Processors, LogService, Power)
    #           mkdir ./res/res2, CreateIndexFile(./res/res2/index.json)
    #           if(type is collection)  (eg Processors)
    #               for each member, mkdir, create index.json
    #               if(type is LogService)
    #                   mkdir ./res/res2/member
    #                   CreateIndexFile for log Entries
    #   else //not a collection (eg AccountService)
    #        for res2 in sublinks:    (eg Accounts)
    #           mkdir ./res/res2, CreateIndexFile(./res/res2/index.json)
    #           if(type is collection)  (eg Accounts, Sessions)
    #               for each member, mkdir, create index.json


    #instantiate transport object which initializes default options
    #    this is the same transport that is used by redfishtool, with program=redfishMockupCreate
    rft=RfTransport()

    # set default verbose level to 1.  so -v will cause verbose level to go to 2
    rft.verbose=1
    
    #initialize properties used here in main
    mockDirPath=None
    mockDir=None
    description=None
    rfFile="index.json"
    
    try:
        opts, args = getopt.gnu_getopt(argv[1:],"VhvqSu:p:r:A:D:d:",
                        ["Version", "help", "quiet", "Secure=",
                         "user=", "password=", "rhost=","Auth=","Dir=, description=]"])
    except getopt.GetoptError:
        rft.printErr("Error parsing options")
        displayUsage(rft)
        sys.exit(1)
        
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            rft.help=True
            displayUsage(rft)
            displayOptions(rft)
            sys.exit(1)
        elif opt in ("-V", "--version"):
            print("{} Version: {}".format(rft.program, rft.version))
            sys.exit(0)
        elif opt in ("-v"):
            rft.verbose = min((rft.verbose+1), 5)
        elif opt in ("-u", "--user"):
            rft.user=arg
        elif opt in ("-p", "--password"):
            rft.password=arg
        elif opt in ("-r", "--rhost"):
            rft.rhost=arg
        elif opt in ("-D", "--Dir"):
            mockDirPath=arg
        elif opt in ("-d", "--description"):
            description=arg
        elif opt in ("-S", "--Secure"):
            rft.secure="Always"
        elif opt in ("-q", "--quiet"):
            rft.quiet=true
        elif opt in ("-A", "--Auth"):           # specify authentication type
            rft.auth=arg
            if not rft.auth in rft.authValidValues:
                rft.printErr("Invalid --Auth option: {}".format(rft.auth))
                rft.printErr("   Valid values: {}".format(rft.authValidValues),noprog=True)
                sys.exit(1)
        else:
            rft.printErr("Error: Unsupported option: {}".format(opt))
            displayUsage(rft)
            sys.exit(1)

    if( rft.rhost is None):
        rft.printErr("Error: -r rHost was not specified and is required by this command. aborting")
        displayUsage(rft)
        displayOptions(rft)
        sys.exit(1)
    if( rft.user is None):
        rft.printErr("Error: -u user was not specified and is required. aborting")
        displayUsage(rft)
        displayOptions(rft)
        sys.exit(1)
    if( rft.password is None):
        rft.printErr("Error: -p password was not specified and is required. aborting")
        displayUsage(rft)
        displayOptions(rft)
        sys.exit(1)


    rft.printVerbose(5,"Main: verbose={}, User={}, Password={}, rhost={}".format(rft.verbose,
                                                        rft.user,rft.password,rft.rhost))
    rft.printVerbose(5,"Main: Auth={}, quiet={}, Secure={}, Dir={} timeout={}".format(rft.token,
                                            rft.auth, rft.quiet, rft.secure, mockDirPath, rft.timeout))

    rft.printVerbose(5,"Main: options parsed.  Now lookup subcommand and execute it")

    # verify we can talk to the rhost
    rc,r,j,d=rft.getVersions(rft,cmdTop=True)
    if( rc != 0 ):
        rft.printErr("ERROR: Cant find Redfish Service at rhost sending GET /redfish  request. aborting")
        sys.exit(1)

    # check if directory redfish is there.  If not, use current working directory
    if mockDirPath is None:
        mockDirPath=os.getcwd()

    #create the full path to the top directory holding the Mockup  
    mockDir=os.path.realpath(mockDirPath) #creates real full path including path for CWD to the -D<mockDir> dir path

    # print out rhost and directory path
    rft.printVerbose(1,"rhost: {}".format(rft.rhost))
    rft.printVerbose(1,"full directory path: {}".format(mockDir))
    rft.printVerbose(1,"description: {}".format(description))
    rft.printVerbose(1,"starting mockup creation")

    #make sure directory is empty (no READ file), and create Read file
    readmeFile=os.path.join(mockDir, "README")
    if os.path.isfile(readmeFile) is True:
        rft.printErr("ERROR: READM file already exists in this directory. aborting")
        sys.exit(1)

    rfdatetime=str(datetime.datetime.now())
    rfdatetime=rfdatetime.split('.',1)[0]
    with open(readmeFile, 'w', encoding='utf-8') as readf:
        readf.write("Redfish Service state stored in Redfish Mockup Format\n")
        readf.write("Program: {},  ver: {}\n".format(rft.program, rft.version))
        readf.write("Created: {}\n".format(rfdatetime))
        readf.write("rhost:  {}\n".format(rft.rhost))
        readf.write("Description: {}\n".format(description))
    if os.path.isfile(readmeFile) is False:
        rft.printErr("ERROR: cant create README file in directory. aborting")
        sys.exit(1)

    #create a ^/redfish directory.  Exit if one already exists--that is an error
    rft.printVerbose(1,"Creating /redfish resource")
    dirPath=os.path.join(mockDir, "redfish")
    if( rfMakeDir(rft, dirPath) is False ):
        rft.printErr("ERROR: cant create /redfish directory. aborting")
        sys.exit(1)

    #copy the versions output to ^/redfish/index.json
    filePath=os.path.join(dirPath,rfFile)
    with open( filePath, 'w', encoding='utf-8' ) as f:
        f.write(r.text)

    #create the /redfish/v1 root dir and copy output of Get ^/redfish/v1 to index.json file
    rft.printVerbose(1,"Creating /redfish/v1 resource")
    rc,r,j,d=rft.rftSendRecvRequest(rft.UNAUTHENTICATED_API, 'GET', r.url, relPath=rft.rootPath)
    if(rc!=0):
        rft.printErr("ERROR: Cant read root service:  GET /redfish/ from rhost. aborting")
        sys.exit(1)
    dirPath=os.path.join(mockDir, "redfish", "v1")
    if( rfMakeDir(rft, dirPath) is False ):
        rft.printErr("ERROR: cant create /redfish/v1 directory. aborting")
        sys.exit(1)
    filePath=os.path.join(dirPath,rfFile)
    with open( filePath, 'w', encoding='utf-8' ) as f:
        f.write(r.text)

    #save the rootURL for later re-use  (if we were redirected, we get the redirected url here)
    rootUrl=r.url
    rootRes=d
           
    #get /redfish/v1/odata and save to mockup
    rft.printVerbose(1,"Creating /redfish/v1/odata resource")
    api="odata"
    rc,r,j,d=rft.rftSendRecvRequest(rft.UNAUTHENTICATED_API, 'GET', rootUrl, relPath=api, jsonData=True )
    if(rc!=0):
        rft.printErr("ERROR: Cant read mandatory API: /redfish/v1/odata. Continuing w/o creating mockup entry")
    else:
        dirPath=os.path.join(mockDir, "redfish", "v1", api)
        if( rfMakeDir(rft, dirPath) is False ):
            rft.printErr("ERROR: cant create directory: /redfish/v1/{}. aborting".format(api))
            sys.exit(1)
        filePath=os.path.join(dirPath,rfFile)
        with open( filePath, 'w', encoding='utf-8' ) as f:
            f.write(r.text)
            
    #get /redfish/v1/$metadata and save to mockup.   Note this is an .xml file stored as index.xml in mockup
    rft.printVerbose(1,"Creating /redfish/v1/$metadata resource")
    api="$metadata"
    # set content-type to xml  (dflt is application/json)
    hdrs = {"Accept": "application/xml", "OData-Version": "4.0" }
    rc,r,j,d=rft.rftSendRecvRequest(rft.UNAUTHENTICATED_API, 'GET', rootUrl, relPath=api, jsonData=False,
                                    headersInput=hdrs)
    if(rc!=0):
        rft.printErr("ERROR: Cant read mandatory API: /redfish/v1/$metadata. Continuing w/o creating mockup entry")
    else:
        dirPath=os.path.join(mockDir, "redfish", "v1", api)
        if( rfMakeDir(rft, dirPath) is False ):
            rft.printErr("ERROR: cant create directory: /redfish/v1/{}. aborting".format(api))
            sys.exit(1)
        filePath=os.path.join(dirPath,"index.xml")
        with open( filePath, 'w', encoding='utf-8' ) as f:
            f.write(r.text)

    # now make create subdirectories for rootService
    # for res in rootLinks:
    #    read the res
    #    mkdir ./res
    #    CreateIndexFile(./res/index.json)     --- read,write to index.json
    #    if(type is collection)
    #        for each member, mkdir, create index.json

    # for res in rootLinks:
    #    mkdir ./res
    #    CreateIndexFile(./res/index.json)     --- read,write to index.json
    #    if(type is collection)
    #        for each member, mkdir, create index.json
    rft.printVerbose(1,"Start Creating resources under root service:")
    for rlink in rootLinks:
        #rft.printErr("rlink:{}".format(rlink))
        if(rlink in rootRes):
            link=rootRes[rlink]
            rft.printVerbose(1,"   Creating resource under root service navigation property: {}".format(rlink))
            rc,r,j,d=readResourceMkdirCreateIndxFile(rft, rootUrl, mockDir, link)
            if(rc!=0):
                rft.printErr("ERROR: got error reading root service resource--continuing. link: {}".format(link))
            resd=d

            # if res type is a collection, then for each member, read res, mkdir, create index file
            if isCollection(resd) is True:  # (eg Systems, Chassis...)
                for member in resd["Members"]:
                    rft.printVerbose(4,"    Collection member: {}".format(member))
                    rc,r,j,d=readResourceMkdirCreateIndxFile(rft,rootUrl, mockDir, member)
                    if(rc!=0):
                        rft.printErr("ERROR: got error reading root service collection member--continuing. link: {}".format(member))
                    memberd=d
                    sublinklist=resourceLinks[rlink]
                    rc,r,j,d=addSecondLevelResource(rft, rootUrl,mockDir,  sublinklist, memberd)
                    if(rc!=0):
                        rft.printErr("ERROR: Error processing 2nd level resource (8)--continuing. link:{}".format(member))
            else:   # its not a collection. (eg accountService) do the 2nd level resources now
                sublinklist=resourceLinks[rlink]
                rc,r,j,d=addSecondLevelResource(rft, rootUrl, mockDir, sublinklist, resd)
                if(rc!=0):
                    rft.printErr("ERROR: Error processing 2nd level resource (9) --continuing")

    rft.printVerbose(1," {} Completed creating mockup".format(rft.program))
    sys.exit(0)





def rfMakeDir(rft, dirPath):
    success=True
    try:
        os.makedirs(dirPath)
    except OSError as ee:
        if( ee.errno == errno.EEXIST):
            rft.printErr("ERROR: rfMakeDir: Directory: already exists. aborting")
            rft.printErr("Directory: {} ".format(dirPath),noprog=True,prepend="            ")
            success=False
        else:
            rft.printErr("ERROR: rfMakeDir: Error creating directory: {}".format(ee.errno))
            success=False
    return(success)



def readResourceMkdirCreateIndxFile(rft, rootUrl, mockDir, link,  jsonData=True):
    #print("building resource tree for link: {}".format(link))
    if not "@odata.id" in link:
        rft.printErr("ERROR:readResourceMkdirCreateIndxFile: no @odata.id property in link: {}".format(link))
        return(5,None,False, None)
    
    absPath=link["@odata.id"]
    if(absPath[0]=='/'):
        relPath=absPath[1:]
    else:
        relPath=absPath

    # read the resource.
    rc,r,j,d=rft.rftSendRecvRequest(rft.AUTHENTICATED_API, 'GET', rootUrl, relPath=absPath, jsonData=jsonData )
    if(rc!=0):
        rft.printErr("ERROR:readResourceMkdirCreateIndxFile: Error reading resource: link:{}".format(link))
        return(5,r,False, None)

    dirPath=os.path.join(mockDir, relPath)
    if( rfMakeDir(rft, dirPath) is False ):
        rft.printErr("ERROR:readResourceMkdirCreateIndxFile: for link:{}, path:{}, cant create directory: {}. aborting".format(link,absPath,dirPath))
        return(5,r,False, None)

    filePath=os.path.join(dirPath,"index.json")
    with open( filePath, 'w', encoding='utf-8' ) as f:
        f.write(r.text)
        
    return(rc, r, j, d )




# sublinklist=resourceLinks[rlink]
def addSecondLevelResource(rft, rootUrl, mockDir, sublinklist, resd):
    if( len(sublinklist)==0 ):
        return(0,None,False,None)
    for rlink2 in sublinklist:   #(ex Processors, Power)
        if( rlink2 in resd):
            link2=resd[rlink2]
            rft.printVerbose(4,"        Creating sub-property: {}".format(rlink2))
            rc,r,j,d=readResourceMkdirCreateIndxFile(rft,rootUrl, mockDir, link2,jsonData=True)
            if(rc!=0):
                rft.printErr("ERROR: got error reading 2nd level resource--continuing. link: {}".format(link2))
                return(rc,r,j,d)
            resd2=d
            # if collection, then get its members
            if isCollection(resd2) is True:  #ex Processors, get /1, /2
                for member2 in resd2["Members"]:
                    rft.printVerbose(4,"          Creating 2nd-level Collection member: {}".format(member2))
                    rc,r,j,d=readResourceMkdirCreateIndxFile(rft,rootUrl,mockDir, member2,jsonData=True)
                    resd3=d
                    if(rc!=0):
                        rft.printErr("ERROR: got error reading 2nd level collection member--continuing. link: {}".format(member2))
                        break
                    #if resource type is LogService, then get the entries expanded collection
                    ns,ver,resType=rft.parseOdataType(rft,resd3)
                    if( resType=="LogService" ):
                        if( "Entries" in resd3):
                            entriesLink=resd3["Entries"]
                            rft.printVerbose(2,"               Creating LogService Entries (Expanded Collection): {}".format(member2))
                            rc,r,j,d=readResourceMkdirCreateIndxFile(rft,rootUrl,mockDir, entriesLink,jsonData=False)
                            if(rc!=0):
                                rft.printErr("ERROR: got error reading logService Entries collection resource--continuing. link: {}".format(entriesLink))
        else:
            rft.printVerbose(2,"       No sub-properties in resource: {}")
            return(0,None,False,None)
    
    return(rc,r,j,d)



                                     

def isCollection(resource):
    if "Members" in resource:
        return True   # its a collection if it has a Members array  (sort of cheating)
    else:
        return False



if __name__ == "__main__":
    main(sys.argv)


'''

'''

