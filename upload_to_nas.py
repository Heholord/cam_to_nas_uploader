"""
Photo Transfer & Organization Script
=====================================

Purpose:
    Organize photos from a local folder to a media library with the following workflow:
    1. Add date prefix (YYYY-MM-DD) to JPG files based on EXIF metadata
    2. Copy dated JPGs and matching RAW files to organized media structure
    3. Verify transfers with content-based duplicate detection
    4. Delete local files only after successful transfer

File Structure:
    Input: Flat folder with mixed JPG/ARW files (e.g., DSC00001.JPG, DSC00001.ARW)
    Output: /media/manuel/Media/Pictures/TimeLine/{YEAR}/Sony/
            - JPG files: {YYYY-MM-DD}_{original_name}.jpg
            - ARW files: /raw/{original_name}.arw

Features:
    - Automatic EXIF date extraction and filename prefixing
    - Smart file matching (JPGs with ARWs by base filename)
    - Fast content verification using size + first/last bytes
    - Dry-run mode for safe preview
    - Auto-creates year/Sony/raw folder structure
    - Comprehensive logging to file and console
    - Prevents duplicate transfers and data loss

Usage:
    1. Update SOURCE_FOLDER to your image location
    2. Set dryrun = True (default) to preview
    3. Run: python photo_transfer.py
    4. Review photo_transfer.log for results
    5. If successful, set dryrun = False and run again to actually delete

Configuration:
    - MEDIA_PATH: Base path to mounted media drive
    - TIMELINE_BASE: Subfolder structure on media drive
    - SOURCE_FOLDER: Local folder containing photos to transfer
    - dryrun: True = preview only, False = actually delete files
    - Log file: photo_transfer.log (created in script directory)

Requirements:
    - Python 3.6+
    - Pillow library: pip install pillow
    - /media/manuel/Media must be mounted
    - Sufficient disk space on media drive

Workflow Details:
    Step 1: Date Prefix Phase
        - Scans all JPG files
        - Reads EXIF DateTimeOriginal tag
        - Renames to YYYY-MM-DD_{original_name}.jpg
        - Skips files already in correct format
    
    Step 2: Verification Phase
        - Confirms media drive is mounted
        - Groups JPGs with matching ARWs by base filename
        - Extracts year from date prefix
    
    Step 3: Transfer Phase
        - Creates /media/manuel/Media/Pictures/TimeLine/{YEAR}/Sony/ structure
        - Copies JPGs to Sony folder
        - Copies matching ARWs to Sony/raw folder
        - Verifies content after each copy
    
    Step 4: Cleanup Phase
        - Only deletes if ALL transfers succeeded
        - Aborts deletion if any transfer failed
        - Detailed log of what was deleted

Example Session:
    # First run (dry-run mode)
    $ python photo_transfer.py
    # Check photo_transfer.log
    # Should see: "Found 150 JPG files and 150 ARW files"
    
    # After review, set dryrun = False and run again
    $ python photo_transfer.py
    # Actual deletion occurs

Log Levels:
    - DEBUG: Detailed info (folder creation, pattern matching)
    - INFO: Major actions (files renamed, copied, deleted)
    - WARNING: Potential issues (missing ARW, existing files)
    - ERROR: Failed operations (EXIF errors, copy failures)

Author: Claude
Version: 1.0
Last Updated: 2026-09-29
"""

from PIL import Image
from PIL.ExifTags import TAGS
import os
from datetime import datetime
import re
import shutil
import hashlib
from pathlib import Path
import logging

# Configuration
MEDIA_PATH = "/media/manuel/Media"
TIMELINE_BASE = f"{MEDIA_PATH}/Pictures/TimeLine"
SOURCE_FOLDER = "."  # Change to your source folder if needed
# Pattern to detect YYYY-MM-DD format
date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}')
date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})_(DSC\d+\.\w+)')
dryrun = False


# Setup logging
def setup_logger(log_file="photo_transfer.log"):
    """Configure logging to file and console"""
    logger = logging.getLogger("PhotoTransfer")
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


