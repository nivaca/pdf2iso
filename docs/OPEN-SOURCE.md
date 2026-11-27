Open-source software used by pdf2iso
====================================

pdf2iso is free software, under the GNU General Public License, version 3
or later (GPL-3.0-or-later).  It is made with, and runs on, the
open-source software listed here, with the licence of each.  Licences are
given as SPDX identifiers; the versions are those pdf2iso 2.1.2 was
checked with.  Each package carries the full text of its own licence.
pdf2iso includes none of them: it imports the Python packages and runs
the programs.


The program
-----------

What pdf2iso needs to run.  The Python packages come from PyPI (`uv run`
installs them by itself, from the PEP 723 header of the script).

| Software | Version | Used for | Licence |
|---|---|---|---|
| [Python](https://www.python.org) | 3.14 or later | The language and its standard library | PSF-2.0 |
| [pikepdf](https://github.com/pikepdf/pikepdf) | 8 or later (checked with 10.18.2) | Reading, repairing and correcting the PDF files; the `--light` route | MPL-2.0 |
| [lxml](https://lxml.de) | 6.1.3 | XML, for pikepdf (XMP metadata) | BSD-3-Clause |
| [packaging](https://github.com/pypa/packaging) | 26.3 | Version numbers, for pikepdf | Apache-2.0 OR BSD-2-Clause |
| [Pillow](https://python-pillow.github.io) | 13.0.0 | Images, for pikepdf | MIT-CMU |
| [Ghostscript](https://www.ghostscript.com) | 10 or later (checked with 10.07.1) | The conversion to PDF/A and PDF/X-4 (`pdfwrite`) | AGPL-3.0-or-later |

pikepdf is built on the C++ library [QPDF](https://qpdf.sourceforge.io)
(Apache-2.0), which its wheels carry inside, with libjpeg-turbo (IJG,
BSD-3-Clause and Zlib).  The Pillow wheels carry FreeType (FTL or
GPL-2.0-or-later), HarfBuzz (MIT), Little CMS (MIT), libpng (Libpng-2.0),
libjpeg-turbo, LibTIFF (libtiff), libwebp (BSD-3-Clause), OpenJPEG
(BSD-2-Clause), libavif (BSD-2-Clause), Brotli (MIT), XZ's liblzma (0BSD),
Zstandard (BSD-3-Clause) and libxcb and libXau (MIT).

The ICC profiles of the output intent are, by default, those that come
with Ghostscript (`srgb.icc` and `default_cmyk.icc`, in its
`iccprofiles` folder), under Ghostscript's licence.  When Ghostscript has
no sRGB profile, pdf2iso takes the one of
[colord](https://www.freedesktop.org/software/colord/) (GPL-2.0-or-later AND
LGPL-2.1-or-later) if it is installed.  A profile given with `--icc` keeps its own licence.


Programs it calls, if installed
-------------------------------

| Software | Version | Used for | Licence |
|---|---|---|---|
| [veraPDF](https://verapdf.org) | checked with 1.30.4 | Checking the PDF/A files (`--validate`); needed by `--light` | GPL-3.0-or-later OR MPL-2.0 |

veraPDF needs a Java runtime, such as
[OpenJDK](https://openjdk.org) (GPL-2.0-only WITH Classpath-exception-2.0).
Without veraPDF, pdf2iso works, but does not validate.


Installing, testing and publishing
----------------------------------

These are used to install, check and publish pdf2iso, and are not part of
the program.

| Software | Used for | Licence |
|---|---|---|
| [GNU Bash](https://www.gnu.org/software/bash/) and [GNU Coreutils](https://www.gnu.org/software/coreutils/) | The installer, `install.sh` | GPL-3.0-or-later |
| [uv](https://github.com/astral-sh/uv) | Running the script with pikepdf, without installing it by hand | Apache-2.0 OR MIT |
| [veraPDF](https://verapdf.org) | Validating every test file, in both routes | GPL-3.0-or-later OR MPL-2.0 |
| [TeX Live](https://tug.org/texlive/) (pdfLaTeX, with hyperref, ocgx2 and other packages) | Making the test files: links, transparency, layers, attachments | LPPL-1.3c and others |
| [Git](https://git-scm.com) | The history of the code; the commit named in the zip (`COMMIT`) | GPL-2.0-only |
| [GitHub CLI](https://cli.github.com) (`gh`) | The releases on GitHub (`tools/release.py`) | MIT |
| [tea](https://gitea.com/gitea/tea) | The releases on Codeberg (`tools/release.py`) | MIT |
| [GnuPG](https://gnupg.org) (`gpg`) | Signing the tag and the files of each release, and checking the signatures (`tools/sign_release.py`) | GPL-3.0-or-later |
| [libsecret](https://gitlab.gnome.org/GNOME/libsecret) (`secret-tool`) | Keeping the Zenodo token in the desktop keyring (`tools/zenodo.py`) | LGPL-2.1-or-later |
| [pytest](https://pytest.org) | The tests of the release tools (`tools/test.py`) | MIT |
