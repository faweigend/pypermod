import logging

import matplotlib.pyplot as plt
import numpy as np
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulator.study_simulator import StudySimulator


def simulate_bartram(plot: bool = False, hz: int = 1) -> dict:
    """
    Runs the whole comparison on observations by Bartram et al.
    :param plot: whether the overview should be plotted or not
    :param hz: Simulation computations per second. 1/hz defines delta t for used agents
    :return: predicted and ground truth measurements in a dict
    """

    # measures taken from Bartram et al.
    w_p = 23300
    cp = 393

    # intensities and time frames tested by Bartram et al
    p_recs = [cp, cp - 50, cp - 100, cp - 150, cp - 200]
    p_exp = cp + (0.3 * w_p) / 30
    t_rec = 60
    rec_times = np.arange(0, 130, 10)

    # three component hydraulic agent configuration fitted to
    # W' and CP group averages reported by Bartram et al.
    p = [28295.84803812729,
         115866.92894681037,
         393.69013448575697,
         125.81789182612417,
         10.42071828931923,
         0.8323218320947604,
         0.034587477091268214,
         0.13458173082205677]

    # setup all used agents
    bart = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    skib = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    weig = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
    hyd = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                            the=p[5], gam=p[6], phi=p[7])
    agents = [skib, weig, hyd, bart]

    # run simulations for all dcp conditions
    dcp_results = []
    ground_truth_v = []
    for p_rec in p_recs:
        result = StudySimulator.standard_comparison(agents=agents, p_exp=p_exp, p_rec=p_rec, rec_times=rec_times)
        dcp_results.append(result)

        # add ground truth as bartram simulation
        gt_ratio = StudySimulator.get_recovery_ratio_caen(bart, p_exp=p_exp, p_rec=p_rec, t_rec=t_rec)
        ground_truth_v.append(gt_ratio)

    # create overview plot if required
    if plot:
        # plot setup
        PlotLayout.set_rc_params()
        fig, axes = plt.subplots(nrows=1, ncols=len(dcp_results),
                                 sharex=True, sharey=True,
                                 figsize=(10, 4))

        for i, result in enumerate(dcp_results):
            for p_res_key, p_res_val in result.items():
                axes[i].plot(rec_times, p_res_val,
                             color=PlotLayout.get_plot_color(p_res_key),
                             linestyle=PlotLayout.get_plot_linestyle(p_res_key))
            axes[i].scatter(t_rec, ground_truth_v[i], color=PlotLayout.get_plot_color("ground_truth"))

        for i, ax in enumerate(axes):
            ax.set_title(r'$D_{CP}$' + "{}".format(cp - p_recs[i]))

            ax.set_xticks([0, t_rec, rec_times[-1]])
            ax.set_xticklabels([0, t_rec, rec_times[-1]])
            ax.grid(axis="y", linestyle=':', alpha=0.5)

            if i == 2:
                ax.set_xlabel("recovery time (sec)")
            if i == 0:
                ax.set_ylabel(r'$W\prime_{bal}$' + " recovery ratio (%)")
                ax.set_yticks([25, 50, 75])
                ax.set_yticklabels([25, 50, 75])

        # Create the legend
        handles = PlotLayout.create_standardised_legend(agents=dcp_results[0].keys(), ground_truth=True)
        fig.legend(handles=handles, loc='upper center', ncol=5)
        fig.suptitle("expenditure intensity: " + r'$P100$' + "\n recovery:", y=0.88, fontsize="medium")
        # finish plot
        plt.tight_layout()
        plt.subplots_adjust(top=0.70, bottom=0.13)
        plt.show()
        plt.close(fig=fig)

    # assemble results dict for big comparison
    ret_results = {}
    names = ["DCP0", "DCP50", "DCP100", "DCP150", "DCP200"]
    for i, name in enumerate(names):
        comp_name = "P100 {} T60".format(name)
        ret_results[comp_name] = {
            PlotLayout.get_plot_label("p_exp"): p_exp,
            PlotLayout.get_plot_label("p_rec"): p_recs[i],
            PlotLayout.get_plot_label("t_rec"): 60,
            PlotLayout.get_plot_label("ground_truth"): ground_truth_v[i]
        }
        for k, v in dcp_results[i].items():
            if k == bart.get_name():
                continue
            ret_results[comp_name][PlotLayout.get_plot_label(k)] = round(v[np.where(rec_times == t_rec)[0][0]], 1)

    return ret_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    simulate_bartram(plot=True, hz=10)
