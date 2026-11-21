# Registro de cambios

Los cambios notables de pdf2iso, que se llamó py-pdfconform hasta la
versión 2.0. Las versiones publicadas, con sus archivos zip, están en
[Codeberg](https://codeberg.org/nivaca/pdf2iso/releases) y
[GitHub](https://github.com/nivaca/pdf2iso/releases).

## 2.1.1 — 2026-11-21

- `docs/OPEN-SOURCE.md` y `docs/OPEN-SOURCE_es.md`: el software de
  código abierto que usa pdf2iso, con la licencia de cada uno.  Los
  README remiten a ellos.
- `docs/DESCRIPCIÓN_es.md` se ciñe a seis secciones, cada una de menos
  de 4000 caracteres, en tercera persona. El programa no cambia.

## 2.1 — 2026-11-18

- **`--light`**, para PDF/A-2b y PDF/A-3b: el PDF/A se hace primero solo
  con pikepdf, sin tocar las páginas, y se conserva si veraPDF lo
  aprueba; si no, el archivo se convierte con Ghostscript como antes.
  Sirve para los escaneos que Ghostscript agranda mucho: un libro de 587
  páginas escaneado por el Internet Archive se queda en 24 MB en lugar
  de 173 MB, y se convierte en 4 segundos en lugar de 72. `--light`
  necesita veraPDF.
- Las imágenes ya no conservan la clave `Interpolate`, que PDF/A prohíbe.

## 2.0 — 2026-11-17

- **py-pdfconform pasa a llamarse pdf2iso**: el script es `pdf2iso.py`,
  la orden que crea `install.sh` es `pdf2iso`, el zip es
  `pdf2iso-v.VERSION.zip`, y los repositorios son nivaca/pdf2iso en
  GitHub y Codeberg. El enlace que haya creado una versión anterior
  (`~/bin/py-pdfconform` o `~/.local/bin/py-pdfconform`) hay que
  borrarlo a mano.
- La conversión no cambia.

## 1.2.2 — 2026-11-17

- Cuando no existe `~/bin`, `install.sh` vuelve a poner el enlace en
  `~/.local/bin`: la 1.2.1 lo llevó por error a `~/.local/share/bin`, que
  no está en el PATH por omisión. El enlace que haya creado allí la 1.2.1
  hay que borrarlo a mano.

## 1.2.1 — 2026-11-17

- `install.sh` avisa cuando veraPDF no está instalado; el programa
  funciona sin él, pero no puede validar los resultados PDF/A.
- Cuando no existía `~/bin`, el enlace iba a `~/.local/share/bin` en
  lugar de `~/.local/bin` (deshecho en la 1.2.2).

## 1.2 — 2026-11-17

- Un instalador para Linux: `./install.sh` crea la orden
  `py-pdfconform`, un enlace simbólico al script en `~/bin` (o en
  `~/.local/bin` si no existe `~/bin`), y comprueba que arranca;
  `./install.sh --uninstall` quita el enlace.
- El archivo `COMMIT` del zip lo pueden leer todos (modo 644).

## 1.1 — 2026-11-16

- Hace falta Python 3.14 o superior (antes, 3.10). Donde el Python del
  sistema es más antiguo, `uv run py-pdfconform.py` descarga uno más
  reciente.
- El zip trae un archivo `COMMIT`, con el commit del que se hizo;
  `tools/release.py` publica una versión en GitHub y Codeberg.
- La conversión no cambia.

## 1.0 — 2026-11-16

- Primera versión: py-pdfconform convierte archivos PDF a PDF/A-1b,
  PDF/A-2b o PDF/A-3b, para el archivo, y a PDF/X-4, para la impresión,
  con Ghostscript y pikepdf (`-t`/`--target`). Los resultados PDF/A se
  validan con veraPDF cuando está instalado; los PDF/X-4 pasan por una
  revisión estructural propia.
- PDF/X-4 recibe un output intent CMYK (el perfil SWOP de Ghostscript, o
  `--icc` con `--condition`) y las claves que necesita en la información
  del documento y en XMP.
- Se corrige lo que Ghostscript deja mal: se eliminan los adjuntos que
  la norma no permite (también en PDF/X-4), se reparan los tipos MIME de
  los demás, se quita el JavaScript y se da nombre a cada configuración
  de contenido opcional. Un aviso indica cuándo se eliminan anotaciones.
- Antes de convertir se comprueban Python, pikepdf, Ghostscript y
  veraPDF; `--version`.
