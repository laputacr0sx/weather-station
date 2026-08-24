# systemd timer

Installed by `bash install.sh` from the repo root. That script fills in the
login name and clone path — do not copy the unit files by hand.

- 05:00–23:45: every 15 minutes
- 00:00–04:00: hourly

Night cadence: edit `OnCalendar=` in `weather-display.timer`, then
`sudo systemctl daemon-reload && sudo systemctl restart weather-display.timer`.
