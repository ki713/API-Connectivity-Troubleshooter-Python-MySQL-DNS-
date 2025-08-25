#!/usr/bin/env python3
import time, socket
from dns import resolver, exception

def resolve_hostnames(hostnames: list[str], timeout: float = 3.0) -> dict:
    """
    Returns map of hostname -> {resolved: bool, addresses: [], cname: [], latency_ms: int, error: str|None}
    """
    out = {}
    res = resolver.Resolver()
    res.lifetime = timeout
    res.timeout = timeout

    for host in hostnames:
        start = time.time()
        info = {"resolved": False, "addresses": [], "cname": [], "latency_ms": None, "error": None}
        try:
            # A/AAAA
            addrs = []
            for rtype in ["A", "AAAA"]:
                try:
                    ans = res.resolve(host, rtype, raise_on_no_answer=False)
                    if ans:
                        addrs.extend([a.address for a in ans])
                except exception.DNSException:
                    pass
            # CNAME
            try:
                ans_c = res.resolve(host, "CNAME", raise_on_no_answer=False)
                if ans_c:
                    info["cname"] = [str(a.target).rstrip(".") for a in ans_c]
            except exception.DNSException:
                pass

            # Fallback to socket if still empty
            if not addrs:
                try:
                    ai = socket.getaddrinfo(host, None)
                    addrs = list({a[4][0] for a in ai})
                except Exception:
                    pass

            info["addresses"] = list(sorted(set(addrs)))
            info["resolved"] = len(info["addresses"]) > 0
        except Exception as e:
            info["error"] = str(e)
        finally:
            info["latency_ms"] = int((time.time() - start) * 1000)
            out[host] = info

    return out
