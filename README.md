# Weather Station

Home dashboard for a Raspberry Pi (Zero 2 W) and a Waveshare 7.3-inch E6
panel (E Ink Spectra 6, 800×480, six colors). The glass shows one page at a
time, in Chinese. Both pages show the home grid cell of the official
two-hour rainfall nowcast, so the next two hours stay visible whichever
page is up. The room page is the six Home Assistant rooms plus that
forecast. The forecast page adds the five-day outlook, wind, UV, and
sunrise. An Observatory warning appears on both pages only while one is
in force.

The Lifebook (the Home Assistant machine) draws both pages. The Pi only
downloads the finished PNG and refreshes the glass. A full-color refresh
takes about 20 seconds, and the picture stays on the glass with no power
after that. The Lifebook still checks on its timer, and it replaces the
PNG only when that refresh is worth the flash:

- Rain at the home cell reaches 0.5 mm in a half hour, or leaves that state, or an Observatory warning changes. The next check publishes it, and never twice inside 10 minutes.
- While that rain continues, the glass updates about every 30 minutes so the countdown stays current.
- Otherwise the glass updates hourly from 05:00 through 23:59, and every two hours from midnight to 05:00. That update also swaps the page.
- A failed warning download keeps the picture already published. Trace rain under 0.5 mm waits for the quiet interval.

If the download fails, or the PNG has not changed, the Pi does not refresh.

Put secrets in a gitignored `.env` at the repo root. The Lifebook copy
holds the Home Assistant token. The Pi copy does not.

```bash
# Lifebook, next to Home Assistant
HA_URL=http://192.168.1.54:8123
HA_TOKEN=your-long-lived-token
DASHBOARD_TOKEN=a-long-random-string

# Raspberry Pi
DASHBOARD_URL=http://192.168.1.54:8765/current.png
DASHBOARD_TOKEN=a-long-random-string
```

## Lifebook

```bash
git clone https://github.com/laputacr0sx/weather-station.git
cd weather-station
bash install.sh
```

On a systemd machine that is not a Pi, that starts two units. One checks
every 15 minutes from 05:00–23:45 and hourly overnight, and writes a new
PNG only when the rule above says so. The other serves `GET /current.png`
on port 8765. The request needs `Authorization: Bearer <DASHBOARD_TOKEN>`.

## Raspberry Pi

Clone the same repo, put the Pi `.env` in place, and run `bash install.sh`.
The script enables SPI and a timer that fetches the image at two minutes
past each Lifebook render. Reboot once if `/dev/spidev0.0` is missing after
install.

```bash
systemctl list-timers weather-display.timer weather-publish.timer
journalctl -u weather-display.service -n 50 --no-pager
journalctl -u weather-publish.service -u weather-serve.service -n 50 --no-pager
```

## Live screenshot

Fetches current HKO and Home Assistant data and writes two 800×480 PNGs (does not touch the panel). The path is the room page. The forecast page is the same name with `_forecast` before the extension:

```bash
PYTHONPATH=src python -m weather_display.run --save tests/output/live.png
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH="src"; python -m weather_display.run --save tests/output/live.png
```
