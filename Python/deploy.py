# upload = deployment of all specified playthings to one function app
# relies on zip file created by pre_deploy.py

# from profile.publishsettings (Azure portal function app > Deployment Center)
app_name = "dlpg-demo"
deployment_user = "$dlpg-demo"
deploy_password_env = "DLPGDEMO_DEPLOY_PWD"  # environment var containing the deployment password

deploy_url = f"https://{app_name}.scm.azurewebsites.net/api/zipdeploy"
zip_path = "../DEPLOY.zip"


import requests
from requests.auth import HTTPBasicAuth
import json
from time import sleep
from os import environ

auth = HTTPBasicAuth(deployment_user, environ[deploy_password_env])  # will get 401 for GET below if not set is desired

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

    # poll progress
    complete = False
    initial = True
    while not complete:
        resp = requests.get(poll_url,  auth=auth)
        progress = json.loads(resp.text)
        if isinstance(progress, list):
            progress = progress[0]
        if initial:
            log_url = progress.get("log_url", None)
            if log_url is not None:
                print("*" * 50)
                print("Log URL: ", log_url)
                print("*" * 50)
                initial = False
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
