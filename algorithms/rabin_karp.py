def rabin_karp_search(text, pattern, base=256, prime=101):
    n = len(text)
    m = len(pattern)
    count = 0
    comparisons = 0

    if m > n:
        return {"found": False, "count": 0, "comparisons": 0}

    h = pow(base, m - 1, prime)
    p_hash = 0
    t_hash = 0

    for i in range(m):
        p_hash = (base * p_hash + ord(pattern[i])) % prime
        t_hash = (base * t_hash + ord(text[i])) % prime

    for i in range(n - m + 1):
        comparisons += 1
        if p_hash == t_hash:
            if text[i:i + m] == pattern:
                count += 1
        if i < n - m:
            t_hash = (base * (t_hash - ord(text[i]) * h) + ord(text[i + m])) % prime
            if t_hash < 0:
                t_hash += prime

    return {
        "found": count > 0,
        "count": count,
        "comparisons": comparisons
    }
