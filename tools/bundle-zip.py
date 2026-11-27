#!/usr/bin/env python3
"""Hace un ZIP del programa, para distribuirlo:
python3 tools/bundle-zip.py [-o CARPETA]

El ZIP es build/release/pdf2iso-v.VERSIÓN.zip (la VERSION de
pdf2iso.py; build/release se crea en la carpeta del programa si hace
falta, y --output da otra carpeta), con el programa en una carpeta del
mismo nombre.  Trae el script, la licencia y los documentos, pero ningún
archivo ni carpeta oculta (.git ...), nada de lo que se genera al correr
o editar el programa (__pycache__, archivos .bak y .tmp ...) y nada de lo
que está en su carpeta sin ser parte de él (build/, dist/, tools/, tests/
y packaging/, con la clave pública que firma las versiones).  Trae además
COMMIT, el commit del que se hizo.
"""

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import time
import zipfile

#  The program's folder (this script is in its tools/)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = "pdf2iso.py"
COMMIT_FILE = "COMMIT"

#  Where the zip goes, unless --output says otherwise: build/release/, where
#  tools/release.py signs it and from where it is published (then deleted)
OUT = os.path.join(ROOT, "build", "release")

#  What is made while the program runs or is edited (as in .gitignore)
LEFT_OUT = ("__pycache__", "*.pyc", "*.bak", "*.tmp", "*~",
            "pdf2iso-v*.zip")
#  What is in the program's folder but not part of it: the folders of the
#  bundles, the tools that make them and the releases, the tests and the
#  public key
NOT_PART = ("build", "dist", "tools", "tests", "packaging")


def version() -> str:
    """VERSION of pdf2iso.py, read from the file (importing it would
    check for pikepdf and Ghostscript, which making a zip does not need)."""
    with open(os.path.join(ROOT, SCRIPT), encoding="utf-8") as f:
        m = re.search(r'^VERSION = "([^"]+)"', f.read(), re.MULTILINE)
    if not m:
        sys.exit(f"bundle-zip.py: there is no VERSION in {SCRIPT}")
    return m.group(1)


def name() -> str:
    """The name of the zip, without .zip: pdf2iso-v.1.0."""
    return f"pdf2iso-v.{version()}"


def files() -> list[str]:
    """The files of the distribution, relative to the program's folder."""
    out = []
    for folder, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if not _left_out(d) and
                         (folder != ROOT or d not in NOT_PART))
        for n in sorted(names):
            if not _left_out(n) and (folder != ROOT or n not in NOT_PART):
                out.append(os.path.relpath(os.path.join(folder, n), ROOT))
    return out


def _left_out(n: str) -> bool:
    return n.startswith(".") or any(fnmatch.fnmatch(n, p) for p in LEFT_OUT)


def built_from() -> str | None:
    """The commit the zip is made from: that of GitHub Actions
    ($GITHUB_SHA), or else HEAD of the repository; None outside one."""
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        out = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                             capture_output=True, text=True)
    except OSError:
        return None
    text = out.stdout.strip()
    return text if out.returncode == 0 and re.fullmatch("[0-9a-f]{40}", text) else None


def bundle(folder: str) -> str:
    """Writes the zip into FOLDER; returns its path."""
    path = os.path.join(folder, name() + ".zip")
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files():
            z.write(os.path.join(ROOT, f), name() + "/" + f.replace(os.sep, "/"))
        commit = built_from()
        if commit:
            info = zipfile.ZipInfo(name() + "/" + COMMIT_FILE,
                                   time.localtime()[:6])
            info.external_attr = 0o100644 << 16     # (writestr gives 0o600)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, commit + "\n")
    os.replace(tmp, path)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tools/bundle-zip.py",
        description=f"Make a zip of the program, to distribute it: "
                    f"{name()}.zip, without hidden files.")
    parser.add_argument("-o", "--output", metavar="FOLDER", default=None,
                        help="the folder to write it in (default: build/release, "
                             "in the program's folder)")
    args = parser.parse_args(argv)
    if args.output is None:
        args.output = OUT
        os.makedirs(OUT, exist_ok=True)
    elif not os.path.isdir(args.output):
        sys.exit(f"bundle-zip.py: there is no folder {args.output}")
    try:
        path = bundle(args.output)
    except OSError as e:
        sys.exit(f"bundle-zip.py: {e}")
    with zipfile.ZipFile(path) as z:
        count = len(z.namelist())
    print(f"Wrote {path} ({count} files, {os.path.getsize(path) / 1e3:.0f} kB).")


if __name__ == "__main__":
    main()
