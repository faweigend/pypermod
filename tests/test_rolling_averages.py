import logging
import os

import matplotlib.pyplot as plt
import pandas as pd
from pypermod import config
from pypermod.data_structure.athlete import Athlete
from pypermod.processing.time_series_processing import time_dependant_rolling_average_center, rolling_average_center, \
    time_dependant_rolling_average_right, rolling_average_right

import utility


if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

athlete = Athlete(os.path.join(config.paths["data_storage"], "VO2_study", "1"))

for test in athlete.iterate_activities_all():
    bbb_times = test.bbb_time_data
    bbb_vo2 = test.vo2_data
    binned_data = utility.bin_data(pd.DataFrame({"sec": bbb_times,
                                                 "vo2": bbb_vo2}))
    bbb_binned_times = binned_data["sec"]
    bbb_vo2_binned = binned_data["vo2"]

    avg_timed = time_dependant_rolling_average_center(bbb_times, bbb_vo2, 30)
    avg_binned = rolling_average_center(bbb_vo2_binned, 30, ignore_zeros=True)

    # compare with pandas rolling average estimations
    pd_binned = bbb_vo2_binned.rolling(31, center=True).mean()
    pd_comp_binned = rolling_average_center(bbb_vo2_binned, 15, ignore_zeros=False)

    avg_timed_right = time_dependant_rolling_average_right(bbb_times, bbb_vo2, 30)
    avg_binned_right = rolling_average_right(bbb_vo2_binned, 30, ignore_zeros=True)

    pd_binned_right = bbb_vo2_binned.rolling(30).mean()
    pd_comp_right_binned = rolling_average_right(bbb_vo2_binned, 30, ignore_zeros=False)

    # set up plot
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2)
    ax.grid(True)
    ax2.grid(True)

    # timed more precise because multiple breaths in one second or seconds without a measurement become possible
    ax.scatter(bbb_times, avg_timed, color='tab:purple', label="timed average 10", s=20)
    ax.scatter(bbb_binned_times, avg_binned, color='tab:orange', label="rolling average 10", s=10)

    ax.scatter(bbb_binned_times, pd_comp_binned, color='tab:red', label="compare rolling average 31 center", s=20)
    ax.scatter(bbb_binned_times, pd_binned, color='tab:blue', label="pandas rolling average 31 center", s=10)

    ax2.scatter(bbb_times, avg_timed_right, color='tab:purple', label="timed average 30 right", s=20)
    ax2.scatter(bbb_binned_times, avg_binned_right, color='tab:orange', label="rolling average 30 right", s=10)

    ax2.scatter(bbb_binned_times, pd_comp_right_binned, color='tab:olive', label="compare rolling average 30 right",
                s=20)
    ax2.scatter(bbb_binned_times, pd_binned_right, color='tab:green', label="pandas rolling average 30 right", s=10)

    ax.set_ylabel("VO2/VCO2 (ml/min)")
    ax.set_title('SRM BBB plot of {}'.format(test.date_time))
    ax.set_xlabel("time in s")

    ax.legend()
    ax2.legend()

    # formant plot
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=-45)
    plt.tight_layout()
    plt.show()
    plt.close(fig)