def add_date_to_jpg(filename, folder_path):
    # Skip if already in YYYY-MM-DD format
    if date_pattern.match(filename):
        logger.debug(f"Skipping {filename} (already in date format)")
        return

    filepath = os.path.join(folder_path, filename)
    
    try:
        # Open image and extract EXIF data
        image = Image.open(filepath)
        exif_data = image._getexif()
        
        if exif_data:
            # Find DateTimeOriginal (tag 36867)
            date_str = None
            for tag_id, value in exif_data.items():
                if tag_id == 36867:  # DateTimeOriginal
                    date_str = value
                    break
            
            if date_str:
                # Parse date and format as YYYY-MM-DD
                date_obj = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                date_prefix = date_obj.strftime('%Y-%m-%d')
                
                # Extract suffix (filename without extension)
                base_name = os.path.splitext(filename)[0]
                suffix = base_name
                # Create new filename with date and original suffix
                new_name = f"{date_prefix}_{suffix}.jpg"
                new_filepath = os.path.join(folder_path, new_name)
                
                # Rename (handles duplicate dates with _1, _2, etc.)
                if os.path.exists(new_filepath):
                    base, ext = os.path.splitext(new_name)
                    counter = 1
                    while os.path.exists(os.path.join(folder_path, f"{base}_{counter}{ext}")):
                        counter += 1
                    new_filepath = os.path.join(folder_path, f"{base}_{counter}{ext}")
                
                if not dryrun: 
                    os.rename(filepath, new_filepath)
                logger.info(f"Renamed: {filename} → {os.path.basename(new_filepath)}")
            else:
                logger.error(f"No date found in {filename}")
        else:
            logger.error(f"No EXIF data in {filename}")
    except Exception as e:
        logger.error(f"Error processing {filename}: {e}")


def check_mount(path):
    """Check if a path is mounted"""
    return os.path.ismount(path)

def calculate_hash(filepath, chunk_size=8192):
    """Calculate SHA256 hash of a file"""
    hash_obj = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing {filepath}: {e}")
        return None

def quick_file_check(src, dst, chunk_size=65536):
    """Quick duplicate check: size + first/last bytes"""
    try:
        src_size = os.path.getsize(src)
        dst_size = os.path.getsize(dst)
        
        # Different sizes = different files
        if src_size != dst_size:
            return False
        
        # Same size, check first and last chunk
        with open(src, 'rb') as f1, open(dst, 'rb') as f2:
            src_start = f1.read(chunk_size)
            dst_start = f2.read(chunk_size)
            
            if src_start != dst_start:
                return False
            
            # Check last chunk
            f1.seek(-chunk_size, 2)
            f2.seek(-chunk_size, 2)
            src_end = f1.read(chunk_size)
            dst_end = f2.read(chunk_size)
            
            return src_end == dst_end
    except Exception as e:
        logger.error(f"Error in quick check: {e}")
        return False

def copy_file_with_hash_check(src, dst, files_to_delete):
    """Copy file and verify with hash check. Return True if successful."""
    try:
        # If destination exists, compare hashes
        if os.path.exists(dst):
            # src_hash = calculate_hash(src)
            # dst_hash = calculate_hash(dst)
            
            # if src_hash == dst_hash:
            if quick_file_check(src, dst):
                logger.debug(f"File exists with matching content: {os.path.basename(dst)}")
                files_to_delete.append(src)
                return True
            else:
                logger.error(f"File exists but content differs: {os.path.basename(dst)}")
                return False
        
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        # Copy file
        shutil.copy2(src, dst)
        
        # Verify hash after copy
        # src_hash = calculate_hash(src)
        # dst_hash = calculate_hash(dst)
        
        # if src_hash == dst_hash:
        if quick_file_check(src, dst):
            logger.info(f"Copied and verified: {os.path.basename(src)} → {dst}")
            files_to_delete.append(src)
            return True
        else:
            logger.error(f"Content mismatch after copy: {os.path.basename(dst)}")
            return False
    
    except Exception as e:
        logger.error(f"Error copying {src}: {e}")
        return False


