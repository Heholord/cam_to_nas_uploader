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

Author: Manuel Esberger (with help from Claude)
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
    """
    Add EXIF date prefix to JPG filename.
    
    Extracts the DateTimeOriginal from JPG EXIF metadata and prepends it
    to the filename in YYYY-MM-DD format. This standardizes photo naming
    for organization and sorting purposes.
    
    Filename transformation:
        - Input:  DSC00001.jpg
        - Output: 2026-09-25_DSC00001.jpg
    
    If a file with the target name already exists, appends a counter:
        - 2026-09-25_DSC00001.jpg
        - 2026-09-25_DSC00001_1.jpg (if first name exists)
    
    Parameters
    ----------
    filename : str
        Name of the JPG file to process (e.g., "DSC00001.jpg").
        Case-insensitive for .jpg extension.
    folder_path : str
        Absolute or relative path to folder containing the file.
        Example: ".", "/home/user/photos", "/media/storage"
    
    Returns
    -------
    None
        Function performs in-place file renaming. No return value.
        Results are logged to logger.
    
    Raises
    ------
    None
        No exceptions are raised. All errors are caught and logged:
        
        - FileNotFoundError: File not found (logged as error)
        - PIL.UnidentifiedImageError: Not a valid image (logged as error)
        - OSError: Permission denied (logged as error)
        - KeyError: EXIF tag missing (logged as error)
    
    Notes
    -----
    - **Skips already-dated files**: Detects YYYY-MM-DD prefix and skips
    - **EXIF tag 36867**: DateTimeOriginal in format "YYYY:MM:DD HH:MM:SS"
    - **Dry-run mode**: Respects global `dryrun` variable
    - **In-place rename**: Uses os.rename() if not in dry-run mode
    - **No backup**: Original file is not backed up before renaming
    - **Requires Pillow**: Depends on PIL.Image for EXIF extraction
    
    Workflow
    --------
    1. Check if filename already has YYYY-MM-DD prefix → skip if yes
    2. Open JPG file with Pillow
    3. Extract EXIF data from image
    4. Find DateTimeOriginal tag (tag ID 36867)
    5. Parse date string: "2026:09:25 14:30:45" → "2026-09-25"
    6. Generate new filename: "{date}_{original_name}.jpg"
    7. Handle duplicates by appending counter (_1, _2, etc.)
    8. Rename file (or log dry-run result)
    
    Examples
    --------
    Single file:
    
    >>> add_date_to_jpg("DSC00001.jpg", ".")
    INFO - Renamed: DSC00001.jpg → 2026-09-25_DSC00001.jpg
    
    File already dated (skipped):
    
    >>> add_date_to_jpg("2026-09-25_DSC00001.jpg", ".")
    DEBUG - Skipping 2026-09-25_DSC00001.jpg (already in date format)
    
    Duplicate handling:
    
    >>> # File 2026-09-25_DSC00001.jpg already exists
    >>> add_date_to_jpg("DSC00001.jpg", ".")
    INFO - Renamed: DSC00001.jpg → 2026-09-25_DSC00001_1.jpg
    
    Batch processing:
    
    >>> for filename in os.listdir("."):
    ...     if filename.lower().endswith(".jpg"):
    ...         add_date_to_jpg(filename, ".")
    
    Error case - no EXIF data:
    
    >>> add_date_to_jpg("photo_no_exif.jpg", ".")
    ERROR - No EXIF data in photo_no_exif.jpg
    
    Dry-run mode:
    
    >>> dryrun = True
    >>> add_date_to_jpg("DSC00001.jpg", ".")
    DEBUG - [DRY RUN] Would rename: DSC00001.jpg → 2026-09-25_DSC00001.jpg
    # File is NOT actually renamed
    
    Common Issues & Solutions
    -------------------------
    
    **No EXIF data in file**
    
    - Some JPGs lack EXIF metadata (screenshots, heavily edited photos)
    - Photos from certain cameras/phone apps may strip EXIF
    - Solution: Add date manually or use file modification time
    
    **File already exists**
    
    - Multiple photos taken at same time with same camera
    - Counter automatically appended (_1, _2, etc.)
    - Solution: Review duplicates, delete if not needed
    
    **Permission denied**
    
    - Insufficient write permissions on folder
    - File locked by another application
    - Solution: Check folder permissions, close photo viewer
    
    See Also
    --------
    collect_jpg_and_raw_files : Collect dated JPGs for transfer
    copy_images : Transfer dated JPGs to media library
    photo_transfer.py : Full workflow using this function
    
    References
    ----------
    - EXIF Tag 36867: DateTimeOriginal (capture time, user-settable)
    - EXIF Tag 36868: DateTimeDigitized (digitization time)
    - EXIF specification: https://en.wikipedia.org/wiki/Exif
    - Pillow documentation: https://pillow.readthedocs.io/
    """

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
    """
    Copy a file with verification and duplicate detection.
    
    Copies a single file from source to destination with content verification
    using fast size + first/last bytes comparison. If destination exists,
    compares content before copying. Files are only marked for deletion if
    verification passes.
    
    Parameters
    ----------
    src : str
        Absolute path to source file
    dst : str
        Absolute path to destination file
    files_to_delete : list
        List to append file paths to (modified in-place). Files are added
        only if copy and verification succeed.
    
    Returns
    -------
    bool
        True if file was successfully copied and verified, or if existing
        file matches content. False if copy failed or content differs.
    
    Raises
    ------
    None
        All exceptions are caught and logged. Function returns False on error.
    
    Notes
    -----
    - Uses quick_file_check() for verification (size + first/last bytes)
    - Creates destination directories automatically
    - Preserves file metadata with shutil.copy2()
    - If destination exists and matches, marks src for deletion
    - If destination exists and differs, logs error and returns False
    
    Examples
    --------
    >>> files_to_delete = []
    >>> success = copy_file_with_hash_check(
    ...     '/local/photo.jpg',
    ...     '/media/photo.jpg',
    ...     files_to_delete
    ... )
    >>> if success:
    ...     print("File copied and verified")
    >>> print(files_to_delete)
    ['/local/photo.jpg']
    
    See Also
    --------
    quick_file_check : Fast duplicate detection
    copy_images : Batch copy multiple files
    """

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
    """
    Collect and organize JPG and ARW files from source folder.
    
    Scans the SOURCE_FOLDER for JPG and ARW files, extracts date information
    from JPG filenames, and groups them by base name for later processing.
    
    JPG files must be in YYYY-MM-DD_{suffix} format (typically created by
    add_date_to_jpg function). ARW files should have matching base names
    without the date prefix.
    
    Returns
    -------
    tuple or None
        A tuple of (jpg_files, arw_files) where:
        
        - **jpg_files** (dict): Maps base_name to (filepath, filename, date_str, year)
            - Example: {'2026-09-25_DSC00001': ('/path/to/2026-09-25_DSC00001.jpg', 
              '2026-09-25_DSC00001.jpg', '2026-09-25', '2026')}
        
        - **arw_files** (dict): Maps base_name to (filepath, filename)
            - Example: {'DSC00001': ('/path/to/DSC00001.arw', 'DSC00001.arw')}
        
        Returns None if no JPG files are found.
    
    Raises
    ------
    None
        Errors are logged but do not raise exceptions. Failed extractions
        are logged as errors and skipped.
    
    Notes
    -----
    - Only processes files with .jpg and .arw extensions (case-insensitive)
    - Requires JPG filenames to match pattern: YYYY-MM-DD_*
    - Logs warnings for files not in correct format
    - Year is extracted from date string (first 4 characters)
    
    Examples
    --------
    >>> jpg_files, arw_files = collect_jpg_and_raw_files()
    >>> print(len(jpg_files), "JPG files found")
    150 JPG files found
    >>> print(list(jpg_files.keys())[:2])
    ['2026-09-25_DSC00001', '2026-09-25_DSC00002']
    
    See Also
    --------
    add_date_to_jpg : Add date prefix to JPG files
    copy_images : Transfer collected files to media library
    """

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
    """
    Copy JPG and ARW files to organized media library structure.
    
    Transfers collected JPG and ARW files to the media library organized
    by year and camera type. Creates necessary folder structure and verifies
    each file after transfer.
    
    JPGs are copied to: {TIMELINE_BASE}/{year}/Sony/
    ARWs are copied to: {TIMELINE_BASE}/{year}/Sony/raw/
    
    Parameters
    ----------
    jpg_files : dict
        Dictionary mapping base_name to (filepath, filename, date_str, year)
        from collect_jpg_and_raw_files()
    arw_files : dict
        Dictionary mapping base_name to (filepath, filename)
        from collect_jpg_and_raw_files()
    
    Returns
    -------
    tuple
        A tuple of (files_to_delete, failed_transfers, successful_transfers):
        
        - **files_to_delete** (list): File paths marked for deletion
        - **failed_transfers** (int): Count of failed transfers
        - **successful_transfers** (int): Count of successful transfers
    
    Raises
    ------
    None
        All exceptions are caught and logged as failures.
    
    Notes
    -----
    - ARWs are matched to JPGs by base filename (suffix extraction)
    - Missing ARW files are logged as warnings but don't fail the JPG
    - Destination folders are auto-created if missing
    - Both JPG and ARW verification must pass to mark for deletion
    - Returns counts for caller to decide on deletion
    
    Examples
    --------
    >>> jpg_files = {...}  # from collect_jpg_and_raw_files()
    >>> arw_files = {...}
    >>> to_del, fails, success = copy_images(jpg_files, arw_files)
    >>> print(f"Transferred: {success}, Failed: {fails}")
    Transferred: 150, Failed: 0
    >>> if fails == 0:
    ...     delete_processed_files_locally(to_del)
    
    See Also
    --------
    collect_jpg_and_raw_files : Prepare files before copying
    copy_file_with_hash_check : Single file copy with verification
    delete_processed_files_locally : Clean up after successful transfer
    """

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
    """
    Delete local files after successful transfer to media library.
    
    Removes files from the local source folder after they have been
    successfully copied and verified on the media library.
    
    Should only be called after all transfers have completed successfully
    (failed_transfers == 0).
    
    Parameters
    ----------
    files_to_delete : list of str
        Absolute file paths to delete. Typically from copy_images()
    
    Returns
    -------
    None
    
    Raises
    ------
    None
        File deletion errors are logged but do not raise exceptions.
        Partial deletions will be logged with mixed success/error messages.
    
    Notes
    -----
    - Logs each deletion as INFO level
    - Catches and logs individual file errors without stopping
    - Does NOT verify files before deletion (assumes caller verified)
    - This is the FINAL STEP - use with caution
    
    Examples
    --------
    >>> files_to_delete = ['/local/photo1.jpg', '/local/photo1.arw']
    >>> delete_processed_files_locally(files_to_delete)
    INFO - Deleted: photo1.jpg
    INFO - Deleted: photo1.arw
    
    See Also
    --------
    copy_images : Returns files_to_delete list
    """

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



    
