"""
Quick check: counts total rows and "Is Laundering" == 1 rows in a transaction
CSV, without loading the whole file into memory. Use this to compare the
HI-Small and LI-Small Transaction files before deciding which one to use.

Usage:
    python check_laundering_counts.py TRANSACTION_FILE.csv
"""

import sys

import pandas as pd

CHUNK_SIZE = 500_000


def main():
    if len(sys.argv) != 2:
        print("Usage: python check_laundering_counts.py TRANSACTION_FILE.csv")
        sys.exit(1)

    path = sys.argv[1]
    total_rows = 0
    total_flagged = 0

    for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE, usecols=["Is Laundering"]):
        total_rows += len(chunk)
        total_flagged += int(chunk["Is Laundering"].sum())

    pct = (total_flagged / total_rows * 100) if total_rows else 0
    print(f"\nFile: {path}")
    print(f"Total rows:        {total_rows:,}")
    print(f"Flagged (=1) rows: {total_flagged:,}")
    print(f"Flagged percentage: {pct:.4f}%")


if __name__ == "__main__":
    main()
