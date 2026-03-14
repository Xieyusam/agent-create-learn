#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/.venv}"
CONFIG_FILE="${CONFIG_FILE:-$SCRIPT_DIR/config.yaml}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-$SCRIPT_DIR/requirements.txt}"
REQUIREMENTS_STAMP="${VENV_DIR}/.requirements.sha256"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env}"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=11

log() {
  printf '[travel-planner] %s\n' "$1"
}

fail() {
  printf '[travel-planner] Error: %s\n' "$1" >&2
  exit 1
}

is_python_compatible() {
  local candidate="$1"
  "${candidate}" - <<PY
import sys
raise SystemExit(0 if sys.version_info >= (${MIN_PYTHON_MAJOR}, ${MIN_PYTHON_MINOR}) else 1)
PY
}

find_python() {
  local candidate

  for candidate in "${PYTHON_BIN:-}" python3.11 python3.10 python3; do
    [[ -n "${candidate}" ]] || continue
    command -v "${candidate}" >/dev/null 2>&1 || continue
    if is_python_compatible "${candidate}"; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  return 1
}

venv_is_usable() {
  local venv_python="$1"
  local venv_pip="$2"

  [[ -x "${venv_python}" ]] || return 1
  [[ -x "${venv_pip}" ]] || return 1
  is_python_compatible "${venv_python}" || return 1
  "${venv_pip}" --version >/dev/null 2>&1 || return 1
}

validate_config() {
  TRAVEL_PLANNER_CONFIG_PATH="${CONFIG_FILE}" "${PYTHON}" - <<'PY'
import os
from src.config import ConfigManager

try:
    ConfigManager(config_path=os.environ["TRAVEL_PLANNER_CONFIG_PATH"])
except Exception as exc:
    raise SystemExit(str(exc))
PY
}

requirements_hash() {
  REQUIREMENTS_PATH="${REQUIREMENTS_FILE}" "${PYTHON}" - <<'PY'
import hashlib
import os
from pathlib import Path

requirements_path = Path(os.environ["REQUIREMENTS_PATH"])
print(hashlib.sha256(requirements_path.read_bytes()).hexdigest())
PY
}

