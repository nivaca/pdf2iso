#!/usr/bin/env python3
"""Publishes a release of pdf2iso on GitHub (with gh) and on
Codeberg (with tea): the tag vVERSION (the VERSION of pdf2iso.py),
with the zip attached.

    python3 tools/release.py [--redo] [--notes TEXT | --notes-file FILE]
                             [--no-build] [--only github|codeberg]
                             [--dry-run] [--yes]

In order, each step only if it is needed:

1. checks that the repository is on main, with nothing left to commit,
   and that gh and tea are installed;
2. makes the zip in dist/ (tools/bundle-zip.py), unless --no-build (then
   the one in dist/ is used);
3. tags HEAD as vVERSION.  If the tag is there already on another commit,
   it stops, unless --redo moves it;
4. pushes main and the tag to the remote (origin, which pushes to both
   GitHub and Codeberg; --redo pushes the tag with --force);
5. on Codeberg, switches releases on for the repository if they are off
   (new repositories may have them off);
6. on each forge, makes the release of the tag, or keeps the existing
   one, and attaches the zip to it, replacing one of the same name.

Before doing anything, it shows the commands it will run and asks; --yes
does not ask, --dry-run only shows them.  The notes of a new release are
--notes or --notes-file (the same on both forges), or else made by GitHub
from the commits (on Codeberg, none); an existing release keeps its
notes.

The repositories are found from the push addresses of the remote; tea
uses the login named codeberg unless --tea-login names another.
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#  bundle-zip.py has a hyphen in its name, so it is loaded from its path
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "bundle_zip", os.path.join(ROOT, "tools", "bundle-zip.py"))
bundle_zip = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bundle_zip)

VERSION = bundle_zip.version()
TAG = f"v{VERSION}"
ZIP = os.path.join("dist", bundle_zip.name() + ".zip")
BRANCH = "main"


class Release:
    """The steps, run (or only shown) in order."""

    def __init__(self, args):
        self.args = args
        self.planned = []           # (description, command)

    # Running ----------------------------------------------------------

    def read(self, *command, check=True) -> str:
        """The output of COMMAND (which only reads, so it runs even with
        --dry-run)."""
        out = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if check and out.returncode != 0:
            sys.exit(f"release.py: {shlex.join(command)}: "
                     f"{(out.stderr or out.stdout).strip()}")
        return out.stdout.strip() if out.returncode == 0 else ""

    def plan(self, description: str, *command):
        self.planned.append((description, list(command)))

    def run_plan(self):
        if not self.planned:
            print("Nothing to do.")
            return
        print(f"Releasing {TAG}:")
        for description, command in self.planned:
            print(f"\n  # {description}\n  {shlex.join(command)}")
        print()
        if self.args.dry_run:
            return
        if not self.args.yes:
            answer = input("Run these commands? [y/N] ").strip().lower()
            if answer not in ("y", "yes", "s", "sí", "si"):
                sys.exit("Nothing done.")
        for description, command in self.planned:
            print(f"\n==> {description}", flush=True)
            if subprocess.run(command, cwd=ROOT).returncode != 0:
                sys.exit(f"release.py: failed: {shlex.join(command)}\n"
                         "The steps before it were done; after fixing the "
                         "cause, run the script again (with --redo if the "
                         "tag was already moved).")
        print(f"\nReleased {TAG}.")

    # Checks -----------------------------------------------------------

    def check(self):
        tools = ("git",) + tuple(
            t for t, f in (("gh", "github"), ("tea", "codeberg"))
            if f in self.forges)
        for tool in tools:
            if not shutil.which(tool):
                sys.exit(f"release.py: {tool} is not installed")
        branch = self.read("git", "rev-parse", "--abbrev-ref", "HEAD")
        if branch != BRANCH:
            sys.exit(f"release.py: on branch {branch}, not {BRANCH}")
        if self.read("git", "status", "--porcelain"):
            message = "there are changes not committed (see git status)"
            if not self.args.dry_run:
                sys.exit(f"release.py: {message}")
            print(f"release.py: (dry run) {message}", file=sys.stderr)

    def repos(self) -> dict:
        """{forge: owner/name}, from the push addresses of the remote."""
        urls = self.read("git", "remote", "get-url", "--push", "--all",
                         self.args.remote).split("\n")
        found = {}
        for url in urls:
            m = re.search(r"(github\.com|codeberg\.org)[:/]+"
                          r"([^/]+/[^/]+?)(?:\.git)?/?$", url)
            if m:
                found["github" if "github" in m[1] else "codeberg"] = m[2]
        for forge in self.forges:
            if forge not in found:
                sys.exit(f"release.py: the remote {self.args.remote} does "
                         f"not push to {forge} (git remote -v)")
        return found

    # Steps ------------------------------------------------------------

    def build(self):
        if self.args.no_build:
            if not os.path.isfile(os.path.join(ROOT, ZIP)):
                sys.exit(f"release.py: there is no {ZIP} (leave out "
                         "--no-build to make it)")
            return
        self.plan("Make the zip", sys.executable,
                  os.path.join("tools", "bundle-zip.py"))

    def tag(self):
        head = self.read("git", "rev-parse", "HEAD")
        tagged = self.read("git", "rev-parse", "--verify", "--quiet",
                           f"refs/tags/{TAG}^{{commit}}", check=False)
        if tagged == head:
            pass
        elif tagged and not self.args.redo:
            sys.exit(f"release.py: {TAG} is already the tag of "
                     f"{tagged[:7]}, not of HEAD ({head[:7]}); raise VERSION "
                     f"in pdf2iso.py for a new release, or --redo "
                     "moves the tag (and replaces the zip of the releases)")
        else:
            self.plan("Move the tag to HEAD" if tagged else "Tag HEAD",
                      "git", "tag", "--force", "--annotate", TAG,
                      "--message", TAG)
        self.plan(f"Push {BRANCH}", "git", "push", self.args.remote, BRANCH)
        #  With --redo the tag is always pushed with --force: the remote
        #  pushes to two forges, and only the first is seen here
        if self.args.redo:
            self.plan("Push the tag (replacing it on the forges)", "git",
                      "push", "--force", self.args.remote, f"refs/tags/{TAG}")
            return
        remote = self.read("git", "ls-remote", "--tags", self.args.remote,
                           f"refs/tags/{TAG}^{{}}", check=False)
        on_remote = remote.split()[0] if remote else ""
        if on_remote == head:
            return
        if on_remote:
            sys.exit(f"release.py: on {self.args.remote}, {TAG} is the tag "
                     f"of {on_remote[:7]}; --redo moves it")
        self.plan("Push the tag", "git", "push", self.args.remote,
                  f"refs/tags/{TAG}")

    def notes(self, github: bool) -> list[str]:
        if self.args.notes_file:
            return ["--notes-file" if github else "--note-file",
                    self.args.notes_file]
        if self.args.notes:
            return ["--notes" if github else "--note", self.args.notes]
        return ["--generate-notes"] if github else []

    def github(self, repo: str):
        exists = subprocess.run(["gh", "release", "view", TAG, "--repo", repo],
                                cwd=ROOT, capture_output=True).returncode == 0
        if exists:
            self.plan("GitHub: attach the zip to the release (replacing the "
                      "one there)", "gh", "release", "upload", TAG, ZIP,
                      "--clobber", "--repo", repo)
        else:
            self.plan("GitHub: make the release", "gh", "release", "create",
                      TAG, ZIP, "--title", TAG, "--verify-tag",
                      *self.notes(True), "--repo", repo)

    def codeberg(self, repo: str):
        login = ["--login", self.args.tea_login]
        where = ["--repo", repo] + login
        settings = json.loads(self.read("tea", "api", *login, f"/repos/{repo}")
                              or "{}")
        if not settings.get("has_releases", True):
            self.plan("Codeberg: switch releases on for the repository",
                      "tea", "api", *login, "-X", "PATCH", f"/repos/{repo}",
                      "-F", "has_releases=true")
            releases = []
        else:
            releases = self.tea_json("releases", "ls", "--limit", "50", *where)
        exists = any(TAG in (r.get("tagname"), r.get("tag")) for r in releases)
        if exists:
            names = {a.get("name") for a in self.tea_json(
                "releases", "assets", "ls", TAG, *where)}
            if os.path.basename(ZIP) in names:
                self.plan("Codeberg: remove the zip of the same name (tea "
                          "cannot replace it)", "tea", "releases", "assets",
                          "delete", TAG, os.path.basename(ZIP), "--confirm",
                          *where)
            self.plan("Codeberg: attach the zip to the release", "tea",
                      "releases", "assets", "create", TAG, ZIP, *where)
        else:
            self.plan("Codeberg: make the release", "tea", "releases",
                      "create", "--tag", TAG, "--title", TAG,
                      *self.notes(False), "--asset", ZIP, *where)

    def tea_json(self, *command) -> list[dict]:
        """The rows tea gives in JSON, with its keys made plain ("tag-_name"
        is tagname)."""
        out = self.read("tea", *command, "--output", "json")
        try:
            rows = json.loads(out or "[]")
        except ValueError:
            sys.exit(f"release.py: tea {' '.join(command)}: not JSON: {out[:200]}")
        return [{re.sub("[^a-z]", "", k.lower()): v for k, v in r.items()}
                for r in rows]

    # All --------------------------------------------------------------

    def __call__(self):
        self.forges = [self.args.only] if self.args.only else ["github", "codeberg"]
        self.check()
        repos = self.repos()
        self.build()
        self.tag()
        for forge in self.forges:
            getattr(self, forge)(repos[forge])
        self.run_plan()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tools/release.py",
        description=f"Publish {TAG} on GitHub and Codeberg, with the zip.")
    parser.add_argument("--redo", action="store_true",
                        help=f"move {TAG} to HEAD if it is on another commit "
                             "(here and on the remote), and replace the zip "
                             "of the releases")
    notes = parser.add_mutually_exclusive_group()
    notes.add_argument("--notes", metavar="TEXT",
                       help="the notes of a new release")
    notes.add_argument("--notes-file", metavar="FILE",
                       help="the notes of a new release, from FILE")
    parser.add_argument("--no-build", action="store_true",
                        help="use the zip in dist/, without making it again")
    parser.add_argument("--only", choices=("github", "codeberg"),
                        help="publish on one forge only")
    parser.add_argument("--remote", default="origin",
                        help="the remote to push to (default: origin)")
    parser.add_argument("--tea-login", default="codeberg",
                        help="the login of tea for Codeberg (default: codeberg)")
    parser.add_argument("-n", "--dry-run", action="store_true",
                        help="only show the commands")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="do not ask before running them")
    args = parser.parse_args(argv)
    if args.notes_file:
        args.notes_file = os.path.abspath(args.notes_file)
    Release(args)()


if __name__ == "__main__":
    main()
