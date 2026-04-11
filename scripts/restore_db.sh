#!/usr/bin/env sh
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <backup-file.sql>"
  exit 1
fi

psql "${DATABASE_URL}" < "$1"
echo "Restore completed from $1"
