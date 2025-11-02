import time
from brute_force import brute_force_search
from kmp import kmp_search
from rabin_karp import rabin_karp_search

def run_all_algorithms(text: str, patterns: list[str]) -> dict:
    results = {}

    start = time.perf_counter()
    bf = brute_force_search(text, patterns)
    bf_time = time.perf_counter() - start

    start = time.perf_counter()
    kmp = kmp_search(text, patterns)
    kmp_time = time.perf_counter() - start

    start = time.perf_counter()
    rk = rabin_karp_search(text, patterns)
    rk_time = time.perf_counter() - start

    results["Brute Force"] = {"time": bf_time, "results": bf}
    results["KMP"] = {"time": kmp_time, "results": kmp}
    results["Rabin-Karp"] = {"time": rk_time, "results": rk}

    return results
