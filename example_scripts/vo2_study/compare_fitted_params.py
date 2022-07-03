import logging
import os

import numpy as np
import pandas as pd

from pypermod.data_structure.athlete import Athlete
from pypermod.fitter.cp_to_tte_fitter import CPMTypes
from pypermod.processing.time_series_processing import time_dependant_rolling_average_center
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod import config

# average window for VO2 measurements.
# The value at the center is the average of all values 15 sec to the left and to the right
vo2_averaging_radius = 15
p_averaging_radius = 4


def ramp_test_and_cp_fitting_table():
    """
    recreates Table 4 of the paper. For every participant, it summarises maximal observed VO2 and power output
    during the ramp test. Further, it adds estimated CP and W' from the method by Monod and Scherrer.
    """
    # summarises results in here
    data = []

    # for every athlete (participant 0 - 5) ...
    for subj in range(5):
        athlete = Athlete(os.path.join(config.paths["data_storage"], "VO2_study", str(subj)))

        # get fitted CP and W' params
        fitting = athlete.get_cp_fitting_of_type(a_type=ActivityTypes.SRM_BBB_TEST)

        # we want CP and W' estimated with the method by Monod and Scherrer.
        cp_params = fitting.get_params(CPMTypes.P2_LINEAR)

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
        avg_vo2 = time_dependant_rolling_average_center(seconds=bbb_times,
                                                        values=vo2,
                                                        time_radius=vo2_averaging_radius)
        max_avg_vo2 = np.max(avg_vo2)

        # get P_peak from ramp test power data
        exercise_srm_data = activity.get_exercise_srm_data()
        exercise_srm_times = exercise_srm_data["sec"]
        exercise_avg_power = time_dependant_rolling_average_center(seconds=exercise_srm_times,
                                                                   values=exercise_srm_data["power"],
                                                                   time_radius=p_averaging_radius)
        p_peak = np.max(exercise_avg_power)

        # finally store all values in our dataframe
        data.append([round(max_avg_vo2, 2),
                     round(p_peak, 2),
                     round(cp_params["cp"]),
                     round(cp_params["w_p"])])
    return pd.DataFrame(data, columns=["VO2_peak", "P_peak", "CP", "W'"])


def hydraulic_fitting_table():
    """
    recreates Table 5 of the paper. For every participant, it summarises the parameters of a fitted hydraulic model.
    """
    # summarises results in here
    data = []
    # for every athlete ...
    for subj in [0, 1, 2, 3, 4]:
        # load athlete object
        athlete = Athlete(os.path.join(config.paths["data_storage"], "VO2_study", str(subj)))
        # load stored hydraulic model configuration of the athlete
        hyd_conf = athlete.get_hydraulic_fitting_of_type(a_type=ActivityTypes.SRM_BBB_TEST)
        # append to collection
        data.append(hyd_conf)
    return pd.DataFrame(data, columns=["LF", "LS", "M_U", "M_LS", "M_LF", "theta", "gamma", "phi"])


if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    # display collected data
    table1 = ramp_test_and_cp_fitting_table()
    print("\n Peak and CP table \n")
    print(table1.to_string())

    table2 = hydraulic_fitting_table()
    print("\n hyd fitting table \n")
    print(table2.to_string())
