from datetime import datetime

import pandas as pd


class WeatherDataProcessor:
    @staticmethod
    def process_data(df):
        df = df.apply(pd.to_numeric, errors='coerce')
        new_data = []
        new_df_column_name = []

        for index, row in df.iterrows():
            for cell in row:
                new_data.append(cell)

            for col in df.columns:
                date_obj = datetime.strptime(f'{index} {col} 2024', '%d %b (%a) %H %Y')
                time_difference = date_obj - datetime.now()
                hours_difference = time_difference.total_seconds() // 3600
                new_df_column_name.append(int(hours_difference))

        new_df = pd.DataFrame(
            new_data, columns=['Temperature'], index=new_df_column_name
        )
        return new_df[(new_df.index >= 0) & (new_df.index < 9)]
