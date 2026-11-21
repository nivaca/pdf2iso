# Changelog

All notable changes to pdf2iso, called py-pdfconform until version 2.0.
The releases, with their zip files, are on
[Codeberg](https://codeberg.org/nivaca/pdf2iso/releases) and
[GitHub](https://github.com/nivaca/pdf2iso/releases).

## Unreleased

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
