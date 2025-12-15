# ATS CV Optimization Pipeline - Complete Documentation

## Overview

This system provides a fully automated pipeline for converting CVs (PDF, DOCX) into ATS-compliant LaTeX format and compiling them to professional PDFs using MiKTeX.

## Features

✅ **Automatic Parsing**: Supports PDF, DOCX, and TXT formats  
✅ **Full Content Preservation**: No truncation - all information is preserved  
✅ **One-Page Layout**: Optimized LaTeX template fits content on a single page  
✅ **Special Character Handling**: Automatic handling of accents and special characters  
✅ **MiKTeX Integration**: Automatic detection and compilation  
✅ **Zero User Intervention**: Fully automated from upload to PDF

## Architecture

### Pipeline Flow

```
CV Upload (PDF/DOCX) 
    ↓
ResumeParser.app API (Parsing)
    ↓
map_parsed_to_template_full() (Data Mapping)
    ↓
render_template_full() (LaTeX Generation)
    ↓
compile_latex_to_pdf() (PDF Compilation via MiKTeX)
    ↓
Final PDF Output
```

## Components

### 1. CV Parsing (`services/resume_parser_api.py`)

Uses ResumeParser.app API to extract structured data from CV files:
- Contact information
- Employment history
- Education
- Skills
- Languages
- Certifications

### 2. Data Mapping (`utils/ats_template_processor.py`)

**`map_parsed_to_template_full()`**: Preserves ALL content without truncation
- All employment history entries
- All bullet points per job
- All education entries
- All skills
- All languages
- All certifications
- Full summary (no character limit)

### 3. LaTeX Template (`data/ats_resume.tex`)

Professional ATS-compliant template with:
- Compact margins (0.4in)
- Optimized spacing
- Professional typography
- UTF-8 encoding for special characters
- Hyperlinks for email
- Clean section formatting

### 4. PDF Compilation (`utils/latex_utils.py`)

**`compile_latex_to_pdf()`**: Automatically:
- Detects MiKTeX installation on Windows
- Searches common installation paths
- Compiles LaTeX to PDF
- Handles errors gracefully

**`find_pdflatex()`**: Finds pdflatex executable in:
- System PATH
- Common MiKTeX locations:
  - `C:\Program Files\MiKTeX\miktex\bin\x64\`
  - `C:\Program Files (x86)\MiKTeX\miktex\bin\x64\`
  - User AppData locations

## Usage

### Via API Endpoint

```python
POST /api/ats_cv
Content-Type: multipart/form-data

Parameters:
- cv_file: UploadFile (PDF, DOCX, TXT)
- target_role: str (optional)
- session_id: str (optional)

Response:
{
    "success": true,
    "ats_latex": "...",  # Generated LaTeX code
    "pdf_base64": "...",  # Base64 encoded PDF
    "pdf_available": true,
    "metadata": {...}
}
```

### Programmatic Usage

```python
from services.resume_parser_api import resume_parser_api
from utils.ats_template_processor import map_parsed_to_template_full, render_template_full
from utils.latex_utils import load_latex_template, compile_latex_to_pdf
import tempfile

# 1. Parse CV
with open("cv.pdf", "rb") as f:
    upload_file = UploadFile(filename="cv.pdf", file=f)
    api_response = resume_parser_api.parse_cv_with_resumeparser(upload_file)
    parsed_data = api_response["data"]["parsed"]

# 2. Generate LaTeX
template = load_latex_template()
template_data = map_parsed_to_template_full(parsed_data)
latex_content = render_template_full(template, template_data)

# 3. Compile to PDF
with tempfile.TemporaryDirectory() as temp_dir:
    pdf_path = compile_latex_to_pdf(latex_content, temp_dir)
    if pdf_path:
        print(f"PDF generated at: {pdf_path}")
