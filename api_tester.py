#!/usr/bin/env python3
import time, json
import requests

def _short_body(text, max_chars=300):
    if text is None:
        return None
    return text[:max_chars] + ("..." if len(text) > max_chars else "")

def run_api_test(api_cfg: dict) -> dict:
    """
    api_cfg example:
    {
      "name": "Get User",
      "method": "GET",
      "url": "https://api.example.com/v1/users/1",
      "headers": {"Authorization": "Bearer <token>"},
      "params": {"verbose": "1"},
      "json": {"k": "v"},
      "timeout": 5,
      "expected_status": 200,
      "verify_tls": true
    }
    """
    method = (api_cfg.get("method") or "GET").upper()
    url = api_cfg["url"]
    headers = api_cfg.get("headers") or {}
    params = api_cfg.get("params") or {}
    json_body = api_cfg.get("json")
    data_body = api_cfg.get("data")
    timeout = api_cfg.get("timeout", 8)
    verify_tls = api_cfg.get("verify_tls", True)
    expected_status = api_cfg.get("expected_status", 200)

    start = time.time()
    error = None
    status_code = None
    body_preview = None

    try:
        resp = requests.request(
            method=method, url=url, headers=headers, params=params, json=json_body,
            data=data_body, timeout=timeout, verify=verify_tls
        )
        status_code = resp.status_code
        body_preview = _short_body(resp.text)
    except Exception as e:
        error = str(e)

    latency_ms = int((time.time() - start) * 1000)

    passed = (error is None) and (status_code == expected_status)

    return {
        "name": api_cfg.get("name", "single-request"),
        "url": url,
        "method": method,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "passed": passed,
        "error": error,
        "body_preview": body_preview
    }

def run_postman_collection(collection_path: str, env: dict | None) -> dict:
    """
    Minimal Postman collection runner (no Newman needed).
    Supports {{var}} replacement using env["values"] or env dict {key:value}.
    Only raw URL + method + headers + body (raw JSON) are supported.
    """
    with open(collection_path, "r", encoding="utf-8") as f:
        col = json.load(f)

    variables = {}
    if env:
        # Postman env format support
        if "values" in env and isinstance(env["values"], list):
            for v in env["values"]:
                if v.get("enabled", True):
                    variables[v["key"]] = v["value"]
        else:
            variables = env

    def substitute(text: str) -> str:
        if not isinstance(text, str):
            return text
        out = text
        for k, v in variables.items():
            out = out.replace("{{" + k + "}}", str(v))
        return out

    items_out = []
    for item in col.get("item", []):
        name = item.get("name", "request")
        req = (item.get("request") or {})
        method = (req.get("method") or "GET").upper()

        url = req.get("url")
        if isinstance(url, dict):
            # Join raw if present, else build
            raw = url.get("raw")
            if raw:
                url = raw
            else:
                host = ".".join(url.get("host", []))
                path = "/".join(url.get("path", []))
                protocol = url.get("protocol", "https")
                query = url.get("query", [])
                qstr = "&".join([f"{q['key']}={q['value']}" for q in query])
                url = f"{protocol}://{host}/{path}" + (f"?{qstr}" if qstr else "")
        url = substitute(url)

        headers = {}
        for h in req.get("header", []):
            if h.get("key"):
                headers[h["key"]] = substitute(h.get("value", ""))

        body_json = None
        body = req.get("body")
        if body and body.get("mode") == "raw" and body.get("raw"):
            raw = substitute(body["raw"])
            try:
                body_json = json.loads(raw)
            except Exception:
                body_json = None  # send as text if needed

        api_cfg = {
            "name": name,
            "method": method,
            "url": url,
            "headers": headers,
            "json": body_json,
            "expected_status": 200,
            "timeout": 10
        }
        res = run_api_test(api_cfg)
        items_out.append(res)

    passed = all(i.get("passed") for i in items_out) if items_out else False
    return {"passed": passed, "items": items_out}
