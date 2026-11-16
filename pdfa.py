#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pikepdf>=8"]
# ///
"""Convert PDF files to PDF/A (PDF/A-1b, 2b or 3b).

The conversion is done by Ghostscript's pdfwrite device, which re-renders the
document, embeds all fonts, converts colours to sRGB and attaches an sRGB
output intent. pikepdf is used before (to open encrypted or damaged files)
and after (to restore document metadata and keep the XMP packet and the
Info dictionary in sync, as PDF/A requires).

If veraPDF (https://verapdf.org) is on the PATH, or given with --verapdf, the
result is validated against the requested flavour.

Requirements: Ghostscript >= 9.54 (``gs``) and pikepdf.

Examples:
    pdfa.py report.pdf                    # -> report_pdfa.pdf (PDF/A-2b)
    pdfa.py report.pdf -o archived.pdf -l 1b
    pdfa.py *.pdf -d out/ --validate
    pdfa.py locked.pdf --password secret
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pikepdf

LEVELS = {"1b": 1, "2b": 2, "3b": 3}

# Places where Ghostscript and common distributions ship an sRGB profile.
ICC_CANDIDATES = [
    "/usr/share/ghostscript/iccprofiles/srgb.icc",
    "/usr/share/ghostscript/*/iccprofiles/srgb.icc",
    "/usr/local/share/ghostscript/iccprofiles/srgb.icc",
    "/usr/local/share/ghostscript/*/iccprofiles/srgb.icc",
    "/opt/homebrew/share/ghostscript/*/iccprofiles/srgb.icc",
    "/opt/homebrew/share/ghostscript/iccprofiles/srgb.icc",
    "/usr/share/color/icc/colord/sRGB.icc",
    "/usr/share/color/icc/sRGB.icc",
    "C:/Program Files/gs/*/iccprofiles/srgb.icc",
    "C:/Windows/System32/spool/drivers/color/sRGB Color Space Profile.icm",
]

INFO_KEYS = ("/Title", "/Author", "/Subject", "/Keywords", "/Creator")

PDFA_DEF = """%!
/ICCProfile ({icc}) def
[/_objdef {{icc_PDFA}} /type /stream /OBJ pdfmark
[{{icc_PDFA}} << /N 3 >> /PUT pdfmark
[{{icc_PDFA}} ICCProfile (r) file /PUT pdfmark
[/_objdef {{OutputIntent_PDFA}} /type /dict /OBJ pdfmark
[{{OutputIntent_PDFA}} <<
  /Type /OutputIntent
  /S /GTS_PDFA1
  /DestOutputProfile {{icc_PDFA}}
  /OutputConditionIdentifier (sRGB IEC61966-2.1)
  /Info (sRGB IEC61966-2.1)
  /RegistryName (http://www.color.org)
>> /PUT pdfmark
[{{Catalog}} << /OutputIntents [ {{OutputIntent_PDFA}} ] >> /PUT pdfmark
"""


class ConversionError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def find_ghostscript() -> str:
    names = ["gs"]
    if os.name == "nt":
        names = ["gswin64c", "gswin32c", "gs"]
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    raise ConversionError("Ghostscript not found (looked for: %s)" % ", ".join(names))


def find_icc_profile(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            raise ConversionError(f"ICC profile not found: {p}")
        return p
    for pattern in ICC_CANDIDATES:
        anchor = Path(pattern).anchor
        for match in sorted(Path(anchor).glob(pattern[len(anchor):])):
            if match.is_file():
                return match
    raise ConversionError("No sRGB ICC profile found; pass one with --icc")


def ps_string(path: Path) -> str:
    """Escape a filesystem path for use inside a PostScript string literal."""
    s = path.resolve().as_posix()
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def pages_with_text(pdf: pikepdf.Pdf) -> int:
    """Count pages that use fonts; a drop after conversion means Ghostscript
    turned pages into images (it does so for transparency in PDF/A-1)."""
    count = 0
    for page in pdf.pages:
        try:
            if page.obj.get("/Resources", {}).get("/Font"):
                count += 1
        except Exception:
            pass
    return count


def read_info(pdf: pikepdf.Pdf) -> dict[str, str]:
    info = {}
    for key in INFO_KEYS:
        try:
            value = pdf.docinfo.get(key)
        except Exception:
            value = None
        if value is not None:
            text = str(value).strip()
            if text:
                info[key] = text
    return info


# --------------------------------------------------------------------------
# Conversion steps
# --------------------------------------------------------------------------

def set_print_flags(pdf: pikepdf.Pdf) -> None:
    """PDF/A wants every annotation printable and visible. Ghostscript drops
    the ones that are not (links made by pdfLaTeX, for example), so set the
    Print flag and clear Invisible, Hidden and NoView beforehand."""
    INVISIBLE, HIDDEN, PRINT, NOVIEW = 1, 2, 4, 32
    for page in pdf.pages:
        for annot in page.obj.get("/Annots", []):
            if not isinstance(annot, pikepdf.Dictionary):
                continue
            if annot.get("/Subtype") == pikepdf.Name.Popup:
                continue
            flags = int(annot.get("/F", 0))
            annot.F = (flags | PRINT) & ~(INVISIBLE | HIDDEN | NOVIEW)


def prepare_input(src: Path, dst: Path, password: str) -> tuple[dict[str, str], int]:
    """Decrypt/repair the input so Ghostscript can read it.

    Returns its Info metadata and the number of pages that carry text."""
    try:
        with pikepdf.open(src, password=password) as pdf:
            info = read_info(pdf)
            text_pages = pages_with_text(pdf)
            set_print_flags(pdf)
            # Saving without encryption also rewrites damaged xref tables.
            pdf.save(dst, encryption=False)
    except pikepdf.PasswordError:
        raise ConversionError(f"{src} is encrypted; supply the password with --password")
    except pikepdf.PdfError as exc:
        raise ConversionError(f"cannot read {src}: {exc}")
    return info, text_pages


def run_ghostscript(gs: str, src: Path, dst: Path, level: int, icc: Path,
                    workdir: Path, verbose: bool) -> None:
    def_file = workdir / "pdfa_def.ps"
    def_file.write_text(PDFA_DEF.format(icc=ps_string(icc)), encoding="ascii",
                        errors="strict")

    cmd = [
        gs,
        "-dBATCH", "-dNOPAUSE", "-dSAFER",
        "-q" if not verbose else "-dQUIET=false",
        f"--permit-file-read={icc.resolve().as_posix()}",
        "-sDEVICE=pdfwrite",
        f"-dPDFA={level}",
        "-dPDFACompatibilityPolicy=1",  # drop offending features, keep going
        f"-dCompatibilityLevel={'1.4' if level == 1 else '1.7'}",
        "-sColorConversionStrategy=RGB",
        "-dEmbedAllFonts=true",
        "-dSubsetFonts=true",
        "-dAutoRotatePages=/None",
        # Keep images as they are: no downsampling.
        "-dDownsampleColorImages=false",
        "-dDownsampleGrayImages=false",
        "-dDownsampleMonoImages=false",
        f"-sOutputFile={dst}",
        str(def_file),
        str(src),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    messages = (proc.stdout + proc.stderr).strip()
    if verbose and messages:
        print(messages, file=sys.stderr)
    if proc.returncode != 0 or not dst.is_file() or dst.stat().st_size == 0:
        raise ConversionError(f"Ghostscript failed (exit {proc.returncode}):\n{messages}")
    # With PDFACompatibilityPolicy=1 Ghostscript gives up on PDF/A, rather
    # than failing, when it meets something it cannot fix.
    lowered = messages.lower()
    if "aborting conversion" in lowered or "not producing pdf/a" in lowered \
            or "reverting to normal pdf output" in lowered:
        raise ConversionError("Ghostscript could not produce PDF/A:\n" + messages)


def finalize(path: Path, dst: Path, level: int, info: dict[str, str],
             text_pages: int) -> list[str]:
    """Restore lost metadata, sync XMP with DocInfo, check PDF/A markers.

    Returns a list of warnings."""
    warnings = []
    with pikepdf.open(path) as pdf:
        if pages_with_text(pdf) < text_pages:
            warnings.append(
                "some pages were rasterized (text is no longer selectable); "
                "this happens with transparency under PDF/A-1, try -l 2b")
        for key, value in info.items():
            if key not in pdf.docinfo or not str(pdf.docinfo[key]).strip():
                pdf.docinfo[key] = value
        with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
            meta.load_from_docinfo(pdf.docinfo, raise_failure=False)
            meta["pdfaid:part"] = str(level)
            meta["pdfaid:conformance"] = "B"

        if "/OutputIntents" not in pdf.Root:
            raise ConversionError("output has no OutputIntent; ICC profile was not embedded")

        # PDF/A-1 is based on PDF 1.4, which has no object streams.
        stream_mode = (pikepdf.ObjectStreamMode.disable if level == 1
                       else pikepdf.ObjectStreamMode.preserve)
        pdf.save(dst, object_stream_mode=stream_mode,
                 min_version="1.4" if level == 1 else "1.7",
                 force_version="1.4" if level == 1 else None)
    return warnings


def validate(verapdf: str, path: Path, level_name: str) -> tuple[bool, str]:
    proc = subprocess.run(
        [verapdf, "--flavour", level_name, "--format", "text", str(path)],
        capture_output=True, text=True, errors="replace",
    )
    out = (proc.stdout + proc.stderr).strip()
    passed = any(line.startswith("PASS") for line in out.splitlines())
    return passed, out


def convert(src: Path, dst: Path, level_name: str, *, password: str = "",
            icc: Path, gs: str, verbose: bool = False) -> list[str]:
    """Convert src to PDF/A at dst; return any warnings."""
    level = LEVELS[level_name]
    with tempfile.TemporaryDirectory(prefix="pdfa-") as tmp:
        work = Path(tmp)
        clean = work / "input.pdf"
        gs_out = work / "gs.pdf"
        final = work / "final.pdf"
        info, text_pages = prepare_input(src, clean, password)
        run_ghostscript(gs, clean, gs_out, level, icc, work, verbose)
        warnings = finalize(gs_out, final, level, info, text_pages)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(final, dst)
    return warnings


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Convert PDF files to PDF/A using Ghostscript and pikepdf.")
    ap.add_argument("inputs", nargs="+", type=Path, help="PDF file(s) to convert")
    out = ap.add_mutually_exclusive_group()
    out.add_argument("-o", "--output", type=Path,
                     help="output file (only with a single input)")
    out.add_argument("-d", "--outdir", type=Path,
                     help="directory for outputs (default: next to each input)")
    ap.add_argument("-l", "--level", choices=sorted(LEVELS), default="2b",
                    help="PDF/A flavour (default: 2b)")
    ap.add_argument("-p", "--password", default="",
                    help="password for encrypted inputs")
    ap.add_argument("--suffix", default="_pdfa",
                    help="suffix added to output names (default: _pdfa)")
    ap.add_argument("--icc", help="sRGB ICC profile to embed (default: autodetect)")
    ap.add_argument("--validate", action="store_true",
                    help="validate with veraPDF; fail if it is missing")
    ap.add_argument("--verapdf", help="path to the veraPDF command-line tool")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="show Ghostscript and veraPDF output")
    args = ap.parse_args(argv)

    if args.output and len(args.inputs) > 1:
        ap.error("--output can only be used with a single input; use --outdir")

    try:
        gs = find_ghostscript()
        icc = find_icc_profile(args.icc)
    except ConversionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    verapdf = args.verapdf or shutil.which("verapdf")
    if args.validate and not verapdf:
        print("error: --validate given but veraPDF was not found", file=sys.stderr)
        return 2

    failures = 0
    for src in args.inputs:
        if args.output:
            dst = args.output
        else:
            folder = args.outdir or src.parent
            dst = folder / f"{src.stem}{args.suffix}.pdf"
        if dst.resolve() == src.resolve():
            print(f"skip {src}: output would overwrite the input", file=sys.stderr)
            failures += 1
            continue
        try:
            warnings = convert(src, dst, args.level, password=args.password, icc=icc, gs=gs,
                    verbose=args.verbose)
        except (ConversionError, OSError) as exc:
            print(f"FAIL {src}: {exc}", file=sys.stderr)
            failures += 1
            continue

        for w in warnings:
            print(f"warning: {src}: {w}", file=sys.stderr)
        status = "OK  "
        if verapdf:
            passed, report = validate(verapdf, dst, args.level)
            if args.verbose or not passed:
                print(report, file=sys.stderr)
            if passed:
                status = "OK  (veraPDF: PASS)"
            else:
                status = "BAD (veraPDF: FAIL)"
                failures += 1
        print(f"{status} {src} -> {dst} [PDF/A-{args.level}]")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
