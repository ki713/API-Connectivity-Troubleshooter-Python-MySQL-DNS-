#!/usr/bin/env python3
"""
Orchestrates API, DB and DNS checks from a single config file.
Generates console summary + CSV/JSON reports.
"""

import argparse, json, time, os, sys, traceback
import pandas as pd
from datetime import datetime
from api_tester import run_api_test, run_postman_collection
from db_checker import verify_mysql_state
from dns_checker import resolve_hostnames

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def ensure_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="API Connectivity Troubleshooter")
    parser.add_argument("--config", required=True, help="Path to config JSON")
    parser.add_argument("--postman", help="Optional Postman collection JSON path")
    parser.add_argument("--env", help="Optional Postman environment JSON path (key/values)")
    parser.add_argument("--out-json", default="report.json", help="Output JSON report")
    parser.add_argument("--out-csv", default="report.csv", help="Output CSV report (flat)")
    args = parser.parse_args()

    cfg = read_json(args.config)
    started = datetime.utcnow().isoformat() + "Z"

    results = {
        "meta": {
            "started_at": started,
            "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
            "tool": "api-connectivity-troubleshooter",
            "version": "1.0.0"
        },
        "dns": {},
        "api": {},
        "db": {},
        "errors": []
    }

    # DNS
    try:
        hostnames = cfg.get("dns", {}).get("hostnames", [])
        if hostnames:
            results["dns"] = resolve_hostnames(hostnames, timeout=cfg.get("dns", {}).get("timeout", 3.0))
    except Exception as e:
        results["errors"].append(f"DNS error: {e}")
        traceback.print_exc()

    # API
    try:
        api_cfg = cfg.get("api", {})
        if args.postman or api_cfg.get("postman_collection"):
            pm_path = args.postman or api_cfg.get("postman_collection")
            pm_env = args.env or api_cfg.get("postman_env")
            pm_env_data = read_json(pm_env) if pm_env and os.path.exists(pm_env) else None
            results["api"] = run_postman_collection(pm_path, pm_env_data)
        elif api_cfg:
            results["api"] = run_api_test(api_cfg)
    except Exception as e:
        results["errors"].append(f"API error: {e}")
        traceback.print_exc()

    # DB
    try:
        db_cfg = cfg.get("db", {})
        if db_cfg:
            results["db"] = verify_mysql_state(db_cfg)
    except Exception as e:
        results["errors"].append(f"DB error: {e}")
        traceback.print_exc()

    results["meta"]["finished_at"] = datetime.utcnow().isoformat() + "Z"

    # Persist JSON
    ensure_dir(args.out_json)
    write_json(args.out_json, results)

    # Flatten to CSV
    rows = []
    # DNS rows
    for host, info in results.get("dns", {}).items():
        rows.append({
            "component": "dns",
            "name": host,
            "status": "ok" if info.get("resolved") else "fail",
            "details": json.dumps(info, ensure_ascii=False),
            "latency_ms": info.get("latency_ms", "")
        })
    # API rows
    api_block = results.get("api", {})
    if api_block:
        if "items" in api_block:  # Postman run
            for item in api_block["items"]:
                rows.append({
                    "component": "api",
                    "name": item.get("name"),
                    "status": "ok" if item.get("passed") else "fail",
                    "details": json.dumps({
                        "status_code": item.get("status_code"),
                        "latency_ms": item.get("latency_ms"),
                        "error": item.get("error"),
                        "url": item.get("url")
                    }, ensure_ascii=False),
                    "latency_ms": item.get("latency_ms", "")
                })
        else:
            rows.append({
                "component": "api",
                "name": api_block.get("name", "single-request"),
                "status": "ok" if api_block.get("passed") else "fail",
                "details": json.dumps({
                    "status_code": api_block.get("status_code"),
                    "latency_ms": api_block.get("latency_ms"),
                    "error": api_block.get("error"),
                    "url": api_block.get("url")
                }, ensure_ascii=False),
                "latency_ms": api_block.get("latency_ms", "")
            })
    # DB rows
    db_block = results.get("db", {})
    if db_block:
        rows.append({
            "component": "db",
            "name": db_block.get("name", "mysql-check"),
            "status": "ok" if db_block.get("passed") else "fail",
            "details": json.dumps({
                "rowcount": db_block.get("rowcount"),
                "sample": db_block.get("sample"),
                "error": db_block.get("error")
            }, ensure_ascii=False),
            "latency_ms": db_block.get("latency_ms", "")
        })

    df = pd.DataFrame(rows, columns=["component", "name", "status", "details", "latency_ms"])
    df.to_csv(args.out_csv, index=False)

    # Console summary
    print("=== API Connectivity Troubleshooter ===")
    for r in rows:
        print(f"[{r['component'].upper():3}] {r['name']:<30} {r['status'].upper():<5} {r['latency_ms']} ms")
    if results["errors"]:
        print("\nErrors captured:")
        for e in results["errors"]:
            print(" -", e)
    print(f"\nSaved: {args.out_json} and {args.out_csv}")

if __name__ == "__main__":
    main()
