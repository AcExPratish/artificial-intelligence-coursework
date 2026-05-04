import csv
import json
import os
import sys
import time

import requests

DATASET_URL = (
    "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/"
    "resolve/main/raw/review_categories/Electronics.jsonl"
)
TARGET_ROWS = 500_000
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "amazon_electronics_500k.csv")

CSV_FIELDS = [
    "rating",
    "title",
    "text",
    "asin",
    "parent_asin",
    "user_id",
    "timestamp",
    "helpful_vote",
    "verified_purchase",
]


def already_complete(path: str, target: int) -> bool:
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        count = sum(1 for _ in f) - 1
    return count >= target


def stream_and_save(url: str, out_path: str, target: int) -> int:
    written = 0
    skipped = 0
    start = time.time()

    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        line_iter = resp.iter_lines(decode_unicode=True, chunk_size=1024 * 1024)

        with open(out_path, "w", encoding="utf-8", newline="") as f_out:
            writer = csv.DictWriter(
                f_out,
                fieldnames=CSV_FIELDS,
                quoting=csv.QUOTE_ALL,
                extrasaction="ignore",
            )
            writer.writeheader()

            for raw_line in line_iter:
                if written >= target:
                    break
                if not raw_line:
                    continue
                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError:
                    skipped += 1
                    continue

                row = {}
                for key in CSV_FIELDS:
                    value = record.get(key, "")
                    if isinstance(value, str):
                        value = value.replace("\r", " ").replace("\n", " ").strip()
                    row[key] = value
                writer.writerow(row)
                written += 1

                if written % 50_000 == 0:
                    elapsed = time.time() - start
                    rate = written / elapsed if elapsed > 0 else 0
                    print(
                        f"  [{written:>7,}/{target:,}] rows written "
                        f"({rate:,.0f} rows/sec, {elapsed:,.1f}s elapsed)",
                        flush=True,
                    )

    if skipped:
        print(f"  Skipped {skipped} malformed lines.")
    return written


def main() -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory : {OUTPUT_DIR}")
    print(f"Output CSV       : {OUTPUT_CSV}")
    print(f"Target rows      : {TARGET_ROWS:,}")
    print(f"Source           : {DATASET_URL}")
    print()

    if already_complete(OUTPUT_CSV, TARGET_ROWS):
        print(f"CSV already contains >= {TARGET_ROWS:,} rows. Nothing to do.")
        return 0

    print("Streaming the dataset (this will take a few minutes)...")
    start = time.time()
    rows = stream_and_save(DATASET_URL, OUTPUT_CSV, TARGET_ROWS)
    elapsed = time.time() - start

    size_mb = os.path.getsize(OUTPUT_CSV) / (1024 * 1024)
    print()
    print("Done.")
    print(f"  Rows written : {rows:,}")
    print(f"  File size    : {size_mb:,.1f} MB")
    print(f"  Time         : {elapsed:,.1f}s")

    if rows < TARGET_ROWS:
        print(
            f"WARNING: only {rows:,} rows were available (expected {TARGET_ROWS:,}).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
