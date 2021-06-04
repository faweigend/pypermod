import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from w_pm_modeling.performance_modeling_utility import PlotLayout
from w_pm_modeling.simulate.study_simulator import StudySimulator


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
    hydr = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2],
                             m_ans=p[3], m_anf=p[4], the=p[5], gam=p[6], phi=p[7])

    # all three other defined W'bal ODE agents
    skib = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    bart = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    weig = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)

    # use simulation function to obtain results
    agents = [skib, bart, weig, hydr]
    results = defaultdict(list)
    for agent in agents:
        for p_rec in p_recs:
            rec_ratio = StudySimulator.get_recovery_ratio_caen(agent, p_exp=p_exp, p_rec=p_rec, t_rec=t_rec)
            results[agent.get_name()].append(rec_ratio)

    # make bartram agent observations the ground truth
    results["ground_truth"] = results.pop(bart.get_name())

    # create overview plot if required
    if plot is True:
        # plot setup
        PlotLayout.set_rc_params()
        fig = plt.figure(figsize=(5, 5))
        ax = fig.add_subplot(1, 1, 1)

        for p_res_key, p_res_val in results.items():
            ax.scatter(np.arange(len(p_res_val)), p_res_val,
                       color=PlotLayout.get_plot_color(p_res_key),
                       marker=PlotLayout.get_plot_marker(p_res_key),
                       s=60)

        ax.set_title("expenditure P100\nrecovery time 60 sec")
        ax.set_xlabel("recovery intensity (" + r'$D_{CP}$' + ")")
        ax.set_xticks(np.arange(len(p_recs)))
        ax.set_xticklabels([50, 100, 150, 200])
        ax.set_ylabel(r'$W\prime_{bal}$' + " recovery ratio (%)")
        ax.grid(axis="y", linestyle=':', alpha=0.5)

        # Create the legend
        handles = PlotLayout.create_standardised_legend(agents=results.keys(),
                                                        scatter=True)
        ax.legend(handles=handles)

        # finish plot
        plt.show()
        plt.close(fig=fig)

    # assemble results dict for big comparison
    ret_results = {}
    names = ["P100 DCP0 T60", "P100 DCP50 T60", "P100 DCP100 T60", "P100 DCP150 T60", "P100 DCP200 T60"]
    for i, name in enumerate(names):
        ret_results[name] = {
            PlotLayout.get_plot_label("p_exp"): p_exp,
            PlotLayout.get_plot_label("p_rec"): p_recs[i],
            PlotLayout.get_plot_label("t_rec"): 60,
            PlotLayout.get_plot_label(bart.get_name()): None
        }
        for k, v in results.items():
            ret_results[name][PlotLayout.get_plot_label(k)] = v[i]

    return ret_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    simulate_bartram(plot=True)
