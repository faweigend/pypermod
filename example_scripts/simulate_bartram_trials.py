import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_modeling.agents.cp_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator

if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1
    # measures taken from Bartram et al.
    w_p = 23300
    cp = 393

    # arbitrarily defined recovery intensity
    p_rec = cp * 0.5
    p_exp = cp + (0.3 * w_p) / 30
    rec_times = np.arange(0, 420, 5)

    # three component hydraulic agent configuration
    ps = [
        [28295.84803812729,
         115866.92894681037,
         393.69013448575697,
         125.81789182612417,
         10.42071828931923,
         0.8323218320947604,
         0.034587477091268214,
         0.13458173082205677]
    ]

    # use simulation function to obtain results
    results = StudySimulator.standard_comparison(w_p=w_p, cp=cp, hyd_agent_configs=ps,
                                                 p_exp=p_exp, p_rec=p_rec, rec_times=rec_times, hz=hz)

    # setup ground truth values and print error measurements
    ground_truth_t = [60]
    bartram_agent = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=1)
    ground_truth_v = [StudySimulator.get_recovery_ratio_caen(bartram_agent,
                                                             p_exp=p_exp,
                                                             p_rec=p_rec,
                                                             t_rec=t) for t in ground_truth_t]
    ground_truth_p_exp = [p_exp]
    ground_truth_p_rec = [p_rec]
    StudySimulator.get_standard_error_measures(w_p=w_p, cp=cp,
                                               hyd_agent_configs=ps, hz=hz,
                                               ground_truth_t=ground_truth_t,
                                               ground_truth_v=ground_truth_v,
                                               ground_truth_p_exp=ground_truth_p_exp,
                                               ground_truth_p_rec=ground_truth_p_rec)

    # plot setup
    PlotLayout.set_rc_params()
    fig = plt.figure(figsize=(8, 5))
    ax = fig.add_subplot()

    ax.scatter(ground_truth_t, ground_truth_v,
               color=PlotLayout.get_plot_color("ground_truth"),
               linestyle=PlotLayout.get_plot_linestyle("ground_truth"))

    # plot simulated agent data
    for p_res_key, p_res_val in results.items():
        ax.plot(rec_times,
                p_res_val,
                linestyle=PlotLayout.get_plot_linestyle(p_res_key),
                color=PlotLayout.get_plot_color(p_res_key))

    # finalise layout
    if p_rec < 50:
        prec_label = "{}W".format(p_rec)
    else:
        prec_label = "{:0>2}CP".format(round((p_rec / cp) * 100.0))

    ax.set_title(r'$P100$' +
                 r'$\rightarrow {}$'.format(prec_label))
    ax.set_xlabel("recovery bout duration (sec)")
    # ax.set_xticks([120, 240, 360])
    ax.set_ylabel("W' recovery ratio (%)")

    # Create the legend
    handles = PlotLayout.create_standardised_legend(agents=results.keys(), ground_truth=True)
    ax.legend(handles=handles)

    # finish plot
    plt.subplots_adjust(right=0.96)
    plt.show()
    plt.close(fig=fig)
