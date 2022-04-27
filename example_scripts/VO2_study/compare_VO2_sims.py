import collections
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
show_plot = True

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
    # ThreeCompVisualisation(agent=hyd_agent)

    # iterate through all TTEs
    for activity in athlete.iterate_activities_of_type_and_protocol(a_type=ActivityTypes.SRM_BBB_TEST,
                                                                    p_type=ProtocolTypes.TTE):
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

        hyd_sim = np.argmax(h)

        # add estimations to results data frame
        row = {
            "athlete": [subject],
            "resistance (Watts)": [int(res)],
            "warmup_end": warmup_end,
            "time VO2_max": [int(vo2_peak_t)],
            "time MU": [int(m_u_t)]
        }
        df_row = pd.DataFrame(row)
        results = results.append(df_row, ignore_index=True)

        # srm_pow = activity.altitude_data
        t = np.arange(len(srm_pow))

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
            ax.scatter(m_u_t, np.max(p_ae_norm), color=Pl.get_plot_color("hyd_ae"),  marker="X", s=80)

            # plot power output
            ax2.plot(t[:int(vo2_peak_t)+10], srm_pow[:int(vo2_peak_t)+10], color=Pl.get_plot_color("intensity"), label="power output", alpha=0.5)

            # label plot
            ax.set_xticks([warmup_end, m_u_t, vo2_peak_t])
            ax.set_xticklabels([
                0,
                int(m_u_t - warmup_end),
                int(vo2_peak_t - warmup_end)
            ])
            ax.set_xlabel("time since exercise start (s)")
            ax2.set_ylabel("power (Watts)")
            ax.set_ylabel("normalised flow/uptake")

            # legends
            ax.legend(loc=2)
            ax2.legend(loc=4)

            # formant plot
            locs, labels = plt.xticks()
            plt.setp(labels, rotation=-45)
            plt.tight_layout()
            plt.show()
            plt.close()

print(results)

print(results["time VO2_max"] - results["warmup_end"])

# # some stats
# vo2 = []
# mu = []
#
# # subject, values
# for s, v in results.items():
#     # num, tte_power, measures
#     for i, (t, m) in enumerate(v.items()):
#         vo2.append(m["vo2_t"])
#         mu.append(m["m_u_t"])
#
# # print mean and std
# vo2 = np.array(vo2)
# mu = np.array(mu)
# logging.info("avg vo2 - mu :  ${} \\pm {}$~seconds".format(np.average(vo2 - mu), np.round(np.std(vo2 - mu), 2)))
# logging.info("min vo2 - mu : ${}$~seconds".format(np.min(vo2 - mu)))