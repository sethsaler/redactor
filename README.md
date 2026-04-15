# Redactor

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A privacy-focused document redaction tool that removes sensitive information from PDFs, CSVs, Excel files, and text documents. Protects payer anonymity in bank statements while preserving financial amounts.

## Quick Start

### One-Line Installation

```bash
curl -fsSL https://raw.githubusercontent.com/sethsaler/redactor/main/install.sh | bash
```

### Or Install via pip

```bash
pip install git+https://github.com/sethsaler/redactor.git
```

### Manual Installation

```bash
git clone https://github.com/sethsaler/redactor.git
cd redactor
pip install -r requirements.txt
```

**Note:** For OCR support (scanned PDFs), install [Tesseract](https://github.com/tesseract-ocr/tesseract):
- macOS: `brew install tesseract`
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- Windows: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

### SSN Mode (Default)

Redact Social Security Numbers from documents:

```bash
python redact_ssns.py statement.pdf
python redact_ssns.py data.csv -v
```

### Bank Statement Mode

Redact numbers, emails, phones, names, and addresses while **preserving currency amounts**:

```bash
python redact_ssns.py bank_statement.pdf --mode bank
python redact_ssns.py transactions.csv --mode bank -o ./redacted/
```

### Comprehensive Mode

Redact everything (SSNs + bank patterns):

```bash
python redact_ssns.py document.pdf --mode all
python redact_ssns.py ./documents/ --mode all --recursive
```

### Working with Excel Files

```bash
python redact_ssns.py report.xlsx --mode bank
python redact_ssns.py *.csv --mode all -v
```

## Features

| Feature | Description |
|---------|-------------|
| **Multiple Formats** | PDF, CSV, TXT, XLSX support |
| **Three Redaction Modes** | `ssn`, `bank`, `all` |
| **OCR Support** | Handles scanned/image-based PDFs via Tesseract |
| **Currency Preservation** | Dollar amounts like `$1,234.56` are kept in bank mode |
| **Multi-Currency** | Supports `$`, `€`, `£`, `¥`, `₹`, `₩`, `¢` |
| **Batch Processing** | Process entire directories recursively |
| **Output Options** | Custom output directory or auto-naming |

## Redaction Patterns

### SSN Mode
- Social Security Numbers: `123-45-6789` and `123456789`
- Validates against SSA rules (invalid area/group/serial numbers)

### Bank Mode
- **Numbers:** Account numbers, routing numbers, check numbers, card numbers (4+ digits)
- **Emails:** All email addresses
- **Phone Numbers:** US, international, and local formats
- **Names:** Capitalized person names (heuristic detection)
- **Addresses:** Street addresses, ZIP codes

**Excluded from redaction:**
- Currency amounts preceded by `$`, `€`, `£`, `¥`, etc.
- Dates

### All Mode
Combines both SSN and bank pattern redaction.

## CLI Reference

```
usage: redact_ssns.py [-h] [-r] [-v] [-o OUTPUT_DIR] [-m {ssn,bank,all}] path

Redact sensitive information from documents (PDF, CSV, TXT, XLSX).

positional arguments:
  path                  File or directory to process (PDF, CSV, TXT, XLSX)

options:
  -h, --help            show this help message and exit
  -r, --recursive       Recurse into subdirectories
  -v, --verbose         Log each item found
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory
  -m {ssn,bank,all}, --mode {ssn,bank,all}
                        Redaction mode (default: ssn)

Modes:
  ssn  - Redact Social Security Numbers only (default)
  bank - Redact numbers (except currency amounts), emails, phones, names, addresses
  all  - Redact both SSNs and bank patterns
```

## Examples

### Basic SSN Redaction
```bash
# Single file
python redact_ssns.py tax_return.pdf

# Verbose output
python redact_ssns.py form.pdf -v

# Output to specific directory
python redact_ssns.py *.pdf -o ./redacted/
```

### Bank Statement Processing
```bash
# Redact account numbers but keep $ amounts
python redact_ssns.py statement.pdf --mode bank

# Process all CSVs in directory
python redact_ssns.py ./exports/ --mode bank -r
```

### Excel Files
```bash
# Redact Excel workbook
python redact_ssns.py report.xlsx --mode bank

# Batch process
python redact_ssns.py ./spreadsheets/ --mode all -r -v
```

## Output

Redacted files are saved with `_redacted` suffix:
- `statement.pdf` → `statement_redacted.pdf`
- `data.csv` → `data_redacted.csv`
- `report.xlsx` → `report_redacted.xlsx`

## Dependencies

| Package | Purpose |
|---------|---------|
| PyMuPDF | PDF text extraction and redaction |
| Pillow | Image processing |
| pytesseract | OCR for scanned PDFs |
| pdf2image | PDF to image conversion |
| openpyxl | Excel (.xlsx) support |

## How It Works

1. **File Detection:** Determines file type from extension
2. **Pattern Matching:** Uses regex to identify sensitive data
3. **Currency Check:** For bank mode, checks if numbers are preceded by currency symbols
4. **Redaction:** 
   - PDFs: Black rectangle annotations
   - Text/CSV: `[REDACTED]` replacement
   - Excel: Cell value replacement
5. **Output:** Saves redacted copy preserving original

## Privacy & Security

- Original files are never modified
- No data is transmitted or stored externally
- All processing is local
- No cloud dependencies

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Issues and pull requests welcome! Please ensure your code follows the existing patterns and includes appropriate tests.

## Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for scanned document support
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) for PDF handling
- [openpyxl](https://openpyxl.readthedocs.io/) for Excel support
