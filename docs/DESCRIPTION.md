How py-pdfconform was made
==========================

py-pdfconform converts PDF files to PDF/A, for long-term archiving, and
to PDF/X-4, for printing.  Nicolas Vaughan made it in 2026.  It does not
convert anything by itself: Ghostscript does the conversion, and the
program prepares the input, corrects what Ghostscript leaves wrong and
checks the result.  It is free software, under the GNU General Public
License, version 3 or later.  Here I explain how it was made, in five
stages.

Nicolas Vaughan is Associate Professor of Literature at the School of Arts
and Humanities of the Universidad de los Andes, Bogotá, Colombia.

1. A PDF/A converter
--------------------

The first version was called `py-pdfa`, and it only made PDF/A.  The
choice of Ghostscript was simple: its `pdfwrite` device can write PDF/A
by itself (`-dPDFA`), it embeds the fonts and converts the colours, and
it is installed almost everywhere.  What Ghostscript needs from outside is
a small PostScript file that attaches an ICC profile as the output
intent; the program writes it for each conversion, with the sRGB profile
that comes with Ghostscript.  With `-dPDFACompatibilityPolicy=1`,
Ghostscript leaves out what the standard forbids instead of giving up.

Around Ghostscript there are two steps with pikepdf.  Before it, pikepdf
opens the input, also when it is encrypted (Ghostscript cannot open a file
protected with a password), and saves a clean copy.  After it, pikepdf
restores the title, author and other data if Ghostscript has lost them
(a precaution), and makes the XMP metadata agree with the document information
dictionary, which PDF/A requires.

The results were checked with veraPDF 1.30.4.  The first tests showed two
problems, both silent.  The links made by pdfLaTeX disappeared: PDF/A
wants every annotation to be printable, pdfLaTeX does not mark them so,
and Ghostscript removes them without a word.  Now the program marks them
before the conversion.  The other problem has no remedy: PDF/A-1 does not
allow transparency, so Ghostscript turns those pages into images, and
their text can no longer be selected.  The program compares the pages
that have fonts before and after, and warns when some were lost.

2. PDF/X-4
----------

PDF/X-4 was added later.  The documentation of Ghostscript contradicts
itself here: one paragraph says `-dPDFX` accepts 1, 3 or 4, and a warning
a little below says that only PDF/X-1 and PDF/X-3 are supported.  So I
tried it with Ghostscript 10.07.  The output was correct PDF/X-4: PDF 1.6,
with the transparency kept, the PDF/X version in the metadata, and a
TrimBox and a BleedBox on each page.  But in some files Ghostscript did
not write `pdf:Trapped` in the XMP metadata, which PDF/X-4 requires; the
step after Ghostscript adds it, together with the title, which PDF/X also
requires (the file name, if the document has none).

The colours are the main difference with PDF/A.  A PDF/X file is prepared
for one printing condition, described by a CMYK profile, so the program
takes the printer's profile (`--icc`) and its registered name
(`--condition`, such as FOGRA39).  For general use, without those
options, it uses the CMYK profile that comes with Ghostscript, a SWOP-like
profile, and calls the condition `Custom`.

veraPDF does not validate PDF/X, and there is no free validator for it.
So I wrote a structural check of the parts that the conversion is
responsible for: the metadata, the output intent, the page boxes and the
annotations.  It is not a complete preflight, and the README says so.

3. A new name
-------------

With two standards, `py-pdfa` was no longer an accurate name.  The project
became `py-pdfconform`, and the script `py-pdfconform.py`, which describes
what it does (making a PDF conform to a standard) and would still fit if
other standards were added.  The option `-l` (level) became `-t`
(target), which accepts `a-2b`, `x-4` and other spellings such as
`PDF/A-2b`.

4. What Ghostscript leaves behind
---------------------------------

While writing the README I tested the claims it was going to make, and
three of them were false.  A file with an attached CSV file and a
JavaScript action, and a LaTeX file with layers (made with the ocgx2
package), all failed veraPDF:

- PDF/A-1 does not allow attachments, and PDF/A-2 only allows attachments
  that are PDF/A themselves; Ghostscript kept them anyway.  Now the
  program removes them in these two levels, with a warning that
  recommends PDF/A-3b.
- In PDF/A-3b, which allows them, Ghostscript writes the MIME type of the
  attachment wrongly ("text/csv" becomes `text#2?csv`).  The program
  restores the original type, gives each attachment an `AFRelationship`
  and lists it in the `AF` array of the catalog.
