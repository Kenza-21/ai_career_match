"""
LaTeX Utilities
Helper functions for LaTeX template processing and PDF compilation
"""
import os
import subprocess
import tempfile
import base64
from typing import Dict, Optional
from fastapi import HTTPException


def escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters while preserving accents and special characters.
    Uses inputenc utf8, so most Unicode characters (including accents) are preserved.
    """
    if not text:
        return ""
    
    # Critical LaTeX special characters that must be escaped
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '|': r'\|',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    
    # Apply replacements
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Note: With \usepackage[utf8]{inputenc} and \usepackage[T1]{fontenc},
    # most Unicode characters including accents (é, è, à, ç, etc.) will be
    # handled automatically. No need to convert them manually.
    
    return text


def load_latex_template() -> str:
    """Load the base LaTeX template from data/ats_resume.tex"""
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "data", 
        "ats_resume.tex"
    )
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500, 
            detail=f"Template not found at {template_path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error loading template: {str(e)}"
        )


def find_pdflatex() -> Optional[str]:
    """Find pdflatex executable, checking common MiKTeX locations on Windows"""
    import shutil
    
    # First, try to find pdflatex in PATH
    pdflatex_path = shutil.which("pdflatex")
    if pdflatex_path:
        return pdflatex_path
    
    # Common MiKTeX installation paths on Windows
    miktex_paths = [
        r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
        r"C:\Program Files (x86)\MiKTeX\miktex\bin\x64\pdflatex.exe",
        r"C:\Program Files\MiKTeX\miktex\bin\pdflatex.exe",
        r"C:\Program Files (x86)\MiKTeX\miktex\bin\pdflatex.exe",
        r"C:\Users\{}\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe".format(os.getenv("USERNAME", "")),
    ]
    
    for path in miktex_paths:
        if os.path.exists(path):
            return path
    
    # Try adding MiKTeX to PATH and searching again
    common_miktex_bins = [
        r"C:\Program Files\MiKTeX\miktex\bin\x64",
        r"C:\Program Files (x86)\MiKTeX\miktex\bin\x64",
        r"C:\Program Files\MiKTeX\miktex\bin",
        r"C:\Program Files (x86)\MiKTeX\miktex\bin",
    ]
    
    for bin_path in common_miktex_bins:
        if os.path.exists(bin_path):
            # Temporarily add to PATH
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = bin_path + os.pathsep + old_path
            pdflatex_path = shutil.which("pdflatex")
            if pdflatex_path:
                return pdflatex_path
            # Restore PATH
            os.environ["PATH"] = old_path
    
    return None


def compile_latex_to_pdf(latex_content: str, output_dir: str) -> Optional[str]:
    """Compile LaTeX to PDF using pdflatex (automatically detects MiKTeX on Windows)"""
    try:
        # Write LaTeX file
        tex_file = os.path.join(output_dir, "generated_resume.tex")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_content)
        
        # Find pdflatex executable
        pdflatex_path = find_pdflatex()
        if not pdflatex_path:
            print("pdflatex not found. Please install MiKTeX or ensure it's in your PATH.")
            return None
        
        print(f"Using pdflatex at: {pdflatex_path}")
        
        # Compile with pdflatex (run twice for references and cross-references)
        pdf_file = os.path.join(output_dir, "generated_resume.pdf")
        
        for run_num in range(2):
            result = subprocess.run(
                [
                    pdflatex_path,
                    "-interaction=nonstopmode",
                    "-output-directory", output_dir,
                    "-halt-on-error",
                    tex_file
                ],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=output_dir
            )
            
            if result.returncode != 0:
                error_output = result.stderr if result.stderr else result.stdout
                print(f"pdflatex error (run {run_num + 1}): {error_output[:500]}")
                # Still try second run, sometimes first run errors are warnings
                if run_num == 1:  # If second run also fails
                    return None
        
        if os.path.exists(pdf_file):
            return pdf_file
        else:
            print(f"PDF file not found at expected location: {pdf_file}")
            return None
            
    except subprocess.TimeoutExpired:
        print("pdflatex timeout (exceeded 60 seconds)")
        return None
    except FileNotFoundError:
        print("pdflatex not found. Please install MiKTeX.")
        return None
    except Exception as e:
        print(f"Compilation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

