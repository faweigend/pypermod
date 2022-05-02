import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from threecomphyd.simulator.three_comp_hyd_simulator import ThreeCompHydSimulator

from pypermod.utility import PlotLayout as Pl
from pypermod.data_structure.athlete import Athlete
from pypermod.processing.time_series_processing import time_dependant_rolling_average_center
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod import config

if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. "
                               "[file=%(filename)s:%(lineno)d]")

# display plots
show_plot = False
latex_printout = True

# the VO2 study had 5 participants
subjects = ['0', '1', '2', '3', '4']

# average window for VO2 measurements.
# The value at the center is the average of all values 15 sec to the left and to the right
vo2_averaging_radius = 15

# measurements per second
hz = 1

# organise results
results = pd.DataFrame()

# plot all data of all athletes
for subject in subjects:

    # create and load athlete object
    athlete = Athlete(os.path.join(config.paths["data_storage"],
                                   "VO2_study",
                                   subject))

    # create hydraulic agent from saved configuration
    conf = athlete.get_hydraulic_fitting_of_type(a_type=ActivityTypes.SRM_BBB_TEST)
    hyd_agent = ThreeCompHydAgent(hz=hz,
                                  lf=conf[0], ls=conf[1],
                                  m_u=conf[2], m_ls=conf[3],
                                  m_lf=conf[4], the=conf[5],
                                  gam=conf[6], phi=conf[7])

    # iterate through all TTEs
    for activity in athlete.iterate_activities_of_type_and_protocol(a_type=ActivityTypes.SRM_BBB_TEST,
                                                                    p_type=ProtocolTypes.TTE):

        # skip these activities due to faulty VO2 data (see manuscript Weigend et al. 2022)
        if activity.id in ["SRMBbbTestA2020-11-02_17:01:12:0", "SRMBbbTestA2020-11-19_16:25:00:0"]:
            logging.info("skipped {} due to faulty VO2 data".format(activity.id))
            continue

        srm_pow = activity.power_data
        bbb_t = activity.bbb_time_data
        bbb_vo2 = activity.vo2_data
        srm_alt = activity.altitude_data

        warmup_end = activity.get_warmup_end_timestamp()
        recovery_start = activity.get_recovery_start_timestamp()

        # average breathing data
        avg_vo2 = time_dependant_rolling_average_center(seconds=bbb_t,
                                                        values=bbb_vo2,
                                                        time_radius=vo2_averaging_radius)

        # simulate hydraulic
        h, g, anf, ans, p_ae, p_an, m_flow, _ = ThreeCompHydSimulator.simulate_course_detail(agent=hyd_agent,
                                                                                             powers=srm_pow,
                                                                                             plot=False)

        # normalise flow data
        max_norm = max(p_ae)
        p_ae_norm = np.array(p_ae) / max_norm

        # normalise uptake data
        uptake_norm = max(avg_vo2)
        avg_bbb_vo2_norm = avg_vo2 / uptake_norm
        bbb_vo2_norm = bbb_vo2 / uptake_norm

        # simulated peak
        m_u_t = np.argmax(p_ae)
        # ground truth peak
        vo2_peak_pos = np.argmax(avg_vo2)
        vo2_peak_t = bbb_t[vo2_peak_pos]

        # SRM resistance
        res = np.max(srm_alt)

        # srm_pow = activity.altitude_data
        t = np.arange(len(srm_pow))

        # add estimations to results data frame
        row = {
            "participant": [subject],
            "resistance (Watts)": [int(res)],
            "\gls{vo2}": [int(vo2_peak_t - warmup_end)],
            "flow from $Ae$": [int(m_u_t - warmup_end)],
            "prediction error": [int(vo2_peak_t - m_u_t)]
        }
        df_row = pd.DataFrame(row)
        results = results.append(df_row, ignore_index=True)

        if show_plot:
            # set up plot
            fig = plt.figure(figsize=(8, 2.8))
            ax = fig.add_subplot(1, 1, 1)
            ax2 = ax.twinx()

            Pl.set_rc_params()
            # ax.set_title("athlete {} - resistance {}".format(subject, int(res)))

            ax.plot(t[:m_u_t], p_ae_norm[:m_u_t], color=Pl.get_plot_color("hyd_ae"), label="flow from $Ae$")
            ax.scatter(bbb_t[:vo2_peak_pos], avg_bbb_vo2_norm[:vo2_peak_pos], color=Pl.get_plot_color("vo2"),
                       label="averaged $\dotV_{\mathrm{O}_2}$",
                       s=5)
            ax.scatter(vo2_peak_t, np.max(avg_bbb_vo2_norm), color=Pl.get_plot_color("vo2"),
                       marker="X", s=80)
            ax.scatter(m_u_t, np.max(p_ae_norm), color=Pl.get_plot_color("hyd_ae"), marker="X", s=80)

            # plot power output
            ax2.plot(t[:int(vo2_peak_t) + 10], srm_pow[:int(vo2_peak_t) + 10], color=Pl.get_plot_color("intensity"),
                     label="power output", alpha=0.5)

            # label plot
            ax.set_xticks([warmup_end, m_u_t, vo2_peak_t])
            ax.set_xticklabels([
                0,
                int(m_u_t - warmup_end),
                int(vo2_peak_t - warmup_end)
            ])
            ax.set_xlabel("time since exercise started (seconds)")
            ax2.set_ylabel("power (Watts)")
            ax.set_ylabel("normalised flow/uptake")

            # legends
            ax.legend(loc=2)
            ax2.legend(loc=4)

            print(df_row)

            # formant plot
            locs, labels = plt.xticks()
            plt.setp(labels, rotation=-45)
            plt.tight_layout()
            plt.show()
            plt.close()

