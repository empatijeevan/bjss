#!/usr/bin/python3
import os
import csv
import requests
from requests.structures import CaseInsensitiveDict
import json
import time

baseURL = os.environ.get('bamboo_ConfBaseURL')
apikey = os.environ.get('bamboo_ConfAPIKeySecret')

headers = { 'Authorization': 'Bearer ' + apikey}

outputfilename = "../output/confqueries.sql"
errorfilename = "../output/conferrors.txt"

#guests = ["nhs.net", "dhsc.gov.uk"]
members = ["nihp.nhs.uk", "test-and-trace.nhs.uk"]

outputfile = open(outputfilename, "x")
outputfile.write("")
outputfile.close()
errorfile = open(errorfilename, "x")
errorfile.write("")
errorfile.close()

file = open("../input/mappings.csv")
csvfile = csv.reader(file)
header = next(csvfile)
mappings = []
for row in csvfile:
    # Changes source username to source UPN if in the members list
    if str(row[0].split("@")[1]) not in members:
        sourceupn = str(row[0].split("@")[0]) + "." + str(row[0].split("@")[1].split(".")[0]) + "@test-and-trace.nhs.uk"
    else:
        # If in members list, set UPN to email
        sourceupn = row[0]
    # Changes source username to source UPN if in the members list
    if str(row[1].split("@")[1]) not in members:
        targetupn = str(row[1].split("@")[0]) + "." + str(row[1].split("@")[1].split(".")[0]) + "@test-and-trace.nhs.uk"
    else:
        # If in members list, set UPN to email
        targetupn = row[1]
    mappings.append((row[0], sourceupn, row[1], targetupn))
    
file.close()

# for x in mappings:
#     print(x)
print("")

requestURL = baseURL + '/rest/api/user'

successcount = 0
failcount = 0

outputfile = open(outputfilename, "a")
errorfile = open(errorfilename, "a")

for row in mappings:
    success = True
    parameters = {
        "username": row[1],
    }
    try:
        response = requests.get(requestURL, headers=headers, params=parameters)
        userkey = response.json()['userKey']
        olduserkey = userkey
    except: 
        olduserkey = "Not found"
        success = False

    parameters = {
        "username": row[3],
    }
    try:
        response = requests.get(requestURL, headers=headers, params=parameters)
        userkey = response.json()['userKey']
        newuserkey = userkey
    except: 
        newuserkey = "Not found"
        success = False
    
    if success == True:
        successcount = successcount + 1
        print("[\x1b[1;32;40m", successcount, "\x1b[0m-\x1b[1;31;40m", failcount, "\x1b[0m] | \x1b[1;32;40mSuccess\x1b[0m -", row[1], "(", olduserkey, ") --->", row[3], "(", newuserkey, ")")

        outputfile.write("UPDATE user_mapping SET username = 'placeholder-" + olduserkey + "', lower_username = 'placeholder-" + olduserkey + "' where user_key = '" + olduserkey + "';\n")
        outputfile.write("UPDATE user_mapping SET username = '" + row[1] + "', lower_username = '" + row[1].lower() + "' where user_key = '" + newuserkey + "';\n")
        outputfile.write("UPDATE user_mapping SET username = '" + row[3] + "', lower_username = '" + row[3].lower() + "' where user_key = '" + olduserkey + "';\n")


    else:
        failcount = failcount + 1
        print("[\x1b[1;32;40m", successcount, "\x1b[0m-\x1b[1;31;40m", failcount, "\x1b[0m] | \x1b[1;31;40mFail\x1b[0m -", row[1], "(", olduserkey, ") --->", row[3], "(", newuserkey, ")")

        if olduserkey == "Not found" and newuserkey == "Not found":
            errorfile.write("Source user (" + row[1] + ") AND target user (" + row[3] + ") not found at " + baseURL + ".\n")
        elif olduserkey == "Not found":
            errorfile.write("Source user (" + row[1] + ") not found at " + baseURL + ".\n")
        elif newuserkey == "Not found":
            errorfile.write("Target user (" + row[3] + ") not found at " + baseURL + ".\n")

outputfile.close()
errorfile.close()
print("\n---")
print("Successful:", successcount)
print("Failed:", failcount)
print("---\n")
