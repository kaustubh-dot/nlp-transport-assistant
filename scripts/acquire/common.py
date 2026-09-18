#!/usr/bin/env python3
"""Common utilities for raw data acquisition, byte-for-byte preservation,

SHA-256 checksum calculation, provenance logging, and manifest recording.
"""

import os
import time
import hashlib
import logging
import csv
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_PATH = os.path.join(BASE_DIR, "metadata", "raw_file_manifest.csv")
LOG_DIR = os.path.join(BASE_DIR, "logs", datetime.now().strftime("%Y-%m-%d"))
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "acquisition.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Acquisition")


def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 checksum for a file on disk."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def register_raw_file(
    file_id: str,
    relative_path: str,
    source_id: str,
    download_url: str,
    retrieved_at: str,
    file_format: str,
    checksum_sha256: str,
    file_size: int,
    dataset_version: str = "1.0",
    published_date: str = "",
    license: str = "REVIEW_REQUIRED",
    notes: str = ""
):
    """Appends or updates a record in metadata/raw_file_manifest.csv."""
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    header = [
        "file_id", "relative_path", "source_id", "download_url", "retrieved_at",
        "file_format", "file_size", "checksum_sha256", "dataset_version",
        "published_date", "license", "notes"
    ]

    existing_rows = []
    file_exists = os.path.exists(MANIFEST_PATH)
    if file_exists:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = [row for row in reader if row.get("file_id") != file_id]

    new_row = {
        "file_id": file_id,
        "relative_path": relative_path,
        "source_id": source_id,
        "download_url": download_url,
        "retrieved_at": retrieved_at,
        "file_format": file_format,
        "file_size": file_size,
        "checksum_sha256": checksum_sha256,
        "dataset_version": dataset_version,
        "published_date": published_date,
        "license": license,
        "notes": notes
    }
    existing_rows.append(new_row)

    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in existing_rows:
            writer.writerow(row)

    logger.info(f"Manifest updated for raw file: {relative_path} ({file_size} bytes, SHA256: {checksum_sha256[:12]}...)")


def download_file_byte_for_byte(
    url: str,
    target_path: str,
    source_id: str,
    file_id: str,
    file_format: str,
    dataset_version: str = "1.0",
    license: str = "REVIEW_REQUIRED",
    notes: str = "",
    headers: Optional[Dict[str, str]] = None,
    rate_limit_delay_sec: float = 2.0
) -> bool:
    """Downloads a file verbatim byte-for-byte and updates manifest."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    req_headers = {"User-Agent": "ChennaiTransitKnowledgeBaseBot/1.0 (Research/Academic NLP Data Acquisition)"}
    if headers:
        req_headers.update(headers)

    logger.info(f"Starting byte-for-byte download from: {url}")
    time.sleep(rate_limit_delay_sec)

    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()

        with open(target_path, "wb") as f:
            f.write(content)

        file_size = os.path.getsize(target_path)
        sha256 = compute_sha256(target_path)
        retrieved_at = datetime.now(timezone.utc).isoformat()
        rel_path = os.path.relpath(target_path, BASE_DIR)

        register_raw_file(
            file_id=file_id,
            relative_path=rel_path,
            source_id=source_id,
            download_url=url,
            retrieved_at=retrieved_at,
            file_format=file_format,
            file_size=file_size,
            checksum_sha256=sha256,
            dataset_version=dataset_version,
            license=license,
            notes=notes
        )
        logger.info(f"Successfully saved {file_size} bytes to {rel_path}")
        return True
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code} fetching {url}: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
