Software de código abierto que usa pdf2iso
==========================================

pdf2iso es software libre, bajo la Licencia Pública General de GNU,
versión 3 o posterior (GPL-3.0-or-later).  Está hecho con el software de
código abierto de esta lista, y funciona sobre él; de cada uno se da la
licencia, con su identificador SPDX.  Las versiones son aquellas con las
que se comprobó pdf2iso 2.1.2.  Cada paquete lleva el texto completo de su
propia licencia.  pdf2iso no incluye ninguno: importa los paquetes de
Python y ejecuta los programas.


El programa
-----------

Lo que pdf2iso necesita para funcionar.  Los paquetes de Python vienen de
PyPI (`uv run` los instala por su cuenta, a partir de la cabecera PEP 723
del script).

| Software | Versión | Para qué | Licencia |
|---|---|---|---|
| [Python](https://www.python.org) | 3.14 o posterior | El lenguaje y su biblioteca estándar | PSF-2.0 |
| [pikepdf](https://github.com/pikepdf/pikepdf) | 8 o posterior (comprobado con 10.18.2) | Leer, reparar y corregir los PDF; la vía `--light` | MPL-2.0 |
| [lxml](https://lxml.de) | 6.1.3 | XML, para pikepdf (metadatos XMP) | BSD-3-Clause |
| [packaging](https://github.com/pypa/packaging) | 26.3 | Números de versión, para pikepdf | Apache-2.0 OR BSD-2-Clause |
| [Pillow](https://python-pillow.github.io) | 13.0.0 | Imágenes, para pikepdf | MIT-CMU |
| [Ghostscript](https://www.ghostscript.com) | 10 o posterior (comprobado con 10.07.1) | La conversión a PDF/A y PDF/X-4 (`pdfwrite`) | AGPL-3.0-or-later |

pikepdf se apoya en la biblioteca de C++ [QPDF](https://qpdf.sourceforge.io)
(Apache-2.0), que va dentro de sus wheels junto con libjpeg-turbo (IJG,
BSD-3-Clause y Zlib).  Las wheels de Pillow llevan FreeType (FTL o
GPL-2.0-or-later), HarfBuzz (MIT), Little CMS (MIT), libpng (Libpng-2.0),
libjpeg-turbo, LibTIFF (libtiff), libwebp (BSD-3-Clause), OpenJPEG
(BSD-2-Clause), libavif (BSD-2-Clause), Brotli (MIT), la liblzma de XZ
(0BSD), Zstandard (BSD-3-Clause), y libxcb y libXau (MIT).

Los perfiles ICC de la intención de salida son, por omisión, los que trae
Ghostscript (`srgb.icc` y `default_cmyk.icc`, en su carpeta
`iccprofiles`), bajo la licencia de Ghostscript.  Si Ghostscript no tiene
perfil sRGB, pdf2iso toma el de
[colord](https://www.freedesktop.org/software/colord/) (GPL-2.0-or-later AND
LGPL-2.1-or-later),
si está instalado.  Un perfil dado con `--icc` conserva su propia
licencia.


Programas que ejecuta, si están instalados
------------------------------------------

| Software | Versión | Para qué | Licencia |
|---|---|---|---|
| [veraPDF](https://verapdf.org) | comprobado con 1.30.4 | Validar los PDF/A (`--validate`); lo necesita `--light` | GPL-3.0-or-later OR MPL-2.0 |

veraPDF necesita un entorno de Java, como
[OpenJDK](https://openjdk.org) (GPL-2.0-only WITH Classpath-exception-2.0).
Sin veraPDF, pdf2iso funciona, pero no valida.


Instalación, pruebas y publicación
----------------------------------

Esto sirve para instalar, comprobar y publicar pdf2iso, y no forma parte
del programa.

| Software | Para qué | Licencia |
|---|---|---|
| [GNU Bash](https://www.gnu.org/software/bash/) y [GNU Coreutils](https://www.gnu.org/software/coreutils/) | El instalador, `install.sh` | GPL-3.0-or-later |
| [uv](https://github.com/astral-sh/uv) | Ejecutar el script con pikepdf, sin instalarlo a mano | Apache-2.0 OR MIT |
| [veraPDF](https://verapdf.org) | Validar cada archivo de prueba, por las dos vías | GPL-3.0-or-later OR MPL-2.0 |
| [TeX Live](https://tug.org/texlive/) (pdfLaTeX, con hyperref, ocgx2 y otros paquetes) | Hacer los archivos de prueba: enlaces, transparencias, capas, adjuntos | LPPL-1.3c y otras |
| [Git](https://git-scm.com) | La historia del código; el commit que se anota en el zip (`COMMIT`) | GPL-2.0-only |
| [GitHub CLI](https://cli.github.com) (`gh`) | Las versiones en GitHub (`tools/release.py`) | MIT |
| [tea](https://gitea.com/gitea/tea) | Las versiones en Codeberg (`tools/release.py`) | MIT |
| [GnuPG](https://gnupg.org) (`gpg`) | Firmar la etiqueta y los archivos de cada versión, y comprobar las firmas (`tools/sign_release.py`) | GPL-3.0-or-later |
| [libsecret](https://gitlab.gnome.org/GNOME/libsecret) (`secret-tool`) | Guardar el token de Zenodo en el llavero del escritorio (`tools/zenodo.py`) | LGPL-2.1-or-later |
| [pytest](https://pytest.org) | Las pruebas de las herramientas de publicación (`tools/test.py`) | MIT |