missing_config_env_vars() {
  CONFIG_PATH="${CONFIG_FILE}" ENV_FILE_PATH="${ENV_FILE}" "${PYTHON}" - <<'PY'
import os
import re
from pathlib import Path

from dotenv import dotenv_values
import yaml

PLACEHOLDER_VALUES = {
    "",
    "your-api-key",
    "your-api-key-here",
    "your-embedding-api-key",
    "replace-me",
    "changeme",
}

def is_missing(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDER_VALUES

def collect_placeholders(value):
    placeholders = set()
    if isinstance(value, dict):
        for item in value.values():
            placeholders.update(collect_placeholders(item))
    elif isinstance(value, list):
        for item in value:
            placeholders.update(collect_placeholders(item))
    elif isinstance(value, str):
        match = re.fullmatch(r"\$\{([A-Z0-9_]+)\}", value.strip())
        if match:
            placeholders.add(match.group(1))
    return placeholders

config_payload = yaml.safe_load(Path(os.environ["CONFIG_PATH"]).read_text(encoding="utf-8")) or {}
placeholders = sorted(collect_placeholders(config_payload))
env_file_path = Path(os.environ["ENV_FILE_PATH"])
env_values = {}

if env_file_path.exists():
    env_values = {
        key: (value or "").strip()
        for key, value in dotenv_values(env_file_path).items()
        if key
    }

missing = []
for name in placeholders:
    env_value = os.getenv(name, "").strip()
    file_value = env_values.get(name, "").strip()
    if is_missing(env_value) and is_missing(file_value):
        missing.append(name)

print("\n".join(missing))
PY
}

ensure_env_file() {
  if [[ -f "${ENV_FILE}" ]]; then
    return
  fi

  if [[ -f "${SCRIPT_DIR}/.env.example" ]]; then
    cp "${SCRIPT_DIR}/.env.example" "${ENV_FILE}"
    log "Created .env from .env.example"
    return
  fi

  : > "${ENV_FILE}"
  log "Created empty .env"
}

upsert_env_var() {
  ENV_FILE_PATH="${ENV_FILE}" ENV_NAME="$1" ENV_VALUE="$2" "${PYTHON}" - <<'PY'
import os
from pathlib import Path

env_path = Path(os.environ["ENV_FILE_PATH"])
env_name = os.environ["ENV_NAME"]
env_value = os.environ["ENV_VALUE"].replace("\n", "").strip()

lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
updated = False
new_lines = []

for line in lines:
    if line.startswith(f"{env_name}="):
        new_lines.append(f"{env_name}={env_value}")
        updated = True
    else:
        new_lines.append(line)

if not updated:
    if new_lines and new_lines[-1] != "":
        new_lines.append("")
    new_lines.append(f"{env_name}={env_value}")

env_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
PY
}

prompt_for_missing_env_vars() {
  local missing_vars_text=""
  local old_ifs="${IFS}"
  local var_name
  local var_value

  missing_vars_text="$(missing_config_env_vars)"
  if [[ -z "${missing_vars_text}" ]]; then
    return 0
  fi

  ensure_env_file

  IFS=$'\n'
  for var_name in ${missing_vars_text}; do
    [[ -n "${var_name}" ]] || continue

    if [[ -t 0 ]]; then
      printf '[travel-planner] Enter value for %s: ' "${var_name}"
    else
      log "Reading value for ${var_name} from standard input"
    fi

    IFS= read -r var_value || var_value=""

    if [[ -t 0 ]]; then
      printf '\n'
    fi

    [[ -n "${var_value}" ]] || fail "Missing configuration value ${var_name}. Set it in ${ENV_FILE} or export it before running the script."

    upsert_env_var "${var_name}" "${var_value}"
    export "${var_name}=${var_value}"
    log "Saved ${var_name} to .env"
  done
  IFS="${old_ifs}"
}

sync_dependencies() {
  local expected_hash
  local installed_hash=""

  expected_hash="$(requirements_hash)"
  if [[ -f "${REQUIREMENTS_STAMP}" ]]; then
    installed_hash="$(<"${REQUIREMENTS_STAMP}")"
  fi

  if [[ "${installed_hash}" == "${expected_hash}" ]]; then
    log "Dependencies are already up to date"
    return
  fi

  log "Installing dependencies"
  "${PYTHON}" -m pip install --upgrade pip
  "${PIP}" install -r "${REQUIREMENTS_FILE}"
  printf '%s\n' "${expected_hash}" > "${REQUIREMENTS_STAMP}"
}

report_memory_mode() {
  TRAVEL_PLANNER_CONFIG_PATH="${CONFIG_FILE}" "${PYTHON}" - <<'PY'
import os

from langgraph.checkpoint.redis import RedisSaver

from src.config import ConfigManager

try:
    config = ConfigManager(config_path=os.environ["TRAVEL_PLANNER_CONFIG_PATH"]).get_memory_config()
    RedisSaver(redis_url=config.redis_url).setup()
    print("[travel-planner] Redis is reachable. RedisSaver persistence will be enabled.")
except Exception:
    print("[travel-planner] Redis is not reachable. The app will fall back to in-memory session storage for this run.")
PY
}

PYTHON_BIN_RESOLVED="$(find_python)" || fail "Python 3.11+ is required."
[[ -f "${REQUIREMENTS_FILE}" ]] || fail "Requirements file not found: ${REQUIREMENTS_FILE}"
[[ -f "${CONFIG_FILE}" ]] || fail "Config file not found: ${CONFIG_FILE}"

if ! venv_is_usable "${VENV_DIR}/bin/python" "${VENV_DIR}/bin/pip"; then
  log "Creating or repairing virtual environment in ${VENV_DIR}"
  rm -rf "${VENV_DIR}"
  "${PYTHON_BIN_RESOLVED}" -m venv "${VENV_DIR}" || fail "Failed to create virtual environment."
fi

PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"

sync_dependencies
prompt_for_missing_env_vars

log "Validating configuration"
(cd "${SCRIPT_DIR}" && validate_config) || fail "Configuration validation failed. Check config.yaml and .env."

report_memory_mode

log "Starting application"
cd "${SCRIPT_DIR}"
export TRAVEL_PLANNER_CONFIG_PATH="${CONFIG_FILE}"
exec "${PYTHON}" main.py
