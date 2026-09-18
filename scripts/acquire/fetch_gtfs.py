#!/usr/bin/env python3
"""Fetches Chennai GTFS feeds (community unified feed) byte-for-byte,

preserving the raw ZIP archive in data/raw/ and unzipping into data/staging/
for subsequent validation, profiling, and normalization.
"""

import os
import sys
import zipfile
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.acquire.common import download_file_byte_for_byte, logger
DATE_STR = datetime.now().strftime("%Y-%m-%d")
RAW_GTFS_DIR = os.path.join(BASE_DIR, "data", "raw", "community_gtfs", DATE_STR)
STAGING_GTFS_DIR = os.path.join(BASE_DIR, "data", "staging", "community_gtfs", DATE_STR)

GTFS_URL = "https://raw.githubusercontent.com/ungalsoththu/ChennaiGTFS/main/data/chennai-unified-gtfs.zip"
TARGET_ZIP = os.path.join(RAW_GTFS_DIR, "chennai-unified-gtfs.zip")


def acquire_gtfs():
    os.makedirs(RAW_GTFS_DIR, exist_ok=True)
    os.makedirs(STAGING_GTFS_DIR, exist_ok=True)

    logger.info("Starting acquisition of Chennai Unified GTFS feed...")
    success = download_file_byte_for_byte(
        url=GTFS_URL,
        target_path=TARGET_ZIP,
        source_id="CHENNAI_COMMUNITY_GTFS",
        file_id=f"CHENNAI_UNIFIED_GTFS_{DATE_STR.replace('-', '')}",
        file_format="ZIP",
        dataset_version="2.0",
        license="ODbL",
        notes="Chennai Unified GTFS (MTC bus + CMRL metro) community feed from ungalsoththu/ChennaiGTFS."
    )

    if not success:
        logger.error("Failed to download GTFS archive.")
        return False

    # Extract strictly into data/staging/ (never modifying data/raw/)
    logger.info(f"Extracting raw archive to staging directory: {STAGING_GTFS_DIR}")
    with zipfile.ZipFile(TARGET_ZIP, "r") as zf:
        zf.extractall(STAGING_GTFS_DIR)
        extracted_files = zf.namelist()
        logger.info(f"Successfully extracted {len(extracted_files)} files: {extracted_files}")

    return True


if __name__ == "__main__":
    acquire_gtfs()
