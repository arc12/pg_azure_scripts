# copy the specified plaything files into DEPLOY and zip
# also runs through the various README.md files and compiles more user-friendly output. This requires pypandoc (read coc about pandoc dependency at https://pypi.org/project/pypandoc/)

deploy_playthings = [  # folder names (these contain the plaything repo files).
    "attribute-issues-pt",  # the first one MUST contain an up-to-date pg_shared and suitable hosts.json
    "hello-world-pt",
    "simpsons-pt",
    "word-generator-pt"
]

# whether to deploy any *Timer folders, which should contain timerTrigger functions to make periodic calls to the Flask "ping" route to keep the app loaded (no cold starts)
deploy_timers = True

# path to folder containing the playthings, which will also be used to create DEPLOY folder
base_path = ".."

skip_dirs = ["__pycache__", ".git", ".vscode"]
skip_files = [".git", ".gitignore", ".gitmodules", ".funcignore", "local.settings.json", "main.py", "README.md", "requirements.txt"]
first_only_files = ["host.json"]  # copy only from 1st listed plaything (files which exist for all)

from os import chdir, walk, path, rmdir, listdir, remove, mkdir
from shutil import copyfile
from zipfile import ZipFile, ZIP_DEFLATED
import markdown
import fitz  # this is pymupdf !
from datetime import datetime as dt

chdir(base_path)

# make documentation, first cleaning old
print("Making merged documentation from markdown:")
out_file = "Playground Documentation.html"
try:
    remove(out_file)
except:
    pass
md_files = [path.join(deploy_playthings[0], "pg_shared", "Plaything Configuration.md")] \
    + [path.join(ptp, "README.md") for ptp in deploy_playthings]
md_str = ""
for mdf in md_files:
    with open(mdf, 'r') as md:
        md_str += "\n".join(md.readlines())
    md_str += "\n\n----\n"
timestamp = dt.now().isoformat(timespec="minutes")
md_str += f"_Generated from markdown source: {timestamp}_"
html = markdown.markdown(md_str)
with open(out_file, 'w', encoding="utf-8") as f:
    f.write(html)
print(f"Created: {out_file}")
# convert to PDF. This DOES NOT do nice page breaks!
out_file = out_file.replace(".html", ".pdf")
mediabox = fitz.paper_rect("a4")
mediabox_loc = mediabox + (36, 36, -36, -36)  # leave borders of 0.5 inches
css = "body {font-family: sans-serif;}"
story = fitz.Story(html=html, user_css=css)
writer = fitz.DocumentWriter(out_file)  # create the writer
more = 1  # will indicate end of input once it is set to 0
while more:  # loop outputting the story
    device = writer.begin_page(mediabox)  # make new page
    more, _ = story.place(mediabox_loc)  # layout into allowed rectangle
    story.draw(device)  # write on page
    writer.end_page()  # finish page
writer.close()  # close output file
print(f"Created: {out_file}")
print()

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

print("Copying files to DEPLOY and zip file:")
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
            # check for and omit *Timer, if so configured
            if not deploy_timers:
                skip_dirs += [d for d in dirs if d.endswith("Timer")]
            # make-dir, copy file, or skip...
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
