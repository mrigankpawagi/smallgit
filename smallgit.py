import os
import sys
import argparse
import hashlib
import json
from datetime import datetime

# Helper function to calculate the hash of a file's content.
# This is similar to what Git does to track changes in files.
def hash_file(filepath):
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

# Function to save the current state of the repository.
# This writes the repository data to a file so it can be loaded later.
def save_state(repo_path, data):
    with open(os.path.join(repo_path, '.smallgit', 'repo_state.json'), 'w') as f:
        json.dump(data, f, indent=4)

# Function to load the current state of the repository from disk.
# This reads the repository data back into memory when we need it.
def load_state(repo_path):
    with open(os.path.join(repo_path, '.smallgit', 'repo_state.json'), 'r') as f:
        return json.load(f)

# Initializes a new repository by creating a .smallgit directory.
def init():
    if os.path.exists(".smallgit"):
        print("Repository already initialized.")
    else:
        os.makedirs(".smallgit")
        # Setting up the basic structure for the repository
        repo_data = {
            "branches": {"main": []},  # A 'main' branch with no commits yet
            "current_branch": "main",  # Start on the 'main' branch
            "staging_area": {},        # Area to store files that are about to be committed
            "commits": {}              # Dictionary to store all commits by their hash
        }
        save_state(".", repo_data)  # Save the initialized repository structure
        print("Initialized empty SmallGit repository.")

# Shows the status of the repository, including the current branch
# and files that are staged for the next commit.
def status():
    repo_data = load_state(".")  # Load the current state of the repo
    print(f"On branch {repo_data['current_branch']}")
    
    # Check if there are files in the staging area
    if repo_data["staging_area"]:
        print("Changes to be committed:")
        for file in repo_data["staging_area"]:
            print(f"  {file}")
    else:
        print("No changes to be committed.")

# Adds files to the staging area.
# Staging files means we are preparing them to be committed in the next step.
def add(files):
    repo_data = load_state(".")  # Load the repository data
    for file in files:
        if os.path.exists(file):  # Check if the file exists
            file_hash = hash_file(file)  # Calculate the hash of the file
            repo_data["staging_area"][file] = file_hash  # Add it to the staging area
            print(f"Added {file} to staging area.")
        else:
            print(f"File {file} not found.")
    save_state(".", repo_data)  # Save the updated state after adding files

# Commits the staged changes by saving them to the repository with a message.
def commit(message):
    repo_data = load_state(".")  # Load the current state of the repository

    # If no files are staged, there is nothing to commit
    if not repo_data["staging_area"]:
        print("No changes to commit.")
        return
    
    # Create a unique hash for the commit, including the message and timestamp
    commit_hash = hashlib.sha1(f"{message}{datetime.now()}".encode()).hexdigest()
    
    # Record the commit details, including message and changes (staged files)
    commit_data = {
        "message": message,
        "timestamp": str(datetime.now()),
        "changes": repo_data["staging_area"].copy()  # Copy current staged files
    }

    # Add the commit to the current branch
    current_branch = repo_data["current_branch"]
    repo_data["commits"][commit_hash] = commit_data
    repo_data["branches"][current_branch].append(commit_hash)  # Link commit to branch
    repo_data["staging_area"] = {}  # Clear the staging area after committing
    save_state(".", repo_data)  # Save the updated repository state
    
    # Print a success message including the first few characters of the commit hash
    print(f"[{commit_hash[:7]}] {message}")

# Displays the history of commits (logs) for the current branch.
def log():
    repo_data = load_state(".")  # Load the current repository state
    current_branch = repo_data["current_branch"]  # Get the current branch name

    # Check if there are commits in the branch
    if repo_data["branches"][current_branch]:
        print(f"Commit history for branch {current_branch}:")
        for commit_hash in reversed(repo_data["branches"][current_branch]):
            commit = repo_data["commits"][commit_hash]
            print(f"commit {commit_hash}")
            print(f"Author: You <you@example.com>")  # A placeholder author
            print(f"Date: {commit['timestamp']}")
            print(f"\n    {commit['message']}\n")
    else:
        print("No commits yet on this branch.")

# Switch to a different branch or checkout a specific commit.
def checkout(branch_or_commit):
    repo_data = load_state(".")  # Load the repository state

    # Check if it's a branch or a commit
    if branch_or_commit in repo_data["branches"]:
        repo_data["current_branch"] = branch_or_commit  # Switch to the branch
        print(f"Switched to branch '{branch_or_commit}'")
    elif branch_or_commit in repo_data["commits"]:
        print(f"Checked out commit {branch_or_commit}")  # Checkout specific commit
    else:
        print(f"Branch or commit {branch_or_commit} not found.")
    
    save_state(".", repo_data)  # Save the updated repository state

# Compares the current files to the staging area or between commits/branches.
def diff(target=None):
    repo_data = load_state(".")  # Load the repository state

    if target:  # If a specific file is targeted
        if target in repo_data["staging_area"]:
            staged_hash = repo_data["staging_area"][target]  # Get the staged hash
            current_hash = hash_file(target)  # Hash the current version of the file

            # Compare the staged version with the current version
            if current_hash != staged_hash:
                print(f"File {target} has changed since it was staged.")
            else:
                print(f"No changes in {target}.")
        else:
            print(f"File {target} is not staged.")
    else:
        # Compare all files in the staging area with the working directory
        print("Comparing current files to staging area:")
        for file in repo_data["staging_area"]:
            staged_hash = repo_data["staging_area"][file]
            current_hash = hash_file(file)
            if current_hash != staged_hash:
                print(f"{file} has changed.")
            else:
                print(f"No changes in {file}.")

# Main function to set up the command-line interface (CLI) for SmallGit.
def main():
    parser = argparse.ArgumentParser(description="Simple Python SmallGit CLI")
    
    # Set up subcommands (init, status, add, commit, log, checkout, diff)
    subparsers = parser.add_subparsers(dest="command")
    
    # SmallGit init
    subparsers.add_parser("init", help="Initialize a new repository")

    # SmallGit status
    subparsers.add_parser("status", help="Show the status of the repository")

    # SmallGit add
    add_parser = subparsers.add_parser("add", help="Add files to the staging area")
    add_parser.add_argument("files", nargs="+", help="List of files to add")

    # SmallGit commit
    commit_parser = subparsers.add_parser("commit", help="Commit the staged changes")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")

    # SmallGit log
    subparsers.add_parser("log", help="Show commit logs")

    # SmallGit checkout
    checkout_parser = subparsers.add_parser("checkout", help="Switch to a branch or commit")
    checkout_parser.add_argument("branch_or_commit", help="Branch or commit to checkout")

    # SmallGit diff
    diff_parser = subparsers.add_parser("diff", help="Show differences between files")
    diff_parser.add_argument("target", nargs="?", help="File to compare")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the appropriate function based on the command
    if args.command == "init":
        init()
    elif args.command == "status":
        status()
    elif args.command == "add":
        add(args.files)
    elif args.command == "commit":
        commit(args.message)
    elif args.command == "log":
        log()
    elif args.command == "checkout":
        checkout(args.branch_or_commit)
    elif args.command == "diff":
        diff(args.target)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
