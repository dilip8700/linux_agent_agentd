#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR=/opt/genai-agent
VENV_DIR=$INSTALL_DIR/.venv
PYTHON=${PYTHON:-python3}

echo "Creating install dir $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
chown root:root "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"

# Detect package manager and install prerequisites (jq, python3-venv if needed)
PKG=""
if command -v dnf >/dev/null 2>&1; then PKG=dnf; fi
if [[ -z "$PKG" ]] && command -v yum >/dev/null 2>&1; then PKG=yum; fi
if [[ -z "$PKG" ]] && command -v apt-get >/dev/null 2>&1; then PKG=apt-get; fi
if [[ -z "$PKG" ]] && command -v zypper >/dev/null 2>&1; then PKG=zypper; fi

install_pkg() {
  case "$PKG" in
    dnf) dnf -y install "$@" || true ;;
    yum) yum -y install "$@" || true ;;
    apt-get) apt-get update -y || true; apt-get install -y "$@" || true ;;
    zypper) zypper --non-interactive install -y "$@" || true ;;
    *) true ;;
  esac
}

if ! command -v jq >/dev/null 2>&1; then install_pkg jq; fi
if ! command -v "$PYTHON" >/dev/null 2>&1; then install_pkg python3 python3-venv; fi

# copy files from current directory (excluding existing venv)
shopt -s dotglob
tmp_sync=$(mktemp -d)
cp -r ./* "$tmp_sync"/ || true
rm -rf "$tmp_sync"/.venv || true
cp -r "$tmp_sync"/* "$INSTALL_DIR"/
rm -rf "$tmp_sync"

# create venv and install deps
"$PYTHON" -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install fastapi uvicorn python-dotenv pyyaml requests google-generativeai

# create env file placeholder if missing
if [ ! -f "$INSTALL_DIR/.env" ]; then
  cat >"$INSTALL_DIR/.env" <<ENV
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
ENV
  chown root:root "$INSTALL_DIR/.env"
  chmod 600 "$INSTALL_DIR/.env"
fi

# create systemd unit (run as root for maximum compatibility)
cat > /etc/systemd/system/genai-agent.service <<UNIT
[Unit]
Description=GenAI Linux Agent
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/genai-agent
Environment="PYTHONPATH=/opt/genai-agent"
EnvironmentFile=/opt/genai-agent/.env
ExecStart=/opt/genai-agent/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --log-level info
Restart=on-failure
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now genai-agent.service

# put agentctl in /usr/local/bin
cp "$INSTALL_DIR/agentctl" /usr/local/bin/agentctl
chmod +x /usr/local/bin/agentctl

echo "Installation complete. Service started. Try: agentctl \"show os version and kernel\""
