import logging
import os

import pandas as pd

from pypermod.data_structure.athlete import Athlete
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod import config


def hydraulic_fitting_table():
    """
    recreates Table 5 of the paper. For every participant, it summarises the parameters of a fitted hydraulic model.
    """
    # summarises results in here
    data = []
    # for every athlete ...
    for subj in range(5):
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

    table2 = hydraulic_fitting_table()
    print("\n hyd fitting table \n")
    print(table2.to_string())
