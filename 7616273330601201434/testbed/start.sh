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
log(){ printf '[ecom-cs] %s\n' "$1"; }
fail(){ printf '[ecom-cs] Error: %s\n' "$1" >&2; exit 1; }
is_python_compatible(){ local c="$1"; "${c}" - <<PY
import sys; raise SystemExit(0 if sys.version_info >= (${MIN_PYTHON_MAJOR}, ${MIN_PYTHON_MINOR}) else 1)
PY
}
find_python(){ local c; for c in "${PYTHON_BIN:-}" python3.12 python3.11 python3 python; do [ -n "${c}" ] || continue; command -v "${c}" >/dev/null 2>&1 || continue; if is_python_compatible "${c}"; then printf '%s\n' "${c}"; return 0; fi; done; return 1; }
venv_python_path(){ if [ -x "${VENV_DIR}/bin/python" ]; then printf '%s\n' "${VENV_DIR}/bin/python"; elif [ -x "${VENV_DIR}/Scripts/python.exe" ]; then printf '%s\n' "${VENV_DIR}/Scripts/python.exe"; else printf '%s\n' "${VENV_DIR}/bin/python"; fi; }
venv_pip_path(){ if [ -x "${VENV_DIR}/bin/pip" ]; then printf '%s\n' "${VENV_DIR}/bin/pip"; elif [ -x "${VENV_DIR}/Scripts/pip.exe" ]; then printf '%s\n' "${VENV_DIR}/Scripts/pip.exe"; else printf '%s\n' "${VENV_DIR}/bin/pip"; fi; }
venv_is_usable(){ local vp="$1" vpp="$2"; [ -x "${vp}" ] || return 1; [ -x "${vpp}" ] || return 1; is_python_compatible "${vp}" || return 1; "${vpp}" --version >/dev/null 2>&1 || return 1; }
requirements_hash(){ REQUIREMENTS_PATH="${REQUIREMENTS_FILE}" "${PYTHON}" - <<'PY'
import hashlib, os
from pathlib import Path
rp=Path(os.environ["REQUIREMENTS_PATH"]); print(hashlib.sha256(rp.read_bytes()).hexdigest())
PY
}
ensure_env_file(){ if [ -f "${ENV_FILE}" ]; then return; fi; if [ -f "${SCRIPT_DIR}/.env.example" ]; then cp "${SCRIPT_DIR}/.env.example" "${ENV_FILE}"; log "Created .env from .env.example"; else : > "${ENV_FILE}"; log "Created empty .env"; fi; }
missing_config_env_vars(){ CONFIG_PATH="${CONFIG_FILE}" ENV_FILE_PATH="${ENV_FILE}" "${PYTHON}" - <<'PY'
import os,re,yaml
from pathlib import Path
try:
    from dotenv import dotenv_values
except Exception:
    def dotenv_values(_): return {}
PLACEHOLDERS={"","your-api-key","your_api_key_here","your-api-key-here","replace-me","changeme"}
def is_missing(v:str)->bool: return (v or "").strip().lower() in PLACEHOLDERS
def collect(value):
    s=set()
    if isinstance(value,dict):
        for v in value.values(): s.update(collect(v))
    elif isinstance(value,list):
        for v in value: s.update(collect(v))
    elif isinstance(value,str):
        m=re.fullmatch(r"\$\{([A-Z0-9_]+)\}",value.strip()); 
        if m: s.add(m.group(1))
    return s
payload=yaml.safe_load(Path(os.environ["CONFIG_PATH"]).read_text(encoding="utf-8")) or {}
names=sorted(collect(payload))
env_file=Path(os.environ["ENV_FILE_PATH"])
file_vals=dotenv_values(env_file) if env_file.exists() else {}
missing=[]
for n in names:
    ev=os.getenv(n,"").strip()
    fv=str(file_vals.get(n,"")).strip()
    if is_missing(ev) and is_missing(fv): missing.append(n)
print("\n".join(missing))
PY
}
upsert_env_var(){ ENV_FILE_PATH="${ENV_FILE}" ENV_NAME="$1" ENV_VALUE="$2" "${PYTHON}" - <<'PY'
import os
from pathlib import Path
p=Path(os.environ["ENV_FILE_PATH"]); n=os.environ["ENV_NAME"]; v=os.environ["ENV_VALUE"].replace("\n","").strip()
lines=p.read_text(encoding="utf-8").splitlines() if p.exists() else []
u=False; out=[]
for line in lines:
    if line.startswith(f"{n}="): out.append(f"{n}={v}"); u=True
    else: out.append(line)
if not u:
    if out and out[-1]!="": out.append("")
    out.append(f"{n}={v}")
p.write_text("\n".join(out).rstrip()+"\n",encoding="utf-8")
PY
}
prompt_for_missing_env_vars(){ local t v n oldifs="${IFS}"; t="$(missing_config_env_vars)"; [ -z "${t}" ] && return 0; ensure_env_file; IFS=$'\n'; for n in ${t}; do [ -n "${n}" ] || continue; if [[ -t 0 ]]; then printf '[ecom-cs] Enter value for %s: ' "${n}"; else log "Reading value for ${n} from stdin"; fi; IFS= read -r v || v=""; if [[ -t 0 ]]; then printf '\n'; fi; [ -n "${v}" ] || fail "Missing configuration value ${n}"; upsert_env_var "${n}" "${v}"; export "${n}=${v}"; log "Saved ${n} to .env"; done; IFS="${oldifs}"; }
validate_config(){ APP_CONFIG_PATH="${CONFIG_FILE}" "${PYTHON}" - <<'PY'
import os,yaml
from pathlib import Path
p=os.environ.get("APP_CONFIG_PATH"); cfg=yaml.safe_load(Path(p).read_text(encoding="utf-8"))
if not isinstance(cfg,dict): raise SystemExit("配置文件格式错误")
cm=cfg.get("current_model"); models=cfg.get("models") or {}
if not cm or cm not in models: raise SystemExit("配置缺失或未定义的 current_model")
m=models.get(cm) or {}
api=str(m.get("api_key") or "").strip(); model=str(m.get("model") or "").strip(); base=str(m.get("base_url") or "").strip()
if not api or api.lower() in {"your-api-key","your_api_key_here","your-api-key-here","replace-me","changeme"} or api.startswith("${}"):
    raise SystemExit("缺少必须的环境变量或 api_key 未设置")
if not model: raise SystemExit("模型配置缺少 model")
if not base: raise SystemExit("模型配置缺少 base_url")
PY
}
PYTHON_BIN_RESOLVED="$(find_python)" || fail "Python 3.11+ is required."
[ -f "${REQUIREMENTS_FILE}" ] || fail "Requirements file not found"
[ -f "${CONFIG_FILE}" ] || fail "Config file not found"
if [ -d "${VENV_DIR}" ]; then true; else log "Creating virtual environment in ${VENV_DIR}"; "${PYTHON_BIN_RESOLVED}" -m venv "${VENV_DIR}" || fail "Failed to create virtual environment"; fi
PYTHON="$(venv_python_path)"
PIP="$(venv_pip_path)"
if ! venv_is_usable "${PYTHON}" "${PIP}"; then rm -rf "${VENV_DIR}"; "${PYTHON_BIN_RESOLVED}" -m venv "${VENV_DIR}" || fail "Failed to create virtual environment"; PYTHON="$(venv_python_path)"; PIP="$(venv_pip_path)"; fi
exp="$(requirements_hash)"; inst=""; [ -f "${REQUIREMENTS_STAMP}" ] && inst="$(<"${REQUIREMENTS_STAMP}")" || true
if [ "${inst}" != "${exp}" ]; then log "Installing dependencies"; "${PYTHON}" -m pip install --upgrade pip; "${PIP}" install -r "${REQUIREMENTS_FILE}"; printf '%s\n' "${exp}" > "${REQUIREMENTS_STAMP}"; else log "Dependencies are already up to date"; fi
prompt_for_missing_env_vars
log "Validating configuration"
(cd "${SCRIPT_DIR}" && validate_config) || fail "Configuration validation failed"
log "Starting application"
cd "${SCRIPT_DIR}"
export APP_CONFIG_PATH="${CONFIG_FILE}"
exec "${PYTHON}" main.py
