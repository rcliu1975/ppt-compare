import os
import shutil
import subprocess
from pathlib import Path
from typing import List

import fitz  # PyMuPDF


def check_libreoffice() -> str:
    """Find the LibreOffice executable."""
    for cmd in ["soffice", "libreoffice", "libreoffice7.6", "libreoffice7.5"]:
        path = shutil.which(cmd)
        if path:
            return path
    raise RuntimeError("LibreOffice is not installed or not in PATH. It is required to convert PPTX to PDF.")


def convert_pptx_to_pdf(pptx_path: str, out_dir: str) -> str:
    """
    Convert a PPTX file to PDF using LibreOffice in headless mode.
    Returns the path to the generated PDF.
    """
    lo_path = check_libreoffice()
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Run LibreOffice headless conversion
    cmd = [
        lo_path,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_path),
        pptx_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"LibreOffice conversion failed: {e.stderr.decode('utf-8', errors='ignore')}")

    pdf_filename = Path(pptx_path).with_suffix(".pdf").name
    pdf_path = out_path / pdf_filename

    if not pdf_path.exists():
        raise FileNotFoundError(f"Expected PDF output not found: {pdf_path}")

    return str(pdf_path)


def convert_pdf_to_images(pdf_path: str, out_dir: str, prefix: str = "slide", dpi: int = 150) -> List[str]:
    """
    Convert a PDF file to PNG images using PyMuPDF.
    Returns a list of image paths.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    image_paths = []

    # PyMuPDF Document
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Calculate zoom factor for DPI (PyMuPDF default is 72)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_path = out_path / f"{prefix}_{page_num:03d}.png"
        pix.save(str(img_path))

        image_paths.append(str(img_path))

    doc.close()
    return image_paths


def render_pptx_slides(pptx_path: str, cache_dir: str, prefix: str = "slide") -> List[str]:
    """
    High-level function to render PPTX to images.
    Caches the PDF and images in cache_dir.
    """
    pdf_path = convert_pptx_to_pdf(pptx_path, cache_dir)
    image_paths = convert_pdf_to_images(pdf_path, cache_dir, prefix=prefix)
    return image_paths
