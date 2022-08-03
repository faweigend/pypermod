import logging
import os

import numpy as np
import pandas as pd

from pypermod.data_structure.athlete import Athlete
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod import config

# averaging window for VO2 measurements.
from pypermod.processing.time_series_processing import time_dependant_rolling_average_right

vo2_averaging = 30
p_averaging = 10


def ramp_test_results_table():
    """
    recreates Table 4 of the paper. For every participant, it summarises observed VO2 max and power output
    during the ramp test.
    """
    # summarises results in here
    data = []

    # for every athlete (participant 1 - 5) ...
    for subj in range(1, 6):
        athlete = Athlete(os.path.join(config.paths["data_storage"], "VO2_study", str(subj)))

        # get the IDs of recorded ramp tests of the athlete
        ramps = athlete.list_activity_ids(a_type=ActivityTypes.SRM_BBB_TEST,
                                          p_type=ProtocolTypes.RAMP)

        # It should be only one. Load the first one.
        activity = athlete.get_activity_by_type_and_id(a_id=ramps[0],
                                                       a_type=ActivityTypes.SRM_BBB_TEST,
                                                       p_type=ProtocolTypes.RAMP)

        # get maximal averaged VO2 from ramp test VO2 data
        vo2 = activity.vo2_data
        bbb_times = activity.bbb_time_data  # breath by breath data has irregular time steps
        avg_vo2 = time_dependant_rolling_average_right(seconds=bbb_times,
                                                       values=vo2,
                                                       window_size=vo2_averaging)
        ramp_vo2_max = np.max(avg_vo2)

        # get P_peak from ramp test power data
        exercise_srm_data = activity.get_exercise_bike_data()
        exercise_srm_times = exercise_srm_data["sec"]
        exercise_avg_power = time_dependant_rolling_average_right(seconds=exercise_srm_times,
                                                                  values=exercise_srm_data["power"],
                                                                  window_size=p_averaging)
        p_peak = np.max(exercise_avg_power)

        # finally store all values in our dataframe
        data.append([subj,
                     round(ramp_vo2_max, 2),
                     round(p_peak, 2)])
    return pd.DataFrame(data, columns=["participant", "VO2_max", "P_peak"])


if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    # display collected data
    table1 = ramp_test_results_table()
    print("\n Peak and CP table \n")
    print(table1.to_string())
