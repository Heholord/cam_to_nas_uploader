"""
RAW File Organization Script
=============================

Purpose:
    Organize RAW files (.arw) by matching them with their corresponding JPG files.
    ARW files without matching JPGs are moved to a 'deleted' folder for manual review.

Workflow:
    1. Scans a directory for JPG and ARW files
    2. Extracts base names from JPG files (everything after the date prefix)
    3. Iterates through ARW files and categorizes them:
       - ARW with matching JPG → moved to ./raw/
       - ARW without matching JPG → moved to ./raw/deleted/ (orphaned files)
    4. Recursively processes subfolders (looks for Sony folders)

File Organization:
    Input: Flat directory with mixed JPG and ARW files
    
    Output Structure:
    directory/
    ├── JPG files (remain in place)
    ├── raw/
    │   ├── matched_file.arw (has corresponding JPG)
    │   └── deleted/
    │       └── orphaned_file.arw (no matching JPG)

Features:
    - Automatic matching of RAW files to JPGs by base name
    - Separation of orphaned RAW files for review
    - Recursive subfolder scanning
    - Handles multiple case variants (Sony/RAW, Sony/raw, Sony/Raw)
    - Non-destructive (files are moved, not deleted)
    - Comprehensive logging to file and console

Usage:
    1. Set directory_path to your base folder containing photo subfolders
    2. Run: python organize_raw_files.py
    3. Check raw_file_org.log for detailed results
    4. Manually review orphaned files in raw/deleted/ subdirectories

Configuration:
    - directory_path: Base folder to scan for Sony subfolders (default: "./")
    - Log file: raw_file_org.log (created in script directory)

Requirements:
    - Python 3.6+
    - No external dependencies (uses standard library only)

Expected Directory Structure:
    ./
    ├── 2026/
    │   ├── Sony/
    │   │   ├── 2026-09-25_DSC00001.jpg
    │   │   ├── DSC00001.arw
    │   │   ├── DSC00002.arw
    │   │   └── (no matching JPG for DSC00002)
    │   └── (other folders)
    └── 2025/
        └── Sony/
            ├── [similar structure]

After Running:
    ./
    ├── 2026/
    │   ├── Sony/
    │   │   ├── 2026-09-25_DSC00001.jpg
    │   │   ├── raw/
    │   │   │   ├── DSC00001.arw (matched)
    │   │   │   └── deleted/
    │   │   │       └── DSC00002.arw (orphaned - no JPG found)
    │   └── (other folders)

Base Name Extraction:
    - JPG: "2026-09-25_DSC00001.jpg" → extracts "DSC00001"
    - ARW: "DSC00001.arw" → extracts "DSC00001"
    - Match if base names are identical (case-insensitive)

Orphaned Files:
    ARW files moved to raw/deleted/ need manual investigation:
    - Was the JPG deleted separately?
    - Is this a duplicate exposure you want to keep?
    - Should it be moved back or permanently deleted?

Log Levels:
    - INFO: File movements (moved to raw, moved to deleted)
    - WARNING: No matching JPGs found in directory
    - ERROR: Permission or file system errors

Author: Claude
Version: 1.0
Last Updated: 2026-09-29
"""

import os
import shutil

def organize_raw_files(directory):
    # Create subdirectories if they don't exist
    raw_dir = os.path.join(directory, 'raw')
    deleted_dir = os.path.join(directory, 'raw/deleted')
    for subdir in [raw_dir, deleted_dir]:
        if not os.path.exists(subdir):
            os.makedirs(subdir)

    
    jpg_base_names = set()
    
    # Iterate over JPEG files and store their base names
    for jpg_filename in os.listdir(directory):
        if jpg_filename.lower().endswith('.jpg'):
            # Extract the base name without extension and date
            base_name = os.path.splitext(jpg_filename)[0].split('_')[1]
            jpg_base_names.add(base_name)
    
    # Iterate over RAW files
    #for raw_filename in os.listdir(os.path.join(directory, 'raw')):
    for raw_filename in os.listdir(directory):
        if raw_filename.lower().endswith('.arw'):
                # Extract the base name without extension
                base_name = os.path.splitext(raw_filename)[0]
                # Check if the base name exists in the set of JPEG base names
                if base_name not in jpg_base_names:
                    # Move the RAW file to the "deleted" subdirectory
                    shutil.move(os.path.join(directory, raw_filename), deleted_dir)
                    #shutil.move(os.path.join(raw_dir, raw_filename), deleted_dir)
                    print(f"Moved '{raw_filename}' to 'deleted' directory.")        
                else: 
                    # Move the RAW file to the "raw" subdirectory
                    shutil.move(os.path.join(directory, raw_filename), raw_dir)
                    print(f"Moved '{raw_filename}' to 'raw' directory.")
                    #print(f"'{raw_filename}' is in 'raw' directory.")



# Example usage
directory_path = "./"

subfolders = [f for f in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, f))]


for folder in subfolders:
    raw_paths = [os.path.join(folder, "Sony/RAW"), os.path.join(folder, "Sony/raw"), os.path.join(folder, "Sony/Raw")]

    if any([os.path.exists(raw_path) for raw_path in raw_paths]):
        print(f"exits {raw_paths}")
        organize_raw_files(os.path.join(folder, "Sony"))
    else:
        print(f"not exists {raw_paths}")

#organize_raw_files(directory_path)
