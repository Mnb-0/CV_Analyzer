# algorithms.py
# Contains all string-searching algorithm implementations.

def _is_word_boundary(text, start, end):
    """Helper function to check for whole-word matches."""
    before = text[start - 1] if start > 0 else " "
    after = text[end] if end < len(text) else " "
    return (not before.isalnum()) and (not after.isalnum())

def brute_force_search(text, pattern):
    """Finds a pattern in text using the Brute Force method."""
    n = len(text); m = len(pattern)
    if m == 0: return 0, 0
    if n < m: return 0, 0
    
    comparisons = 0
    found_count = 0
    
    for i in range(n - m + 1):
        j = 0
        while j < m:
            comparisons += 1
            if text[i + j] != pattern[j]:
                break
            j += 1
        
        if j == m and _is_word_boundary(text, i, i + m):
            found_count += 1
            
    return found_count, comparisons

def rabin_karp_search(text, pattern):
    """Finds a pattern in text using the Rabin-Karp method."""
    n = len(text); m = len(pattern)
    if m == 0: return 0, 0
    if n < m: return 0, 0

    comparisons = 0
    found_count = 0
    base = 256
    mod = 2305843009213693951  # A large prime
    
    pat_hash = 0
    win_hash = 0
    
    for i in range(m):
        pat_hash = (pat_hash * base + ord(pattern[i])) % mod
        win_hash = (win_hash * base + ord(text[i])) % mod
        
    power = pow(base, m - 1, mod)

    if pat_hash == win_hash:
        match = True
        for j in range(m):
            comparisons += 1
            if text[j] != pattern[j]:
                match = False
                break
        if match and _is_word_boundary(text, 0, m):
            found_count += 1

    for i in range(1, n - m + 1):
        lead_char_val = ord(text[i - 1])
        new_char_val = ord(text[i + m - 1])
        
        win_hash = (win_hash - (lead_char_val * power) % mod + mod) % mod
        win_hash = (win_hash * base) % mod
        win_hash = (win_hash + new_char_val) % mod

        if win_hash == pat_hash:
            match = True
            for j in range(m):
                comparisons += 1
                if text[i + j] != pattern[j]:
                    match = False
                    break
            if match and _is_word_boundary(text, i, i + m):
                found_count += 1
                
    return found_count, comparisons

def kmp_search(text, pattern):
    """Finds a pattern in text using the Knuth-Morris-Pratt (KMP) method."""
    n = len(text); m = len(pattern)
    if m == 0: return 0, 0
    if n < m: return 0, 0
    
    # Build Longest Proper Prefix which is also Suffix (LPS) array
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
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

    comparisons = 0
    found_count = 0
    i = 0  # index for text
    j = 0  # index for pattern
    
    while i < n:
        comparisons += 1
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == m:
                if _is_word_boundary(text, i - j, i):
                    found_count += 1
                j = lps[j - 1]
        else:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
                
    return found_count, comparisons