#!/bin/bash
# AEGIS AI — Service Installer
# Creates systemd user service for persistent background operation

set -e

AEGIS_DIR="$HOME/aegis_omni_xeon"
VENV="$AEGIS_DIR/.venv/bin/python3"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "=== AEGIS AI Service Installer ==="

# Create systemd user service directory
mkdir -p "$SERVICE_DIR"

# Create the daemon service
cat > "$SERVICE_DIR/aegis-daemon.service" << EOF
[Unit]
Description=AEGIS AI Security Daemon — Persistent Threat Monitoring
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=$VENV $AEGIS_DIR/aegis_daemon.py
Restart=always
RestartSec=10
Environment=HOME=$HOME
Environment=PATH=$HOME/aegis_omni_xeon/.venv/bin:/usr/local/bin:/usr/bin:/bin
WorkingDirectory=$AEGIS_DIR

[Install]
WantedBy=default.target
EOF

# Create the API server service
cat > "$SERVICE_DIR/aegis-api.service" << EOF
[Unit]
Description=AEGIS AI REST API Server
After=network-online.target aegis-daemon.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=$VENV -m modules.api_server
Restart=always
RestartSec=10
Environment=HOME=$HOME
Environment=AEGIS_PORT=8443
Environment=PATH=$HOME/aegis_omni_xeon/.venv/bin:/usr/local/bin:/usr/bin:/bin
WorkingDirectory=$AEGIS_DIR

[Install]
WantedBy=default.target
EOF

# Reload systemd, enable and start
systemctl --user daemon-reload
systemctl --user enable aegis-daemon.service
systemctl --user enable aegis-api.service
systemctl --user start aegis-daemon.service
systemctl --user start aegis-api.service

# Enable lingering so services survive logout
loginctl enable-linger $(whoami) 2>/dev/null || echo "Note: lingering may require sudo"

echo ""
echo "=== AEGIS Services Installed ==="
echo "Daemon: systemctl --user status aegis-daemon"
echo "API:    systemctl --user status aegis-api"
echo "Logs:   journalctl --user -u aegis-daemon -f"
echo ""
echo "Services will auto-start on boot and auto-restart on crash."
