#!/usr/bin/env python3
import time, json
import mysql.connector

def verify_mysql_state(db_cfg: dict) -> dict:
    """
    db_cfg example:
    {
      "name": "user-sync-check",
      "host": "127.0.0.1",
      "port": 3306,
      "user": "root",
      "password": "secret",
      "database": "appdb",
      "query": "SELECT id, status FROM users WHERE id = 1",
      "expect_rows_min": 1
    }
    """
    name = db_cfg.get("name", "mysql-check")
    start = time.time()
    error = None
    rowcount = 0
    sample = None

    try:
        conn = mysql.connector.connect(
            host=db_cfg.get("host", "127.0.0.1"),
            port=db_cfg.get("port", 3306),
            user=db_cfg["user"],
            password=db_cfg["password"],
            database=db_cfg.get("database")
        )
        cur = conn.cursor(dictionary=True)
        cur.execute(db_cfg["query"])
        rows = cur.fetchall()
        rowcount = len(rows)
        sample = rows[0] if rows else None
        cur.close()
        conn.close()
    except Exception as e:
        error = str(e)

    latency_ms = int((time.time() - start) * 1000)
    expect_min = db_cfg.get("expect_rows_min", 1)
    passed = (error is None) and (rowcount >= expect_min)

    return {
        "name": name,
        "rowcount": rowcount,
        "sample": sample,
        "latency_ms": latency_ms,
        "passed": passed,
        "error": error
    }
