import os
import re

def remove_first_date(directory):
    # Regular expression to match dates in the format YYYY-MM-DD
    date_pattern = r'\d{4}-\d{2}-\d{2}_'
    # Compile the regex pattern
    date_regex = re.compile(date_pattern)
    
    # Iterate over files in the directory
    for filename in os.listdir(directory):
        # Find all occurrences of the date pattern in the filename
        dates = date_regex.findall(filename)
        # If there are at least two occurrences of the date pattern
        if len(dates) >= 2:
            # Remove the first occurrence of the date pattern from the filename
            new_filename = filename.replace(dates[0], '', 1)
            # Rename the file
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
            print(f"Renamed '{filename}' to '{new_filename}'")


# def remove_first_underscore(directory):
#     # Regular expression to match dates in the format YYYY-MM-DD
#     pattern = r'_*'
#     # Compile the regex pattern
#     regex = re.compile(pattern)
    
#     # Iterate over files in the directory
#     for filename in os.listdir(directory):
#         # Find all occurrences of the date pattern in the filename
#         findings = regex.findall(filename)
#         if len(findings) >= 1:
#             new_filename = filename.replace('_', '', 1)
#             # Rename the file
#             #os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
#             print(f"Renamed '{filename}' to '{new_filename}'")


# def add_underscore(directory):
#     # Regular expression to match dates in the format YYYY-MM-DD
#     pattern = r'd{2}DSC*'
#     # Compile the regex pattern
#     regex = re.compile(pattern)
    
#     # Iterate over files in the directory
#     for filename in os.listdir(directory):
#         # Find all occurrences of the date pattern in the filename
#         findings = regex.findall(filename)
#         if len(findings) >= 1:
#             new_filename = filename.replace('DSC', '_DSC', 1)
#             # Rename the file
#             # os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
#             print(f"Renamed '{filename}' to '{new_filename}'")


# def fix_filenames(directory):
#     # Regular expression to match filenames without "_" between date and "DSC"
#     pattern = r'(\d{4}-\d{2}-\d{2})(DSC\d+\.\w+)'
#     # Compile the regex pattern
#     regex = re.compile(pattern)
    
#     # Iterate over files in the directory
#     for filename in os.listdir(directory):
#         # Check if the filename matches the pattern
#         match = regex.match(filename)
#         if match:
#             # Extract date and "DSC" part
#             date_part, dsc_part = match.groups()
#             # Add "_" between date and "DSC"
#             new_filename = f"{date_part}_{dsc_part}"
#             # Rename the file
#             #os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
#             print(f"Renamed '{filename}' to '{new_filename}'")


# Example usage
directory_path = "./2024/Sony"
# remove_first_date(directory_path)
# remove_first_(directory_path)
remove_first_date(directory_path)
