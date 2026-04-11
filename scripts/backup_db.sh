#!/usr/bin/env sh
set -e

timestamp=$(date +"%Y%m%d_%H%M%S")
backup_dir="${BACKUP_DIR:-./var/backups}"
mkdir -p "$backup_dir"

pg_dump "${DATABASE_URL}" > "${backup_dir}/inventory_${timestamp}.sql"
echo "Backup created: ${backup_dir}/inventory_${timestamp}.sql"
