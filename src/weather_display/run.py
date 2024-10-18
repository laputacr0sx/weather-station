import logging
from datetime import datetime
import platform

from PIL import Image, ImageDraw

from weather_display import EPD_HEIGHT, EPD_WIDTH
from weather_display.lib.render.dashboard import render_minor_dashboard
from weather_display.lib.render.footer import render_footer_section
from weather_display.lib.render.forecast import render_forecast_section
from weather_display.lib.render.header import render_header_section
from weather_display.lib.render.rainfall import render_rainfall_section
from weather_display.lib.util.calculate_time import get_record_time_diff
from weather_display.lib.util.convert_date_string import get_now_str
from weather_display.lib.util.current_weather import get_current_weather
from weather_display.lib.util.env_sensor import EnvironmentData
from weather_display.lib.util.gregorian import get_gregorian_date
from weather_display.lib.util.humidity import get_humidity_data
from weather_display.lib.util.sun import get_sun_status
from weather_display.lib.util.uv_index import get_uv_data
from weather_display.lib.util.weather_forecast import get_weather_forecast
from weather_display.lib.util.wind import get_wind_data
# from weather_display.lib.waveshare_epd import epd7in5_V2


logging.basicConfig(
    filename="./error.log",  # Log file name
    level=logging.DEBUG,  # Log level
    format="%(asctime)s\t----[%(levelname)s]----\t%(message)s",  # Log format
    datefmt="%Y-%m-%d %H:%M:%S",  # Date format
)


def main():
    try:
        # logging.info("Initiate EPD7in5")
        # epd = epd7in5_V2.EPD()

        # logging.info("init and Clear")
        # epd.init()
        # epd.Clear()

        logging.info("Reading from BME280")
        env = EnvironmentData(temperature=27.9, humidity=63.1, pressure=1009.5)
        logging.info("Enviroment Data GOT!")

        logging.info("Gathering System Information")

        now: datetime = datetime.now()
        logging.info("Current Datetime GOT! ")

        weather = get_current_weather()
        logging.info("Current Weather GOT! ")

        forecast = get_weather_forecast()
        logging.info("Weatherforecast GOT! ")

        uv = get_uv_data()[0]
        logging.info("UV Data GOT! ")

        wind = get_wind_data()
        logging.info("Wind Data GOT!")

        sun = get_sun_status()
        logging.info("Sun Data GOT!")

        time_diff = get_record_time_diff(now, weather.temperature.record_time)

        humidity = get_humidity_data()
        logging.info("Humidity Data GOT!")

        greg = get_gregorian_date()
        logging.info("Gregorian Date GOT!")

        location = "沙田馬鞍山"
        now_str = get_now_str(now)

        logging.info("Generating Image")
        main_image = Image.new("1", (EPD_WIDTH, EPD_HEIGHT), 255)

        logging.info("Drawing Image")
        draw = ImageDraw.Draw(main_image)

        logging.info("Rendering different sections...")
        render_header_section(
            greg, weather, humidity, location, now_str, draw, main_image
        )
        render_forecast_section(forecast, draw, main_image)
        render_rainfall_section(main_image)
        render_minor_dashboard(env, wind, uv, weather, sun, draw, main_image)
        render_footer_section(draw, time_diff, now)
        logging.info("Rendering Process Finished")

        logging.info("Display Image")
        main_image.show()
        # epd.display(epd.getbuffer(main_image))
        #
        # epd.sleep()

        logging.info("Displaying Image Success")

    except IOError as e:
        logging.info(e)

    except Exception:
        # Log the exception with traceback
        logging.error("An error occurred", exc_info=True)


if __name__ == "__main__":
    main()
