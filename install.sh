#!/usr/bin/env bash
# One-shot Pi setup: venv, deps, systemd timer. No path or username editing.
set -euo pipefail

REPO=$(cd "$(dirname "$0")" && pwd)

if [ "$(id -u)" -eq 0 ] && [ -z "${SUDO_USER:-}" ]; then
  echo "Run as a normal user (the script will sudo when it needs to)." >&2
  exit 1
fi

if [ -n "${SUDO_USER:-}" ]; then
  INSTALL_USER=$SUDO_USER
else
  INSTALL_USER=$(id -un)
fi

PYTHON="$REPO/.venv/bin/python"
is_pi() {
  grep -qi "raspberry pi" /proc/device-tree/model 2>/dev/null && return 0
  grep -qi raspberry /proc/cpuinfo 2>/dev/null && return 0
  return 1
}

echo "Repo: $REPO"
echo "User: $INSTALL_USER"

if ! python3 -c "import venv" 2>/dev/null; then
  sudo apt-get update
  sudo apt-get install -y python3-venv python3-pip
fi

if is_pi; then
  sudo apt-get update
  sudo apt-get install -y python3-venv python3-pip python3-spidev python3-gpiozero python3-lgpio
  python3 -m venv --system-site-packages "$REPO/.venv"
else
  python3 -m venv "$REPO/.venv"
fi

"$PYTHON" -m pip install -U pip
"$PYTHON" -m pip install -r "$REPO/src/requirements.txt"

SITE=$("$PYTHON" -c "import site; print(site.getsitepackages()[0])")
echo "$REPO/src" > "$SITE/weather-station.pth"

if is_pi; then
  if [ ! -e /dev/spidev0.0 ] && command -v raspi-config >/dev/null; then
    sudo raspi-config nonint do_spi 0 || true
    echo "SPI enabled. Reboot once if the first refresh cannot open the panel."
  fi
  sudo usermod -aG spi,gpio "$INSTALL_USER" 2>/dev/null || true

  UNIT=$(mktemp)
  sed -e "s|__USER__|$INSTALL_USER|g" \
      -e "s|__REPO__|$REPO|g" \
      -e "s|__PYTHON__|$PYTHON|g" \
      "$REPO/deploy/systemd/weather-display.service.in" > "$UNIT"
  sudo cp "$UNIT" /etc/systemd/system/weather-display.service
  sudo cp "$REPO/deploy/systemd/weather-display.timer" /etc/systemd/system/weather-display.timer
  rm -f "$UNIT"
  sudo systemctl daemon-reload
  sudo systemctl enable --now weather-display.timer
  sudo systemctl start weather-display.service || true
  echo "Timer on. Logs: journalctl -u weather-display.service -n 50"
else
  echo "Not a Raspberry Pi — venv is ready. Preview: $PYTHON -m weather_display.run"
fi
