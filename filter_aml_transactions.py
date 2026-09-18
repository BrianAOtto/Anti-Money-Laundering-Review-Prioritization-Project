"""
Filters the IBM AML transaction file down to a manageable working set for Power BI.

What it does:
  - Reads the (huge) transaction CSV in chunks, so it never loads the whole
    file into memory at once.
  - Renames the two duplicate "Account" columns to "From Account" and
    "To Account" so there's no ambiguity downstream.
  - Keeps every single row where Is Laundering == 1 (the flagged/confirmed
    laundering transactions) — these are rare and valuable, so none get lost.
  - Keeps a random sample of the non-flagged rows, at a ratio you control
    (default: 10x the number of flagged rows), so the dashboard has enough
    "normal" transactions for contrast without loading in tens of millions
    of rows that don't add to the story.
  - Writes the combined result to a new, much smaller CSV that Power BI can
    load comfortably.

Usage:
    python filter_aml_transactions.py INPUT_FILE.csv OUTPUT_FILE.csv [--ratio 10]

Requirements:
    pip install pandas
"""

import argparse
import sys

import pandas as pd

CHUNK_SIZE = 500_000  # rows per chunk — adjust down if memory is tight


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="Path to the raw IBM AML transaction CSV")
    parser.add_argument("output_file", help="Path to write the filtered CSV to")
    parser.add_argument(
        "--ratio",
        type=int,
        default=10,
        help="How many non-flagged rows to sample per flagged row (default: 10)",
    )
    args = parser.parse_args()

    flagged_chunks = []
    nonflagged_reservoir = []  # will hold a running random sample
    total_rows = 0
    total_flagged = 0
    total_nonflagged_seen = 0

    print(f"Reading {args.input_file} in chunks of {CHUNK_SIZE:,} rows...")

    for i, chunk in enumerate(pd.read_csv(args.input_file, chunksize=CHUNK_SIZE)):
        # Rename the duplicate "Account" columns based on position.
        # Expected raw header order:
        # Timestamp, From Bank, Account, To Bank, Account, Amount Received,
        # Receiving Currency, Amount Paid, Payment Currency, Payment Format,
        # Is Laundering
        cols = list(chunk.columns)
        account_positions = [j for j, c in enumerate(cols) if c == "Account"]
        if len(account_positions) == 2:
            cols[account_positions[0]] = "From Account"
            cols[account_positions[1]] = "To Account"
            chunk.columns = cols
        elif "Account.1" in cols:
            # pandas already auto-deduped them on a prior pass
            chunk = chunk.rename(columns={"Account": "From Account", "Account.1": "To Account"})

        total_rows += len(chunk)

        flagged = chunk[chunk["Is Laundering"] == 1]
        nonflagged = chunk[chunk["Is Laundering"] == 0]

        total_flagged += len(flagged)
        total_nonflagged_seen += len(nonflagged)

        if len(flagged) > 0:
            flagged_chunks.append(flagged)

        # Reservoir-style sampling: sample a fraction of each chunk's
        # non-flagged rows up front. We'll trim to the exact target count
        # at the end once we know the true flagged total.
        if len(nonflagged) > 0:
            nonflagged_reservoir.append(nonflagged.sample(frac=0.02, random_state=42))

        print(f"  chunk {i + 1}: {len(chunk):,} rows read "
              f"({total_rows:,} total, {total_flagged:,} flagged so far)")

    print(f"\nDone reading. Total rows: {total_rows:,}")
    print(f"Total flagged (Is Laundering == 1): {total_flagged:,}")
    print(f"Total non-flagged: {total_nonflagged_seen:,}")

    flagged_df = pd.concat(flagged_chunks, ignore_index=True) if flagged_chunks else pd.DataFrame()
    nonflagged_pool = pd.concat(nonflagged_reservoir, ignore_index=True) if nonflagged_reservoir else pd.DataFrame()

    target_nonflagged = min(len(nonflagged_pool), total_flagged * args.ratio)
    nonflagged_sample = nonflagged_pool.sample(n=target_nonflagged, random_state=42)

    result = pd.concat([flagged_df, nonflagged_sample], ignore_index=True)
    result = result.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

    result.to_csv(args.output_file, index=False)

    print(f"\nWrote {len(result):,} rows to {args.output_file} "
          f"({total_flagged:,} flagged + {len(nonflagged_sample):,} sampled non-flagged)")


if __name__ == "__main__":
    sys.exit(main())
