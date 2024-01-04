#!/usr/bin/env python3
import os
import re
import sys
import semver
import subprocess

def git(*args):
    return subprocess.check_output(["git"] + list(args))

def verify_env_var_presence(name):
    if name not in os.environ:
        raise Exception(f"Expected the following environment variable to be set: {name}")

def extract_gitlab_url_from_project_url():
    project_url = os.environ['CI_PROJECT_URL']
    project_path = os.environ['CI_PROJECT_PATH']

    return project_url.split(f"/{project_path}", 1)[0]

def extract_merge_request_id_from_commit():
    message = git("log", "-1", "--pretty=%B")
    matches = re.search(r'(\S*\/\S*!)(\d+)', message.decode("utf-8"), re.M|re.I)

    if matches == None:
        raise Exception(f"Unable to extract merge request from commit message: {message}")

    return matches.group(2)

def bump(latest):

    merge_request_labels = os.environ.get("CI_COMMIT_MESSAGE")

    print(merge_request_labels)

    if re.search(r'(MINOR|minor)', merge_request_labels):
        return semver.bump_minor(latest)
    elif re.search(r'(MAJOR|major)', merge_request_labels):
        return semver.bump_major(latest)
    else:
        return semver.bump_patch(latest)
    
def createVariables(latest):
    file_input = f"export TAG={latest}"
    file = open('.variables', 'a')
    file.write(file_input)
    file.close()

def main():
    env_list = ["CI_REPOSITORY_URL", "CI_PROJECT_ID", "CI_PROJECT_URL", "CI_PROJECT_PATH", "NPA_USERNAME", "NPA_PASSWORD"]
    [verify_env_var_presence(e) for e in env_list]

    try:
        latest = git("describe", "--tags", "--first-parent", "--match", "[[:digit:]]*.[[:digit:]]*.[[:digit:]]*").decode().strip()
    except subprocess.CalledProcessError:
        # Default to version 1.0.0 if no tags are available
        version = "1.0.0"
    else:
        # Skip already tagged commits
        if '-' not in latest:
            print(latest)
            return 0

        version = bump(latest)
    

    createVariables(version)
    print(version)

    return 0


if __name__ == "__main__":
    sys.exit(main())
