py-pdfconform
=============

*(English: [README.md](README.md))*

py-pdfconform convierte archivos PDF a dos normas ISO: PDF/A, para el
archivo a largo plazo (PDF/A-1b, PDF/A-2b y PDF/A-3b), y PDF/X-4, para la
impresión.  Es un solo script de Python, `py-pdfconform.py`.  La conversión
la hace Ghostscript; pikepdf abre antes los archivos cifrados o dañados y
corrige después los metadatos.  Luego se comprueba cada resultado: los
PDF/A con veraPDF, si está instalado, y los PDF/X-4 con una revisión
estructural propia.  Es software libre, bajo la Licencia Pública General
de GNU (véase "Licencia").

Lo escribí yo, Nicolas Vaughan (<nicolasvaughan@proton.me>), en 2026.  Empezó como `py-pdfa`, un
conversor a PDF/A, y tomó su nombre actual cuando se le añadió PDF/X-4.

[Nicolas Vaughan](https://artehum.uniandes.edu.co/profesores/nicolas-vaughan/)
es profesor asociado de Literatura de la Facultad de Artes y Humanidades
de la Universidad de los Andes, Bogotá, Colombia.

Instalación
-----------

### Qué se necesita

- Python 3.14 o superior.
- Ghostscript 10 o superior (la orden `gs`; `gswin64c` en Windows).
- pikepdf, la biblioteca de Python.
- veraPDF (<https://verapdf.org/software/>), solo para validar los PDF/A.
  Es opcional.

En Fedora:

    sudo dnf install ghostscript python3-pikepdf

En Debian y Ubuntu:

    sudo apt install ghostscript python3-pikepdf

En macOS, con Homebrew:

    brew install ghostscript
    pip3 install pikepdf

### Obtener el programa

Se copia `py-pdfconform.py` en cualquier carpeta y se ejecuta con `python3
py-pdfconform.py`.  No hay que instalar nada más.  Con
[uv](https://docs.astral.sh/uv/), el script declara su propia
dependencia, así que `uv run py-pdfconform.py ...` funciona sin instalar
antes pikepdf (Ghostscript sigue haciendo falta).  uv también descarga por
su cuenta Python 3.14 cuando el del sistema es más antiguo, como en
Debian 13; allí, `uv run` es la manera más sencilla de usar el programa.

Uso
---

    python3 py-pdfconform.py informe.pdf                 # informe_pdfa.pdf, PDF/A-2b
    python3 py-pdfconform.py informe.pdf -t a-1b -o archivado.pdf
    python3 py-pdfconform.py *.pdf -d convertidos/ --validate
    python3 py-pdfconform.py cerrado.pdf -p secreto      # archivo cifrado
    python3 py-pdfconform.py volante.pdf -t x-4          # volante_pdfx.pdf, PDF/X-4
    python3 py-pdfconform.py volante.pdf -t x-4 --icc PSOcoated_v3.icc --condition FOGRA51

El archivo de salida queda junto al de entrada, con `_pdfa` o `_pdfx`
añadido al nombre, salvo que `-o` o `-d` digan otra cosa.  El programa
nunca escribe sobre la entrada.  Por cada archivo imprime una línea, `OK`
o `BAD` con el resultado de la comprobación, o `FAIL` si no pudo hacer la
conversión; las advertencias van antes.

| Opción | Significado |
|--------|-------------|
| `-t`, `--target` | `a-1b`, `a-2b` (por omisión), `a-3b` o `x-4`.  También acepta otras grafías: `PDF/A-2b`, `pdfa2b`, `2b`, `PDF/X-4`, `x4`. |
| `-o`, `--output` | El archivo de salida (solo con una entrada). |
| `-d`, `--outdir` | La carpeta de los archivos de salida. |
| `-p`, `--password` | La contraseña de una entrada cifrada. |
| `--suffix` | Lo que se añade a los nombres de salida, en lugar de `_pdfa` o `_pdfx`. |
| `--icc` | El perfil ICC de la intención de salida: un perfil sRGB para PDF/A, el perfil CMYK de la imprenta para PDF/X-4.  Por omisión, los perfiles del propio Ghostscript. |
| `--condition` | Solo PDF/X-4: el nombre registrado de la condición de impresión que describe el perfil de `--icc`, como `FOGRA39`.  Por omisión, `Custom`. |
| `--validate` | Solo PDF/A: termina con un error si no encuentra veraPDF, en lugar de convertir sin validar. |
| `--verapdf` | La ruta de la orden de veraPDF, si no está en el PATH. |
| `-v`, `--verbose` | Muestra los mensajes de Ghostscript y de veraPDF. |
| `--version` | Muestra la versión del programa. |

Antes de tocar ningún archivo, el programa comprueba lo que necesita:
Python 3.14 o superior, pikepdf 8 o superior, Ghostscript 10 o superior,
un perfil ICC utilizable y veraPDF cuando `--validate` o `--verapdf` lo
piden.  Si falta algo, dice qué falta y cómo conseguirlo.

El código de salida es 0 cuando todos los archivos se convirtieron y
pasaron su comprobación, 1 cuando alguno falló y 2 cuando el programa no
pudo empezar porque le falta algo.

Qué norma elegir
----------------

**PDF/A-2b** es la opción por omisión, y la adecuada para casi todo
archivo.  Conserva las transparencias y las capas, y los archivos y
repositorios que piden PDF/A normalmente la aceptan.  Los archivos
adjuntos se quitan (PDF/A-2 solo admite adjuntos que sean a su vez
PDF/A), con una advertencia.

**PDF/A-1b** es la versión más antigua, basada en PDF 1.4.  Conviene
usarla solo cuando un archivo la exige.  PDF/A-1 no admite transparencias,
así que Ghostscript convierte en imagen cada página que las tenga: la
página se ve igual, pero su texto ya no se puede seleccionar ni buscar, y
sus enlaces se pierden.  El programa avisa cuando ocurre.  También se
quitan los adjuntos.

**PDF/A-3b** es PDF/A-2b con permiso para llevar adjuntos de cualquier
tipo, así que conserva los del archivo de entrada.

**PDF/X-4** sirve para enviar a imprenta.  Todos los colores se convierten
a CMYK para una condición de impresión (véase la sección siguiente), las
transparencias se conservan y cada página recibe un TrimBox y un BleedBox.
Los enlaces, comentarios y demás anotaciones se quitan, porque PDF/X no
los admite en la página impresa; el programa dice cuántos quitó.  También
se quitan los adjuntos: a la imprenta no le sirven, y las descripciones
públicas de PDF/X-4 no dejan claro si los admite.

La "b" de los niveles de PDF/A indica que se conserva el aspecto de las
páginas.  Los niveles "a" y "u" exigen además una estructura etiquetada y
correspondencias Unicode para todo el texto, que Ghostscript no puede
garantizar, y por eso el programa no los ofrece.

PDF/X-4 y los perfiles de color
-------------------------------

Un archivo PDF/X declara para qué condición de impresión se prepararon sus
colores: un tipo de prensa y de papel, descrito por un perfil ICC CMYK.
Sin `--icc`, el programa usa el perfil que trae Ghostscript, "Artifex
CMYK SWOP Profile", cercano a la impresión offset de bobina
estadounidense sobre papel estucado, y llama `Custom` a la condición.
Basta para un archivo de uso general.  Para un trabajo de imprenta real,
hay que preguntar a la imprenta qué perfil usar y darlo con su nombre
registrado:

| Condición | Perfil | Uso |
|-----------|--------|-----|
| `FOGRA39` | ISO Coated v2 (ECI) | Offset sobre papel estucado, Europa (norma anterior) |
| `FOGRA51` | PSO Coated v3 (ECI) | Offset sobre papel estucado, Europa |
| `FOGRA52` | PSO Uncoated v3 (ECI) | Offset sobre papel no estucado, Europa |
| `CGATS TR 006` | GRACoL 2006 Coated | Offset sobre papel estucado, Estados Unidos |

Los perfiles de la ECI se descargan de <https://www.eci.org/>.  El
programa comprueba que el perfil sea de verdad CMYK, y rechaza uno RGB.

Las cajas de página se ajustan al tamaño de la página, sin sangrado.  Es
lo correcto para documentos que no imprimen hasta el borde del papel; un
diseño con sangrado tiene que prepararse así en el programa que lo hizo.

Cómo funciona
-------------

La conversión tiene cuatro pasos.

1. pikepdf abre la entrada, con la contraseña si la tiene, y guarda una
   copia sin cifrar.  Al guardarla también rehace las tablas de
   referencias cruzadas dañadas.  En este punto el programa conserva el
   título, el autor, el asunto, las palabras clave y el creador, y marca
   cada anotación como imprimible: PDF/A lo pide, y sin eso Ghostscript
   las quita (los enlaces que hace pdfLaTeX, por ejemplo).
2. El dispositivo `pdfwrite` de Ghostscript escribe de nuevo el archivo
   según la norma (`-dPDFA=1`, `2` o `3`, o `-dPDFX=4`).  Incrusta todas
   las fuentes, convierte los colores (a sRGB para PDF/A, a CMYK para
   PDF/X), adjunta el perfil ICC como intención de salida y deja fuera lo
   que la norma prohíbe.  Las imágenes no se reducen de resolución.
3. pikepdf repone los metadatos que Ghostscript haya perdido y hace que los
   metadatos XMP coincidan con el diccionario de información del
   documento, como exigen ambas normas.  También corrige lo que
   Ghostscript deja mal o deja atrás: quita el JavaScript (Ghostscript lo
   mueve a un lugar donde los validadores no miran), da a los adjuntos un
   tipo MIME válido, quita los adjuntos en todas las normas salvo
   PDF/A-3b y elimina de las capas los ajustes automáticos que ambas
   normas prohíben.  Para PDF/X-4 fija además el título (el nombre del
   archivo, si el documento no tiene), `Trapped` y `GTS_PDFXVersion`.
4. Se comprueba el resultado (véase la sección siguiente).

Validación
----------

Los PDF/A se validan con veraPDF, el validador de referencia de la PDF
Association, cuando se encuentra la orden `verapdf`.  La línea de cada
archivo dice `veraPDF: PASS` o `veraPDF: FAIL`; si falla, se muestra el
informe de veraPDF.

veraPDF no valida PDF/X.  Los PDF/X-4 reciben, en cambio, una revisión
escrita para este programa, que mira aquello de lo que la conversión
responde: la versión de PDF/X en los metadatos XMP, el título, las fechas
e identificadores, `Trapped`, la intención de salida y su perfil, el
TrimBox y el BleedBox de cada página y las anotaciones.  No revisa cómo se
usa cada color y cada fuente dentro de las páginas.  Una verificación
previa completa de PDF/X necesita Adobe Acrobat Pro o callas pdfToolbox, y
antes de un trabajo de imprenta importante es prudente que la imprenta
revise un archivo.

Limitaciones
------------

- Ghostscript escribe de nuevo todo el archivo.  Lo que una norma no
  admite se deja fuera: el JavaScript, los adjuntos (salvo en PDF/A-3b) y,
  en PDF/X, las anotaciones.  El programa avisa de cada caso.
- Los colores se convierten, a sRGB para PDF/A y a CMYK para PDF/X.  Con
  un documento de colores de impresión exactos (tintas planas, un perfil
  CMYK concreto), hay que revisar el resultado.
- En PDF/A-1b, las páginas con transparencias se vuelven imágenes (véase
  "Qué norma elegir").
- Solo se producen los niveles "b" de PDF/A.

Publicar una versión
--------------------

El ZIP del programa se hace con

    $ python3 tools/bundle-zip.py [-o CARPETA]

Escribe `dist/py-pdfconform-v.1.0.zip` (con la `VERSION` de
`py-pdfconform.py`; `-o` da otra carpeta), con el programa dentro de una
carpeta del mismo nombre.  Contiene el script, la licencia y los
documentos, y un archivo `COMMIT` con el commit del que se hizo.  No
contiene archivos ocultos (`.git`...), ni lo que se genera al ejecutar o
editar el programa (`__pycache__`...), ni `dist/` y `tools/`.

Una versión en GitHub y Codeberg, con el ZIP, se publica con

    $ python3 tools/release.py [--redo] [--notes TEXTO | --notes-file ARCHIVO]
          [--no-build] [--only github|codeberg] [--dry-run] [--yes]

Necesita `gh` (GitHub) y `tea` (Codeberg), y una rama `main` limpia.  Hace
el ZIP, etiqueta el commit como `vVERSION`, sube `main` y la etiqueta, y
crea la versión en cada forja (o conserva la que ya existe), le adjunta
el ZIP y reemplaza el que tenga el mismo nombre.  Si el repositorio de
Codeberg tiene las versiones desactivadas, primero las activa.  Muestra
las órdenes y pregunta antes de ejecutarlas; `--dry-run` solo las
muestra.  Para una versión nueva hay que subir antes `VERSION` en
`py-pdfconform.py`: si la etiqueta está en otro commit, el script se
detiene, salvo que `--redo` la mueva, lo que rehace una versión.

Licencia
--------

py-pdfconform se distribuye bajo la Licencia Pública General de GNU (GPL),
versión 3 o (a su elección) cualquier versión posterior (véase
[LICENCE.txt](LICENCE.txt)): cualquiera puede usarlo, copiarlo,
modificarlo y redistribuirlo, también con fines comerciales, pero un
programa modificado o mayor que lo incluya debe distribuirse bajo la
misma licencia, con su código fuente.  El aviso de copyright reconoce a
Nicolas Vaughan (<nicolasvaughan@proton.me>, 2026).  Ghostscript, pikepdf y veraPDF son
programas aparte, con sus propias licencias; py-pdfconform los ejecuta o
los importa, pero no los incluye.
