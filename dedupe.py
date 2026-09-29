import os
import logging
from pathlib import Path

# Setup logging
def setup_logger(log_file="dedup_images.log"):
    """Configure logging to file and console"""
    logger = logging.getLogger("ImageDedup")
    logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
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

def find_and_remove_duplicates(folder_path, dryrun=True):
    """Find duplicate images and remove one copy"""
    
    # Supported image extensions (case-insensitive)
    image_extensions = {'.jpg', '.jpeg', '.arw', '.png', '.gif', '.bmp'}
    
    # Group files by base name (without extension)
    file_groups = {}
    
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        
        if not os.path.isfile(filepath):
            continue
        
        # Get file info
        name, ext = os.path.splitext(filename)
        
        if ext.lower() not in image_extensions:
            continue
        
        # Group by base name
        if name not in file_groups:
            file_groups[name] = []
        
        file_groups[name].append((filepath, filename, ext.lower()))
    
    logger.info(f"Scanning {folder_path}")
    logger.info(f"Found {len(file_groups)} unique base names")
    
    deleted_count = 0
    
    # Check groups with more than one file
    for base_name, files in file_groups.items():
        if len(files) <= 1:
            continue
        
        logger.info(f"Found {len(files)} variants of {base_name}")
        
        # Sort by extension (keep first, delete others)
        # This prioritizes: jpg > arw > others
        priority = {'.jpg': 0, '.jpeg': 1, '.arw': 2}
        files.sort(key=lambda x: priority.get(x[2], 999))
        
        # Compare each pair
        keep_file = files[0]
        keep_path, keep_name, keep_ext = keep_file
        
        for dup_file in files[1:]:
            dup_path, dup_name, dup_ext = dup_file
            
            # Check if files are identical
            if quick_file_check(keep_path, dup_path):
                logger.warning(f"Duplicates found: keeping {keep_name}, deleting {dup_name}")
                
                if not dryrun:
                    try:
                        os.remove(dup_path)
                        logger.info(f"Deleted: {dup_name}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error deleting {dup_name}: {e}")
                else:
                    logger.debug(f"[DRY RUN] Would delete: {dup_name}")
                    deleted_count += 1
            else:
                logger.warning(f"Files {keep_name} and {dup_name} have different content")
    
    logger.info("=" * 60)
    logger.info(f"Deduplication complete - Deleted: {deleted_count} files")
    logger.info("=" * 60)

if __name__ == "__main__":
    folder = "/media/manuel/Media/Pictures/TimeLine/2026/Sony"  # Change to your folder path
    
    # # First run with dryrun=True to see what would be deleted
    # logger.info("DRY RUN - No files will be deleted")
    # find_and_remove_duplicates(folder, dryrun=True)
    
    # Uncomment to actually delete files:
    logger.info("\nACTUAL RUN - Deleting duplicate files")
    find_and_remove_duplicates(folder, dryrun=False)