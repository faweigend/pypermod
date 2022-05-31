import logging
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pypermod.data_structure.athlete import Athlete
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.fitter.cp_to_tte_fitter import CPMTypes
from pypermod.utility import PlotLayout
from pypermod import config

from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from threecomphyd.simulator.three_comp_hyd_simulator import ThreeCompHydSimulator


def get_all_tte_predictions(show_plot=False) -> pd.DataFrame:
    """
    This function checks all conducted TTEs of the VO2 data set. It summarises test conditions and observed
    times to exhaustion in a table and adds model predictions of the hydraulic and CP model.
    :param show_plot: if True, the function displays the power-duration curve for hydraulic and CP model
    to compare energy expenditure
    :return: the overview table as a pandas dataframe
    """
    # store results in here
    results = pd.DataFrame()

    # for every participant...
    for subj in [0, 1, 2, 3, 4]:
        # ... load data as an athlete object
        athlete = Athlete(os.path.join(config.paths["data_storage"], "VO2_study", str(subj)))

        # get fitted CP params
        fitting = athlete.get_cp_fitting_of_type(a_type=ActivityTypes.SRM_BBB_TEST)
        cp_params = fitting.get_params(CPMTypes.P2MONOD)
        wp = cp_params["w_p"]
        cp = cp_params["cp"]

        # create hydraulic agent
        conf = athlete.get_hydraulic_fitting_of_type(a_type=ActivityTypes.SRM_BBB_TEST)
        hyd_agent = ThreeCompHydAgent(lf=conf[0], ls=conf[1],
                                      m_u=conf[2], m_ls=conf[3],
                                      m_lf=conf[4], the=conf[5],
                                      gam=conf[6], phi=conf[7],
                                      hz=1)

        tte_ms = fitting.get_ttes()
        for t, i in tte_ms.iterate_pairs():
            tte_hyd = ThreeCompHydSimulator.tte(hyd_agent, p_work=i)
            tte_cp = wp / (i - cp)

            # add estimations to results data frame
            row = {
                "athlete": [subj],
                "resistance (Watts)": [int(i)],
                "observed": [int(t)],
                PlotLayout.get_plot_label(hyd_agent.get_name()): [int(tte_hyd)],
                "two-parameter": [round(tte_cp)]
            }
            df_row = pd.DataFrame(row)
            results = results.append(df_row, ignore_index=True)

        # The plot helps to compare energy expenditure dynamics
        # creates two power-duration curves, one for the hydraulic model and one according to CP and W'
        if show_plot:
            resolution = 1
            ts_ext = np.arange(90, 800, 20 / resolution)
            powers_ext = [((wp + x * cp) / x) for x in ts_ext]
            PlotLayout.set_rc_params()
            fig = plt.figure(figsize=(6, 3.2))
            ax = fig.add_subplot()
            hyd_curve = [ThreeCompHydSimulator.tte(hyd_agent, x) for x in powers_ext]
            ax.plot(hyd_curve, powers_ext, label='$hydaulic_{weig}$')
            ax.plot(ts_ext, powers_ext, label='two-parameter')
            ax.scatter(tte_ms.times, tte_ms.measures, label='observed TTE')
            ax.set_xlabel("time to exhaustion (seconds)")
            ax.set_ylabel("constant exercise intensity (Watts)")
            ax.legend()
            plt.tight_layout()
            plt.show()
            plt.close(fig)

    return results.sort_values(by=['athlete', 'resistance (Watts)'])


def get_categorised_tte_predictions() -> pd.DataFrame:
    """
    This function returns Table 3 of our VO2 paper. TTEs of all participants of the VO2 data set are categorised into
    "lowest", "low", "medium", "high", "highest". We scrutinised prediction errors of models in these categories to detect
    prediction bias.
    :return: the table as a pandas dataframe
    """
    # get all ttes from function above
    ann_results = get_all_tte_predictions()
    participants = ann_results['athlete'].unique()

    # test specific stats. i increases from lowest to highest resistance
    categorised_rmse = pd.DataFrame()
    names = ["lowest", "low", "medium", "high", "highest"]
    for i in range(len(names)):

        row = {"resistance category": [names[i]]}

        # filter resistance category
        filtered_tests = pd.DataFrame()
        for subj in range(len(participants)):
            subj_tests = ann_results[ann_results["athlete"] == subj]
            subj_test = subj_tests.sort_values(by='resistance (Watts)').iloc[i]
            filtered_tests = filtered_tests.append(subj_test, ignore_index=True)

        # basic stats of filtered ttes
        row.update({
            "observed TTE": ["{} & {}".format(round(filtered_tests["observed"].mean(), 2),
                                              round(filtered_tests["observed"].std(), 2))]
        })
        # model prediction errors on filtered ttes
        for j, col in enumerate(ann_results.columns):
            if j > 2:  # athletes, resistance, observed are skipped
                vals = (filtered_tests[col] - filtered_tests["observed"])
                avgv = round(vals.mean(), 2)
                stdv = round(vals.std(), 2)

                row.update({
                    col: ["{} & {}".format(avgv, stdv)]
                })
        # add to dataframe
        categorised_rmse = categorised_rmse.append(pd.DataFrame(row))

    # Add overall stats
    row = {
        "resistance category": ["overall"],
        "observed TTE": [
            "{} & {}".format(
                round(ann_results["observed"].mean(), 2),
                round(ann_results["observed"].std(), 2))
        ]
    }
    # and overall model prediction errors
    for j, col in enumerate(ann_results.columns):
        if j > 2:  # athletes, resistance, observed are skipped
            vals = (ann_results[col] - ann_results["observed"])
            avgv = round(vals.mean(), 2)
            stdv = round(vals.std(), 2)

            row.update({
                col: ["{} & {}".format(avgv, stdv)]
            })

    # return complete dataframe
    return categorised_rmse.append(pd.DataFrame(row))


if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    # display collected data and model predictions
    ann_results = get_all_tte_predictions(show_plot=False)
    print("\n \n OVERVIEW TABLE \n \n")
    print(ann_results.to_string())

    categorised_error = get_categorised_tte_predictions()
    print("\n \n TTE CATEGORY TABLE \n \n")
    print(categorised_error.to_string())