- PDF/A forbids the automatic settings of the layers (`AS`) that ocgx2
  writes, and requires a name for each layer configuration.  The program
  removes the first and adds the second.

The fourth problem did not fail veraPDF, and that made it worse.
Ghostscript moves a JavaScript action that runs when the document opens to
a non-standard entry of the catalog, `/A`, where veraPDF does not look: the
file passed, with the script still inside.  Now the program removes
JavaScript from the catalog, the pages and the annotations, and says so.

5. Version 1.0
--------------

Before calling it 1.0 I looked at what happens when something is
missing.  The program already stopped with a message when there was no
Ghostscript or no ICC profile, but without pikepdf Python only printed a
traceback, and nothing checked the versions.  Now, before it touches any
file, it checks Python (then 3.10 or later), pikepdf (8 or later), Ghostscript
(10 or later, as `gs --version` says), the ICC profile and, when it is
asked for, veraPDF.  If something is missing, it says what and how to get
it, and ends with the exit code 2.  I tried each case in a faked
environment: no pikepdf, Python 3.9, no Ghostscript, a false Ghostscript
9.56, a wrong path to veraPDF.

The version is a constant, `VERSION`, at the top of the script, and
`--version` shows it.  Two tools in `tools/`, smaller copies of those of
py-words, make the releases.  `bundle-zip.py` makes the ZIP of the
distribution, `py-pdfconform-v.1.0.zip`, with the script, the licence and
the documents in a folder of the same name, and a file `COMMIT` with the
commit it was made from.  `release.py` makes the ZIP, tags the commit,
pushes the tag, and makes the release with the ZIP on GitHub and on
Codeberg; it shows the commands before running them, and stops if the tag
is already on another commit.  The first release on Codeberg failed with a
message that explained nothing ("The target couldn't be found"): the
repository had releases switched off.  `release.py` now looks at this
setting and switches them on if needed.  Version 1.0 was published on both
forges on 16 November 2026.

Version 1.1 raised the minimum to Python 3.14, as in my other programs,
and gathered what is done with each file (converting it and checking the
result) into one function, `process()`.  The conversion itself did not
change.  Version 1.2 added an installer for Linux, `install.sh`, which makes
the command `py-pdfconform` as a symbolic link to the script in `~/bin`,
or in `~/.local/bin` when there is no `~/bin`.

Testing
-------

The test files were a pdfLaTeX document with transparency and a link; the
same document encrypted with AES-256; a PDF made by hand with an
unembedded Helvetica font and CMYK colour; a PDF without a title; the
first five pages of a document of 394 pages made by WeasyPrint, with
images, an outline and links; a document with an attached CSV file and a
JavaScript action; a LaTeX document with layers; and a LaTeX document
with an RGB photograph, a PNG with transparency, a CMYK JPEG and colour
gradients.  Each was converted to the four targets.  All the PDF/A results pass veraPDF, and all the PDF/X-4
results pass the structural check.  The check itself was tested on files
that should fail it (the original documents and PDF/A files), and it
failed them.  I also looked at the PDF/X-4 results inside: the colours
are only CMYK, the text can be extracted, and the transparency is still
there.

Later I checked the PDF/X-4 results more closely.  A separate scan looked
for RGB colour anywhere in the files (also in transparency groups and soft
masks), fonts not embedded, a missing trailer ID, dates in the XMP
metadata that differ from those of the Info dictionary, and the features
PDF/X forbids; it found nothing.  Every page was rendered before and after
the conversion and compared: nothing was lost or moved.  Bright screen
colours come out duller, since CMYK ink cannot print them; to be sure the
conversion itself was right, I converted the same colours with littleCMS
and the same CMYK profile, and Ghostscript's results agree within a few
units.  The scan did find that the attached file was kept.  Whether
PDF/X-4 allows attachments could not be confirmed from public sources, so
the program now removes them in PDF/X-4 too, with a warning, and the
structural check rejects a PDF/X-4 file that has one.

The program is one file of around 800 lines; the two tools in `tools/`
add around 400 more.  `release.py` was tried with `--dry-run`, which only
shows its plan: on the repository as it was after 1.0 (it would replace
the ZIP of the existing releases), and in a copy of it with a new commit,
first with the same version (it stops) and then with version 1.1 (it
would tag, push and make both releases).
