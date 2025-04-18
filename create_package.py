#!/usr/bin/env python3
import zipfile
import os

def create_ankiaddon_package():
    """Create an .ankiaddon package file from the addon files."""
    files_to_include = [
        "__init__.py",
        "README.md",
        "manifest.json",
        "addon.json",
        "install_deps.py",
        "requirements.txt"
    ]
    
    # Create build directory if it doesn't exist
    os.makedirs("build", exist_ok=True)
    
    # Create the zip file
    output_file = "build/brainscape_to_anki.ankiaddon"
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file)
            else:
                print(f"Warning: File {file} not found, skipping")
    
    print(f"Package created: {output_file}")
    print(f"To install in Anki: Tools → Add-ons → Install from file... → select {output_file}")

if __name__ == "__main__":
    create_ankiaddon_package() 