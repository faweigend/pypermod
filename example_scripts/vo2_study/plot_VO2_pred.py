import logging
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pypermod.processing.time_series_processing import time_dependant_rolling_average_right

from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from threecomphyd.simulator.three_comp_hyd_simulator import ThreeCompHydSimulator

from pypermod.utility import PlotLayout as Pl
from pypermod.data_structure.athlete import Athlete
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod import config


def get_vo2_predictions(show_plot=False) -> pd.DataFrame:
    """
    Creates Table 1 of our paper and optional plots like Figure 4. Hydraulic model predictions for VO2 are compared
    to actual observations. The prediction error is the time difference between when the predicted VO2 reached its
    maximum vs when the observed VO2 reached its maximum.
    :param show_plot: displays a plot for every test if True
    :return: a pandas dataframe with all test conditions and prediction errors
    """
    # measurements per second
    hz = 1
    # organise results
    results = pd.DataFrame()
    # for every participant (1 - 5) ...
    for subj in range(1, 6):

        # create and load athlete object
        athlete = Athlete(os.path.join(config.paths["data_storage"],
                                       "VO2_study",
                                       str(subj)))

        # create hydraulic agent from saved configuration
        conf = athlete.get_hydraulic_fitting_of_type_and_protocol(a_type=ActivityTypes.SRM_BBB_TEST,
                                                                  p_type=ProtocolTypes.TTE)
        hyd_agent = ThreeCompHydAgent(hz=hz,
                                      lf=conf[0], ls=conf[1],
                                      m_u=conf[2], m_ls=conf[3],
                                      m_lf=conf[4], the=conf[5],
                                      gam=conf[6], phi=conf[7])

        # iterate through all TTEs
        for activity in athlete.iterate_activities_of_type_and_protocol(a_type=ActivityTypes.SRM_BBB_TEST,
                                                                        p_type=ProtocolTypes.TTE):

            # skip these activities due to faulty VO2 data (see manuscript Weigend et al. 2022)
            if activity.id in ["SrmBbbTestA2020-11-02_17:01:12:0", "SrmBbbTestA2020-11-19_16:25:00:0"]:
                logging.info("skipped {} due to faulty VO2 data".format(activity.id))
                continue

            srm_pow = activity.power_data
            bbb_t = activity.bbb_time_data
            bbb_vo2 = activity.vo2_data
            srm_alt = activity.altitude_data

            warmup_end = activity.get_warmup_end_timestamp()

            # average breathing data
            avg_vo2 = time_dependant_rolling_average_right(seconds=bbb_t,
                                                           values=bbb_vo2,
                                                           window_size=30)

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
                "participant": [subj],
                "power (W)": [int(res)],
                "observed": [int(vo2_peak_t - warmup_end)],
                "$\mathrm{hydraulic}_\mathrm{weig}$": [int(m_u_t - warmup_end)],
                "prediction error": [int(vo2_peak_t - m_u_t)]
            }
            df_row = pd.DataFrame(row)
            results = results.append(df_row, ignore_index=True)

            if show_plot:
                Pl.set_rc_params()
                # set up plot
                fig = plt.figure(figsize=(8, 3.5))
                ax = fig.add_subplot(1, 1, 1)
                ax2 = ax.twinx()

                ax.set_title("participant {} - power {}".format(subj, int(res)))

                # power output
                d = np.zeros(len(srm_pow[:int(vo2_peak_t) + 10]))
                ax2.fill_between(t[:int(vo2_peak_t) + 10], srm_pow[:int(vo2_peak_t) + 10],
                                 where=srm_pow[:int(vo2_peak_t) + 10] >= d, interpolate=True,
                                 color=Pl.get_plot_color("intensity"),
                                 alpha=0.3,
                                 label="power output")

                # simulated
                ax.plot(t[:m_u_t], p_ae_norm[:m_u_t], color=Pl.get_plot_color("hyd_ae"),
                        label="predicted $\dotV_{\mathrm{O}_2}$ by $\mathrm{hydraulic}_\mathrm{weig}$", linewidth=2)
                ax.scatter(m_u_t, np.max(p_ae_norm), color=Pl.get_plot_color("hyd_ae"), marker="X", s=80)

                # observed
                p_avg = avg_bbb_vo2_norm[:vo2_peak_pos]
                p_bbt = bbb_t[:vo2_peak_pos]
                p_avg = p_avg[p_bbt > 0]
                p_bbt = p_bbt[p_bbt > 0]
                ax.scatter(p_bbt, p_avg, color=Pl.get_plot_color("vo2"),
                           label="averaged breath-by-breath $\dotV_{\mathrm{O}_2}$",
                           s=10)
                ax.scatter(vo2_peak_t, np.max(avg_bbb_vo2_norm), color=Pl.get_plot_color("vo2"),
                           marker="X", s=80)

                # label plot
                ax.set_xticks([warmup_end, m_u_t, vo2_peak_t])
                ax.set_xticklabels([
                    0,
                    int(m_u_t - warmup_end),
                    int(vo2_peak_t - warmup_end)
                ])
                ax.set_xlabel("time since exercise started (s)")
                ax2.set_ylabel("power (W)")
                ax.set_ylabel("normalised flow/uptake")

                # legends
                ax.legend(loc=2)
                ax2.legend(loc=4)

                print(df_row)

                # formant plot
                plt.tight_layout()
                plt.show()
                plt.close()

    return results.sort_values(by=['participant', 'power (W)'])


if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. "
                               "[file=%(filename)s:%(lineno)d]")
    results = get_vo2_predictions(show_plot=True)

    print("\n \n OVERVIEW TABLE \n \n")

    print(results.to_string())
    print("mean error ", results["prediction error"].mean(), "std", results["prediction error"].std())
