import io
from datetime import datetime, timedelta
from typing import Any

import matplotlib.pyplot as plt
from numpy._typing import _UnknownType
from pandas import DataFrame, Series


class WeatherVisualizer:
    @staticmethod
    def create_plot(df_filtered: Series | DataFrame):
        plt.figure(figsize=(1.8, 0.65), dpi=300)

        font = {'family': 'Cubic 11', 'size': 4}
        plt.rc('font', **font)

        plt.plot(
            df_filtered.index,
            df_filtered['Temperature'],
            color='black',
            marker='o',
            linestyle='-',
            linewidth=1,
            markersize=1,
        )

        # Set y-ticks
        plt.yticks(sorted(df_filtered['Temperature'].unique()), color='black')
        plt.grid(False)

        # Create x-ticks
        xticks = df_filtered.index
        all_hour_labels = [
            (datetime.now() + timedelta(hours=int(x) + 1)).strftime('%H:00')
            for x in xticks
        ]

        # Set major and minor ticks
        major_ticks = xticks[::2]
        major_labels = all_hour_labels[::2]

        plt.gca().set_xticks(major_ticks)
        plt.gca().set_xticks(xticks, minor=True)
        plt.gca().set_xticklabels(major_labels, color='black')

        plt.gca().tick_params(axis='x', which='minor', length=2)
        plt.gca().tick_params(axis='x', which='major', length=4)

        # Annotate extremes
        max_temp = df_filtered['Temperature'].max()
        min_temp = df_filtered['Temperature'].min()
        max_index = df_filtered['Temperature'].idxmax()
        min_index = df_filtered['Temperature'].idxmin()

        h_offset = 0.4
        plt.text(
            max_index,
            max_temp - h_offset,
            f'{max_temp}°C',
            fontsize=2,
            color='black',
            ha='center',
            va='bottom',
        )
        plt.text(
            min_index,
            min_temp + h_offset,
            f'{min_temp}°C',
            fontsize=2,
            color='black',
            ha='center',
            va='top',
        )

        return plt
