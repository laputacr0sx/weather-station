from selenium import webdriver


def get_chrome_options():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')
    return chrome_options


HKO_TEXT_URL = 'https://maps.weather.gov.hk/ocf/text_e.html?mode=0&station=SHA'
XPATH_TEMP_FORECAST = '/html/body/div/div/div/div/div[1]/div[1]/div[3]/div/div[3]/div/div[2]/div/div/div[2]'
XPATH_HEADERS = '/html/body/div/div/div/div/div[1]/div[1]/div[3]/div/div[3]/div/div[2]/div/div/div[2]/table/tbody/tr[1]'
