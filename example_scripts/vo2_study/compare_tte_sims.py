import logging
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib  # for rcparams

from pypermod.data_structure.athlete import Athlete
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.fitter.cp_to_tte_fitter import CPMTypes
from pypermod.utility import PlotLayout
from pypermod import config

from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from threecomphyd.simulator.three_comp_hyd_simulator import ThreeCompHydSimulator

if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    # prints results tables in LATEX format if True
    latex_printout = False
    # display plots
    show_plot = True

    subjects = [0, 1, 2, 3, 4]
    hz = 1  # observations are in seconds

    # organise results
    results = pd.DataFrame()

    for subj in subjects:

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

        resolution = 1
        ts_ext = np.arange(90, 800, 20 / resolution)
        powers_ext = [((wp + x * cp) / x) for x in ts_ext]

        if show_plot:
            PlotLayout.set_rc_params()
            matplotlib.rcParams['axes.labelsize'] = 10.5
            fig = plt.figure(figsize=(6, 3.2))
            ax = fig.add_subplot()
            hyd_curve = [ThreeCompHydSimulator.tte(hyd_agent, x) for x in powers_ext]
            ax.plot(hyd_curve, powers_ext, label='$hydaulic_{weig}$')
            ax.plot(ts_ext, powers_ext, label='two-parameter')
            ax.scatter(tte_ms.times, tte_ms.measures, label='observed TTE')
            ax.set_xlabel("time-to-exhaustion (seconds)")
            ax.set_ylabel("constant exercise intensity (Watts)")
            ax.legend()
            plt.tight_layout()
            plt.show()
            plt.close(fig)

    ann_results = results.sort_values(by=['athlete', 'resistance (Watts)'])

    print("\n \n OVERVIEW TABLE \n \n")
    if not latex_printout:
        print(ann_results)
    else:
        ### LATEX prints
        # the TTEs detail table
        print("\\begin{table}[] "
              "\\begin{adjustwidth}{-0.75in}{-0.75in}\\centering "
              "\\begin{tabular}{ c c " + " ".join(["S[table-format=3.2]"] * (len(ann_results.columns) - 2)) + "}")
        # multicolumns
        print("\\toprule")
        latex_str = "\\multicolumn{2}{c}{test setup} & " \
                    "\\multicolumn{" + str(len(ann_results.columns) - 2) + "}{c}{times-to-exhaustion (seconds)}\\\\"
        print(latex_str)
        print("\\cmidrule(r){1-2} \\cmidrule(l){3-" + str(len(ann_results.columns)) + "}")
        # column names
        latex_str = " & ".join(["\\multicolumn{1}{c}{" + str(x) + "}" for x in ann_results.columns]) + "\\\\"
        print(latex_str)
        print("\\midrule")
        # content
        for _, row in ann_results.iterrows():
            latex_str = ""
            for _, item in row.iteritems():
                latex_str += "{} & ".format(item)
            latex_str = latex_str[:-2] + "\\\\"
            print(latex_str)
        # # RMSE
        # print("\\addlinespace[2mm]")
        # latex_str = " & & \\multicolumn{1}{c}{RMSE} "
        # for i, col in enumerate(results.columns):
        #     if i > 2:  # athletes, resistance, observed are skipped
        #         rmse = ((ann_results[col] - ann_results["observed"]) ** 2).mean() ** .5
        #         latex_str += " & {}".format(round(rmse, 2))
        # latex_str += "\\\\"
        # print(latex_str)
        # Mean +- STD
        # latex_str = " & & \\multicolumn{1}{c}{avg} "
        # for i, col in enumerate(results.columns):
        #     if i > 2:  # athletes, resistance, observed are skipped
        #         vals = (ann_results[col] - ann_results["observed"]).abs()
        #         avgv = vals.mean()
        #         stdv = vals.std()
        #         latex_str += " & {}$\\pm${}".format(round(avgv, 2), round(stdv, 2))
        # latex_str += "\\\\"
        # print(latex_str)
        # table end
        print("\\bottomrule "
              "\\end{tabular} "
              "\\end{adjustwidth} "
              "\\caption{} "
              "\\label{tab:ttes_detail} "
              "\\end{table}")

    # test specific stats. i increases from lowest to highest resistance
    tte_specific_rmse = pd.DataFrame()
    names = ["lowest", "low", "medium", "high", "highest"]
    for i in range(len(names)):

        row = {"resistance category": [names[i]]}

        filtered_tests = pd.DataFrame()
        for subj in range(len(subjects)):
            subj_tests = ann_results[ann_results["athlete"] == subj]
            subj_test = subj_tests.sort_values(by='resistance (Watts)').iloc[i]
            filtered_tests = filtered_tests.append(subj_test, ignore_index=True)

        row.update({
            "observed TTE": ["{} & {}".format(round(filtered_tests["observed"].mean(), 2),
                                              round(filtered_tests["observed"].std(), 2))]
        })

        # filtered test specific stats
        for j, col in enumerate(results.columns):
            if j > 2:  # athletes, resistance, observed are skipped
                vals = (filtered_tests[col] - filtered_tests["observed"])
                avgv = round(vals.mean(), 2)
                stdv = round(vals.std(), 2)

                row.update({
                    col: ["{} & {}".format(avgv, stdv)]
                })

        tte_specific_rmse = tte_specific_rmse.append(pd.DataFrame(row))

    row = {
        "resistance category": ["overall"],
        "observed TTE": [
            "{} & {}".format(
                round(ann_results["observed"].mean(), 2),
                round(ann_results["observed"].std(), 2))
        ]
    }
    # filtered test specific stats
    for j, col in enumerate(results.columns):
        if j > 2:  # athletes, resistance, observed are skipped
            vals = (ann_results[col] - ann_results["observed"])
            avgv = round(vals.mean(), 2)
            stdv = round(vals.std(), 2)

            row.update({
                col: ["{} & {}".format(avgv, stdv)]
            })

            print(col, np.sqrt(
                np.sum(np.power(vals, 2)) /
                len(vals)
            ) / np.mean(ann_results["observed"]))
    tte_specific_rmse = tte_specific_rmse.append(pd.DataFrame(row))

    # separate the two tables
    print("\n \n TTE CATEGORY TABLE \n \n")

    if not latex_printout:
        print(tte_specific_rmse)
    else:
        ### print LATEX
        print("\\begin{table}[] "
              "\\begin{adjustwidth}{-0.75in}{-0.75in}\\centering "
              "\\begin{tabular}{ c " + " ".join(["S[table-format=4.2] @{${}\pm{}$} S[table-format=3.2]"] *
                                                (len(tte_specific_rmse.columns) - 1)) + "}")
        # multicolumns
        print("\\toprule")
        latex_str = "resistance category & " \
                    "\\multicolumn{2}{c}{observed TTE } &" \
                    "\\multicolumn{" + str((len(tte_specific_rmse.columns) - 2) * 2) + "}{c}{prediction error} \\\\"
        print(latex_str)
        print("\\cmidrule(l){4-" + str(len(tte_specific_rmse.columns) * 2 - 1) + "}")
        # column names
        latex_str = "\\multicolumn{3}{c}{} & " + " & ".join(
            ["\\multicolumn{2}{c}{" + str(x) + "}" for x in tte_specific_rmse.columns[2:]]) + "\\\\"
        print(latex_str)
        print("\\midrule")
        # content
        for _, row in tte_specific_rmse.iterrows():
            latex_str = ""
            for _, item in row.iteritems():
                latex_str += "{} & ".format(item)
            latex_str = latex_str[:-2] + "\\\\"
            print(latex_str)
        print("\\bottomrule "
              "\\end{tabular} "
              "\\end{adjustwidth} "
              "\\caption{Each athlete completed five TTE trials and, e.g., the ``lowest'' intensity category are the lowest-intensity trials of all athletes together. The ``overall'' category entails all TTE trials of all athletes. Prediction error is the average difference between observed TTE and model prediction.} "
              "\\label{tab:tte_categories} "
              "\\end{table}")