results = results.sort_values(by=['participant', 'resistance (Watts)'])

print("\n \n OVERVIEW TABLE \n \n")
if not latex_printout:
    print(results)
    print("mean error ", results["error"].mean(), "std", results["error"].std())

else:
    ### LATEX prints
    # the TTEs detail table
    print("\\begin{table}[] "
          "\\begin{adjustwidth}{-0.75in}{-0.75in}\\centering "
          "\\begin{tabular}{" + " ".join(["S[table-format=3]"] * (len(results.columns))) + "}")
    # multicolumns
    print("\\toprule")
    latex_str = "\\multicolumn{2}{c}{test setup} & " \
                "\\multicolumn{2}{c}{time until max was reached (seconds)} & " \
                "\multicolumn{1}{c}{}\\\\"
    print(latex_str)
    print("\\cmidrule(r){1-2} \\cmidrule(l){3-4}")

    # column names
    latex_str = " & ".join(["\\multicolumn{1}{c}{" + str(x) + "}" for x in results.columns]) + "\\\\"
    print(latex_str)
    print("\\midrule")
    # content
    for _, row in results.iterrows():
        latex_str = ""
        for _, item in row.iteritems():
            latex_str += "{} & ".format(item)
        latex_str = latex_str[:-2] + "\\\\"
        print(latex_str)
    # MEAN STD
    print("\\bottomrule"
          "\\addlinespace[2mm]")
    latex_str = " \\multicolumn{2}{c}{avg$\pm$std} "
    for i, col in enumerate(results.columns):
        if i > 1:  # athletes, resistance, observed are skipped
            vals = results[col]
            avgv = vals.mean()
            stdv = vals.std()
            latex_str += " & {}$\\pm${}".format(int(round(avgv, 0)), int(round(stdv, 0)))
    latex_str += "\\\\"
    print(latex_str)
    # table end
    print("\\end{tabular} "
          "\\end{adjustwidth} "
          "\\caption{The summary of all hydraulic prediction evaluations. The example of participant 1 with 396"
          " W from \Cref{fig:tte} is in row 9. The columns \"time until max was reached\" "
          "inform about the seconds it took from the onset of exercise to reach the maximal"
          " averaged \gls{vo2} (blue dots in \Cref{fig:tte}) or maximal flow from $Ae$ "
          "(azure line in \Cref{fig:tte}). The prediction error is the difference between these two times.} "
          "\\label{tab:vo2_detail} "
          "\\end{table}")
