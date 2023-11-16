# upload the Config folder to Azure file share
# This will upload all files found locally but not delete anything on Azure. Hence: it can be pointed at a local "patch" folder with only new/updated material.
from azure.storage.fileshare import ShareClient

# resource_group = "Playground"
# storage_container = "dlpgstorage"
account_url = "https://dlpgstorage.file.core.windows.net"
share_name = "config"

# can find token in portal or by "az storage account keys list -g Playground -n dlpgstorage". Store in env var DLPGSTORAGE_KEY

local_path = "../Config"
ignore_items = ".git"

from os import listdir, path, environ

sc = ShareClient(account_url, share_name=share_name, credential=environ["DLPGSTORAGE_KEY"])  # exception if not set is desired

# recursive function is a bit messy keeping track of parallel local/Azure paths with possible Windows path separators
def process_level(rel_dir = ""):
    full_dir = path.join(local_path, rel_dir)
    remote_dirs = [az["name"] for az in sc.list_directories_and_files(rel_dir) if az["is_directory"]]
    for item in [i for i in listdir(full_dir) if i not in ignore_items]:
        item_path = path.join(full_dir, item)
        az_path = rel_dir.replace("\\", "/")   
        az_path += ("/" if len(az_path) > 0 else "") + item
        if path.isfile(item_path):
            print(f"upload {item} to {rel_dir}")
            fc = sc.get_file_client(az_path)
            with open(item_path, 'rb') as f:
                fc.upload_file(f)
        elif path.isdir(item_path):
            if item not in remote_dirs:
                print(f"create remote dir {item} in {rel_dir}")
                sc.create_directory(az_path)
            process_level(path.join(rel_dir, item))

process_level()

print("FINISHED")