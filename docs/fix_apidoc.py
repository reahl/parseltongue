#!/usr/bin/env python3
"""
Script to fix sphinx-apidoc generated files for reahl.ptongue namespace package.
This script:
1. Renames files from ptongue.* to reahl.ptongue.*
2. Updates automodule references inside files
3. Updates toctree references to match renamed files
4. Updates modules.rst to reference correct files
"""

import os
import re
import shutil
from pathlib import Path


def fix_apidoc_files(api_dir="api"):
    """Fix sphinx-apidoc generated files for namespace package."""
    api_path = Path(api_dir)
    
    if not api_path.exists():
        print(f"API directory {api_dir} does not exist")
        return
    
    # Step 1: Rename files
    file_mapping = {}
    for file_path in api_path.glob("ptongue*.rst"):
        old_name = file_path.name
        new_name = old_name.replace("ptongue", "reahl.ptongue")
        new_path = api_path / new_name
        
        print(f"Renaming {old_name} -> {new_name}")
        shutil.move(str(file_path), str(new_path))
        file_mapping[old_name] = new_name
    
    # Step 2: Update content in all .rst files
    for file_path in api_path.glob("*.rst"):
        print(f"Processing {file_path.name}")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix automodule references (avoid double replacement)
        content = re.sub(r'.. automodule:: (?!reahl\.)ptongue(?=\s|$)', 
                        '.. automodule:: reahl.ptongue', content)
        content = re.sub(r'.. automodule:: (?!reahl\.)ptongue\.', 
                        '.. automodule:: reahl.ptongue.', content)
        
        # Fix package title and its underline
        def fix_title_underline(match):
            title = match.group(1)
            underline_char = match.group(2)[0]  # Get the first character of the underline
            new_title = title.replace('ptongue', 'reahl.ptongue')
            new_underline = underline_char * len(new_title)
            return f"{new_title}\n{new_underline}"
        
        # Match title followed by underline (=, -, ~, etc.)
        content = re.sub(r'^(.*ptongue.*)\n([=\-~^"]+)$', 
                        fix_title_underline, content, flags=re.MULTILINE)
        
        # Fix toctree references to match renamed files
        for old_file, new_file in file_mapping.items():
            old_ref = old_file.replace('.rst', '')
            new_ref = new_file.replace('.rst', '')
            # Handle both indented and non-indented toctree entries
            content = re.sub(rf'^(\s*){re.escape(old_ref)}$', 
                           rf'\1{new_ref}', content, flags=re.MULTILINE)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  Updated content in {file_path.name}")
        else:
            print(f"  No changes needed in {file_path.name}")
    
    # Step 3: Remove any remaining old ptongue*.rst files (in case sphinx-apidoc ran again)
    for file_path in api_path.glob("ptongue*.rst"):
        if file_path.name not in file_mapping.values():  # Don't remove renamed files
            print(f"Removing old file: {file_path.name}")
            file_path.unlink()
    
    print("Fix complete!")


if __name__ == "__main__":
    fix_apidoc_files()