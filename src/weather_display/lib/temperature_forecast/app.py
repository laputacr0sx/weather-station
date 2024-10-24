import io

from .data_processor import WeatherDataProcessor
from .scraper import WeatherScraper
from .visualizer import WeatherVisualizer


def get_temperature_plot():
    try:
        # Scrape data
        scraper = WeatherScraper()
        raw_data = scraper.scrape_weather_data()

        # Process data
        processor = WeatherDataProcessor()
        processed_data = processor.process_data(raw_data)

        # Visualize data
        visualizer = WeatherVisualizer()
        plt = visualizer.create_plot(processed_data)

        # Save the plot
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()

        buf.seek(0)

        return buf.getvalue()

    except Exception as e:
        print(f'An error occurred: {e}')
        return bytes('', 'utf-8')
