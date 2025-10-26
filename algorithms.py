from typing import List, Dict
import time

# -------------------------------------------------------
# Brute Force Algorithm
# -------------------------------------------------------
def brute_force_search(text: str, patterns: List[str]) -> Dict[str, dict]:
    results = {}
    n = len(text)

    for pattern in patterns:
        m = len(pattern)
        occurrences = []
        comparison_count = 0

        for i in range(n - m + 1):
            match = True
            for j in range(m):
                comparison_count += 1
                if text[i + j] != pattern[j]:
                    match = False
                    break
            if match:
                occurrences.append(i)

        results[pattern] = {
            "occurrences": occurrences,
            "comparisons": comparison_count
        }
    return results


# -------------------------------------------------------
# Knuth–Morris–Pratt (KMP) Algorithm
# -------------------------------------------------------
def compute_lps_array(pattern: str) -> List[int]:
    lps = [0] * len(pattern)
    length = 0
    i = 1

    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps


def kmp_search(text: str, patterns: List[str]) -> Dict[str, dict]:
    results = {}
    n = len(text)

    for pattern in patterns:
        m = len(pattern)
        lps = compute_lps_array(pattern)
        i = 0  # index for text
        j = 0  # index for pattern
        occurrences = []
        comparison_count = 0

        while i < n:
            comparison_count += 1
            if text[i] == pattern[j]:
                i += 1
                j += 1

            if j == m:
                occurrences.append(i - j)
                j = lps[j - 1]
            elif i < n and text[i] != pattern[j]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1

        results[pattern] = {
            "occurrences": occurrences,
            "comparisons": comparison_count
        }
    return results


# -------------------------------------------------------
# Rabin–Karp Algorithm
# -------------------------------------------------------
def rabin_karp_search(text: str, patterns: List[str], d: int = 256, q: int = 101) -> Dict[str, dict]:
    results = {}
    n = len(text)

    for pattern in patterns:
        m = len(pattern)
        if m == 0 or n < m:
            results[pattern] = {"occurrences": [], "comparisons": 0}
            continue

        h = pow(d, m - 1, q)
        p = 0  # hash value for a pattern
        t = 0  # hash value for a text window
        comparison_count = 0
        occurrences = []

        # Initial hash computation
        for i in range(m):
            p = (d * p + ord(pattern[i])) % q
            t = (d * t + ord(text[i])) % q

        for i in range(n - m + 1):
            # Compare hash values
            comparison_count += 1
            if p == t:
                # Check for spurious hits
                if text[i:i + m] == pattern:
                    occurrences.append(i)
                    comparison_count += m  # character-by-character confirmation

            if i < n - m:
                # Rolling hash: remove leading char, add trailing char
                t = (d * (t - ord(text[i]) * h) + ord(text[i + m])) % q
                if t < 0:
                    t += q

        results[pattern] = {
            "occurrences": occurrences,
            "comparisons": comparison_count
        }
    return results

def run_all_algorithms(text: str, patterns: list[str]) -> dict:
    """
    Run Brute Force, KMP, and Rabin–Karp on the same text and pattern list.
    Returns a structured dictionary of results and timings.
    """
    results = {}

    # --- Brute Force ---
    start = time.perf_counter()
    bf_result = brute_force_search(text, patterns)
    bf_time = time.perf_counter() - start

    # --- KMP ---
    start = time.perf_counter()
    kmp_result = kmp_search(text, patterns)
    kmp_time = time.perf_counter() - start

    # --- Rabin-Karp ---
    start = time.perf_counter()
    rk_result = rabin_karp_search(text, patterns)
    rk_time = time.perf_counter() - start

    # --- Consolidate ---
    results["Brute Force"] = {
        "time": bf_time,
        "results": bf_result
    }
    results["KMP"] = {
        "time": kmp_time,
        "results": kmp_result
    }
    results["Rabin-Karp"] = {
        "time": rk_time,
        "results": rk_result
    }

    return results
