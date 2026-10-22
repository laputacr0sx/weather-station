# systemd timer

Installed by `bash install.sh` from the repo root. That script fills in the
login name and clone path — do not copy the unit files by hand.

Lifebook checks and serves the image. The Pi downloads it. A full-color
refresh takes about 20 seconds, so most checks leave `current.png` alone.

- Lifebook check: 05:00–23:45 every 15 minutes, and hourly from 00:00–04:00
- Pi fetch: two minutes later (`:02`, `:17`, `:32`, `:47`, and `:02` at night)
- Glass, when rain is under 0.5 mm and no warning changed: hourly by day, every two hours overnight. That refresh swaps the page.
- Glass, when the home cell expects at least 0.5 mm in a half hour: about every 30 minutes
- Glass, when that rain state or an Observatory warning changes: the next check, and not again for 10 minutes. The page stays put.

`weather-publish.service` draws the pages. `weather-serve.service` serves
`/current.png`. `weather-display.service` on the Pi downloads that file and
refreshes the panel. The Lifebook remembers which page comes next and when
the glass last changed. The Pi remembers the hash of the last image it
showed, and skips the refresh when the file is unchanged.

Night cadence: edit `OnCalendar=` in the timer for that machine, then
`sudo systemctl daemon-reload` and restart that timer.
