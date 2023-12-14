from git import Repo
from os import path, listdir

# Automate some BASIC git interactions across the range of repos in the playground: playthings, config, notebooks.
# Especially take care of the pg_shared git submodule.
# This does not cover all use cases, but should allow the common maintenance tasks to be done quickly and reliably, 
# while allowing for bailout when use of CLI or GUI git is needed.

# >>>>>> RUNTIME SETTINGS <<<<<<<
# Working modes are either just checking for un-tracked/committed files and doing something about them
with_commits = True
# Model of working is one execution for pg_shared and one for main plaything (consider doing as loop, see below), controlled by this:
for_pg_shared = False

# folder containing Playthings
pt_root_path = ".."

# scan all folders ending -pt
playthings = [d for d in listdir(pt_root_path) if d.endswith("-pt")]
# print(playthings)

# Imposed limitations:
# Only work on develop branch
REQUIRED_BRANCH = "develop"

change_types = {"A": "New", "R": "Renamed", "M": "Modified", "T": "Changed type", "D": "Deleted"}

# # Two loops around, first for pg_shared then the plaything themselves
# for for_pg_shared in [True, False]:
# Check for un-tracked or un-committed files, adding, committing, and pushing if necessary (push if a commit or staging area has a past commit)
for p in playthings:
    repo_path = path.join(pt_root_path, p, "pg_shared") if for_pg_shared else path.join(pt_root_path, p)
    h = f"Working on {repo_path}"
    print(h)
    print("=" * len(h))

    repo = Repo(repo_path)
    if repo.active_branch.name != REQUIRED_BRANCH:
        raise Exception(f"Must be on 'develop' branch but {p} is on {repo.active_branch}")

    add_files = []
    do_pg_shared = False
    for diff in repo.index.diff(None):  # compare working files to staging area
        # deleted files are "off piste"
        if diff.change_type == "D":
            raise Exception(f"Deleted file found at {diff.b_path}. Handle this yourself!")
        # new files are "on piste", as changes...
        print(f"\t{change_types[diff.change_type]} file: {diff.b_path}")  # b_bath should be OK for new, changed, or moved
        # simply adding "pg_shared" causes carnage because it seems to NOT be recognised as a submodule when doing repo.index.add
        if diff.b_path != "pg_shared":
            add_files.append(diff.b_path)
        else:
            do_pg_shared = True
    # add to staging if necessary
    if with_commits and (len(add_files) > 0):
            print(f"Adding {len(add_files)} file(s) to staging area.")
            repo.index.add(add_files)
    # is there anything in staging, commit. There might have been a manual add to staging.
    staged = repo.index.diff(repo.head.commit)  # compare staging to head commit
    if len(staged) > 0:
        print("Staged files:")
        print("\n".join([f"\t{sf.b_path} ({change_types[sf.change_type]})" for sf in staged]))
        if with_commits:
            msg = input("Enter commit message (empty string to abort): ")
            if msg == "":
                raise KeyboardInterrupt("Commit aborted")
            repo.index.commit(msg)
    # Now separately add and commit the pg_shared house-keeping. These will already have the appropriate commit msg in the pg_shared repo.
    if with_commits and do_pg_shared:
        print("Committing pg_shared changes")
        repo.git.add("pg_shared")
        repo.index.commit("updated submodule pg_shared")
    # interactions with the remote repo
    origin = repo.remotes.origin
    # a fetch allows us to inspect the work to be done before executing pull or push (both of which return lists even when no real work done)
    fetched = origin.fetch()
    head = repo.head.ref
    tracking = head.tracking_branch()
    remote_commits_pending = list(tracking.commit.iter_items(repo, f'{head.path}..{tracking.path}'))
    local_commits_pending = list(head.commit.iter_items(repo, f'{tracking.path}..{head.path}'))
    # first pull as there we might be behind... in which case a manual merge is on the cards
    if len(remote_commits_pending) > 0:
        pull_list = origin.pull()
        if len(pull_list) > 0:
            print("Pulled from remote!")
            print("\n".join([f"\t{pi.commit.summary}" for pi in pull_list]))
        merge_edits = repo.index.diff(None)  # has auto-merge failed? 
        if len(merge_edits) > 0:
            raise Exception(f"Perform a manual merge edit for {p} then run the script again.")    
    # push the commit(s). 
    if len(local_commits_pending) > 0:
        push_info = origin.push()
        push_info.raise_if_error()
        if len(push_info) > 0:
            print("Push completed")
            print("\n".join([f"\t{pi.local_ref.commit.summary}" for pi in push_info]))

    print("-" * 40, "\n")
