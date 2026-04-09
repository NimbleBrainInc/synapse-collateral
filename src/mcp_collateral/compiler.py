"""Typst compilation pipeline.

Compiles Typst source to PDF or PNG. Knows nothing about templates,
starters, or workspaces -- just takes source and produces bytes.

The compiler uses --root pointing to BASE_DIR so that absolute Typst
paths like /assets/ resolve correctly. If components.typ exists in
BASE_DIR, it is copied to COMPILE_DIR so that
`#import "/components.typ": *` works from the compile directory.

Source is written to COMPILE_DIR (_compile/ inside BASE_DIR) and
cleaned up after each compilation.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .store import BASE_DIR, COMPILE_DIR, FONTS_DIR


def _find_typst() -> str:
    """Find typst binary -- check bundled location first, then PATH."""
    bundled = Path(__file__).parent.parent.parent / "bin" / "typst"
    if bundled.exists() and bundled.is_file():
        return str(bundled)
    found = shutil.which("typst")
    if found:
        return found
    msg = "typst binary not found. Install Typst or ensure it is on PATH."
    raise FileNotFoundError(msg)


def _clean_compile_dir() -> None:
    """Remove all files from the compile directory."""
    if COMPILE_DIR.exists():
        shutil.rmtree(COMPILE_DIR)
    COMPILE_DIR.mkdir(parents=True, exist_ok=True)


def compile_source(
    source: str,
    logo_data: dict[str, bytes] | None = None,
    output_format: str = "pdf",
    page: int | None = None,
) -> list[bytes]:
    """Compile Typst source to PDF or PNG pages.

    Returns a list of bytes objects (one for PDF, one per page for PNG).

    Writes source to COMPILE_DIR (~/.collateral/_compile/), copies
    components.typ if it exists, compiles with --root pointing to
    BASE_DIR, and cleans up after.
    """
    typst_bin = _find_typst()

    try:
        _clean_compile_dir()

        # Copy components.typ into compile dir if it exists
        components_path = BASE_DIR / "components.typ"
        if components_path.exists():
            shutil.copy2(components_path, COMPILE_DIR / "components.typ")

        # Write brand assets to _compile/brand/
        brand_dir = COMPILE_DIR / "brand"
        brand_dir.mkdir(parents=True, exist_ok=True)
        if logo_data:
            for filename, data in logo_data.items():
                (brand_dir / filename).write_bytes(data)

        # Write source
        (COMPILE_DIR / "document.typ").write_text(source)

        if output_format == "pdf":
            out_path = COMPILE_DIR / "output.pdf"
            _run_typst(typst_bin, "_compile/document.typ", str(out_path))
            return [out_path.read_bytes()]
        else:
            out_pattern = str(COMPILE_DIR / "output-{n}.png")
            pages_arg = str(page) if page is not None else None
            _run_typst(
                typst_bin,
                "_compile/document.typ",
                out_pattern,
                fmt="png",
                pages=pages_arg,
            )
            png_files = sorted(COMPILE_DIR.glob("output-*.png"))
            return [p.read_bytes() for p in png_files]
    finally:
        _clean_compile_dir()


def _run_typst(
    typst_bin: str,
    input_file: str,
    output: str,
    fmt: str = "pdf",
    pages: str | None = None,
) -> None:
    """Run the typst compiler.

    Args:
        typst_bin: Path to the typst binary.
        input_file: Input file path relative to BASE_DIR (e.g. "_compile/document.typ").
        output: Absolute path for the output file.
        fmt: Output format ("pdf" or "png").
        pages: Optional page range for PNG output.
    """
    cmd = [
        typst_bin,
        "compile",
        "--root",
        str(BASE_DIR),
        "--font-path",
        str(FONTS_DIR),
    ]
    if fmt == "png":
        cmd.extend(["--format", "png"])
    if pages:
        cmd.extend(["--pages", pages])
    cmd.extend([str(BASE_DIR / input_file), output])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        msg = f"Typst compilation failed: {result.stderr.strip()}"
        raise RuntimeError(msg)
