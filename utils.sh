#!/bin/bash
# Wrapper to run all checks and generate reports
set -e

CONFIG=${1:-config.example.json}
OUT_JSON=${2:-report.json}
OUT_CSV=${3:-report.csv}

echo "Using config: $CONFIG"
python3 troubleshoot.py --config "$CONFIG" --out-json "$OUT_JSON" --out-csv "$OUT_CSV"
