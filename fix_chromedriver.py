"""
fix_chromedriver.py — clears cached undetected-chromedriver and downloads
the correct driver for the currently installed Chrome version.

Run with: python fix_chromedriver.py
"""
import glob
import os
import shutil
import sys

import undetected_chromedriver as uc

# ── 1. Find and wipe all cached chromedriver executables ──────────────────────
cache_dirs = [
    os.path.expandvars(r"%APPDATA%\undetected_chromedriver"),
    os.path.expandvars(r"%TEMP%"),
    os.path.expandvars(r"%USERPROFILE%\appdata\roaming\undetected_chromedriver"),
]

# Also check wherever uc stores its own data_path
try:
    uc_data = uc.TARGET_VERSION  # may not exist, just try
except Exception:
    pass

removed = []
for d in cache_dirs:
    if not os.path.exists(d):
        continue
    for pattern in ["chromedriver*", "undetected_chromedriver*"]:
        for f in glob.glob(os.path.join(d, pattern)):
            try:
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)
                removed.append(f)
                print(f"  Removed: {f}")
            except Exception as e:
                print(f"  Could not remove {f}: {e}")

if removed:
    print(f"\nCleared {len(removed)} cached file(s).")
else:
    print("No cached files found in standard locations.")

# ── 2. Let uc auto-download the correct driver for this Chrome version ─────────
print("\nDownloading correct ChromeDriver for your Chrome version...")
try:
    driver = uc.Chrome(headless=True, use_subprocess=False)
    driver.get("about:blank")
    driver.quit()
    print("Success! ChromeDriver is now matched to your Chrome version.")
except Exception as e:
    print(f"Error during test launch: {e}")
    print("\nTry running: pip install --upgrade undetected-chromedriver")
    sys.exit(1)

print("\nDone — you can now run batch_fast50.py")
