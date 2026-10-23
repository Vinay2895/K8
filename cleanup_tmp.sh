
#!/usr/bin/env bash
set -Eeuo pipefail

TARGET_DIR="/tmp"
THRESHOLD_MB=200
RETENTION_DAYS=3
DRY_RUN="${DRY_RUN:-1}"

LOG_FILE="/var/log/tmp-cleanup.log"

# Safety check: only allow cleanup of /tmp
if [[ "$TARGET_DIR" != "/tmp" ]]; then
    echo "ERROR: Unexpected target directory."
    exit 1
fi

# Calculate directory usage in MB
USAGE_MB=$(du -sm -- "$TARGET_DIR" | awk '{print $1}')

echo "[$(date '+%F %T')] /tmp usage: ${USAGE_MB} MB" \
    | tee -a "$LOG_FILE"

# Run cleanup only when usage exceeds 200 MB
if (( USAGE_MB <= THRESHOLD_MB )); then
    echo "Usage is within threshold. No cleanup needed." \
        | tee -a "$LOG_FILE"
    exit 0
fi

echo "Usage exceeds ${THRESHOLD_MB} MB. Checking old files..." \
    | tee -a "$LOG_FILE"

# Delete regular files older than 3 days.
# Dry-run mode lists eligible files without deleting them.
if [[ "$DRY_RUN" == "1" ]]; then
    find "$TARGET_DIR" -xdev -type f \
        -mmin +$((RETENTION_DAYS * 24 * 60)) -print \
        | tee -a "$LOG_FILE"
    echo "DRY RUN: No files were deleted." | tee -a "$LOG_FILE"
else
    find "$TARGET_DIR" -xdev -type f \
        -mmin +$((RETENTION_DAYS * 24 * 60)) \
        -print -delete \
        | tee -a "$LOG_FILE"
    echo "Cleanup completed." | tee -a "$LOG_FILE"
fi
