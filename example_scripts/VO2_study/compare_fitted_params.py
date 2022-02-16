import logging
import os

import numpy as np

from pypermod.data_structure.athlete import Athlete
from pypermod.fitter.cp_to_tte_fitter import CPMTypes
from pypermod.processing.time_series_processing import time_dependant_rolling_average_center
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod import config

if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

# average window for VO2 measurements.
# The value at the center is the average of all values 15 sec to the left and to the right
vo2_averaging_radius = 15
p_averaging_radius = 4

subjects = [0, 1, 2, 3, 4]

# summarises results in here
data = []

# for every athlete ...
for subj in subjects:
    athlete = Athlete(os.path.join(config.paths["data_storage"], "VO2_study", str(subj)))

    # get fitted CP params
    fitting = athlete.get_cp_fitting_of_type(a_type=ActivityTypes.SRM_BBB_TEST)
    cp_params = fitting.get_params(CPMTypes.P2MONOD)

    # get the ramp test of the athlete
    ramps = athlete.list_activity_ids(a_type=ActivityTypes.SRM_BBB_TEST,
                                      p_type=ProtocolTypes.RAMP)
    assert len(ramps) == 1  # it should only be one
    activity = athlete.get_activity_by_type_and_id(a_id=ramps[0],
                                                   a_type=ActivityTypes.SRM_BBB_TEST,
                                                   p_type=ProtocolTypes.RAMP)

    # estimate VO2 peak from ramp test VO2 data
    vo2 = activity.vo2_data
    bbb_times = activity.bbb_time_data
    avg_vo2 = time_dependant_rolling_average_center(seconds=bbb_times,
                                                    values=vo2,
                                                    time_radius=vo2_averaging_radius)
    vo2_peak = np.max(avg_vo2)

    # estimate P peak from ramp test power data
    exercise_srm_data = activity.get_exercise_srm_data()
    exercise_srm_times = exercise_srm_data["sec"]
    exercise_avg_power = time_dependant_rolling_average_center(seconds=exercise_srm_times,
                                                               values=exercise_srm_data["power"],
                                                               time_radius=p_averaging_radius)
    p_peak = np.max(exercise_avg_power)

    hyd_conf = athlete.get_hydraulic_fitting_of_type(a_type=ActivityTypes.SRM_BBB_TEST)

    data.append([round(vo2_peak, 2),
                 round(p_peak, 2),
                 round(cp_params["cp"]),
                 round(cp_params["w_p"]),
                 hyd_conf])

print()
print("Peak and CP table")
print()

# first part of the table
for i, row in enumerate(data):
    print("{} & {} & {} & {} & {} \\\\".format(
        i, row[0], row[1], row[2], row[3]))

print("\\hline \n\\hline")

# avg and std part of the table
np_data = np.array([x[:4] for x in data])
p_str = "avg $\\pm$ std "
for val in range(np_data.shape[1]):
    p_str += "& ${} \\pm {}$".format(
        np.round(np.average(np_data[:, val]), 2),
        np.round(np.std(np_data[:, val]), 2)
    )
p_str += "\\\\"
print(p_str)

print()
print("hyd fitting table")
print()

# hyd fitting table
for i, row in enumerate(data):
    if row[4] is None:
        row[4] = [0, 0, 0, 0, 0, 0, 0, 0]

    hyd_conf = [round(x, 2) for x in row[4]]
    print("{} & {} & {} & {} & {} & {} & {} & {} & {} \\\\".format(
        i, hyd_conf[0], hyd_conf[1], hyd_conf[2], hyd_conf[3],
        hyd_conf[4], hyd_conf[5], hyd_conf[6], hyd_conf[7]))

print("\\hline \n\\hline")

# avg and std part of the table
np_data = np.array([x[4] for x in data])
p_str = "avg $\\pm$ std "
for val in range(np_data.shape[1]):
    p_str += "& ${} \\pm {}$".format(
        np.round(np.average(np_data[:, val]), 2),
        np.round(np.std(np_data[:, val]), 2)
    )
p_str += "\\\\"
print(p_str)
