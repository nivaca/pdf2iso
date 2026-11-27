#!/usr/bin/env python3
"""Publica una versión de pdf2iso en GitHub (con gh) y en Codeberg (con
tea): la etiqueta vVERSIÓN (la VERSION de pdf2iso.py), firmada, con el
ZIP y su firma (ARCHIVO.asc), SHA256SUMS y su firma, y la clave pública
que los comprueba, adjuntos; y el depósito de la versión en Zenodo,
publicado (con --zenodo-draft, solo como borrador).

    python3 tools/release.py [--redo] [--notes TEXT | --notes-file FILE]
                             [--no-build] [--no-tests] [--only github|codeberg]
                             [--no-zenodo] [--dry-run] [--yes]

Todo se firma con la clave del proyecto (SIGNING_KEY, la misma en todos
los proyectos del autor), y cada firma se comprueba solo con la clave
pública que se publica (packaging/RPM-GPG-KEY-pdf2iso), antes de publicar
nada.

En orden, cada paso solo si hace falta:

1. comprueba que el repositorio esté en main, sin nada por confirmar, que
   gh, tea y gpg estén instalados, que la clave de firma esté en gpg y,
   salvo con --no-zenodo, que haya un token de Zenodo en $ZENODO_TOKEN o
   en el llavero;
2. corre las pruebas, cada archivo en un proceso propio, a la vez
   (tools/test.py; salvo con --no-tests);
3. hace el ZIP en build/release/ (tools/bundle-zip.py), salvo con
   --no-build (entonces se usa el que haya en build/release/);
4. lo firma (tools/sign_release.py: build/release/pdf2iso-v.VERSIÓN.zip.asc,
   y build/release/SHA256SUMS con su .asc) y comprueba cada firma solo con
   la clave pública; gpg pide la frase de contraseña;
5. pone en HEAD la etiqueta vVERSIÓN, firmada con la misma clave (git tag
   --sign), y la comprueba (git tag --verify).  Si la etiqueta ya está en
   otro commit, se detiene, salvo que --redo la mueva;
6. reúne el depósito para Zenodo en build/zenodo/ (tools/zenodo.py
   collect: el árbol de la etiqueta, firmado, con SHA256SUMS y la clave
   pública, y cada firma comprobada solo con esa clave);
7. sube main y la etiqueta al remoto (origin, que sube a la vez a GitHub
   y a Codeberg; --redo sube la etiqueta con --force);
8. en Codeberg, activa las versiones del repositorio si están apagadas
   (los repositorios nuevos pueden tenerlas así);
9. en cada forja, hace la versión de la etiqueta, o conserva la que haya,
   y le adjunta los archivos, en lugar de los que tengan el mismo nombre;
10. salvo con --no-zenodo, sube build/zenodo/ a Zenodo y lo publica
   (tools/zenodo.py upload --publish), con un DOI nuevo; con --zenodo-draft
   queda como borrador, para publicarlo a mano;
11. borra build/release/ y build/zenodo/: las forjas y Zenodo ya tienen lo
   que contenían, y aquí no se guarda nada de una versión (dist/ no se
   usa).

Antes de hacer nada, muestra las órdenes que va a correr y pregunta; con
--yes no pregunta, y con --dry-run solo las muestra.  Las notas de una
versión nueva son --notes o --notes-file (las mismas en las dos forjas)
o, si no, las que hace GitHub con los commits (en Codeberg, ninguna); una
versión que ya está conserva sus notas.

Los repositorios salen de las direcciones de subida del remoto; tea usa
la sesión llamada codeberg, salvo que --tea-login nombre otra.
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
# Lo que se publica se hace y se firma en build/release/, no en dist/: aquí
# no se guarda nada de una versión una vez publicada (no hay RPM)
OUT = os.path.join("build", "release")
ZIP = os.path.join(OUT, bundle_zip.name() + ".zip")
BRANCH = "main"
# La clave con que se firma todo lo publicado: la misma en todos los
# proyectos del autor (la que fija packaging/build-rpm.sh en los que hacen
# un RPM)
SIGNING_KEY = "81870643CA221AF90C30554EBE6832CD35994948"
PUBLIC_KEY = os.path.join("packaging", "RPM-GPG-KEY-pdf2iso")
SUMS = os.path.join(OUT, "SHA256SUMS")


def zenodo_token() -> bool:
    """Whether tools/zenodo.py finds a Zenodo token, in $ZENODO_TOKEN or
    in the desktop keyring (secret-tool)."""
    tool = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "tools", "zenodo.py")
    done = subprocess.run([sys.executable, tool, "check-token"],
                          capture_output=True, check=False)
    return done.returncode == 0


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
        tools = ("git", "gpg") + tuple(
            t for t, f in (("gh", "github"), ("tea", "codeberg"))
            if f in self.forges)
        for tool in tools:
            if not shutil.which(tool):
                sys.exit(f"release.py: {tool} is not installed")
        # Todo se firma, siempre: sin la clave no hay versión
        if subprocess.run(["gpg", "--batch", "--list-secret-keys", SIGNING_KEY],
                          capture_output=True).returncode != 0:
            sys.exit(f"release.py: the signing key {SIGNING_KEY} is not in "
                     "this machine's gpg keyring; import it first")
        if not os.path.isfile(os.path.join(ROOT, PUBLIC_KEY)):
            sys.exit(f"release.py: there is no {PUBLIC_KEY}, the public key "
                     "published with the release")
        # (sin token se para aquí, antes de hacer nada, y no al final)
        if not self.args.no_zenodo and not self.args.dry_run \
                and not zenodo_token():
            sys.exit("release.py: the upload to Zenodo needs a token "
                     "(see tools/zenodo.py check-token); --no-zenodo "
                     "leaves it out")
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

    def tests(self):
        if not self.args.no_tests:
            # (a la vez, cada archivo en su proceso: tools/test.py)
            self.plan("Run the tests", sys.executable,
                      os.path.join("tools", "test.py"))

    def build(self):
        if self.args.no_build:
            if not os.path.isfile(os.path.join(ROOT, ZIP)):
                sys.exit(f"release.py: there is no {ZIP} (leave out "
                         "--no-build to make it)")
            return
        if not self.args.dry_run:
            os.makedirs(os.path.join(ROOT, OUT), exist_ok=True)
        self.plan("Make the zip", sys.executable,
                  os.path.join("tools", "bundle-zip.py"), "--output", OUT)

    def sign(self):
        """Every file published signed (FILE.asc), with SHA256SUMS and its
        signature, and each signature checked with only the public key
        published."""
        signed = [f for f in self.files if f != PUBLIC_KEY]
        self.plan("Sign the files, and check each signature with the "
                  "published key", sys.executable,
                  os.path.join("tools", "sign_release.py"), "--key",
                  SIGNING_KEY, "--public", PUBLIC_KEY, "--sums", SUMS,
                  *signed)
        self.files = (signed + [f"{f}.asc" for f in signed]
                      + [SUMS, f"{SUMS}.asc", PUBLIC_KEY])

    def tag(self):
        head = self.read("git", "rev-parse", "HEAD")
        tagged = self.read("git", "rev-parse", "--verify", "--quiet",
                           f"refs/tags/{TAG}^{{commit}}", check=False)
        #  A tag on HEAD from before releases were signed is signed now,
        #  and pushed again, replacing the old one on the forges
        unsigned = tagged == head and subprocess.run(
            ["git", "tag", "--verify", TAG], cwd=ROOT,
            capture_output=True).returncode != 0
        if tagged == head and not unsigned:
            pass
        elif tagged and tagged != head and not self.args.redo:
            sys.exit(f"release.py: {TAG} is already the tag of "
                     f"{tagged[:7]}, not of HEAD ({head[:7]}); raise VERSION "
                     f"in pdf2iso.py for a new release, or --redo "
                     "moves the tag (and replaces the files of the releases)")
        else:
            self.plan("Sign the tag of HEAD (it was not signed)" if unsigned
                      else "Move the tag to HEAD, signed" if tagged
                      else "Tag HEAD, signed", "git", "tag", "--force",
                      "--sign", "--local-user", SIGNING_KEY, TAG,
                      "--message", TAG)
            self.plan("Check the signature of the tag", "git", "tag",
                      "--verify", TAG)
        #  The deposit for Zenodo, from the tag (uploaded at the end)
        self.plan("Zenodo: collect the deposit in build/zenodo/",
                  sys.executable, os.path.join("tools", "zenodo.py"),
                  "collect", "--tag", TAG)
        self.plan(f"Push {BRANCH}", "git", "push", self.args.remote, BRANCH)
        #  With --redo the tag is always pushed with --force: the remote
        #  pushes to two forges, and only the first is seen here
        if self.args.redo or unsigned:
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
            self.plan("GitHub: attach the files to the release (replacing "
                      "those there)", "gh", "release", "upload", TAG,
                      *self.files, "--clobber", "--repo", repo)
        else:
            self.plan("GitHub: make the release", "gh", "release", "create",
                      TAG, *self.files, "--title", TAG, "--verify-tag",
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
            old = [os.path.basename(f) for f in self.files
                   if os.path.basename(f) in names]
            if old:
                self.plan("Codeberg: remove the files of the same name (tea "
                          "cannot replace them)", "tea", "releases", "assets",
                          "delete", TAG, *old, "--confirm", *where)
            self.plan("Codeberg: attach the files to the release", "tea",
                      "releases", "assets", "create", TAG, *self.files,
                      *where)
        else:
            assets = [a for f in self.files for a in ("--asset", f)]
            self.plan("Codeberg: make the release", "tea", "releases",
                      "create", "--tag", TAG, "--title", TAG,
                      *self.notes(False), *assets, *where)

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
        self.files = [ZIP, PUBLIC_KEY]
        self.check()
        repos = self.repos()
        self.tests()
        self.build()
        self.sign()
        self.tag()
        for forge in self.forges:
            getattr(self, forge)(repos[forge])
        if not self.args.no_zenodo:
            self.plan("Zenodo: upload the deposit" + (" as a draft (not published)" if self.args.zenodo_draft
                                                       else " and publish it"),
                      sys.executable, os.path.join("tools", "zenodo.py"), "upload",
                      *([] if self.args.zenodo_draft else ["--publish"]))
        #  Once all is published, nothing of it stays here
        self.plan("Delete what was published from build/ (the forges and "
                  "Zenodo have it)", "rm", "-rf", OUT,
                  os.path.join("build", "zenodo"))
        self.run_plan()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tools/release.py",
        description=f"Publish {TAG} on GitHub and Codeberg, with the zip, "
                    "all signed, and publish its deposit on Zenodo.")
    parser.add_argument("--redo", action="store_true",
                        help=f"move {TAG} to HEAD if it is on another commit "
                             "(here and on the remote), and replace the "
                             "files of the releases")
    notes = parser.add_mutually_exclusive_group()
    notes.add_argument("--notes", metavar="TEXT",
                       help="the notes of a new release")
    notes.add_argument("--notes-file", metavar="FILE",
                       help="the notes of a new release, from FILE")
    parser.add_argument("--no-build", action="store_true",
                        help="use the zip in build/release/, without making it "
                             "again")
    parser.add_argument("--no-tests", action="store_true",
                        help="don't run the tests first")
    parser.add_argument("--only", choices=("github", "codeberg"),
                        help="publish on one forge only")
    parser.add_argument("--remote", default="origin",
                        help="the remote to push to (default: origin)")
    parser.add_argument("--tea-login", default="codeberg",
                        help="the login of tea for Codeberg (default: codeberg)")
    parser.add_argument("--no-zenodo", action="store_true",
                        help="don't upload the deposit to Zenodo (by default it is uploaded and "
                             "published, with the token in $ZENODO_TOKEN or the keyring)")
    parser.add_argument("--zenodo-draft", action="store_true",
                        help="upload it to Zenodo as a draft, not published")
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
