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

Author: Manuel Esberger, Docs by Claude
Version: 1.0
Last Updated: 2026-09-29
"""

import os
import shutil
import logging

# Setup logging
def setup_logger(log_file="raw_file_org.log"):
    """Configure logging to file and console"""
    logger = logging.getLogger("RawFileOrg")
    logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()


def organize_raw_files(directory):
    """
    Organize RAW files by matching them with JPGs.
    
    Args:
        directory: Path to directory containing JPG and ARW files
    """
    logger.info(f"Organizing RAW files in: {directory}")
    
    # Create subdirectories if they don't exist
    raw_dir = os.path.join(directory, 'raw')
    deleted_dir = os.path.join(directory, 'raw/deleted')
    
    for subdir in [raw_dir, deleted_dir]:
        if not os.path.exists(subdir):
            os.makedirs(subdir)
            logger.debug(f"Created directory: {subdir}")

    jpg_base_names = set()
    
    # Iterate over JPEG files and store their base names
    for jpg_filename in os.listdir(directory):
        if jpg_filename.lower().endswith('.jpg'):
            try:
                # Extract the base name without extension and date
                # e.g., "2026-09-25_DSC00001.jpg" → "DSC00001"
                base_name = os.path.splitext(jpg_filename)[0].split('_')[1]
                jpg_base_names.add(base_name)
                logger.debug(f"Found JPG: {jpg_filename} (base: {base_name})")
            except IndexError:
                logger.warning(f"Could not extract base name from JPG: {jpg_filename}")
    
    if not jpg_base_names:
        logger.warning(f"No JPG files found in {directory}")
    else:
        logger.info(f"Found {len(jpg_base_names)} JPG files")
    
    # Iterate over RAW files
    for raw_filename in os.listdir(directory):
        if raw_filename.lower().endswith('.arw'):
            try:
                # Extract the base name without extension
                base_name = os.path.splitext(raw_filename)[0]
                src_path = os.path.join(directory, raw_filename)
                
                # Check if the base name exists in the set of JPEG base names
                if base_name not in jpg_base_names:
                    # Move the RAW file to the "deleted" subdirectory
                    dst_path = os.path.join(deleted_dir, raw_filename)
                    shutil.move(src_path, dst_path)
                    logger.info(f"Moved '{raw_filename}' to 'deleted' directory (no matching JPG)")
                else:
                    # Move the RAW file to the "raw" subdirectory
                    dst_path = os.path.join(raw_dir, raw_filename)
                    shutil.move(src_path, dst_path)
                    logger.info(f"Moved '{raw_filename}' to 'raw' directory (matched with JPG)")
            except Exception as e:
                logger.error(f"Error processing {raw_filename}: {e}")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting RAW file organization")
    logger.info("=" * 60)
    
    # Example usage
    directory_path = "./"
    
    subfolders = [f for f in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, f))]
    logger.debug(f"Found {len(subfolders)} subfolders in {directory_path}")
    
    for folder in subfolders:
        # Check for Sony folder with various case combinations
        raw_paths = [
            os.path.join(folder, "Sony/RAW"),
            os.path.join(folder, "Sony/raw"),
            os.path.join(folder, "Sony/Raw")
        ]
        
        if any([os.path.exists(raw_path) for raw_path in raw_paths]):
            logger.info(f"Found Sony folder: {folder}")
            organize_raw_files(os.path.join(folder, "Sony"))
        else:
            logger.debug(f"No Sony folder found in: {folder}")
    
    logger.info("=" * 60)
    logger.info("RAW file organization complete")
    logger.info("=" * 60)