import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import HKO_TEXT_URL, XPATH_HEADERS, XPATH_TEMP_FORECAST, get_chrome_options


class WeatherScraper:
    def __init__(self):
        self.driver = None

    def setup_driver(self):
        self.driver = webdriver.Chrome(options=get_chrome_options())

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def scrape_weather_data(self):
        try:
            self.setup_driver()
            if self.driver is None:
                raise Exception('No Chromium Driver Established')

            self.driver.get(HKO_TEXT_URL)

            temperature_forecast = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, XPATH_TEMP_FORECAST))
            )

            # Extract headers
            headers = temperature_forecast.find_element(
                By.XPATH, XPATH_HEADERS
            ).find_elements(By.TAG_NAME, 'th')
            header_texts = [header.text.strip() for header in headers[1:]]

            # Extract rows
            rows = temperature_forecast.find_elements(By.TAG_NAME, 'tr')
            table_data = []
            table_index = []

            for row in rows[1:]:
                date = row.find_element(By.TAG_NAME, 'th').text.strip()
                table_index.append(date)
                cells = row.find_elements(By.TAG_NAME, 'td')
                row_data = [cell.text.strip() for cell in cells]
                table_data.append(row_data)

            return pd.DataFrame(table_data, table_index, header_texts)

        except Exception as e:
            print(e)

        finally:
            self.close_driver()
