import os
import re
import sys

# === CONFIG ===
FOLDER = r"C:\Users\Muneeb\Desktop\CV_Analyzer\DataSet"   # <-- change this
RECURSIVE = True                    # include subfolders
DRY_RUN = False                     # True = just preview, False = actually delete

# Match "(1)", "(12)", "( 3 )", etc.
pattern = re.compile(r"\(\s*\d+\s*\)")

if not os.path.exists(FOLDER):
    print(f"Path does not exist: {FOLDER}")
    sys.exit(1)

deleted_count = 0
checked_count = 0

def base_without_parens(name):
    """Strip numbered parentheses from base filename."""
    return pattern.sub("", name).strip()

if RECURSIVE:
    walker = os.walk(FOLDER)
else:
    walker = [(FOLDER, [], os.listdir(FOLDER))]

for root, dirs, files in walker:
    # Group by base name (without extension)
    by_base = {}
    for fname in files:
        checked_count += 1
        name, ext = os.path.splitext(fname)
        clean_base = base_without_parens(name)
        key = (clean_base.lower(), ext.lower())
        by_base.setdefault(key, []).append(fname)

    # Process duplicates per (basename, extension)
    for (base, ext), variants in by_base.items():
        if len(variants) > 1:
            # Keep the cleanest one (no parentheses)
            keep = sorted(variants, key=lambda x: pattern.search(x) is not None)[0]
            for f in variants:
                if f != keep:
                    full_path = os.path.join(root, f)
                    if DRY_RUN:
                        print(f"[DRY-RUN] Would delete: {full_path}")
                        deleted_count += 1
                    else:
                        try:
                            os.remove(full_path)
                            print(f"Deleted duplicate: {full_path}")
                            deleted_count += 1
                        except Exception as e:
                            print(f"Failed to delete {full_path}: {e}")

print("\nSummary:")
print(f"  Files checked: {checked_count}")
print(f"  Files deleted (or would be deleted in dry run): {deleted_count}")
