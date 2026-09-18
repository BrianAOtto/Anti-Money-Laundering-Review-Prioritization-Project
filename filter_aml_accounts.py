"""
Filters the IBM AML Account file down to only the accounts that are actually
referenced in your already-filtered Transaction file.

Why this works differently than the transaction filter:
  The Transaction file was filtered by randomly sampling non-flagged rows,
  because each transaction is its own independent event. The Account file
  is different -- it's a lookup/reference table, so a random sample would
  likely drop accounts that your filtered transactions still point to,
  breaking the joins in Power BI. Instead, this script keeps exactly the
  accounts your filtered transaction file needs -- no more, no less.

What it does:
  - Reads your filtered Transaction file (small, e.g. HI-Small_filtered.csv)
    and builds a list of every (Bank, Account) pair used on either the
    "From" side or the "To" side of a transaction.
  - Reads the (huge) raw Account file in chunks, so it never loads the
    whole thing into memory at once.
  - Keeps only the Account rows whose (Bank ID, Account Number) match
    something in that needed list.
  - Writes the matched rows to a new, much smaller CSV.

Usage:
    python filter_aml_accounts.py FILTERED_TRANSACTION_FILE.csv ACCOUNT_FILE.csv OUTPUT_FILE.csv

Requirements:
    pip install pandas
"""

import sys

import pandas as pd

CHUNK_SIZE = 500_000  # rows per chunk -- adjust down if memory is tight


def main():
    if len(sys.argv) != 4:
        print("Usage: python filter_aml_accounts.py FILTERED_TRANSACTION_FILE.csv ACCOUNT_FILE.csv OUTPUT_FILE.csv")
        sys.exit(1)

    trans_path, account_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    print(f"Reading {trans_path} to find which accounts are actually used...")
    trans = pd.read_csv(trans_path)

    # These column names match what filter_aml_transactions.py already
    # renamed them to: "From Account" / "To Account".
    from_pairs = set(zip(trans["From Bank"], trans["From Account"]))
    to_pairs = set(zip(trans["To Bank"], trans["To Account"]))
    needed_pairs = from_pairs | to_pairs

    print(f"Found {len(needed_pairs):,} unique (Bank, Account) pairs referenced "
          f"across {len(trans):,} transactions.")

    matched_chunks = []
    total_rows = 0
    total_matched = 0

    print(f"\nReading {account_path} in chunks of {CHUNK_SIZE:,} rows...")

    for i, chunk in enumerate(pd.read_csv(account_path, chunksize=CHUNK_SIZE)):
        total_rows += len(chunk)

        chunk_pairs = list(zip(chunk["Bank ID"], chunk["Account Number"]))
        mask = [pair in needed_pairs for pair in chunk_pairs]
        matched = chunk[mask]

        total_matched += len(matched)
        if len(matched) > 0:
            matched_chunks.append(matched)

        print(f"  chunk {i + 1}: {len(chunk):,} rows read "
              f"({total_rows:,} total, {total_matched:,} matched so far)")

    print(f"\nDone reading. Total account rows scanned: {total_rows:,}")
    print(f"Matched accounts kept: {total_matched:,}")

    result = pd.concat(matched_chunks, ignore_index=True) if matched_chunks else pd.DataFrame()
    result.to_csv(output_path, index=False)

    print(f"\nWrote {len(result):,} rows to {output_path}")

    missing = len(needed_pairs) - len(result)
    if len(result) < len(needed_pairs):
        print(f"\nNote: {len(needed_pairs) - len(result.drop_duplicates()):,} referenced (Bank, Account) "
              f"pairs were not found in the Account file. This can happen if a bank/account "
              f"in the transaction data doesn't have a corresponding row in the Account file -- "
              f"worth spot-checking a few in Power BI once loaded.")


if __name__ == "__main__":
    sys.exit(main())
