# Weather Station

E-paper dashboard for a Raspberry Pi (Zero 2 W).

## Run on a Pi

```bash
git clone https://github.com/laputacr0sx/weather-station.git
cd weather-station
bash install.sh
```

No path, username, or hardware-flag editing. The script creates a venv,
installs dependencies, enables SPI, writes systemd units for this clone and
login, and starts the timer.

On a Raspberry Pi the panel is used automatically. On a laptop the same
command set stops at a venv; `./.venv/bin/python -m weather_display.run`
opens a preview window.

Refresh: every 15 minutes from 05:00–23:45, hourly overnight.

```bash
systemctl list-timers weather-display.timer
journalctl -u weather-display.service -n 50 --no-pager
```

If SPI was off before install, reboot once so `/dev/spidev0.0` appears.
