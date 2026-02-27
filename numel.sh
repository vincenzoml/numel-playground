#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UV_ROOT="${ROOT_DIR}/.numel/uv"
export UV_CACHE_DIR="${UV_CACHE_DIR:-${ROOT_DIR}/.numel/cache}"
export UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-${ROOT_DIR}/.numel/python}"
UV_BIN=""

resolve_uv_bin() {
  if [[ -x "${UV_ROOT}/uv" ]]; then
    UV_BIN="${UV_ROOT}/uv"
  elif [[ -x "${UV_ROOT}/bin/uv" ]]; then
    UV_BIN="${UV_ROOT}/bin/uv"
  fi
}

resolve_uv_bin
if [[ -z "${UV_BIN}" ]]; then
  mkdir -p "${UV_ROOT}"
  if command -v curl >/dev/null 2>&1; then
    env UV_UNMANAGED_INSTALL="${UV_ROOT}" sh -c "$(curl -LsSf https://astral.sh/uv/install.sh)"
  elif command -v wget >/dev/null 2>&1; then
    env UV_UNMANAGED_INSTALL="${UV_ROOT}" sh -c "$(wget -qO- https://astral.sh/uv/install.sh)"
  else
    echo "error: curl or wget is required to install uv" >&2
    exit 1
  fi
  resolve_uv_bin
fi

if [[ -z "${UV_BIN}" ]]; then
  echo "error: uv was installed but binary not found under ${UV_ROOT}" >&2
  exit 1
fi

"${UV_BIN}" python install 3.14
export UV_BIN
exec "${UV_BIN}" run --python 3.14 "${ROOT_DIR}/bootstrap.py" "$@"
