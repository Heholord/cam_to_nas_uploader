# Photo Transfer Tools

[![Documentation Status](https://readthedocs.org/projects/cam-to-nas-uploader/badge/?version=latest)](https://cam-to-nas-uploader.readthedocs.io/)

Professional photo organization and management tools.

## Features

- 📅 Automatic EXIF date extraction and JPG renaming
- 📁 Organized transfer to media library with year/camera structure
- 🔄 RAW file organization and orphan detection
- 🔍 Duplicate image detection and removal

## Documentation

📖 **[Full Documentation](https://cam-to-nas-uploader.readthedocs.io/)**

## Quick Start

```bash
python photo_transfer.py
```

See [docs](https://cam-to-nas-uploader.readthedocs.io/) for detailed usage.

## Scripts

| Script                  | Purpose                                 |
| ----------------------- | --------------------------------------- |
| `photo_transfer.py`     | Main workflow: rename, transfer, verify |
| `organize_raw_files.py` | Organize RAWs by JPG matching           |
| `dedup_images.py`       | Find and remove duplicates              |

## Requirements

- Python 3.6+
- Pillow (for EXIF): `pip install pillow`