```

## LaTeX Template Structure

The template uses a compact, professional layout:

```latex
\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}  % Handles accents automatically
\usepackage[T1]{fontenc}
\usepackage[margin=0.4in]{geometry}  % Compact margins
```

**Sections:**
1. Header (Name, Contact Info)
2. Profile/Summary
3. Education
4. Professional Experience
5. Technical Skills
6. Languages
7. Certifications

## Special Character Handling

The system automatically handles:
- **Accents**: é, è, à, ç, ñ, ü, etc. (via UTF-8 inputenc)
- **Special Characters**: &, %, $, #, _, {, }, etc. (escaped)
- **Unicode**: All Unicode characters are preserved

## MiKTeX Installation & Setup

### Windows Installation

1. Download MiKTeX from: https://miktex.org/download
2. Install to default location: `C:\Program Files\MiKTeX\`
3. The system will automatically detect it

### Manual PATH Setup (if needed)

If MiKTeX is installed in a non-standard location:

```powershell
$env:PATH += ";C:\Your\MiKTeX\Path\miktex\bin\x64"
```

### Verification

```python
from utils.latex_utils import find_pdflatex
pdflatex_path = find_pdflatex()
if pdflatex_path:
    print(f"Found pdflatex at: {pdflatex_path}")
else:
    print("pdflatex not found. Please install MiKTeX.")
```

## Troubleshooting

### PDF Not Generated

1. **Check MiKTeX Installation**:
   ```python
   from utils.latex_utils import find_pdflatex
   print(find_pdflatex())
   ```

2. **Check LaTeX Compilation Errors**:
   - Review console output for pdflatex errors
   - Check temporary directory for `.log` files

3. **Verify Template Syntax**:
   - Ensure all placeholders are properly escaped
   - Check for unmatched braces

### Content Truncation

The system uses `map_parsed_to_template_full()` and `render_template_full()` which preserve ALL content. If you see truncation:

1. Verify you're using the full-content functions (not `_optimized`)
2. Check that `preserve_all_content=True` in `generate_ats_latex()`

### Special Characters Not Displaying

1. Ensure `\usepackage[utf8]{inputenc}` is in template
2. Verify file encoding is UTF-8 when writing LaTeX
3. Check that `escape_latex()` is being used correctly

## Best Practices

1. **Content Length**: While all content is preserved, very long CVs may overflow one page. The template is optimized but may need manual adjustment for extremely long content.

2. **File Formats**: PDF and DOCX are recommended. TXT works but may lose formatting.

3. **Error Handling**: Always check `pdf_available` in API response before using PDF.

4. **Testing**: Test with various CV formats and lengths to ensure proper handling.

## File Locations

- **LaTeX Template**: `backend/data/ats_resume.tex`
- **Template Processor**: `backend/utils/ats_template_processor.py`
- **LaTeX Utils**: `backend/utils/latex_utils.py`
- **API Routes**: `backend/routes/ats_routes.py`
- **Parser Service**: `backend/services/resume_parser_api.py`

## API Reference

### `map_parsed_to_template_full(parsed_data: Dict) -> Dict`

Maps ResumeParser.app response to template variables with full content preservation.

**Returns:**
- `name`: Full name
- `title`: Job title
- `email`, `phone`, `location`: Contact info
- `summary`: Full summary (no truncation)
- `experience`: All jobs with all bullet points
- `education`: All education entries
- `skills`: All skills (deduplicated)
- `languages`: All languages
- `certifications`: All certifications

### `render_template_full(template: str, data: Dict) -> str`

Renders LaTeX template with data, preserving all content.

### `compile_latex_to_pdf(latex_content: str, output_dir: str) -> Optional[str]`

Compiles LaTeX to PDF using automatically detected MiKTeX.

**Returns:** Path to generated PDF or `None` if compilation fails.

## Example Output

The generated PDF will have:
- Professional one-page layout
- All CV information preserved
- Proper formatting and spacing
- Clickable email links
- ATS-friendly structure

## Support

For issues or questions:
1. Check console output for error messages
2. Verify MiKTeX installation
3. Review LaTeX compilation logs
4. Ensure ResumeParser.app API is accessible

