"""
Build script for generating comprehensive Sphinx documentation.

This script automates the documentation building process and provides
options for different output formats.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, check=True, capture_output=True, text=True
        )
        print(f"Success {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Fail {cmd}")
        print(f"Error: {e.stderr}")
        return False


def install_dependencies():
    """Install required dependencies."""
    print("Installing documentation dependencies...")
    return run_command("pip install -r docs/requirements.txt")


def clean_build():
    """Clean previous build artifacts."""
    print("Cleaning previous build...")
    docs_dir = Path("docs")
    build_dir = docs_dir / "_build"

    if build_dir.exists():
        import shutil

        shutil.rmtree(build_dir)
        print("Cleaned build directory")

    return True


def build_html():
    """Build HTML documentation."""
    print("Building HTML documentation...")
    return run_command("python -m sphinx -M html . _build", cwd="docs")


def build_pdf():
    """Build PDF documentation (requires LaTeX)."""
    print("Building PDF documentation...")
    return run_command("python -m sphinx -M latexpdf . _build", cwd="docs")


def build_epub():
    """Build EPUB documentation."""
    print("Building EPUB documentation...")
    return run_command("python -m sphinx -M epub . _build", cwd="docs")


def open_docs():
    """Open the generated documentation."""
    html_file = Path("docs/_build/html/index.html")
    if html_file.exists():
        import webbrowser

        webbrowser.open(f"file://{html_file.absolute()}")
        print(f"✓ Opened documentation in browser")
    else:
        print("✗ HTML documentation not found")


def main():
    parser = argparse.ArgumentParser(description="Build IR Remote Controller docs")
    parser.add_argument(
        "--format",
        choices=["html", "pdf", "epub", "all"],
        default="html",
        help="Output format",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean build directory first"
    )
    parser.add_argument(
        "--install", action="store_true", help="Install dependencies first"
    )
    parser.add_argument(
        "--open", action="store_true", help="Open documentation after building"
    )

    args = parser.parse_args()

    success = True

    if args.install:
        success &= install_dependencies()

    if args.clean:
        success &= clean_build()

    if not success:
        print("Failed during setup phase")
        sys.exit(1)

    if args.format == "html" or args.format == "all":
        success &= build_html()

    if args.format == "pdf" or args.format == "all":
        success &= build_pdf()

    if args.format == "epub" or args.format == "all":
        success &= build_epub()

    if success:
        print("\n Documentation built successfully!")

        if args.open and (args.format == "html" or args.format == "all"):
            open_docs()

        print(f"\nDocumentation available at:")
        print(f"  HTML: docs/_build/html/index.html")
        if args.format == "pdf" or args.format == "all":
            print(f"  PDF:  docs/_build/latex/irremotecontroller.pdf")
        if args.format == "epub" or args.format == "all":
            print(f"  EPUB: docs/_build/epub/IRRemoteController.epub")
    else:
        print("\n Documentation build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
