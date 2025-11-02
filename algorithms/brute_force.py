def brute_force_search(text, pattern):
    n = len(text)
    m = len(pattern)
    count = 0
    comparisons = 0

    for i in range(n - m + 1):
        match = True
        for j in range(m):
            comparisons += 1
            if text[i + j] != pattern[j]:
                match = False
                break
        if match:
            count += 1

    return {
        "found": count > 0,
        "count": count,
        "comparisons": comparisons
    }