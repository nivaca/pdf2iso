# Changelog

All notable changes to pdf2iso, called py-pdfconform until version 2.0.
The releases, with their zip files, are on
[Codeberg](https://codeberg.org/nivaca/pdf2iso/releases) and
[GitHub](https://github.com/nivaca/pdf2iso/releases).

## Unreleased

- `tools/zenodo.py`: the description of the deposit is now the whole
  README of the tag, in HTML. The draft also gets the contributor (the
  project leader), the languages, the copyright, the repository on GitHub,
  the programming language and the development status, these last through
  Zenodo's records API (its deposit API doesn't take them). The token can
  be kept in the desktop keyring (`secret-tool store --label="Zenodo
  token" service zenodo`) instead of `$ZENODO_TOKEN`; `tools/zenodo.py
  check-token` says whether there is one.

- **Signed releases.** The tag of each release is signed, and every file
  published has its signature (`FILE.asc`), with `SHA256SUMS`, signed too,
  and the public key `packaging/RPM-GPG-KEY-pdf2iso`, all attached to the
  release. `tools/release.py` signs them (`tools/sign_release.py`) and
  checks every signature with only that key before anything is published; an
  unsigned tag already on the commit is signed and pushed again.
- `tools/zenodo.py` prepares the deposit of a release for Zenodo. `collect`
  puts in `dist/zenodo/` the tree of the tag as
  `pdf2iso-VERSION-source.tar.gz`, with its signature, a signed `SHA256SUMS`
  of the deposit and the public key, and checks every signature with only
  that key (`--packages` adds the files of the release). `upload` sends it
  to Zenodo as a draft, a new version of the deposit if there is one
  already, and never publishes it. `tools/release.py` now collects the
  deposit after the tag and uploads it as a draft, unless `--no-zenodo`. The
  metadata are in `.zenodo.json`.
- `tools/zenodo.py`: the description of the deposit leaves out the line
  that points to the README in other languages and the Screenshots section,
  whose images Zenodo does not show.

## 2.1.1 — 2026-11-21

- `docs/OPEN-SOURCE.md` and `docs/OPEN-SOURCE_es.md`: the open-source
  software pdf2iso uses, with the licence of each.  The READMEs point
  to them.
- `docs/DESCRIPCIÓN_es.md` keeps to six sections, each under 4000
  characters, in the third person. The program does not change.

## 2.1 — 2026-11-18

- **`--light`**, for PDF/A-2b and PDF/A-3b: the PDF/A is first made with
  pikepdf only, leaving the pages as they are, and kept if veraPDF passes
  it; otherwise the file is converted with Ghostscript as before. This is
  for scans that Ghostscript makes much larger: a book of 587 pages
  scanned by the Internet Archive stays at 24 MB instead of 173 MB, and
  converts in 4 seconds instead of 72. `--light` needs veraPDF.
- Images no longer keep the `Interpolate` key, which PDF/A forbids.

## 2.0 — 2026-11-17

- **py-pdfconform is now pdf2iso**: the script is `pdf2iso.py`, the
  command made by `install.sh` is `pdf2iso`, the zip is
  `pdf2iso-v.VERSION.zip`, and the repositories are nivaca/pdf2iso on
  GitHub and Codeberg. A link made by an earlier version
  (`~/bin/py-pdfconform` or `~/.local/bin/py-pdfconform`) must be
  removed by hand.
- The conversion does not change.

## 1.2.2 — 2026-11-17

- When there is no `~/bin`, `install.sh` puts the link in `~/.local/bin`
  again: 1.2.1 moved it by mistake to `~/.local/share/bin`, which is not
  on the PATH by default. A link made there by 1.2.1 must be removed by
  hand.

## 1.2.1 — 2026-11-17

- `install.sh` warns when veraPDF is not installed; the program works
  without it, but cannot validate PDF/A results.
- When there is no `~/bin`, the link went in `~/.local/share/bin` instead
  of `~/.local/bin` (undone in 1.2.2).

## 1.2 — 2026-11-17

- An installer for Linux: `./install.sh` makes the command
  `py-pdfconform`, a symbolic link to the script in `~/bin` (or in
  `~/.local/bin` if there is no `~/bin`), and checks that it starts;
  `./install.sh --uninstall` removes the link.
- The `COMMIT` file in the zip is readable by all (mode 644).

## 1.1 — 2026-11-16

- Python 3.14 or later is needed (it was 3.10). Where the system's Python
  is older, `uv run py-pdfconform.py` fetches a newer one.
- The zip has a file `COMMIT`, with the commit it was made from;
  `tools/release.py` publishes a release on GitHub and Codeberg.
- The conversion does not change.

## 1.0 — 2026-11-16

- First version: py-pdfconform converts PDF files to PDF/A-1b, PDF/A-2b
  or PDF/A-3b, for archiving, and to PDF/X-4, for printing, with
  Ghostscript and pikepdf (`-t`/`--target`). PDF/A results are validated
  with veraPDF when it is installed; PDF/X-4 results get a structural
  check of their own.
- PDF/X-4 gets a CMYK output intent (Ghostscript's SWOP profile, or
  `--icc` with `--condition`) and the keys it needs in the document
  information and XMP.
- What Ghostscript leaves wrong is corrected: attachments the standard
  does not allow are removed (in PDF/X-4 too), the MIME types of the
  others repaired, JavaScript removed, and every optional content
  configuration named. A warning says when annotations are removed.
- Python, pikepdf, Ghostscript and veraPDF are checked before converting;
  `--version`.
