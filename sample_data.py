"""
sample_data.py

Downsamples the PaySim synthetic financial fraud dataset into a smaller,
Tableau-friendly CSV while preserving ALL fraud cases (since they are rare
and critical for accurate fraud-rate visuals).

Usage:
    python sample_data.py
    python sample_data.py --input my_file.csv --output my_sample.csv --sample-size 200000
"""

import argparse
import os
import sys

import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Downsample the PaySim fraud dataset for Tableau Public."
    )
    parser.add_argument(
        "--input",
        default="PS_20174392719_1491204439457_log.csv",
        help="Path to the full PaySim CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        default="paysim_sample.csv",
        help="Path to write the sampled CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=200_000,
        help="Number of non-fraud rows to randomly sample (default: %(default)s)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: %(default)s)",
    )
    return parser.parse_args()


def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"ERROR: Could not find '{path}' in the current folder.")
        print("Make sure the CSV is in the same directory as this script, "
              "or pass the correct path with --input.")
        sys.exit(1)

    print(f"Loading '{path}' ...")
    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"ERROR: Failed to read CSV — {e}")
        sys.exit(1)

    print(f"Loaded {len(df):,} rows and {len(df.columns)} columns.")
    return df


def validate_columns(df: pd.DataFrame) -> None:
    required = {"isFraud", "type", "amount"}
    missing = required - set(df.columns)
    if missing:
        print(f"ERROR: Dataset is missing expected column(s): {missing}")
        print(f"Columns found: {list(df.columns)}")
        sys.exit(1)


def build_sample(df: pd.DataFrame, sample_size: int, random_state: int) -> pd.DataFrame:
    fraud = df[df["isFraud"] == 1]
    non_fraud = df[df["isFraud"] == 0]

    n_available = len(non_fraud)
    n_to_sample = min(sample_size, n_available)
    if n_to_sample < sample_size:
        print(f"NOTE: Requested {sample_size:,} non-fraud rows, but only "
              f"{n_available:,} are available. Using {n_to_sample:,} instead.")

    non_fraud_sample = non_fraud.sample(n=n_to_sample, random_state=random_state)

    combined = (
        pd.concat([fraud, non_fraud_sample])
        .sample(frac=1, random_state=random_state)  # shuffle
        .reset_index(drop=True)
    )
    return combined, fraud


def print_summary(full_df: pd.DataFrame, fraud_df: pd.DataFrame, sample_df: pd.DataFrame) -> None:
    print("\n--- Summary ---")
    print(f"Original dataset:  {len(full_df):,} rows")
    print(f"Fraud cases kept:  {len(fraud_df):,} rows (100% retained)")
    print(f"Final sample size: {len(sample_df):,} rows")
    print(f"Fraud rate in sample: {sample_df['isFraud'].mean() * 100:.3f}%")
    print("\nTransaction type breakdown in sample:")
    print(sample_df["type"].value_counts())
    print("\nFraud count by transaction type:")
    print(sample_df[sample_df["isFraud"] == 1]["type"].value_counts())


def main():
    args = parse_args()

    df = load_data(args.input)
    validate_columns(df)

    sample_df, fraud_df = build_sample(df, args.sample_size, args.random_state)
    print_summary(df, fraud_df, sample_df)

    sample_df.to_csv(args.output, index=False)
    print(f"\nSaved sampled dataset to '{args.output}' "
          f"({os.path.getsize(args.output) / 1_000_000:.1f} MB)")
    print("Load this file into Tableau Public.")


if __name__ == "__main__":
    main()