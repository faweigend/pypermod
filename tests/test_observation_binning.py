import logging
import os

import matplotlib.pyplot as plt

from pypermod.processing import time_series_processing
from pypermod.data_structure.athlete import Athlete
from pypermod import config
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes

if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

athlete = Athlete(os.path.join(config.paths["data_storage"], "VO2_study", "0"))

for test in athlete.iterate_activities_of_type_and_protocol(ActivityTypes.SRM_BBB_TEST, ProtocolTypes.TTE):
    bbb_data = test.bbb_data
    one = time_series_processing.bin_data(bbb_data, bin_size=1)
    two = time_series_processing.bin_data(bbb_data, bin_size=2)
    five = time_series_processing.bin_data(bbb_data, bin_size=5)
    fifteen = time_series_processing.bin_data(bbb_data, bin_size=15)

    # set up plot
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(1, 1, 1)
    fig.subplots_adjust(right=0.7)
    ax.grid(True)

    # plot bbb curves
    ax.plot(one['sec'], one['vo2'], color='tab:purple', label="1 s")
    ax.plot(two['sec'], two['vo2'], color='tab:red', label="2 s")
    ax.plot(five['sec'], five['vo2'], color='tab:orange', label="5 s")
    ax.plot(fifteen['sec'], fifteen['vo2'], color='tab:green', label="15 s")

    ax.set_ylabel("VO2/VCO2 (ml/min)")
    ax.set_title('SRM BBB plot of {}'.format(test.date_time))
    ax.set_xlabel("time in s")

    ax.legend()

    # formant plot
    locs, labels = plt.xticks()
    plt.setp(labels, rotation=-45)
    plt.tight_layout()
    plt.show()
