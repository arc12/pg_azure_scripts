# copy the specified plaything files into DEPLOY and zip

deploy_playthings = [  # folder names (these contain the plaything repo files).
    "attribute-issues-pt",  # the first one MUST contain an up-to-date pg_shared and suitable hosts.json
    "hello-world-pt",
    "simpsons-pt",
    "word-generator-pt"
]

# path to folder containing the playthings, which will also be used to create DEPLOY folder
base_path = ".."

skip_dirs = ["__pycache__", ".git", ".vscode"]
skip_files = [".git", ".gitignore", ".gitmodules", ".funcignore", "local.settings.json", "main.py", "README.md", "requirements.txt"]
first_only_files = ["host.json"]  # copy only from 1st listed plaything (files which exist for all)

from os import chdir, walk, path, rmdir, listdir, remove, mkdir
from shutil import copyfile
from zipfile import ZipFile, ZIP_DEFLATED

chdir(base_path)

# clean DEPLOY
def deep_del(start_dir):
    if path.exists(start_dir):
        for item in listdir(start_dir):
            item_path = path.join(start_dir, item)
            if path.isfile(item_path):
                remove(item_path)
            else:
                deep_del(item_path)
        rmdir(start_dir)
deep_del("DEPLOY")
mkdir("DEPLOY")

requirements_entries = set()

with ZipFile("DEPLOY.zip", 'w', compression=ZIP_DEFLATED) as z:
    for pt in deploy_playthings:
        # read and accumulate requirements
        with open(path.join(pt, "requirements.txt"), 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or (len(line) == 0):
                    continue
                requirements_entries.add(line)
        # make dirs and copy files. This will throw an exception if any dir already exists, which should only happen if a developer fails to follow dir name conventions
        for root, dirs, files in walk(pt):
            print(root)
            dirs[:] = [d for d in dirs if d not in skip_dirs]  # this in an in-place modification of dirs, which is rquired to prune what is used in the next iteration of walk
            for dn in dirs:
                mkdir(path.join(root, dn).replace(pt, "DEPLOY"))
                # provisional cheat - exclude pg_shared from future iterations. # TODO fetch pg_shared from github to ensure latest.
                if dn == "pg_shared":
                    skip_dirs.append(dn)
            for fn in files:
                if fn not in skip_files:
                    f_path = path.join(root, fn)
                    copyfile(f_path, f_path.replace(pt, "DEPLOY"))
                    z.write(f_path, arcname=f_path.replace(pt, ""))
                    print(f"F: {fn}")
                    if (fn in first_only_files) and (pt == deploy_playthings[0]):
                        skip_files.append(fn)

    # synthesise requirements.txt as the union of all.
    # This will only work if versions are either not used or kept in sync. If not in sync, the multiple entries will surely cause barf, swearing, ...
    req_path = path.join("DEPLOY", "requirements.txt")
    with open(req_path, 'w') as f:
        f.writelines([f"{r}\n" for r in requirements_entries])
    z.write(req_path, arcname="requirements.txt")