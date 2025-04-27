<p align="center"><img width="200" src="./.github/logo.png"></p>
<h2 align="center">Exfix</h2>

<div align="center">


  ![Status](https://img.shields.io/badge/status-active-success?style=for-the-badge)
  [![GitHub Issues](https://img.shields.io/github/issues/itskovacs/immich-exfix?style=for-the-badge&color=ededed)](https://github.com/itskovacs/immich-exfix/issues)
  [![License](https://img.shields.io/badge/license-MIT-2596be?style=for-the-badge)](/LICENSE)

</div>

<p align="center">🛠️ EXIF date fixer for Immich — fixes what it can, skips what it can't.</p>
<br>

---

*exfix* sets missing EXIF date tag in your photos and videos for correct timeline display in [Immich](https://github.com/immich-app/immich).

> [!WARNING]
Always backup your files!

> [!IMPORTANT]
*exfix* **does not** hard-set the date to `1970:01:01 00:00:01`. If no tag is available, file is left untouched.

It scans the given directory, detects if files have the tags used by Immich ([source](https://github.com/immich-app/immich/blob/main/server/src/services/metadata.service.ts#L36C1-L47C3)), and if not, tries to recover them from other existing tags, ensuring Immich timeline consistency.

**If no usable metadata exists, files are left untouched.**

> [!TIP]
You can use the option `--dry-run` to see how many files would be fixed, skipped or would fail.  
You can use the option `--backup` to keep original files and create modified ones aside.


<br>

## 🌱 Getting Started

Clone the repo and run *exfix*.

> [!NOTE]
[exiftool](https://exiftool.org/) binary must be in your system path.

```bash
  # Clone repository
  git clone https://github.com/itskovacs/immich-exfix.git
  cd immich-exfix
  python exfix.py /path/to/your/photo/library
```

<br>

## 🚀 Usage
```
usage: exfix.py [-h] [--workers WORKERS] [--dry-run] [-v] [--backup] source_dir

positional arguments:
  source_dir         Folder path to scan

options:
  --workers WORKERS  Number of parallel workers (default: 4)
  --dry-run          Do not modify files, only show actions
  -v, --verbose      Verbose logs
  --backup           Keep original files (default is overwrite)
```

**Example**
```bash
# Simulate the run without modifying any files
python exfix.py /mnt/photos --dry-run
```

```bash
# Run with 8 workers without modifying any files
python exfix.py /mnt/photos --dry-run
```

<br>

## 🧠 How it works
Based on multiple sources:
- https://github.com/immich-app/immich/discussions/7654
- https://github.com/immich-app/immich/discussions/12650
- https://github.com/immich-app/immich/blob/main/server/src/services/metadata.service.ts

*exfix* does the following :

1. Recursively scans supported files (.jpg, .jpeg, .png, .mp4, .mov, etc.)
2. For each file:
    1. Check if any [Immich-used](https://github.com/immich-app/immich/blob/main/server/src/services/metadata.service.ts#L36C1-L47C3) tag exists
    2. If not, checks for fallback tags exist (*GPSDateStamp*, *ModifyDate*, *GPSDateTime*, *SubSecModifyDate*, *FileModifyDate*)
    3. Fixes files by setting `DateTimeOriginal` from fallback tag value, or leaves it untouched
3. Summarize
    - Files processed (fixed)
    - Files skipped (tag exists)
    - Files unprocessable (no tag to use)
    - Files error (error on file, see details)