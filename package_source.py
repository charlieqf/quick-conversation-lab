import os
import zipfile
from datetime import datetime

def zip_project(output_filename, source_dir):
    # Exclusion rules (folders)
    EXCLUDE_DIRS = {
        'venv', 
        'node_modules', 
        'materials', 
        '.git', 
        '__pycache__', 
        'dist', 
        'build', 
        '.idea', 
        '.vscode',
        'artifacts',
        '.gemini'
    }
    
    # Exclusion rules (extensions)
    EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.zip', '.tar.gz'}

    # Exclusion rules (specific files)
    EXCLUDE_FILES = {'.DS_Store', 'Thumbs.db'}

    print(f"Packaging source code from '{source_dir}' into '{output_filename}'...")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        row_count = 0
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                if any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    continue
                if file == output_filename: # Don't zip the output file itself
                    continue

                file_path = os.path.join(root, file)
                # stored relative path in zip
                arcname = os.path.relpath(file_path, source_dir)
                
                try:
                    zipf.write(file_path, arcname)
                    row_count += 1
                    if row_count % 100 == 0:
                        print(f"Added {row_count} files...", end='\r')
                except Exception as e:
                    print(f"Failed to add {file_path}: {e}")

    print(f"\nSuccess! Created {output_filename}")
    print(f"Total files: {row_count}")
    file_size_mb = os.path.getsize(output_filename) / (1024 * 1024)
    print(f"Total size: {file_size_mb:.2f} MB")

if __name__ == "__main__":
    # Naming the zip file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_zip = f"source_code_{timestamp}.zip"
    
    # Current directory
    current_dir = os.getcwd()
    
    zip_project(output_zip, current_dir)
