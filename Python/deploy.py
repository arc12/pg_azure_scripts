# upload = deployment of all specified playthings to one function app
# relies on zip file created by pre_deploy.py

# from profile.publishsettings (Azure portal)
deployment_user = "$dlpg-test1"
# pwd stored in env variable DLPGTEST1_DEPLOY_PWD
# app_name = "dlpg-test1"
deploy_url = "https://dlpg-test1.scm.azurewebsites.net/api/zipdeploy"
zip_path = "../DEPLOY.zip"

import requests
from requests.auth import HTTPBasicAuth
import json
from time import sleep
from os import environ

auth = HTTPBasicAuth(deployment_user, environ["DLPGTEST1_DEPLOY_PWD"])  # exception if not set is desired

# check existing deployments and allow bail out
resp = requests.get(deploy_url.replace("zipdeploy", "deployments"),  auth=auth)
if resp.status_code != 200:
    print("FAILED to get list of existing deployments; HTTP status = ", resp.status_code)
    exit()
progress = json.loads(resp.text)
proceed = True
if len(progress) > 0:
    print("EXISTING DEPLOYMENTS")
    print(json.dumps(progress, indent=2))
    proceed = input("Enter 'y' to proceed with deployment: ") == "y"
    
if proceed:
    with open(zip_path, 'rb') as z:
        print("Posting Zip")
        resp = requests.post(f"{deploy_url}?isAsync=true", files={"file": z}, auth=auth)
        print("HTTP response code:", resp.status_code)
        if resp.status_code > 400:
            exit()
        print(json.dumps(dict(resp.headers), indent=2))
        poll_url = resp.headers.get("Location", None)
        print("Log URL: ", resp.log_url)

    # poll progress
    complete = False
    while not complete:
        resp = requests.get(poll_url,  auth=auth)
        progress = json.loads(resp.text)
        if isinstance(progress, list):
            progress = progress[0]
        print(progress["status_text"])
        print(progress["message"])
        print(progress["progress"])
        print(f"active: {progress['active']}, complete: {progress['complete']}")
        print()
        complete = progress['complete']
        if not complete:
            print("sleeping 10s")
            sleep(10)

    print("COMPLETED")
else:
    print("ABORTED")
