#!/usr/bin/env bash

set -euo pipefail

if ! command -v mc >/dev/null 2>&1; then
  echo "✗ The MinIO client (mc) is required but not installed." >&2
  echo "  Install from https://min.io/download#/mc or run via Docker: docker run --rm -it minio/mc" >&2
  exit 1
fi

: "${AVATAR_STORAGE_ENDPOINT:?Set AVATAR_STORAGE_ENDPOINT in your environment}"
: "${AVATAR_STORAGE_ACCESS_KEY:?Set AVATAR_STORAGE_ACCESS_KEY in your environment}"
: "${AVATAR_STORAGE_SECRET_KEY:?Set AVATAR_STORAGE_SECRET_KEY in your environment}"
: "${AVATAR_STORAGE_BUCKET:?Set AVATAR_STORAGE_BUCKET in your environment}"

BACKUP_DIR=${1:-backups}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_PATH="${BACKUP_DIR}/avatar-backup-${TIMESTAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"

ALIAS="avatar-backup-$$"
TMP_DIR=$(mktemp -d)

cleanup() {
  mc alias rm "${ALIAS}" >/dev/null 2>&1 || true
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

mc alias set "${ALIAS}" "${AVATAR_STORAGE_ENDPOINT}" \
  "${AVATAR_STORAGE_ACCESS_KEY}" "${AVATAR_STORAGE_SECRET_KEY}" >/dev/null

echo "⏳ Syncing bucket ${AVATAR_STORAGE_BUCKET} to temp directory..."
mc cp --recursive "${ALIAS}/${AVATAR_STORAGE_BUCKET}" "${TMP_DIR}/" >/dev/null

echo "🗜️  Creating archive ${ARCHIVE_PATH}..."
tar -czf "${ARCHIVE_PATH}" -C "${TMP_DIR}" .

echo "✅ Avatar backup written to ${ARCHIVE_PATH}"
