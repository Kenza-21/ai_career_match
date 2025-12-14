import os
import shutil
import subprocess

# 1️⃣ Add MiKTeX bin folder to PATH (adjust to your installation)
miktex_path = r"C:\Program Files\MiKTeX\miktex\bin\x64"
os.environ["PATH"] += os.pathsep + miktex_path

# 2️⃣ Verify pdflatex is now found
pdflatex_path = shutil.which("pdflatex")
if pdflatex_path is None:
    print("❌ pdflatex not found! Check your MiKTeX path.")
else:
    print(f"✅ pdflatex detected at: {pdflatex_path}")

# 3️⃣ Optional: test compilation (replace 'cv_ats.tex' with your LaTeX file)
tex_file = "cv_ats.tex"
if pdflatex_path:
    try:
        subprocess.run([pdflatex_path, tex_file], check=True)
        print("✅ PDF generated successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ PDF compilation failed: {e}")
