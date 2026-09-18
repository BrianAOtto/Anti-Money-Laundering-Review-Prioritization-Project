# AML Transaction Review Prioritization Dashboard

A Power BI dashboard that simulates how an anti-money-laundering (AML) analyst might triage flagged transactions for manual review — built as a scoped, self-directed portfolio project during a career break, using a real-world public dataset.

## Overview

Banks generate far more automated AML alerts than analysts can review line by line. This project simulates a small piece of that workflow: taking a set of system-flagged transactions and building a dashboard that helps an analyst quickly see volume, patterns, and — most importantly — which flagged transactions represent the largest dollar exposure and should be reviewed first.

The project deliberately stays honest about its own limits (see **Limitations & Caveats** below) rather than overstating what a 2–3 day scoped project can claim.

## Dataset

Source: [IBM Transactions for Anti-Money Laundering (AML)](https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml) — a synthetic but realistically-structured transaction dataset released by IBM on Kaggle, simulating interbank payment activity with a small percentage of transactions labeled as laundering.

This project uses the **HI-Small** variant:
- `HI-Small_Trans.csv` — 5,078,345 transactions, of which 5,177 (≈0.10%) are labeled `Is Laundering = 1`
- `HI-Small_accounts.csv` — reference table of accounts by bank

Because the full transaction file is too large to work with comfortably in Power BI Desktop for a scoped project, a **stratified sample** was built using custom Python scripts:
- All 5,177 flagged transactions were kept in full
- Non-flagged transactions were randomly sampled at a 10:1 ratio (non-flagged : flagged), producing 56,947 total transactions
- The accounts file was then filtered down to exactly the (Bank, Account) pairs referenced by the sampled transactions, preserving full referential integrity for the Power BI joins

This sampling approach is disclosed explicitly throughout the dashboard — see **Limitations & Caveats**.

## Methodology / Focus

**Data preparation (Python/pandas):** Three scripts, included in this repo, handle the raw-to-sampled pipeline:
- [`check_laundering_counts.py`](check_laundering_counts.py) — counts total and flagged rows in a transaction file without loading it fully into memory, used to compare the HI-Small and LI-Small variants before choosing HI-Small
- [`filter_aml_transactions.py`](filter_aml_transactions.py) — reads the full transaction file in chunks, keeps every flagged (`Is Laundering = 1`) row, and randomly samples non-flagged rows at a configurable ratio (10:1 by default) to build the working dataset
- [`filter_aml_accounts.py`](filter_aml_accounts.py) — filters the accounts reference table down to exactly the (Bank, Account) pairs referenced by the sampled transactions, preserving full referential integrity for the Power BI joins

**Data modeling (Power BI):** The account lookup table was split into two role-playing dimensions — `Sender` and `Receiver` — each with its own active relationship back to the transactions table, since a single account table can't serve both roles with one relationship. Calculated columns (`RELATED()`) pull sender/receiver bank and entity names into the transaction table for readable reporting.

**Currency normalization:** The raw dataset records `Amount Paid` in the transaction's original currency (USD, Euro, Ruble, Bitcoin, etc.), which makes any cross-currency sort or ranking analytically invalid if left unconverted — a $10,000 transaction and a ¥10,000 transaction are not the same size. A manually-built currency exchange rate lookup table and a calculated `Amount Paid (USD Equivalent)` column normalize every transaction to a common unit, making the prioritization ranking and KPI totals meaningful across currencies.

**Dashboard components:**
- Four KPI cards: Total Transactions, Total Flagged Transactions, Flagged % (labeled as a sampled-dataset statistic), and Total Flagged Amount (USD-normalized)
- Three breakdown/trend charts: flagged transactions by Payment Format, by Payment Currency, and by Transaction Date
- A Top 10 Prioritization Table: the ten highest-value flagged transactions by USD-equivalent amount, meant to represent where a real analyst's attention would go first
- A Payment Currency slicer for interactive filtering across the whole page

## Key Findings

- **ACH dominates flagged volume.** The large majority of flagged transactions in the sample moved through ACH transfers rather than cash, card, or crypto rails.
- **Flagged value is extremely concentrated.** The 10 largest flagged transactions account for roughly 90% of the total flagged dollar value across all 5,177+ flagged transactions in the sample — a long-tail distribution where a handful of very large transactions dominate total exposure. This supports a "review the largest transactions first" triage approach.
- **Counterparty location isn't the same as settlement currency.** The single largest transaction in the dataset (~$15.7bn USD-equivalent) was sent to a bank located in Mexico but settled in Canadian Dollars — a reminder that a receiving bank's country and a transaction's payment currency are two independent fields, and conflating them would produce a wrong read of the data.
- **Flagged activity is not evenly spread over time.** The daily count of flagged transactions in the sample rises, peaks, and declines over the ~2.5-week window covered by the dataset rather than staying flat.

## Limitations & Caveats

This project is a portfolio demonstration, not a production AML tool, and a few things are important to be upfront about:

- **The 9% "Flagged %" figure is a sampling artifact, not a real-world laundering rate.** The dataset was intentionally oversampled 10:1 (non-flagged:flagged) to keep the working file size manageable. The true rate in the underlying full dataset is closer to 0.10%. Any percentage calculated from this sample describes the sample, not real-world prevalence.
- **USD conversion rates are static and illustrative**, entered manually for this project rather than pulled from a live/real-time exchange rate feed. They're accurate enough to demonstrate correct cross-currency methodology, but shouldn't be read as precise financial figures.
- **This is a synthetic dataset.** IBM's AML dataset is generated to simulate realistic transaction patterns, not real bank data, so findings here illustrate an analytical approach rather than real financial intelligence.

## Tools Used

- **Python (pandas)** — data filtering, stratified sampling, referential-integrity-preserving account extraction
- **Power BI Desktop** — data modeling (relationships, role-playing dimensions), DAX (calculated columns and measures), and dashboard/report design

## About Me

[Add your standard "About Me" blurb here, matching your Movie Correlation / Nashville Housing / Covid project READMEs for consistency.]
