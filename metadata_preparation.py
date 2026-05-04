import csv
import json
import os
import sys
import time

import requests

META_URL = (
    "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/"
    "resolve/main/raw/meta_categories/meta_Electronics.jsonl"
)
HERE = os.path.dirname(os.path.abspath(__file__))
REVIEWS_CSV = os.path.join(HERE, "amazon_electronics_500k.csv")
OUTPUT_CSV = os.path.join(HERE, "amazon_electronics_meta.csv")

META_FIELDS = [
    "parent_asin",
    "title",
    "main_category",
    "categories",
    "store",
    "price",
    "average_rating",
    "rating_number",
    "description",
    "features",
]


def load_target_asins(reviews_csv: str) -> set:
    if not os.path.exists(reviews_csv):
        raise FileNotFoundError(
            f"Reviews CSV not found at {reviews_csv}. Run data_preparation.py first."
        )

    asins = set()
    with open(reviews_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pa = row.get("parent_asin") or row.get("asin")
            if pa:
                asins.add(pa)
    return asins


def normalise_record(record: dict) -> dict:
    row = {}
    for key in META_FIELDS:
        value = record.get(key, "")
        if key == "categories" and isinstance(value, list):
            value = " > ".join(str(c) for c in value if c)
        elif key in ("description", "features") and isinstance(value, list):
            value = " ".join(str(s) for s in value if s)
        if isinstance(value, str):
            value = value.replace("\r", " ").replace("\n", " ").strip()
        row[key] = value
    return row


def stream_and_filter(url: str, target_asins: set, out_path: str) -> tuple:
    kept = 0
    scanned = 0
    skipped_bad_json = 0
    start = time.time()

    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        line_iter = resp.iter_lines(decode_unicode=True, chunk_size=1024 * 1024)

        with open(out_path, "w", encoding="utf-8", newline="") as f_out:
            writer = csv.DictWriter(
                f_out,
                fieldnames=META_FIELDS,
                quoting=csv.QUOTE_ALL,
                extrasaction="ignore",
            )
            writer.writeheader()

            for raw_line in line_iter:
                if not raw_line:
                    continue
                scanned += 1
                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError:
                    skipped_bad_json += 1
                    continue

                pa = record.get("parent_asin")
                if pa not in target_asins:
                    continue

                writer.writerow(normalise_record(record))
                kept += 1

                if kept >= len(target_asins):
                    print("  All target ASINs matched - stopping stream early.")
                    break

                if scanned % 100_000 == 0:
                    elapsed = time.time() - start
                    print(
                        f"  scanned {scanned:>9,} | matched {kept:>7,}/"
                        f"{len(target_asins):,} | {elapsed:,.1f}s",
                        flush=True,
                    )

    if skipped_bad_json:
        print(f"  Skipped {skipped_bad_json} malformed lines.")
    return kept, scanned


def main() -> int:
    print(f"Reviews CSV : {REVIEWS_CSV}")
    print(f"Output CSV  : {OUTPUT_CSV}")
    print(f"Source      : {META_URL}")
    print()

    print("PASS 1: collecting unique parent_asin values from the reviews CSV...")
    t0 = time.time()
    target = load_target_asins(REVIEWS_CSV)
    print(f"  {len(target):,} unique parent_asin values  ({time.time() - t0:,.1f}s)")
    print()

    print("PASS 2: streaming metadata file and filtering...")
    t0 = time.time()
    kept, scanned = stream_and_filter(META_URL, target, OUTPUT_CSV)
    elapsed = time.time() - t0

    size_mb = os.path.getsize(OUTPUT_CSV) / (1024 * 1024)
    coverage = kept / len(target) * 100 if target else 0
    print()
    print("Done.")
    print(f"  Lines scanned : {scanned:,}")
    print(f"  Records kept  : {kept:,}")
    print(f"  Coverage      : {coverage:,.2f}% of reviewed products have metadata")
    print(f"  File size     : {size_mb:,.1f} MB")
    print(f"  Time          : {elapsed:,.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
