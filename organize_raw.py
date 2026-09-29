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
