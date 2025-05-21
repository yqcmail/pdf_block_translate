import fitz

try:
    doc = fitz.open()  # Try to open a non-existent PDF to check if fitz is working
    print("PyMuPDF (fitz) imported and working successfully!")
except Exception as e:
    print(f"Error using PyMuPDF (fitz): {e}")
