import logging
import os

import pandas as pd

from pypermod.data_structure.athlete import Athlete
from pypermod.fitter.cp_to_tte_fitter import CPMTypes
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod import config


def cp_fitting_table():
    """
    for every participant, it summarises estimated CP and W' and associated SEE% for all 2P models.
    """
    # summarises results in here
    data = []

    # for every athlete (participant 0 - 4) ...
    for subj in range(5):
        athlete = Athlete(os.path.join(config.paths["data_storage"], "VO2_study", str(subj)))

        # get fitted CP and W' params of all models
        cp_fitting = athlete.get_cp_fitting_of_type(a_type=ActivityTypes.SRM_BBB_TEST)

        vals = []

        # check the 2 parameter models to compare
        # for p2_model in [CPMTypes.P2_LINEAR, CPMTypes.P2_HYP, CPMTypes.P2_1dTIME]:
        #     params = cp_fitting.get_params(p2_model)
        #
        #     # SEE% value were precomputed by fitting object
        #     cp_see_p = params["cp_see%"]
        #     w_p_see_p = params["wp_see%"]
        #
        #     # append to values object
        #     vals += [w_p_see_p, cp_see_p]

        # get best fit
        b_fit = cp_fitting.get_best_2p_fit()
        vals += [round(b_fit["cp"]), b_fit["cp_see%"],
                 round(b_fit["w_p"]), b_fit["wp_see%"],
                 b_fit["model"]]

        # finally store all values in our dataframe
        data.append(vals)

    return pd.DataFrame(data, columns=["CP(W)", "SEE(%)", "W\'(J)", "SEE(%)", "model"])


if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    # display collected data
    table1 = cp_fitting_table()
    print("\n Peak and CP table \n")
    print(table1.to_string())
