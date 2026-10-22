import argparse
import logging
import os
from datetime import datetime
from pathlib import Path

from requests import HTTPError

from weather_display.lib.render.home_dashboard import render_forecast_page, render_now_page
from weather_display.lib.util.current_weather import get_current_weather
from weather_display.lib.util.display_backend import present
from weather_display.lib.util.gregorian import get_gregorian_date
from weather_display.lib.util.home_assistant import fetch_rooms, placeholder_rooms
from weather_display.lib.util.humidity import get_humidity_data
from weather_display.lib.util.rainfall_nowcast import get_home_nowcast
from weather_display.lib.util.sun import get_sun_status
from weather_display.lib.util.uv_index import get_uv_data
from weather_display.lib.util.warnings import get_warnings
from weather_display.lib.util.weather_forecast import get_weather_forecast
from weather_display.lib.util.wind import get_wind_data
from weather_display.refresh import GlassFacts, rain_attention


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s\t[%(levelname)s]\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Render the weather dashboard")
    parser.add_argument(
        "--save",
        metavar="PATH",
        help="Write a live PNG instead of showing the EPD or a preview window",
    )
    return parser.parse_args(argv)


def _outdoor_c(weather):
    try:
        return float(weather.temperature.data[0].value)
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def _icon_id(weather):
    try:
        return int(weather.icon[0])
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def _lunar(greg):
    year = getattr(greg, 'lunar_year', '') or ''
    date = getattr(greg, 'lunar_date', '') or ''
    if len(year) >= 5:
        return f'{year[:3]}{date}[{year[4:5]}]'
    text = f'{year}{date}'.strip()
    return text or None


def _wind_text(wind):
    station = getattr(wind, 'station', '') or ''
    direction = getattr(wind, 'wind_direction', '') or ''
    speed = getattr(wind, 'avg_wind_speed', '') or ''
    place = f'{station}{direction}'.strip()
    if speed:
        return f'風 {place} {speed}公里'.strip()
    if place:
        return f'風 {place}'
    return ''


def page_for(when: datetime) -> str:
    """First page when nothing has been stored yet.

    Later refreshes alternate from the stored page. This clock fallback
    still steps every 15 minutes from 05:00 and hourly overnight, so a
    missing state file lands on a stable page for that time.
    """
    if 5 <= when.hour <= 23:
        tick = ((when.hour - 5) * 60 + when.minute) // 15
    else:
        tick = when.hour
    return 'forecast' if tick % 2 else 'now'


def page_state_path() -> Path | None:
    override = os.environ.get('WEATHER_DISPLAY_PAGE_STATE', '').strip()
    if override:
        return Path(override)
    state_dir = os.environ.get('STATE_DIRECTORY', '').split(':', 1)[0].strip()
    if state_dir:
        return Path(state_dir) / 'page'
    return None


def choose_page(state_path: Path | None, when: datetime, *, flip: bool = True) -> str:
    """Return the page to show, and remember it.

    ``flip=False`` keeps the page already on the glass. An urgent rain or
    warning update uses that so the panel does not also swap pages.
    """
    last = ''
    if state_path is not None:
        try:
            last = state_path.read_text(encoding='utf-8').strip()
        except OSError:
            last = ''
    if not flip and last in ('now', 'forecast'):
        return last
    if last == 'now':
        page = 'forecast'
    elif last == 'forecast':
        page = 'now'
    else:
        page = page_for(when)
    if state_path is not None:
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(page + '\n', encoding='utf-8')
        except OSError:
            logging.warning('Could not store dashboard page')
    return page


def render_pair():
    """Fetch the live readings and draw both pages.

    Returns ``(now, forecast, when, facts)``. ``facts`` is what the refresh
    policy compares, not the pixels.
    """
    logging.info('Gathering System Information')

    now: datetime = datetime.now()
    logging.info('Current Datetime GOT! ')

    weather = get_current_weather()
    logging.info('Current Weather GOT! ')

    uv = get_uv_data()[0]
    logging.info('UV Data GOT! ')

    wind = get_wind_data()
    logging.info('Wind Data GOT!')

    sun = get_sun_status()
    logging.info('Sun Data GOT!')

    humidity = get_humidity_data()
    logging.info('Humidity Data GOT!')

    greg = get_gregorian_date()
    logging.info('Gregorian Date GOT!')

    nowcast = get_home_nowcast()
    if nowcast is None:
        logging.warning('Rainfall nowcast unavailable')
    else:
        logging.info('Home nowcast GOT! peak=%.2f' % nowcast.peak_per_slot_mm)

    fetched_warnings = get_warnings()
    warnings_known = fetched_warnings is not None
    warnings = fetched_warnings or []
    if not warnings_known:
        logging.warning('Warnings unavailable')
    elif warnings:
        logging.info('Warnings GOT! %s', ' '.join(item.name for item in warnings))
    else:
        logging.info('No warning in force')

    try:
        forecast = list(get_weather_forecast().weather_forecast)[:5]
        logging.info('Forecast GOT! %s days', len(forecast))
    except Exception:
        logging.error('Forecast unavailable', exc_info=True)
        forecast = []

    try:
        rooms = fetch_rooms()
        logging.info(
            'Home Assistant GOT! %s',
            ', '.join(f'{room.name}={room.temperature_c}' for room in rooms),
        )
    except Exception:
        logging.error('Home Assistant unavailable', exc_info=True)
        rooms = placeholder_rooms()

    outdoor = dict(
        outdoor_c=_outdoor_c(weather),
        outdoor_humidity=getattr(humidity, 'humidity', None),
        icon_id=_icon_id(weather),
        location='沙田馬鞍山',
        when=now,
        lunar=_lunar(greg),
    )
    logging.info('Rendering dashboard pages')
    shared = dict(nowcast=nowcast, warnings=warnings)
    now_image = render_now_page(rooms, **outdoor, **shared)
    forecast_image = render_forecast_page(
        forecast=forecast,
        wind_text=_wind_text(wind),
        uv_text=str(uv.uv_index),
        sun_rise=sun.rise,
        sun_set=sun.set,
        **outdoor,
        **shared,
    )
    logging.info('Rendering Process Finished')
    facts = GlassFacts(
        attention=rain_attention(nowcast, now),
        warnings=tuple(item.name for item in warnings),
        warnings_known=warnings_known,
    )
    return now_image, forecast_image, now, facts


def main(argv=None):
    args = parse_args(argv)
    try:
        now_image, forecast_image, now, _facts = render_pair()
        if args.save:
            path = Path(args.save)
            path.parent.mkdir(parents=True, exist_ok=True)
            forecast_path = path.with_name(f'{path.stem}_forecast{path.suffix}')
            now_image.save(path)
            forecast_image.save(forecast_path)
            logging.info('Wrote %s', path)
            logging.info('Wrote %s', forecast_path)
        else:
            page = choose_page(page_state_path(), now)
            logging.info('Display %s page', page)
            present(forecast_image if page == 'forecast' else now_image)
            logging.info('Displaying Image Success')
    except HTTPError as e:
        logging.error(e)

    except IOError as e:
        logging.info(e)

    except Exception:
        # Log the exception with traceback
        logging.error('An error occurred', exc_info=True)


if __name__ == '__main__':
    main()
