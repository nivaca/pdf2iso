pdf2iso
=============

*(Español: [README_es.md](README_es.md))*

pdf2iso converts PDF files to two ISO standards: PDF/A, for
long-term archiving (PDF/A-1b, PDF/A-2b and PDF/A-3b), and PDF/X-4, for
printing.  It is a single Python script, `pdf2iso.py`.  The conversion
itself is done by Ghostscript; pikepdf opens encrypted or damaged files
before it, and corrects the metadata after it.  Each result is then
checked: PDF/A files with veraPDF, if it is installed, and PDF/X-4 files
with a structural check of their own.  It is free software, under the
GNU General Public License (see "Licensing").

I am Nicolas Vaughan (<nicolasvaughan@proton.me>), and I wrote it in 2026.  It began as `py-pdfa`, a
PDF/A converter; when PDF/X-4 was added it became `py-pdfconform`, and in
version 2.0 it took its present name, `pdf2iso`.

[Nicolas Vaughan](https://artehum.uniandes.edu.co/profesores/nicolas-vaughan/)
is Associate Professor of Literature at the School of Arts and Humanities
of the Universidad de los Andes, Bogotá, Colombia.

Installation
------------

### What is needed

- Python 3.14 or later.
- Ghostscript 10 or later (the `gs` command; `gswin64c` on Windows).
- pikepdf, the Python library.
- veraPDF (<https://verapdf.org/software/>), only to validate PDF/A
  files.  It is optional.

On Fedora:

    sudo dnf install ghostscript python3-pikepdf

On Debian and Ubuntu:

    sudo apt install ghostscript python3-pikepdf

On macOS, with Homebrew:

    brew install ghostscript
    pip3 install pikepdf

### Getting the program

Copy `pdf2iso.py` anywhere and run it with `python3 pdf2iso.py`.
There is nothing else to install.  If you use
[uv](https://docs.astral.sh/uv/), the script declares its own dependency,
so `uv run pdf2iso.py ...` works without installing pikepdf first
(Ghostscript is still needed).  uv also fetches Python 3.14 by itself when
the system's Python is older, as it is in Debian 13; there, `uv run` is the
simplest way to use the program.

### A command (Linux)

To run it as `pdf2iso` from any folder, unzip the program where it
will stay and run

    $ ./install.sh

This makes a symbolic link to `pdf2iso.py`, called `pdf2iso`,
in `~/bin` if that folder exists, or else in `~/.local/bin` (made if need
be).  Nothing is copied and nothing needs root, so the program's folder
must stay where it is; after moving it, run `./install.sh` again.  The
installer says if the folder of the link is not in your PATH, and how to
add it, and at the end it runs `pdf2iso --version` to see that
Python and pikepdf are there.  It also warns when veraPDF is not
installed: the program works without it, but then it cannot validate
PDF/A results.  Running it again is harmless: it leaves a
link that is already right, and replaces one that points to another copy
(an older version, for example), but never a file that is not a link.
`./install.sh --uninstall` removes the link, if it points to this copy.

Usage
-----

    python3 pdf2iso.py report.pdf                  # report_pdfa.pdf, PDF/A-2b
    python3 pdf2iso.py report.pdf -t a-1b -o archived.pdf
    python3 pdf2iso.py *.pdf -d converted/ --validate
    python3 pdf2iso.py locked.pdf -p secret        # encrypted file
    python3 pdf2iso.py flyer.pdf -t x-4            # flyer_pdfx.pdf, PDF/X-4
    python3 pdf2iso.py flyer.pdf -t x-4 --icc PSOcoated_v3.icc --condition FOGRA51

The output file goes next to the input, with `_pdfa` or `_pdfx` added to
its name, unless `-o` or `-d` says otherwise.  The program never writes
over the input.  For each file it prints one line, `OK` or `BAD` with the
result of the check, or `FAIL` if the conversion could not be done, and
warnings go before it.

| Option | Meaning |
|--------|---------|
| `-t`, `--target` | `a-1b`, `a-2b` (the default), `a-3b` or `x-4`.  Other spellings are accepted too: `PDF/A-2b`, `pdfa2b`, `2b`, `PDF/X-4`, `x4`. |
| `-o`, `--output` | The output file (only with a single input). |
| `-d`, `--outdir` | The folder for the output files. |
| `-p`, `--password` | The password of an encrypted input. |
| `--suffix` | What is added to the output names, instead of `_pdfa` or `_pdfx`. |
| `--icc` | The ICC profile of the output intent: an sRGB profile for PDF/A, the printer's CMYK profile for PDF/X-4.  By default, Ghostscript's own profiles. |
| `--condition` | PDF/X-4 only: the registered name of the printing condition that the `--icc` profile describes, such as `FOGRA39`.  By default, `Custom`. |
| `--light` | PDF/A-2b and 3b only: first try a light conversion that keeps the pages as they are, without Ghostscript, and keep it if veraPDF passes it; otherwise convert with Ghostscript. Needs veraPDF (see "Scans that grow"). |
| `--validate` | PDF/A only: stop with an error if veraPDF is not found, instead of converting without validating. |
| `--verapdf` | The path of the veraPDF command, if it is not on the PATH. |
| `-v`, `--verbose` | Show the messages of Ghostscript and of veraPDF. |
| `--version` | Show the version of the program. |

Before touching any file, the program checks what it needs: Python 3.14
or later, pikepdf 8 or later, Ghostscript 10 or later, a usable ICC
profile, and veraPDF when `--validate` or `--verapdf` asks for it.  If
something is missing, it says what and how to get it.

The exit code is 0 when every file was converted and passed its check, 1
when some file failed, and 2 when the program could not start because
something it needs is missing.

Which standard to choose
------------------------

**PDF/A-2b** is the default, and the right choice for most archiving.  It
keeps transparency and layers, and archives that ask for PDF/A normally
accept it.  Attached files are removed (PDF/A-2 only allows attachments
that are PDF/A themselves), with a warning.

**PDF/A-1b** is the oldest version, based on PDF 1.4.  Use it only when an
archive asks for it.  PDF/A-1 does not allow transparency, so Ghostscript
turns every page that has transparency into an image: the page looks the
same, but its text can no longer be selected or searched, and its links
are lost.  The program warns when this happens.  Attached files are
removed too.

**PDF/A-3b** is PDF/A-2b with permission to have files of any type
attached, so the attachments of the input are kept.

**PDF/X-4** is for sending to a printer.  All colours are converted to
CMYK for one printing condition (see the next section), transparency is
kept, and each page gets a TrimBox and a BleedBox.  Links, comments and
other annotations are removed, because PDF/X does not allow them on the
printed page; the program says how many it removed.  Attached files are
removed too: a file for the printer has no use for them, and the public
descriptions of PDF/X-4 do not make clear whether it allows them.

The "b" in the PDF/A levels means that the appearance of the pages is
preserved.  The "a" and "u" levels need, in addition, a tagged structure
and Unicode mappings for all the text, which Ghostscript cannot guarantee,
so the program does not offer them.

PDF/X-4 and colour profiles
---------------------------

A PDF/X file says for which printing condition its colours were prepared:
a kind of press and paper, described by a CMYK ICC profile.  Without
`--icc`, the program uses the profile that comes with Ghostscript, "Artifex
CMYK SWOP Profile", which is close to US web offset printing on coated
paper,
and names the condition `Custom`.  That is enough for a general-purpose
file.  For a real print job, ask the printer which profile to use, and
give it with its registered name:

| Condition | Profile | Use |
|-----------|---------|-----|
| `FOGRA39` | ISO Coated v2 (ECI) | Offset on coated paper, Europe (older standard) |
| `FOGRA51` | PSO Coated v3 (ECI) | Offset on coated paper, Europe |
| `FOGRA52` | PSO Uncoated v3 (ECI) | Offset on uncoated paper, Europe |
| `CGATS TR 006` | GRACoL 2006 Coated | Offset on coated paper, United States |

The ECI profiles can be downloaded from <https://www.eci.org/>.  The
program checks that the profile is really a CMYK profile, and refuses an
RGB one.

The page boxes are set to the size of the page, without bleed.  That is
correct for documents that do not print to the edge of the paper.  A
design with bleed needs to be prepared with it in the program that made
it.

Scans that grow
---------------

Ghostscript writes every page again, and some kinds of images it cannot
write back as they came.  Scans are the usual case: JBIG2, the compact
format of many black-and-white scans, comes out several times larger, and
the layered pages of the Internet Archive's scans (a JBIG2 mask over small
JPEG 2000 images) are stored again at full resolution.  A book of 587 pages
from the Internet Archive, 24 MB, became 173 MB.

For such files there is `--light`, for PDF/A-2b and PDF/A-3b.  It first
tries to make the PDF/A with pikepdf only, without Ghostscript: it adds the
metadata and the output intent, removes what the standard forbids (as in
step 3 below), and leaves the pages as they are.  Then veraPDF checks the
result.  If it passes, that is the output, and its line says `pages kept`;
if not, the program says so and converts with Ghostscript as usual.  The
book above stayed at 24 MB, passed veraPDF, and took 4 seconds instead of
72.  The light route works when the file already has what PDF/A asks of
the pages (fonts embedded, except those of invisible text such as the OCR
layer of a scan, and colours it allows); a file with fonts missing in its
visible text always needs Ghostscript.  `--light` needs veraPDF, since
without it there is no way to know whether the light result is valid.

How it works
------------

The conversion has four steps.

1. pikepdf opens the input, with the password if it has one, and saves an
   unencrypted copy.  Saving it also rebuilds damaged cross-reference
   tables.  At this point the program keeps the title, author, subject,
   keywords and creator, and marks every annotation as printable: PDF/A
   asks for it, and without it Ghostscript removes them (the links made
   by pdfLaTeX, for example).
2. Ghostscript's `pdfwrite` device writes the file again under the
   standard (`-dPDFA=1`, `2` or `3`, or `-dPDFX=4`).  It embeds all the
   fonts, converts the colours (to sRGB for PDF/A, to CMYK for PDF/X),
   attaches the ICC profile as the output intent, and leaves out what the
   standard forbids.  Images are not downsampled.
3. pikepdf restores any metadata that Ghostscript lost and makes the XMP
   metadata agree with the document information dictionary, as both
   standards require.  It also corrects what Ghostscript leaves wrong or
   behind: it removes JavaScript (Ghostscript moves it to a place where
   validators do not look), gives attached files a valid MIME type, takes
   out the attachments in every target except PDF/A-3b, and
   removes from the layers the automatic settings that both standards
   forbid.  For PDF/X-4 it also sets the title (the file name, if the
   document has none), `Trapped` and `GTS_PDFXVersion`.
4. The result is checked (see the next section).

Validation
----------

PDF/A files are validated with veraPDF, the reference validator of the
PDF Association, when the `verapdf` command is found.  The line of each
file says `veraPDF: PASS` or `veraPDF: FAIL`; with a failure, the report of
veraPDF is shown.

veraPDF does not validate PDF/X.  PDF/X-4 files get, instead, a check
written for this program, which looks at what the conversion is
responsible for: the PDF/X version in the XMP metadata, the title, the
dates and identifiers, `Trapped`, the output intent and its profile, the
TrimBox and BleedBox of every page, and the annotations.  It does not
check how each colour and font is used inside the pages.  A complete
PDF/X preflight needs a commercial tool such as callas pdfToolbox, and before an
important print job it is wise to let the printer check one file.

Limitations
-----------

- Ghostscript writes the whole file again.  What a standard does not allow
  is left out: JavaScript, attachments (except in PDF/A-3b), and in PDF/X
  the annotations.  The program warns about each of these.
- Colours are converted, to sRGB for PDF/A and to CMYK for PDF/X.  For a
  document with exact print colours (spot colours, a specific CMYK
  profile), check the result.
- In PDF/A-1b, pages with transparency become images (see "Which
  standard to choose").
- Only the "b" levels of PDF/A are produced.

Making a release
----------------

The ZIP of the program is made with

    $ python3 tools/bundle-zip.py [-o FOLDER]

It writes `build/release/pdf2iso-v.2.1.2.zip` (with the `VERSION` of
`pdf2iso.py`; `-o` gives another folder), with the program inside a
folder of the same name.  It contains the script, the licence and the
documents, and a file `COMMIT` with the commit it was made from.  It does
not contain hidden files (`.git` ...), nor what is made while the program
runs or is edited (`__pycache__` ...), nor `build/`, `dist/` and `tools/`.

The tests are run with

    $ python3 tools/test.py [-j N] [-v] [NAME ...]

each test file in a `pytest` of its own, as many at once as there are
processors (`-j` changes it).

A release on GitHub and Codeberg, with the ZIP, is made with

    $ python3 tools/release.py [--redo] [--notes TEXT | --notes-file FILE]
          [--no-build] [--no-tests] [--only github|codeberg] [--dry-run] [--yes]

It needs `gh` (GitHub) and `tea` (Codeberg), and a clean `main`.  It runs
the tests (`tools/test.py`, each test file in a process of its own, all at
once; `--no-tests` leaves them out), makes the ZIP, tags the commit `vVERSION`, pushes `main` and the tag, and makes
the release on each forge (or keeps the existing one), attaching the ZIP
and replacing one of the same name.  The ZIP, its signature and
`SHA256SUMS` are made in `build/release/`, and the deposit for Zenodo in
`build/zenodo/`; both are deleted at the end, once published, so nothing
of a release is kept here.  If releases are switched off for the
repository on Codeberg, it switches them on first.  It shows the commands
and asks before running them; `--dry-run` only shows them.  For a new
release, raise `VERSION` in `pdf2iso.py` first: if the tag is on
another commit, the script stops, unless `--redo` moves it, which remakes
a release.

Licensing
---------

pdf2iso is distributed under the GNU General Public License, version
3 or (at your option) any later version (see [LICENCE.txt](LICENCE.txt)):
anybody can use, copy, change and redistribute it, even commercially, but
a changed or bigger program that includes it must be distributed under the
same licence, with its source code.  The copyright notice recognizes
Nicolas Vaughan (<nicolasvaughan@proton.me>, 2026).  Ghostscript, pikepdf and veraPDF are
separate programs, with their own licences; pdf2iso runs them or
imports them, but does not include them.  The open-source software
pdf2iso uses, with the licence of each, is listed in
[docs/OPEN-SOURCE.md](docs/OPEN-SOURCE.md).
