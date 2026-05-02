import os
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import List


def check_libreoffice() -> str | None:
    """Find the LibreOffice executable, checking PATH and default Windows locations."""
    # Check in PATH first
    for cmd in ["soffice", "libreoffice", "libreoffice7.6", "libreoffice7.5"]:
        path = shutil.which(cmd)
        if path:
            return path
            
    # Check default Windows installation paths
    if os.name == 'nt':
        windows_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]
        for p in windows_paths:
            if os.path.exists(p):
                return p
                
    return None


def convert_pptx_to_pdf(pptx_path: str, out_dir: str) -> str | None:
    lo_path = check_libreoffice()
    if not lo_path:
        return None
        
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

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
    except subprocess.CalledProcessError:
        return None

    pdf_filename = Path(pptx_path).with_suffix(".pdf").name
    pdf_path = out_path / pdf_filename

    if not pdf_path.exists():
        return None

    return str(pdf_path)


def convert_pdf_to_images(pdf_path: str, out_dir: str, prefix: str = "slide", dpi: int = 150) -> List[str]:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return []
        
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    image_paths = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_path = out_path / f"{prefix}_{page_num:03d}.png"
        pix.save(str(img_path))
        image_paths.append(str(img_path))

    doc.close()
    return image_paths


def convert_pptx_to_images_msoffice(pptx_path: str, out_dir: str, prefix: str = "slide") -> List[str]:
    """
    Export PPTX to images using Microsoft PowerPoint via COM automation (Windows only).
    """
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        return []

    try:
        pythoncom.CoInitialize()
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        
        abs_pptx = os.path.abspath(pptx_path)
        abs_out = os.path.abspath(out_dir)
        os.makedirs(abs_out, exist_ok=True)
        
        # Open in background
        presentation = powerpoint.Presentations.Open(abs_pptx, ReadOnly=True, WithWindow=False)
        
        image_paths = []
        for i, slide in enumerate(presentation.Slides):
            img_name = f"{prefix}_{i:03d}.png"
            img_path = os.path.join(abs_out, img_name)
            # Export to PNG (Width=1920 for high quality)
            slide.Export(img_path, "PNG", 1920)
            image_paths.append(img_path)
            
        presentation.Close()
        powerpoint.Quit()
        return image_paths
    except Exception as e:
        warnings.warn(f"MS Office COM automation failed: {e}")
        return []
    finally:
        try:
            pythoncom.CoUninitialize()
        except:
            pass

def render_pptx_slides(pptx_path: str, cache_dir: str, prefix: str = "slide") -> List[str]:
    """
    Render PPTX to images.
    On Windows, tries Microsoft Office (PowerPoint) first.
    Falls back to LibreOffice + PyMuPDF on all platforms.
    Gracefully returns an empty list if tools are missing.
    """
    if os.name == 'nt':
        ms_images = convert_pptx_to_images_msoffice(pptx_path, cache_dir, prefix)
        if ms_images:
            return ms_images
            
    # Fallback to LibreOffice
    pdf_path = convert_pptx_to_pdf(pptx_path, cache_dir)
    if not pdf_path:
        warnings.warn(f"Skipping visual extraction for {pptx_path} (LibreOffice not found and MS Office not available).")
        return []
        
    return convert_pdf_to_images(pdf_path, cache_dir, prefix=prefix)

