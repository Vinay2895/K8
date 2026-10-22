
#!/usr/bin/env python3

import os
import subprocess
import time
import logging

TARGET_DIR = "/tmp"
THRESHOLD_MB = 200
RETENTION_DAYS = 3
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"

LOG_FILE = "/var/log/tmp-cleanup.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)


def get_usage_mb():
    result = subprocess.run(
        ["du", "-sm", "--", TARGET_DIR],
        check=True,
        capture_output=True,
        text=True
    )
    return int(result.stdout.split()[0])


def cleanup_tmp():
    if TARGET_DIR != "/tmp":
        raise ValueError("Unexpected target directory")

    usage_mb = get_usage_mb()
    logging.info("/tmp usage: %s MB", usage_mb)

    if usage_mb <= THRESHOLD_MB:
        logging.info("Below threshold; no cleanup required.")
        return

    cutoff = time.time() - RETENTION_DAYS * 24 * 60 * 60
    deleted_count = 0

    # Walk /tmp without following symbolic links or crossing filesystems.
    root_device = os.stat(TARGET_DIR).st_dev

    for current_dir, dirs, files in os.walk(
        TARGET_DIR, topdown=True, followlinks=False
    ):
        dirs[:] = [
            name for name in dirs
            if not os.path.islink(os.path.join(current_dir, name))
            and os.stat(os.path.join(current_dir, name)).st_dev
            == root_device
        ]

        for name in files:
            path = os.path.join(current_dir, name)

            try:
                if os.path.islink(path):
                    continue

                info = os.stat(path, follow_symlinks=False)

                if not os.path.isfile(path):
                    continue

                if info.st_dev != root_device or info.st_mtime >= cutoff:
                    continue

                if DRY_RUN:
                    logging.info("WOULD DELETE: %s", path)
                else:
                    os.unlink(path)
                    deleted_count += 1
                    logging.info("DELETED: %s", path)

            except FileNotFoundError:
                # A temporary file may disappear during the scan.
                continue
            except OSError as exc:
                logging.warning("Could not process %s: %s", path, exc)

    if DRY_RUN:
        logging.info("DRY RUN completed; no files deleted.")
    else:
        logging.info("Cleanup completed; files deleted: %s", deleted_count)


if __name__ == "__main__":
    cleanup_tmp()
