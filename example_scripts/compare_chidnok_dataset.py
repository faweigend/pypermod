import logging

import matplotlib.pyplot as plt
import numpy as np
from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_fix_tau import WbalODEAgentFixTau
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from pypermod.utility import PlotLayout
from pypermod.simulator.study_simulator import StudySimulator

from example_scripts.fitting_tau_chidnok import fit_taus_chidnok


def compare_chidnok_dataset(plot: bool = False, hz: int = 1) -> dict:
    """
    Runs the whole comparison on observations by Chidnok et al.
    :param plot: whether the overview should be plotted or not
    :param hz: Simulation computations per second. 1/hz defines delta t for used agents
    :return: predicted and ground truth measurements in a dict
    """

    # averaged values from Chidnok et al. paper
    cp = 241
    w_p = 21100

    # predefined intensities from paper
    p_exp = 329
    hig = 173
    med = 95
    low = 20

    # assemble for simulation
    p_recs = [hig, med, low]
    t_rec = 30
    rec_times = np.arange(0, 70, 2)

    # fitting to ground truth values from paper
    ground_truth_fitted = fit_taus_chidnok()
    ground_truth_fit_ratio = []
    for i, tau in enumerate(ground_truth_fitted):
        agent = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz, tau=tau)
        ratio = StudySimulator.get_recovery_ratio_wb1_wb2(agent, p_exp=p_exp, p_rec=p_recs[i], t_rec=t_rec)
        ground_truth_fit_ratio.append(ratio)

    # fitted to Chidnok et al. (w_p=21100, cp=241) with recovery from Caen et al.
    # general settings for three component hydraulic agent
    p = [20047.50153689523,
         115140.99890071881,
         240.68973456248304,
         95.20145903978242,
         10.205583305433073,
         0.7283879087791809,
         0.15441713985950212,
         0.24669788914354474]

    # setup all used agents
    bart = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
    skib = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
    weig = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
    hyd = ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                            the=p[5], gam=p[6], phi=p[7])
    agents = [skib, weig, hyd, bart]

    dcp_results = []
    ground_truth_v = []
    for i, p_rec in enumerate(p_recs):
        result = StudySimulator.standard_comparison(agents=agents, p_exp=p_exp, p_rec=p_rec, rec_times=rec_times)
        dcp_results.append(result)

        fix_tau = WbalODEAgentFixTau(w_p=w_p, cp=cp, hz=hz, tau=ground_truth_fitted[i])
        gt_ratio = StudySimulator.get_recovery_ratio_wb1_wb2(fix_tau, p_exp=p_exp, p_rec=p_rec, t_rec=t_rec)
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
            ax.set_title("{} watts".format(p_recs[i]))

            ax.set_xticks([0, t_rec, rec_times[-1]])
            ax.set_xticklabels([0, t_rec, rec_times[-1]])
            ax.grid(axis="y", linestyle=':', alpha=0.5)

            if i == 1:
                ax.set_xlabel("recovery time (sec)")
            if i == 0:
                ax.set_ylabel(r'$W\prime_{bal}$' + " recovery ratio (%)")
                ax.set_yticks([25, 50, 75])
                ax.set_yticklabels([25, 50, 75])

        # Create the legend
        handles = PlotLayout.create_standardised_legend(agents=dcp_results[0].keys(), ground_truth=True)
        fig.legend(handles=handles, loc='upper center', ncol=5)
        fig.suptitle("expenditure intensity: " + r'$P240$' + "\n recovery:", y=0.88, fontsize="medium")
        # finish plot
        plt.tight_layout()
        plt.subplots_adjust(top=0.70, bottom=0.13)
        plt.show()
        plt.close(fig=fig)

    # assemble dict for model comparison
    ret_results = {}
    for i, p_rec in enumerate(p_recs):
        name = "329 watts {} watts T30".format(p_rec)
        ret_results[name] = {
            PlotLayout.get_plot_label("p_exp"): p_exp,
            PlotLayout.get_plot_label("p_rec"): p_rec,
            PlotLayout.get_plot_label("t_rec"): 30,
            PlotLayout.get_plot_label("ground_truth"): round(ground_truth_fit_ratio[i], 1)
        }
        for k, v in dcp_results[i].items():
            ret_results[name][PlotLayout.get_plot_label(k)] = round(v[np.where(rec_times == t_rec)[0][0]], 1)

    return ret_results


if __name__ == "__main__":
    # general settings
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")
    compare_chidnok_dataset(plot=True, hz=10)