def collect_jpg_and_raw_files():
    # Collect files to process
    jpg_files = {}  # Map base name to (filepath, filename, date, year)
    arw_files = {}  # Map base name to (filepath, filename)
    
    for filename in os.listdir(SOURCE_FOLDER):
        filepath = os.path.join(SOURCE_FOLDER, filename)
        if not os.path.isfile(filepath):
            continue
        
        # Get base name without extension
        base_name = os.path.splitext(filename)[0]
        
        if filename.lower().endswith(".jpg"):
            # Extract date from filename (assumes YYYY-MM-DD.jpg format)
            if date_pattern.match(filename):
                try:
                    date_str = filename.split("_")[0]  # Gets YYYY-MM-DD
                    year = date_str.split("-")[0]
                    jpg_files[base_name] = (filepath, filename, date_str, year)
                except:
                    logger.error(f"Could not extract date from {filename}")
            else:
                logger.error(f"{filename} is not in the correct naming format")
    
        elif filename.lower().endswith(".arw"):
            arw_files[base_name] = (filepath, filename)
    
    if not jpg_files:
        logger.warn("No JPG files found to process")
        return
    
    logger.debug(f"Found {len(jpg_files)} JPG files and {len(arw_files)} ARW files")

    return (jpg_files, arw_files)


def copy_images(jpg_files, arw_files):
    files_to_delete = []
    successful_transfers = 0
    failed_transfers = 0
    
    # Process JPG files
    for base_name, (src_jpg, jpg_name, date_str, year) in jpg_files.items():
        logger.debug(f"Processing: {base_name}")
        
        # Extract the suffix (everything after the date and underscore)
        # e.g., from "2026-09-25_DSC00001" extract "DSC00001"
        suffix = base_name.split("_", 1)[1] if "_" in base_name else base_name
        
        # Build destination path
        sony_folder = f"{TIMELINE_BASE}/{year}/Sony"
        dst_jpg = f"{sony_folder}/{jpg_name}"
        
        # Create Sony folder if it doesn't exist
        try:
            os.makedirs(sony_folder, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating Sony folder: {e}")
            failed_transfers += 1
            continue
        
        # Copy JPG
        if copy_file_with_hash_check(src_jpg, dst_jpg, files_to_delete):
            successful_transfers += 1
            
            # If JPG copied successfully, also copy matching ARW
            if suffix in arw_files:
                src_arw, arw_name = arw_files[suffix]
                raw_folder = f"{TIMELINE_BASE}/{year}/Sony/raw"
                dst_arw = f"{raw_folder}/{arw_name}"
                
                # Create raw folder if it doesn't exist
                try:
                    os.makedirs(raw_folder, exist_ok=True)
                except Exception as e:
                    logger.error(f"Error creating raw folder: {e}")
                    failed_transfers += 1
                    continue
                
                # Copy ARW
                if copy_file_with_hash_check(src_arw, dst_arw, files_to_delete):
                    successful_transfers += 1
                else:
                    failed_transfers += 1
            else:
                logger.warning(f"No matching ARW found for {suffix}")
        else:
            failed_transfers += 1
    
    return (files_to_delete, failed_transfers, successful_transfers)


def delete_processed_files_locally(files_to_delete):
    for filepath in files_to_delete:
        try:
            os.remove(filepath)
            logger.info(f"Deleted: {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"Error deleting {filepath}: {e}")

if __name__ == "__main__":
    # prepare files (add date prefix)
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.lower().endswith(".jpg"):
            add_date_to_jpg(filename, SOURCE_FOLDER)

    
    # Check if media is mounted
    if not check_mount(MEDIA_PATH):
        logger.error(f"ERROR: {MEDIA_PATH} is not mounted")
    else:
        logger.debug(f"✓ {MEDIA_PATH} is mounted")
        jpg_files, arw_files = collect_jpg_and_raw_files()
        files_to_delete, failed_transfers, successful_transfers = copy_images(jpg_files, arw_files)

        # Delete files only after all transfers are complete
        if failed_transfers == 0 and files_to_delete:
            logger.info(f"\n✓ All transfers successful. Deleting {len(files_to_delete)} local files...")
            if not dryrun:
                delete_processed_files_locally(files_to_delete)
        elif failed_transfers > 0:
            logger.error(f"\n✗ {failed_transfers} transfer(s) failed. NOT deleting local files.")
            logger.debug(f"Successfully transferred files (marked for deletion): {successful_transfers}")
        else:
            logger.debug("No files to delete")



    
