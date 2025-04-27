#!/usr/bin/env python3

import subprocess
import json
import sys
import os
from pathlib import Path
import argparse
import concurrent.futures
from enum import Enum

# Immich used tags https://github.com/immich-app/immich/blob/main/server/src/services/metadata.service.ts#L36C1-L47C3
IMMICH_DATE_TAGS = [
    "SubSecDateTimeOriginal",
    "DateTimeOriginal",
    "SubSecCreateDate",
    "CreationDate",
    "CreateDate",
    "SubSecMediaCreateDate",
    "MediaCreateDate",
    "DateTimeCreated",
    "SourceImageCreateTime",
]

# Tags to use if available
FALLBACK_TAGS = [
    "GPSDateTime",
    "GPSDateStamp",
    "SubSecModifyDate",
    "ModifyDate",
    "FileModifyDate",
]

SUPPORTED_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
)


class Status(Enum):
    DRY = "dry"
    PROCESSED = "processed"
    SKIPPED = "skipped"
    MISSING = "missing"
    ERROR = "error"


def read_exif(filepath):
    try:
        output = subprocess.run(
            ["exiftool", "-j", str(filepath)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        return json.loads(output.stdout)[0]
    except subprocess.CalledProcessError as error:
        print(f"[ERROR] Failed to read EXIF: {error} | {filepath}")
        return None


def fix_exif(filepath, dry_run=False, backup=False, verbose=False):
    filepath = str(filepath)
    exif_data = read_exif(filepath)
    if not exif_data:
        print(f"[EXFIX] No EXIF data found | {filepath}")
        return Status.ERROR

    # Check if Immich tags exist
    if any(tag in exif_data for tag in IMMICH_DATE_TAGS):
        if verbose:
            print(f"[SKIP] Immich date tag exists | {filepath}")
        return Status.SKIPPED

    # Try fallback tags
    for ftag in FALLBACK_TAGS:
        if ftag in exif_data:
            tag_value = exif_data[ftag]
            if dry_run:
                print(f"[EXFIX] [DRY-RUN] {filepath}: Date from '{ftag}' ({tag_value})")
                return Status.DRY

            print(f"[EXFIX] {filepath}: {ftag} ({tag_value})")
            cmd = ["exiftool"]
            if not backup:
                cmd.append("-overwrite_original")
            cmd += [f"-SubSecDateTimeOriginal<{ftag}", filepath]
            try:
                subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                return Status.PROCESSED
            except subprocess.CalledProcessError as error:
                print(f"[ERROR] Failed to fix EXIF: {error} | {filepath}")
                return Status.ERROR

    print(f"[WARN] Missing date tag, nothing to do | {filepath}")
    return Status.MISSING


def process_folder(source_dir, workers=4, dry_run=False, backup=False, verbose=False):
    path = Path(source_dir)
    files = [f for f in path.rglob("*") if f.suffix.lower() in SUPPORTED_EXTENSIONS]

    print(f"[EXFIX] {len(files)} supported files.")
    MISSING_EXIF = PROCESSED = SKIPPED = ERROR = DRY = 0

    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(fix_exif, file, dry_run, backup, verbose) for file in files
        ]

        # Optional: wait for completion and catch exceptions
        for future in concurrent.futures.as_completed(futures):
            try:
                status = future.result()
                match status:
                    case Status.PROCESSED:
                        PROCESSED += 1
                    case Status.SKIPPED:
                        SKIPPED += 1
                    case Status.MISSING:
                        MISSING_EXIF += 1
                    case Status.ERROR:
                        ERROR += 1
                    case Status.DRY:
                        DRY += 1

            except Exception as error:
                print(f"[ERROR] Exception in worker: {error}")

    print(f"\nFinished processing {len(files)} files:")
    if dry_run:
        print(f"    {DRY} dry-run processed")
    else:
        print(f"    {PROCESSED} processed")
    print(f"    {SKIPPED} skipped")
    print(f"    {MISSING_EXIF} missing tags, unable to fix")
    print(f"    {ERROR} failed to fix (see errors detail)")


def main():
    parser = argparse.ArgumentParser(
        description="Try to fix missing EXIF date tag for Immich, https://github.com/itskovacs/immich-exfix."
    )
    parser.add_argument("source_dir", help="Folder path to scan")
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of parallel workers (default: 4)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Do not modify files, only show actions"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logs")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Keep original files (default is overwrite)",
    )

    args = parser.parse_args()

    if not Path(args.source_dir).is_dir():
        print("Source_dir is not a folder or does not exist")
        sys.exit(1)

    process_folder(
        args.source_dir,
        workers=args.workers,
        dry_run=args.dry_run,
        backup=args.backup,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
