import argparse
from pathlib import Path

from docx2pdf import convert as docx_to_pdf
from pdf2docx import Converter as PDF2DOCX
import subprocess
import shutil

try:
    from google.colab import files as colab_files  # type: ignore
except ImportError:  # pragma: no cover
    colab_files = None

def install_libreoffice():
    print("Installing LibreOffice... This may take a moment.")
    subprocess.run(['apt-get', 'update'], check=True)
    subprocess.run(['apt-get', 'install', '-y', 'libreoffice'], check=True)
    print("LibreOffice installed.")

# Ensure LibreOffice is installed if we are in a Linux environment and docx2pdf relies on it
import platform
if platform.system() == "Linux":
    # Check if soffice is available, if not, install LibreOffice
    if not shutil.which("soffice"):
        install_libreoffice()


def convert_docx_to_pdf(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        docx_to_pdf(str(src), str(dst))
    except Exception:
        # Fallback to soffice if docx2pdf fails (e.g., on Linux without MS Word)
        soffice = shutil.which("soffice")
        if not soffice:
            raise RuntimeError("docx2pdf requires Word and LibreOffice (soffice) was not found for fallback.")
        subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(dst.parent),
                str(src),
            ],
            check=True,
        )


def convert_pdf_to_docx(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Try LibreOffice first (better quality), fallback to pdf2docx
    soffice = shutil.which("soffice")
    if soffice:
        try:
            subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--convert-to",
                    "docx",
                    "--outdir",
                    str(dst.parent),
                    str(src),
                ],
                check=True,
                capture_output=True,
            )
            # LibreOffice outputs to same name with .docx extension
            libreoffice_output = dst.parent / src.with_suffix(".docx").name
            if libreoffice_output.exists() and libreoffice_output != dst:
                libreoffice_output.rename(dst)
            return
        except subprocess.CalledProcessError:
            pass  # Fall through to pdf2docx

    # Fallback to pdf2docx
    pdf = PDF2DOCX(str(src))
    pdf.convert(str(dst))
    pdf.close()


def _prompt_for_file() -> Path:
    if not colab_files:
        raise ValueError("No input provided. Pass a file path when running outside Colab.")

    while True:
        print("Please upload a DOCX or PDF resume...")
        uploaded = colab_files.upload()
        if not uploaded:
            print("⚠️  No file uploaded. Try again.")
            continue

        name = next(iter(uploaded))
        path = Path(name).resolve()
        if path.suffix.lower() not in (".docx", ".pdf"):
            print(f"⚠️  '{name}' is not a DOCX/PDF. Please upload a supported file.")
            continue

        print(f"✓ Uploaded: {name}")
        return path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert resumes between DOCX and PDF.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="Source resume file (.docx or .pdf). If omitted inside Colab, you'll be prompted to upload.",
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Optional output path (default: output_resume.*)"
    )
    parser.add_argument(
        "--to",
        choices=("pdf", "docx"),
        help="Force output format instead of inferring from the input extension.",
    )
    args, extras = parser.parse_known_args(argv)
    if extras:
        print(f"Ignoring extra args: {' '.join(extras)}")

    if args.input:
        src = args.input.resolve()
    else:
        src = _prompt_for_file()

    # Show the path we ended up with to make debugging easier.
    print(f"Using source file: {src}")

    if not src.exists():
        raise FileNotFoundError(src)

    src_ext = src.suffix.lower()
    if src_ext not in (".docx", ".pdf"):
        raise ValueError("Only .docx and .pdf files are supported.")

    target_ext = f".{args.to.lower()}" if args.to else (".pdf" if src_ext == ".docx" else ".docx")

    if target_ext == src_ext:
        raise ValueError("Input and output types are the same; choose the opposite format.")

    if args.output:
        out = args.output
        if out.suffix.lower() != target_ext:
            out = out.with_suffix(target_ext)
    else:
        out = Path("output_resume").with_suffix(target_ext)

    if target_ext == ".pdf":
        convert_docx_to_pdf(src, out)
    else:
        convert_pdf_to_docx(src, out)

    print(f"✅ Saved to {out}")


if __name__ == "__main__":
    # In Colab/IPython, we define the functions but do not automatically call main()
    # to prevent conflicts with kernel-injected arguments.
    print("This cell defines functions for DOCX/PDF conversion.")
    print("To use it, please call the 'main' function directly with your arguments, for example:")
    print("main(['your_document.docx', '-o', 'output.pdf'])")
    print("Or, to be prompted to upload a file, call: main([])")
