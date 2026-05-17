"""PDF text extraction with SHA256-based caching."""

import hashlib
import subprocess
from pathlib import Path


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_pdf(pdf_path: Path, cache_dir: Path) -> str:
    """Extract text from a PDF using pdftotext -layout.
    Returns cached result if PDF hasn't changed."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    fhash = _hash_file(pdf_path)
    cache_file = cache_dir / f"{fhash}.txt"

    if cache_file.exists():
        return cache_file.read_text()

    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, check=True,
    )
    text = result.stdout
    cache_file.write_text(text)
    return text


def extract_all(data_dir: Path, cache_dir: Path) -> list[tuple[Path, str]]:
    """Extract text from all PDFs under data_dir.
    Returns list of (pdf_path, extracted_text) tuples."""
    results = []
    for pdf in sorted(data_dir.rglob("*.pdf")):
        text = extract_pdf(pdf, cache_dir)
        results.append((pdf, text))
    return results
