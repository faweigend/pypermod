import logging
import os

import matplotlib.pyplot as plt
import pandas as pd
from pypermod import config
from pypermod.data_structure.athlete import Athlete

import utility

from sportsparsing.data_parser import DataParser
from sportsparsing.activities.activity_types import ActivityTypes
from sportsparsing.activities.protocol_types import ProtocolTypes

if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

athlete = Athlete(os.path.join(config.paths["data_storage"], "VO2_study", "0"))

for test in athlete.iterate_activities_all():
    bbb_times = test.bbb_time_data
    bbb_vo2 = test.vo2_data
    binned_data = utility.bin_data(pd.DataFrame({"sec": bbb_times,
                                                 "vo2": bbb_vo2}))
    bbb_binned_times = binned_data["sec"]
    bbb_vo2_binned = binned_data["vo2"]

    # rolling average
    avg_binned = utility.rolling_average_center(bbb_vo2_binned, 10, ignore_zeros=True)

    # compare with pandas rolling average estimations
    pd_comp_binned = utility.rolling_average_center(bbb_vo2_binned, 15, ignore_zeros=False)
    pd_binned = bbb_vo2_binned.rolling(31, center=True).mean()

    # timed AVG
    avg_timed = utility.time_dependant_rolling_average_center(bbb_times, bbb_vo2, 10)

    # set up plot
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(1, 1, 1)
    fig.subplots_adjust(right=0.7)
    ax.grid(True)

    # plot bbb curves
    ax.scatter(bbb_times, avg_timed, color='tab:purple', label="timed average 10", s=20)
    ax.scatter(bbb_binned_times, avg_binned, color='tab:orange', label="rolling average 10", s=10)

    ax.scatter(bbb_binned_times, pd_comp_binned, color='tab:red', label="compare rolling average 15", s=20)
    ax.scatter(bbb_binned_times, pd_binned, color='tab:blue', label="pandas rolling average 31 center", s=10)

    ax.set_ylabel("VO2/VCO2 (ml/min)")
    ax.set_title('SRM BBB plot of {}'.format(test.date_time))
    ax.set_xlabel("time in s")

    ax.legend()

    # formant plot
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=-45)
    plt.tight_layout()
    plt.show()
    plt.close(fig)
