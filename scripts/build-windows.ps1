$ErrorActionPreference = "Stop"

# Execute this script in Windows with Python 3.11+ from the repository root.
python -m pip install -e ".[packaging]"
python -m PyInstaller --noconfirm --clean --windowed --name HairSalonManagement --paths src --add-data "images;images" --collect-all PySide6 src/hair_salon_management/__main__.py

Write-Host "Executable created in dist\HairSalonManagement\HairSalonManagement.exe"
