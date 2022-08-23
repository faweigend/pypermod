import logging
import matplotlib.pyplot as plt
import numpy as np
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from pypermod.simulator.study_simulator import StudySimulator
from pypermod.utility import PlotLayout
from pypermod.agents.hyd_agents.three_comp_hyd_agent import ThreeCompHydAgent

# This script recreates the plot 4.1 of our paper [paper](https://arxiv.org/abs/2108.04510)
if __name__ == "__main__":
    # set logging level to the highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

# set matplotlib parameters to standard
PlotLayout.set_rc_params()

# simulation precision
hz = 10

# parameters for W'bal agents
w_p = 23300
cp = 393

# parameters for hydraulic agent
p = [
    23111.907625379536,
    65845.27856132743,
    391.57216549178816,
    148.88277278309968,
    24.148071239095923,
    0.7300850921939723,
    0.010572800716668246,
    0.24210496214582158
]

# instantiate all agents
bart = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
skib = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
weig = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)
hyd = ThreeCompHydAgent(hz=hz, lf=p[0], ls=p[1],
                        m_u=p[2], m_ls=p[3], m_lf=p[4],
                        the=p[5], gam=p[6], phi=p[7])

# store agents in a list
agents = [skib, weig, bart, hyd]

# simulation parameters
rec_times = np.arange(0, 380, 10)  # all recovery times to be estimated
p_rec = cp * 0.33  # recovery intensity
# we simulate recovery after four distinct work intensities. Labels state the predicted time to exhaustion in seconds
# As an example 100 means predicted to lead to exhaustion in 100 seconds. The intensities are estimated in the next step
p_work_labels = [
    100,  # bartram
    240,
    360,
    480  # weigend
]
# estimate intensities from labels using the critical power model equation
p_works = [cp + w_p / x for x in p_work_labels]

# create the matplotlib figure
fig, axes = plt.subplots(1, 4, figsize=(10, 4))
legend_handles = []

# one plot for every p_work setting
for i in range(4):

    # simulate p_work, p_rec, and rec_times for all agents
    results = StudySimulator.standard_comparison(agents=agents, p_work=p_works[i], p_rec=p_rec, rec_times=rec_times)

    # parse simulation results from returned dict and plot into axes objects
    for p_res_key, p_res_val in results.items():
        axes[i].plot(rec_times, p_res_val,
                     color=PlotLayout.get_plot_color(p_res_key),
                     linestyle=PlotLayout.get_plot_linestyle(p_res_key))
    if i == 0:  # bartram observations
        axes[i].scatter(60, results[bart.get_name()][6])
    if i == 3:  # weigend observations
        axes[i].scatter([120, 240, 360], [42.0, 52.0, 59.5])

    # create a nicely formatted p_work and p_rec title
    axes[i].set_title(
        "$P_{\mathrm{work}} = P" + str(p_work_labels[i]) + "{}$ \n  $P_{\mathrm{rec}}   = 33\%$ of $CP$"
    )
    # add some grid lines
    axes[i].grid(linestyle=":", axis="y")
    # format ticks and labels
    axes[i].set_yticks([0, 25, 50, 75])
    if i == 0:
        axes[i].set_yticklabels(["0%", "25%", "50%", "75%"])
    else:
        axes[i].set_yticklabels([])
    axes[i].set_xticks([120, 240, 360])

# plot a standardised legend above
legend_handles = PlotLayout.create_standardised_legend(agents=[x.get_name() for x in agents],
                                                       ground_truth=True,
                                                       errorbar=False)
fig.legend(handles=legend_handles,
           loc='upper center',
           ncol=5,
           labelspacing=0.)
fig.text(0.5, 0.04, '$T_{\mathrm{rec}}$ (seconds)', ha='center')
fig.text(0.01, 0.5, 'recovery ratio (%)', va='center', rotation='vertical')

# finish the plot
plt.tight_layout()
plt.subplots_adjust(left=0.09, bottom=0.17, right=0.99, top=0.74)
plt.show()
plt.close(fig)
