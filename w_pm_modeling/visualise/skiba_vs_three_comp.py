import itertools
import logging
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.lines as mlines

from w_pm_modeling.agents.cp_agents.cp_agent_bartram import CpAgentBartram
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2012 import CpAgentSkiba2012
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2015 import CpAgentSkiba2015
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.simulation.simulator_basis import SimulatorBasis
from w_pm_hydraulic.simulate.three_comp_hyd_simulator import ThreeCompHydSimulator

# Measures and formatting for caen values
from w_pm_modeling.performance_modeling_utility import plot_colors, plot_labels

ferguson_measures = {
    "P6 - 20W": [[0, 120, 360, 900], [0, 37.0, 65.0, 86.0]]  # p6 20W
}
caen_measures = {
    "P4 - CP33": [[0, 120, 240, 360], [0, 55, 61, 70.5]],  # p4 cp33
    "P4 - CP66": [[0, 120, 240, 360], [0, 49, 55, 58]],  # p4 cp66
    "P8 - CP33": [[0, 120, 240, 360], [0, 42, 52, 59.5]],  # p8 cp33
    "P8 - CP66": [[0, 120, 240, 360], [0, 38, 37.5, 50]]  # p8 cp33
}
# combined cp33 and cp66 measures
caen_combination = {
    "P4": [[120, 240, 360], [51.8, 57.7, 64.0], [2.8, 4.3, 5.8]],
    "P8": [[120, 240, 360], [40.1, 44.8, 54.8], [3.9, 3.0, 3.8]]
}

caen_colors = {
    "P4 - CP33": "tab:blue",
    "P4 - CP66": "tab:orange",
    "P8 - CP33": "tab:green",
    "P8 - CP66": "tab:red"
}


def simulate_sreedhara_trials(agent_three_comp: ThreeCompHydAgent):
    """
    Simulates trials done by Ferguson et al. with all available recovery agents
    :param agent_three_comp:
    :return: results in a dict
    """
    hz = agent_three_comp.hz
    w_p = 12082  # averages from paper
    cp = 302

    agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

    # exercise intensity at p4
    t_exp = 240
    p_exp = (w_p / t_exp) + cp

    # recovery intensities
    p_rec_l = 20  # low intensity from paper too
    p_rec_m = 188.1  # med intensity
    p_rec_h = 255.5  # high intensity

    # trial combinations T1 - T9
    trials = [p_rec_l, p_rec_m, p_rec_h]

    # results target storing recovery ratios
    trial_results = {
        "ground_truth": {
            p_rec_l: {120: 33.7,
                      360: 40.62,
                      900: 39.01},
            p_rec_m: {120: 18.95,
                      360: 31.51,
                      900: 19.2},
            p_rec_h: {120: 3.31,
                      360: 6.47,
                      900: -15.53}
        },
        "agents": {
        }
    }

    agent_order = [agent_bartram, agent_skiba_2015, agent_three_comp, agent_skiba_2012]

    # get the recovery dynamics for every agent and every recovery intensity
    for agent in agent_order:

        # trials are various recovery intensities
        agent_trials = {}
        for trial in trials:
            dynamics = SimulatorBasis.get_recovery_dynamics_sreedhara(agent,
                                                                      p_exp=p_exp,
                                                                      t_exp=t_exp,
                                                                      p_rec=trial,
                                                                      t_rec=900)
            agent_trials[trial] = dynamics
            logging.info("{} done".format(agent.get_name()))
        trial_results["agents"][agent.get_name()] = agent_trials

    return trial_results


def simulate_bartram_trials(agent_three_comp_list,
                            w_p: float,
                            cp: float,
                            prec: float):
    """
    :param agent_three_comp_list: a list of three comp agents to simulate
    :param w_p: skiba agent parameter to compare to
    :param cp: skiba agent parameter to compare to
    :param prec: recovery intensity
    :return: results in a dict
    """

    hz = agent_three_comp_list[0].hz

    agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

    agents = [agent_skiba_2015, agent_bartram, agent_skiba_2012]

    # trial intensities
    p_exp = cp + (0.3 * w_p) / 30
    p_rec = prec
    recovery_times = list(np.arange(0, 420, 5))
    # results target storing recovery ratios
    trial_results = defaultdict(dict)

    # estimate recovery ratios for integral agents
    for t_rec in recovery_times:
        for agent in agents:
            # get the whole dynamics from the simulator
            ratio = SimulatorBasis.get_recovery_ratio_caen(agent,
                                                           p_exp=p_exp,
                                                           p_rec=p_rec,
                                                           t_rec=t_rec)
            # add recovery ratio to target dict
            trial_results[t_rec].update({agent.get_name(): ratio})

        # add each hydraulic agent with an individual number
        for i, hyd_agent in enumerate(agent_three_comp_list):
            ratio = SimulatorBasis.get_recovery_ratio_caen(hyd_agent,
                                                           p_exp=p_exp,
                                                           p_rec=p_rec,
                                                           t_rec=t_rec)
            trial_results[t_rec].update({
                "{}_{}".format(hyd_agent.get_name(), i): ratio
            })

    return trial_results


def simulate_ferguson_trials(agent_three_comp_list):
    """
    Simulates trials done by Ferguson et al. with all available recovery agents
    :param agent_three_comp_list: list of three comp hyd agents
    :param plot:
    :return: results in a dict
    """
    hz = agent_three_comp_list[0].hz

    w_p = 21600
    cp = 212

    agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

    p6 = 269  # taken from the paper
    p_rec = 20  # from paper too

    # results target storing recovery ratios
    trial_results = {
        "ground_truth": {
            "means": {
                120: 37,
                360: 65,
                900: 86
            },
            "stds": {
                120: 5,
                360: 6,
                900: 4
            }
        },
        "agents": {
        }
    }

    # to get the final plot legend in the right order
    agent_order = [agent_bartram, agent_skiba_2015, agent_skiba_2012]

    for agent in agent_order:
        # get the whole dynamics from the simulator
        dynamics = SimulatorBasis.get_recovery_dynamics_caen(agent,
                                                             p_exp=p6,
                                                             p_rec=p_rec,
                                                             t_rec=900)
        # add recovery ratio to target dict
        trial_results["agents"].update({agent.get_name(): dynamics})
        logging.info("{} done".format(agent.get_name()))

    for i, agent_hyd in enumerate(agent_three_comp_list):
        # get the whole dynamics from the simulator
        dynamics = SimulatorBasis.get_recovery_dynamics_caen(agent_hyd,
                                                             p_exp=p6,
                                                             p_rec=p_rec,
                                                             t_rec=900)
        # add recovery ratio to target dict
        trial_results["agents"].update({
            "{}_{}".format(agent_hyd.get_name(), i): dynamics
        })
        logging.info("{}_{} done".format(agent_hyd.get_name(), i))

    return trial_results


def simulate_caen_2021_trials(agent_three_comp_list):
    """
    :param agent_three_comp_list: list of three comp hyd agents
    :return: results in a dict
    """
    hz = agent_three_comp_list[0].hz

    # means from the paper
    w_p = 19200
    cp = 269

    agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

    p_exp = (w_p / 240) + cp  # 348 in the paper

    get = 179  # from the paper
    p_rec = get * 0.9  # recovery at 90% of GET

    # results target storing recovery ratios
    trial_results = {
        "ground_truth": {
            "means": {
                30: 28.6,
                60: 34.8,
                120: 44.2,
                180: 50.5,
                240: 55.1,
                300: 56.8,
                600: 73.7,
                900: 71.3
            },
            "stds": {
                30: 8.2,
                60: 11.1,
                120: 9.7,
                180: 12.1,
                240: 13.3,
                300: 16.4,
                600: 19.3,
                900: 20.8
            }
        },
        "agents": {
        }
    }

    # to get the final plot legend in the right order
    agent_order = [agent_bartram, agent_skiba_2015, agent_skiba_2012]

    for agent in agent_order:
        # get the whole dynamics from the simulator
        dynamics = SimulatorBasis.get_recovery_dynamics_caen(agent,
                                                             p_exp=p_exp,
                                                             p_rec=p_rec,
                                                             t_rec=900)
        # add recovery ratio to target dict
        trial_results["agents"].update({agent.get_name(): dynamics})
        logging.info("{} done".format(agent.get_name()))

    for i, agent_hyd in enumerate(agent_three_comp_list):
        # get the whole dynamics from the simulator
        dynamics = SimulatorBasis.get_recovery_dynamics_caen(agent_hyd,
                                                             p_exp=p_exp,
                                                             p_rec=p_rec,
                                                             t_rec=900)
        # add recovery ratio to target dict
        trial_results["agents"].update({
            "{}_{}".format(agent_hyd.get_name(), i): dynamics
        })
        logging.info("{}_{} done".format(agent_hyd.get_name(), i))

    return trial_results


def simulate_felippe_trials(agent_three_comp: ThreeCompHydAgent):
    """
    Simulates trials done by Felippe et al. with all available recovery agents
    :param agent_three_comp:
    :return: results in a dict
    """
    hz = agent_three_comp.hz
    w_p = 22000
    cp = 173

    agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

    p6 = 223  # taken from the paper
    p_rec = 0  # from paper too (passive recovery)

    # results target storing recovery ratios
    trial_results = {
        "ground_truth": {
            180: (142.0 / 377.0) * 100.0,
            360: (180.0 / 397.0) * 100.0,
            900: (254.0 / 400.0) * 100.0
        },
        "agents": {
        }
    }

    # to get the final plot legend in the right order
    agent_order = [agent_bartram, agent_skiba_2015, agent_skiba_2012, agent_three_comp]

    for agent in agent_order:
        # get the whole dynamics from the simulator
        dynamics = SimulatorBasis.get_recovery_dynamics_caen(agent,
                                                             p_exp=p6,
                                                             p_rec=p_rec,
                                                             t_rec=900)
        # add recovery ratio to target dict
        trial_results["agents"].update({agent.get_name(): dynamics})
        logging.info("{} done".format(agent.get_name()))

    return trial_results


def simulate_chidnok_trials(agent_three_comp: ThreeCompHydAgent, plot: bool = False):
    """
    Expects the three comp hyd model to be fitted to CP of 241 Watts and W' of 21100 Joule.
    Simulates the trials made by Chidnok et al. 2012
    :param agent_three_comp:
    :param plot:
    :return:
    """

    hz = agent_three_comp.hz

    cp = 241
    w_p = 21100

    agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

    agents = [agent_skiba_2012, agent_skiba_2015, agent_three_comp, agent_bartram]

    # predefined intensities by paper
    p6_p = 329
    sev = 270
    hig = 173
    med = 95
    low = 20

    # experimental trials
    trials = [(p6_p, sev), (p6_p, hig), (p6_p, med), (p6_p, low)]
    # results target with ground truth
    trial_results = {
        "ground_truth": {
            (p6_p, sev): {"T": 323, "std": 29},
            (p6_p, hig): {"T": 557, "std": 90},
            (p6_p, med): {"T": 759, "std": 243},
            (p6_p, low): {"T": 1224, "std": 497}
        }
    }

    # now all the trials
    for trial in trials:
        # history for debug plots
        w_p_hist_2015 = [agent_skiba_2015.w_p]
        w_p_hist_2012 = [agent_skiba_2012.w_p]
        w_p_hist_bart = [agent_bartram.w_p]

        # 2700 steps of trial0 intervals of 30 interspaced with trial1 intervals of 60
        whole_test = ([trial[0]] * 60 + [trial[1]] * 30) * 30
        for agent in agents:
            bal = SimulatorBasis.simulate_course(agent=agent,
                                                 course_data=whole_test)
            try:
                end_t = bal.index(0)

                # add a dict if necessary
                if agent.get_name() not in trial_results:
                    trial_results[agent.get_name()] = {}

                trial_results[agent.get_name()].update({trial: {"T": end_t}})

            except ValueError:
                end_t = len(bal)

            # if agent is a cp agent, keep track of w_p bal
            if isinstance(agent, CpAgentSkiba2012):
                w_p_hist_2012 = bal[0:end_t]
            if isinstance(agent, CpAgentBartram):
                w_p_hist_bart = bal[0:end_t]
            if isinstance(agent, CpAgentSkiba2015):
                w_p_hist_2015.append(agent.get_w_p_balance())

        # some debug plots
        if plot is True:
            fig = plt.figure()
            ax = fig.add_subplot()
            ax.plot(w_p_hist_2012, label=plot_labels[agent_skiba_2012.get_name()])
            ax.plot(w_p_hist_bart, label=plot_labels[agent_bartram.get_name()])
            ax.plot(w_p_hist_2015, label=plot_labels[agent_skiba_2015.get_name()])
            ax.axvline(60)
            ax.axvline(90)
            ax.legend()
            plt.show()
            plt.close(fig=fig)

    return trial_results


def simulate_skiba_2014_trials(agent_three_comp: ThreeCompHydAgent,
                               w_p: int,
                               cp: int,
                               plot: bool = False):
    """
    Simulates trials from the skiba 2014 publication Effect of Work and Recovery Durations on W'
    Reconstitution during Intermittent Exercise. https://insights.ovid.com/crossref?an=00005768-201407000-00020
    :param agent_three_comp: three comp agent to simulate
    :param w_p: skiba agent parameter to compare to
    :param cp: skiba agent parameter to compare to
    :param plot: whether debug plots should be shown
    :return: results in a dict
    """

    hz = agent_three_comp.hz
    agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)
    integral_agents = [agent_skiba_2012]

    agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
    agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
    differential_agents = [agent_three_comp, agent_skiba_2015, agent_bartram]

    # p4 equals p6+, which is p6 plus 50% diff p6 and cp
    p4 = (w_p / 240) + cp
    # recovery is simply at 20 Watts
    p_rec = 20

    trials = [(20, 5), (20, 10), (20, 20),
              (20, 30), (40, 30), (60, 30)]
    trial_results = defaultdict(dict)

    for trial in trials:

        # search for the number of bouts that results in W'exp of ~50%
        balance = w_p
        num_of_intervals = 0

        # Derive the optimal amount of work and recovery bouts (W'exp of ~50%)
        while True:
            # set up the total test with the increasing number of work and recovery bouts
            num_of_intervals += 1
            total_test = ([p4] * trial[0] + [p_rec] * trial[1]) * num_of_intervals
            bal_hist = agent_skiba_2012.estimate_w_p_bal_to_data(total_test)

            # check balance
            balance_before = balance
            balance = bal_hist[-1]

            if balance <= w_p / 2:
                # use the other opt if balance shrunk too much
                if abs(balance - w_p / 2) > abs(balance_before - w_p / 2):
                    print("balance: ", balance, abs(balance - w_p / 2), " 50%: ", w_p / 2, "BALANCE_BEFORE: ",
                          balance_before, abs(balance_before - w_p / 2))
                    num_of_intervals -= 1
                else:
                    print("BALANCE: ", balance, abs(balance - w_p / 2), " 50%: ", w_p / 2, "balance_before: ",
                          balance_before, abs(balance_before - w_p / 2))
                break

        p_traces = {}

        # run test for integral agents
        for agent in integral_agents:
            # assemble whole protocol
            p_intervals = ([p4] * trial[0] + [p_rec] * trial[1]) * num_of_intervals
            p_exhaust = [p4] * 3000
            p_total = p_intervals + p_exhaust
            # get W'bal history from agent
            bal_hist = agent.estimate_w_p_bal_to_data(p_total)
            # find point of exhaustion
            # Exhaust was used to just get the time of the final exhaustive bout.
            # But turned out to be impractical because of the 50% depletion protocol before
            exhaust_start = len(p_intervals)
            t_end = bal_hist.index(0)  # - exhaust_start
            # estimate total workload
            w_total = sum(bal_hist[exhaust_start:t_end])
            trial_results[trial].update({"W_{}".format(agent.get_name()): w_total,
                                         "T_{}".format(agent.get_name()): t_end})
            # plot the p_trace later on
            p_traces.update({agent.get_name(): bal_hist[0:bal_hist.index(0)]})

        # run test for differential agents
        for agent in differential_agents:
            agent.reset()
            w_total = 0
            w_bal_hist = []

            # do the intermittent part (A)
            for i in range(num_of_intervals):
                # work bout
                agent.set_power(p4)
                for step in range(0, trial[0] * hz):
                    step_power = agent.perform_one_step()
                    w_total += step_power
                    w_bal_hist.append(step_power)
                # recovery bout
                agent.set_power(p_rec)
                for step in range(0, trial[1] * hz):
                    step_power = agent.perform_one_step()
                    w_total += step_power
                    w_bal_hist.append(step_power)

            # this was used to just get the time of the final exhaustive bout.
            # But turned out to be impractical because of the 50% depletion protocol before
            # exhaust_start = agent.get_time()
            exhaust_hist = []
            # exhaust agent (B)
            steps = 0
            agent.set_power(p4)
            while agent.is_exhausted() is False and steps < 3000:
                step_power = agent.perform_one_step()
                w_total += step_power
                steps += 1
                w_bal_hist.append(step_power)
                exhaust_hist.append(step_power)

            trial_results[trial].update({"W_{}".format(agent.get_name()): sum(exhaust_hist),
                                         "T_{}".format(agent.get_name()): agent.get_time()})  # - exhaust_start})

            p_traces.update({agent.get_name(): w_bal_hist})

        # some debug plots
        if plot is True:
            fig = plt.figure()
            ax = fig.add_subplot()
            for k, v in p_traces.items():
                ax.plot(v, label=k)
            ax.axvline(trial[0])
            ax.axvline(trial[0] + trial[1])
            ax.legend()
            plt.show()
            plt.close(fig=fig)

    return trial_results


def simulate_caen_trials(agent_three_comp: ThreeCompHydAgent,
                         w_p: int,
                         cp: int):
    """
    simulates the trials by Caen et al. and compares available agents to it
    :param agent_three_comp:
    :param w_p:
    :param cp:
    :return: recovery ratio results and ground truth in a dict
    """
    hz = agent_three_comp.hz
    agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
    agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
    differential_agents = [agent_three_comp, agent_skiba_2015, agent_bartram]

    agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)
    integral_agents = [agent_skiba_2012]

    # power level and recovery level estimations for the trials
    p_4 = (w_p + 240 * cp) / 240
    p_8 = (w_p + 480 * cp) / 480
    cp_33 = cp * 0.33
    cp_66 = cp * 0.66

    # create all the comparison trials
    trials = [(p_4, cp_33, 120),
              (p_4, cp_33, 240),
              (p_4, cp_33, 360),
              (p_4, cp_66, 120),
              (p_4, cp_66, 240),
              (p_4, cp_66, 360),
              (p_8, cp_33, 120),
              (p_8, cp_33, 240),
              (p_8, cp_33, 360),
              (p_8, cp_66, 120),
              (p_8, cp_66, 240),
              (p_8, cp_66, 360)]

    # plot the data
    trial_results = {
        (p_4, cp_33, 120): {"ground_truth": 55.0},
        (p_4, cp_33, 240): {"ground_truth": 61.0},
        (p_4, cp_33, 360): {"ground_truth": 70.5},
        (p_4, cp_66, 120): {"ground_truth": 49.0},
        (p_4, cp_66, 240): {"ground_truth": 55.0},
        (p_4, cp_66, 360): {"ground_truth": 58.0},
        (p_8, cp_33, 120): {"ground_truth": 42.0},
        (p_8, cp_33, 240): {"ground_truth": 52.0},
        (p_8, cp_33, 360): {"ground_truth": 59.5},
        (p_8, cp_66, 120): {"ground_truth": 38.0},
        (p_8, cp_66, 240): {"ground_truth": 37.5},
        (p_8, cp_66, 360): {"ground_truth": 50.0},
    }

    # estimate agent ratios
    for trial in trials:
        p_exp, p_rec, t_rec = trial

        # estimate recovery ratios for integral agents
        for agent in integral_agents:
            ratio = agent.get_recovery_ratio(p_exp, p_rec, t_rec)
            trial_results[trial].update({agent.get_name(): ratio})

        # now for the differential agents
        for agent in differential_agents:
            # exhaust agent first time
            steps = 0
            agent.reset()
            agent.set_power(p_exp)
            while agent.is_exhausted() is False and steps < 3000:
                agent.perform_one_step()
                steps += 1
            if agent.is_exhausted() is False:
                raise UserWarning("Exhaustion not reached")
            t1 = agent.get_time()

            # recover agent for trial recovery time
            agent.set_power(p_rec)
            for _ in range(t_rec * hz):
                agent.perform_one_step()
            t2 = agent.get_time()

            # exhaust agent second time
            steps = 0
            agent.set_power(p_exp)
            while agent.is_exhausted() is False and steps < 3000:
                agent.perform_one_step()
                steps += 1
            t3 = agent.get_time()

            # add recovery ratio to target dict
            trial_results[trial].update({agent.get_name(): ((t3 - t2) / t1) * 100.0})

    return trial_results


def exhaustion_comparison_overview(cp_agent, three_comp_agent=None, axis=None):
    """
    plots a TTE curve for CP agent and matches it to
    three comp agent times to exhaustion
    :param cp_agent:
    :param three_comp_agent:
    """

    if axis is None:
        fig = plt.figure(figsize=(8, 5))
        # plot curve
        ax = fig.add_subplot(1, 1, 1)
    else:
        fig = None
        ax = axis

    w_p = cp_agent.w_p
    cp = cp_agent.cp

    ts_ext = np.arange(120, 901, 20)
    ts = [120, 240, 360, 600, 900]
    powers = [((w_p + x * cp) / x) for x in ts]
    powers_ext = [((w_p + x * cp) / x) for x in ts_ext]

    # plot CP curve
    # times = [CpBasisSimulator.simulate_tte(skiba_agent, x) for x in powers_ext]
    ax.plot(ts_ext, powers_ext, linestyle='-', label="two parameter\nmodel", color="tab:pink")

    # mark P4 and P8
    ax.scatter(ts, powers, color="tab:pink")
    ax.get_xaxis().set_ticks(ts)
    ax.set_xticklabels([int(p / 60) for p in ts])
    ax.get_yaxis().set_ticks(powers)
    ax.set_yticklabels(["P{}".format(int(p / 60)) for p in ts])

    # plot three comp agent
    if three_comp_agent is not None:
        hyd_fitted_times_ext = [ThreeCompHydSimulator.simulate_tte_hydraulic_detail(three_comp_agent, x) for x in
                                powers_ext]
        hyd_powers_ext = powers_ext
        ax.plot(hyd_fitted_times_ext, hyd_powers_ext,
                linestyle='-', label="three component\nmodel", color="tab:cyan")

        # scatter just a few
        hyd_fitted_times = [ThreeCompHydSimulator.simulate_tte_hydraulic_detail(three_comp_agent, x) for x in powers]
        hyd_powers = powers
        ax.scatter(hyd_fitted_times, hyd_powers, color="tab:cyan")

    ax.axhline(y=cp,
               color='r',
               label="critical power (CP)",
               linestyle="--")

    # label axis and lines
    ax.set_xlabel("time to exhaustion (min)")
    # ax.set_ylim((0, max(powers)))
    ax.set_ylabel("power (W)")
    ax.legend()
    # ax.set_xlim((0, max(times)))
    # ax.set_yscale('log')
    # ax.set_xscale('log')

    # if no axis object was sent, display result
    if axis is None:
        plt.tight_layout()
        plt.show()
        plt.close(fig)


def multiple_exhaustion_comparison_overview(w_p: float, cp: float, ps: list, black_and_white: bool = False):
    """
    :param cp_agent:
    :param ps: a list of agent parameters
    """

    # some journals request black and white plots
    if black_and_white is True:
        hyd_color = "tab:green"
        two_p_color = "tab:black"
    else:
        hyd_color = plot_colors["ThreeCompHydAgent"]
        two_p_color = plot_colors["ground_truth"]

    fig = plt.figure(figsize=(8, 3.4))
    # plot curve
    ax = fig.add_subplot(1, 1, 1)

    resolution = 1

    ts_ext = np.arange(120, 1801, 20 / resolution)
    ts = [120, 240, 360, 600, 900, 1800]
    powers = [((w_p + x * cp) / x) for x in ts]
    powers_ext = [((w_p + x * cp) / x) for x in ts_ext]

    # mark P4 and P8
    ax.get_xaxis().set_ticks(ts)
    ax.set_xticklabels([int(p / 60) for p in ts])

    # ax.get_yaxis().set_ticks(powers)
    # ax.set_yticklabels(["P{}".format(int(p / 60)) for p in ts])
    ax.get_yaxis().set_ticks([])
    ax.set_yticklabels([])

    # small zoomed in detail window
    insert_ax = ax.inset_axes([0.3, 0.40, 0.3, 0.45])
    detail_obs = resolution * 5
    detail_ts = [120, 150, 180, 210]
    # detail_ps = [((w_p + x * cp) / x) for x in detail_ts]
    detail_ps = []

    # plot three comp agent
    for p in ps:
        three_comp_agent = ThreeCompHydAgent(hz=1, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                             the=p[5], gam=p[6], phi=p[7])

        hyd_fitted_times_ext = [ThreeCompHydSimulator.simulate_tte_hydraulic_detail(three_comp_agent, x) for x in
                                powers_ext]
        hyd_powers_ext = powers_ext
        ax.plot(hyd_fitted_times_ext, hyd_powers_ext,
                linestyle='-', linewidth=1, color=hyd_color)

        insert_ax.plot(hyd_fitted_times_ext[:detail_obs], hyd_powers_ext[:detail_obs],
                       linestyle='-', linewidth=1, color=hyd_color)

    # plot CP curve
    insert_ax.plot(ts_ext[:detail_obs], powers_ext[:detail_obs],
                   linestyle='-', linewidth=2, label="critical power\nmodel", color=two_p_color)
    ax.plot(ts_ext, powers_ext,
            linestyle='-', linewidth=2, label="critical power\nmodel", color=two_p_color)

    # to get the nice 2, 2.5, 3, 3.5 view
    formatted = []
    for p in detail_ts:
        val = round((p / 60), 1)
        if val % 1 == 0:
            formatted.append(int(val))
        else:
            formatted.append(val)

    insert_ax.get_xaxis().set_ticks(detail_ts)
    insert_ax.set_xticklabels(formatted)
    insert_ax.get_yaxis().set_ticks(detail_ps)
    insert_ax.set_yticklabels(["P{}".format(p) for p in formatted])
    insert_ax.set_title("detail view")

    # label axis and lines
    ax.set_xlabel("time to exhaustion (min)")
    ax.set_ylabel("intensity (watt)", labelpad=10)
    # insert number of models only if more than 1 was plotted
    if len(ps) > 1:
        ax.plot([], linestyle='-', linewidth=1, color=hyd_color, label="hydraulic model ({})".format(len(ps)))
    else:
        ax.plot([], linestyle='-', linewidth=1, color=hyd_color, label="hydraulic model")
    ax.legend()
    # ax.grid(axis='y')

    plt.tight_layout()
    plt.show()
    plt.close(fig)


def multiple_caen_recovery_overview_cp_distinct(w_p: float, cp: float, ps: list,
                                                black_and_white: bool = False,
                                                cp_distinct: bool = True):
    if black_and_white is True:
        c_colors = ["black", "black", "black", "black"]
        hyd_color = "tab:grey"
    else:
        c_colors = [plot_colors["ground_truth"]] * 4
        hyd_color = plot_colors["ThreeCompHydAgent"]

    # power level and recovery level estimations for the trials
    p_4 = (w_p + 240 * cp) / 240
    p_8 = (w_p + 480 * cp) / 480
    cp_33 = cp * 0.33
    cp_66 = cp * 0.66

    # create all the comparison trials
    exp_ps = [p_4, p_8]
    rec_ps = [cp_33, cp_66]
    rec_ts = [10, 20, 25, 30, 35, 40, 45, 50, 60, 70, 90, 110, 130, 150, 170, 240, 300, 360]
    # rec_ts = [120, 240, 360]

    # set up the values and formatting
    caen = list(caen_measures.values())
    names = list(caen_measures.keys())

    # Create the grid plot
    fig = plt.figure(figsize=(8, 3.4))
    axes = []

    if cp_distinct is True:
        # changed order to rearrange recovery plots in overview
        axes.append(fig.add_subplot(2, 2, 1))
        axes.append(fig.add_subplot(2, 2, 2))
        axes.append(fig.add_subplot(2, 2, 3))
        axes.append(fig.add_subplot(2, 2, 4))
    else:
        # only two plots with combined recovery intensities
        axes.append(fig.add_subplot(1, 2, 1))
        axes.append(fig.add_subplot(1, 2, 2))

    # add three component model data
    for p in ps:
        # set up agent according to parameters set
        three_comp_agent = ThreeCompHydAgent(hz=1, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                             the=p[5], gam=p[6], phi=p[7])

        # data will be stored in here
        three_comp_data = []
        # let the created agend do all the trial combinations
        combs = list(itertools.product(exp_ps, rec_ps))
        for comb in combs:
            rec_times, rec_percent = [0], [0]
            for rt in rec_ts:
                ratio = SimulatorBasis.get_recovery_ratio_caen(three_comp_agent, comb[0], comb[1], rt)
                rec_times.append(rt)
                rec_percent.append(ratio)
            three_comp_data.append([rec_times, rec_percent])

        if cp_distinct is True:
            # plot a line for each combination for the created agent
            for i, data in enumerate(three_comp_data):
                axes[i].plot(three_comp_data[i][0], three_comp_data[i][1],
                             linestyle='-', linewidth=1, color=hyd_color)
        else:
            # sort into p4s and p8s
            p4s, p8s = [], []
            for i, comb in enumerate(combs):
                if comb[0] == exp_ps[0]:
                    p4s.append(three_comp_data[i][1])
                else:
                    p8s.append(three_comp_data[i][1])

            # get the means
            p4s = [(p4s[0][x] + p4s[1][x]) / 2 for x in range(len(p4s[0]))]
            p8s = [(p8s[0][x] + p8s[1][x]) / 2 for x in range(len(p8s[0]))]
            # plot into both available axes
            axes[0].plot(three_comp_data[0][0], p4s, linestyle='-', linewidth=1, color=hyd_color)
            axes[1].plot(three_comp_data[0][0], p8s, linestyle='-', linewidth=1, color=hyd_color)

    if cp_distinct is True:
        # distinct data observed by Caen
        for i, setup in enumerate(caen):
            # axes[i].plot(setup[0], setup[1], linestyle='-', linewidth=1, color=c_colors[i])
            axes[i].scatter(setup[0], setup[1], color=c_colors[i], label="caen {}".format(names[i]))
            # axes[i].set_title("Caen {}".format(names[i]))
    else:
        # combined data reported by Caen
        axes[0].errorbar(caen_combination["P4"][0],
                         caen_combination["P4"][1],
                         caen_combination["P4"][2],
                         label="Caen et al.",
                         linestyle='None',
                         marker='o',
                         capsize=3,
                         color=c_colors[0])
        axes[0].set_title("P4")
        axes[1].errorbar(caen_combination["P8"][0],
                         caen_combination["P8"][1],
                         caen_combination["P8"][2],
                         label="Caen et al.",
                         linestyle='None',
                         marker='o',
                         capsize=3,
                         color=c_colors[1])
        axes[1].set_title("P8")

    # insert number of models only if more than 1 was plotted
    if len(ps) > 1:
        axes[0].plot([], linestyle='-', linewidth=1, color=hyd_color, label="hydraulic model ({})".format(len(ps)))
    else:
        axes[0].plot([], linestyle='-', linewidth=1, color=hyd_color, label="hydraulic model")

    # format axis
    for ax in axes:
        ax.set_ylim(0, 70)
        ax.set_xlim(0, 370)
        ax.set_xticks([0, 120, 240, 360])
        ax.set_xticklabels([0, 2, 4, 6])
        ax.set_yticks([0, 20, 40, 60, 80])
        ax.legend(loc='lower right')
        # ax.grid(axis='y')

    fig.text(0.5, 0.04, 'recovery duration (min)', ha='center')
    fig.text(0.01, 0.5, 'recovery (%)', va='center', rotation='vertical')
    plt.tight_layout()
    plt.subplots_adjust(left=0.09, bottom=0.16, top=0.91)

    plt.show()
    plt.close(fig)


def caen_recovery_overview(w_p, cp, three_comp_agent=None):
    skiba_2015_agent = CpAgentSkiba2015(w_p, cp, 10)
    skiba_2012_agent = CpAgentSkiba2012(w_p, cp)

    # power level and recovery level estimations for the trials
    p_4 = (w_p + 240 * cp) / 240
    p_8 = (w_p + 480 * cp) / 480
    cp_33 = cp * 0.33
    cp_66 = cp * 0.66

    # create all the comparison trials
    exp_ps = [p_4, p_8]
    rec_ps = [cp_33, cp_66]
    # rec_ts = [60, 120, 180, 240, 300, 360]
    rec_ts = [120, 240, 360]

    # set up the values and formatting
    caen = list(caen_measures.values())
    names = list(caen_measures.keys())
    colors = list(caen_colors.values())

    # plot the data
    fig = plt.figure(figsize=(8, 5))
    ax1 = fig.add_subplot(1, 1, 1)

    # get the skiba sim data
    skiba_2012_agent_data = []
    skiba_2015_agent_data = []
    for rec_p in rec_ps:
        rec_times, rec_percent = [0], [0]
        for rt in rec_ts:
            ratio = SimulatorBasis.get_recovery_ratio_caen(skiba_2012_agent, p_4, rec_p, rt)
            rec_times.append(rt)
            rec_percent.append(ratio)
        skiba_2012_agent_data.append([rec_times, rec_percent])

        rec_times, rec_percent = [0], [0]
        for rt in rec_ts:
            ratio = SimulatorBasis.get_recovery_ratio_caen(skiba_2015_agent, p_4, rec_p, rt)
            rec_times.append(rt)
            rec_percent.append(ratio)
        skiba_2015_agent_data.append([rec_times, rec_percent])

    # data observed by Caen
    for i, setup in enumerate(caen):
        ax1.plot(setup[0], setup[1], linestyle='-', label="{}".format(names[i]), color=colors[i], alpha=0.5)
        ax1.scatter(setup[0], setup[1], color=colors[i])

    # add three component model data
    three_comp_data = []
    if three_comp_agent is not None:
        combs = list(itertools.product(exp_ps, rec_ps))
        for comb in combs:
            rec_times, rec_percent = [0], [0]
            for rt in rec_ts:
                ratio = SimulatorBasis.get_recovery_ratio_caen(three_comp_agent, comb[0], comb[1], rt)
                rec_times.append(rt)
                rec_percent.append(ratio)
            three_comp_data.append([rec_times, rec_percent])

        for i, data in enumerate(three_comp_data):
            ax1.plot(three_comp_data[i][0], three_comp_data[i][1], linestyle=':', color=colors[i],
                     label="three component {}".format(names[i]))

    # include skiba
    ax1.plot(skiba_2012_agent_data[0][0], skiba_2012_agent_data[0][1], linestyle='--', color="tab:grey",
             label="skiba2012 - CP33")
    ax1.plot(skiba_2012_agent_data[1][0], skiba_2012_agent_data[1][1], linestyle='-.', color="tab:grey",
             label="skiba2012 - CP66")

    # format axis
    # ax1.set_ylim(0, 110)
    ax1.set_xlim(0, 370)
    ax1.set_xticks([0, 120, 240, 360])
    ax1.set_xticklabels([0, 2, 4, 6])
    ax1.set_yticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    ax1.legend(loc='upper left')  # , bbox_to_anchor=(1, 1))
    # ax1.legend()
    ax1.set_ylabel("recovery (%)")
    ax1.set_xlabel("recovery duration (min)")

    plt.tight_layout()
    plt.show()
    plt.close(fig)

    # Create the grid plot
    fig = plt.figure(figsize=(14, 8))
    axes = []
    for i in range(4):
        axes.append(fig.add_subplot(2, 2, i + 1))

    # data observed by Caen
    for i, setup in enumerate(caen):
        axes[i].plot(setup[0], setup[1], linestyle='-', label="Caen {}".format(names[i]), color=colors[i], alpha=0.5)
        axes[i].scatter(setup[0], setup[1], color=colors[i])

    # add three component model data
    if three_comp_agent is not None:
        for i, data in enumerate(three_comp_data):
            axes[i].plot(three_comp_data[i][0], three_comp_data[i][1], linestyle=':', color=colors[i],
                         label="three component {}".format(names[i]))

    # axes[0].set_title("P4 - CP33")
    # axes[1].set_title("P4 - CP66")
    # axes[2].set_title("P8 - CP33")
    # axes[3].set_title("P8 - CP66")

    # axes[0].plot(skiba_2012_agent_data[0][0], skiba_2012_agent_data[0][1], linestyle='--', color="tab:grey",
    #              label="skiba2012")
    # axes[0].plot(skiba_2015_agent_data[0][0], skiba_2015_agent_data[0][1], linestyle='-.', color="tab:grey",
    #              label="skiba2015")
    #
    # axes[1].plot(skiba_2012_agent_data[1][0], skiba_2012_agent_data[1][1], linestyle='--', color="tab:grey",
    #              label="skiba2012")
    # axes[1].plot(skiba_2015_agent_data[1][0], skiba_2015_agent_data[1][1], linestyle='-.', color="tab:grey",
    #              label="skiba2015")
    #
    # axes[2].plot(skiba_2012_agent_data[0][0], skiba_2012_agent_data[0][1], linestyle='--', color="tab:grey",
    #              label="skiba2012")
    # axes[2].plot(skiba_2015_agent_data[0][0], skiba_2015_agent_data[0][1], linestyle='-.', color="tab:grey",
    #              label="skiba2015")
    #
    # axes[3].plot(skiba_2012_agent_data[1][0], skiba_2012_agent_data[1][1], linestyle='--', color="tab:grey",
    #              label="skiba2012")
    # axes[3].plot(skiba_2015_agent_data[1][0], skiba_2015_agent_data[1][1], linestyle='-.', color="tab:grey",
    #              label="skiba2015")

    for ax in axes:
        ax.set_ylim(0, 110)
        ax.set_xlim(0, 370)
        ax.set_xticks([0, 120, 240, 360])
        ax.set_yticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        ax.legend()

    axes[0].set_ylabel("recovery (%)")
    axes[2].set_ylabel("recovery (%)")
    axes[2].set_xlabel("recovery duration (s)")
    axes[3].set_xlabel("recovery duration (s)")

    plt.tight_layout()
    plt.show()
    plt.close(fig)


def exp_rec_compare(skiba_agent, three_comp_agent):
    """
    creates exhaustion and recovery time comparison curves
    :param skiba_agent:
    :param three_comp_agent:
    :return:
    """

    cp = skiba_agent.cp

    def do_the_thing(agent, rec_power):
        """gets exhaustion and recovery times for various settings"""
        p, t, r = [], [], []

        for power in range(int(cp * 1.05), cp * 3, 10):
            agent.reset()
            # Exhaust...
            steps = 0
            agent.set_power(power)
            while not agent.is_exhausted() and steps < 10000:
                agent.perform_one_step()
                steps += 1

            p.append(power)
            t.append(agent.get_time())

            # ... and recover
            steps = 0
            agent.set_power(rec_power)
            while not agent.is_equilibrium() and steps < 10000:
                agent.perform_one_step()
                steps += 1
            r.append(agent.get_time() - t[-1])

        return p, t, r

    def plot_the_curves(title: str, skiba_p, skiba_t, skiba_r, hyd_p, hyd_t, hyd_r):
        """creates comparison plot with given lists"""
        # plot the curves
        fig = plt.figure()
        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2, sharey=ax1)

        fig.suptitle(title)

        # ttes
        ax1.plot(skiba_t, skiba_p, linestyle='-', color='tab:green', label="skiba")
        ax1.plot(hyd_t, hyd_p, linestyle='-', color='tab:orange', label="hyd")

        # recovery times
        ax2.plot(skiba_r, skiba_p, linestyle='-', color='tab:green', label="skiba")
        ax2.plot(hyd_r, hyd_p, linestyle='-', color='tab:orange', label="hyd")

        ax1.set_ylabel("power")
        ax1.set_xlabel("time (s)")
        ax2.set_xlabel("time (s)")

        ax1.set_title("expenditure")
        ax2.set_title("recovery")

        ax1.legend()

        plt.tight_layout()
        plt.show()
        plt.close(fig)

    skiba_p, skiba_t, skiba_r = do_the_thing(skiba_agent, 0)
    hyd_p, hyd_t, hyd_r = do_the_thing(three_comp_agent, 0)
    plot_the_curves("rec: 0", skiba_p, skiba_t, skiba_r, hyd_p, hyd_t, hyd_r)

    skiba_p, skiba_t, skiba_r = do_the_thing(skiba_agent, cp * 0.33)
    hyd_p, hyd_t, hyd_r = do_the_thing(three_comp_agent, cp * 0.33)
    plot_the_curves("rec: 33%", skiba_p, skiba_t, skiba_r, hyd_p, hyd_t, hyd_r)

    skiba_p, skiba_t, skiba_r = do_the_thing(skiba_agent, cp * 0.66)
    hyd_p, hyd_t, hyd_r = do_the_thing(three_comp_agent, cp * 0.66)
    plot_the_curves("rec: 66%", skiba_p, skiba_t, skiba_r, hyd_p, hyd_t, hyd_r)


def curve_compare(skiba_agent, three_comp_agent):
    """
    creates exhaustion comparison curves after several recovery times
    :param skiba_agent:
    :param three_comp_agent:
    :return:
    """

    cp = skiba_agent.cp

    def do_the_thing(agent, rec_power, rec_time):
        """gets exhaustion and recovery times for various settings"""
        p, t1, t2 = [], [], []

        for power in range(int(cp * 1.05), cp * 3, 10):
            agent.reset()
            # Exhaust...
            steps = 0
            agent.set_power(power)
            while not agent.is_exhausted() and steps < 10000:
                agent.perform_one_step()
                steps += 1

            p.append(power)
            t1.append(agent.get_time())

            t_time = rec_time + agent.get_time()
            # ... and recover and...
            agent.set_power(rec_power)
            while agent.get_time() < t_time:
                agent.perform_one_step()

            # ...exhaust again.
            t_minus = agent.get_time()
            steps = 0
            agent.set_power(power)
            while not agent.is_exhausted() and steps < 10000:
                agent.perform_one_step()
                steps += 1
            t2.append(agent.get_time() - t_minus)

        return p, t1, t2

    def plot_the_curves(rec_pow, rec_t):
        """creates comparison plot with given lists"""

        skiba_p, skiba_t, skiba_r = do_the_thing(skiba_agent, rec_pow, rec_t)
        hyd_p, hyd_t, hyd_r = do_the_thing(three_comp_agent, rec_pow, rec_t)

        # plot the curves
        fig = plt.figure(figsize=(9, 5))
        ax1 = fig.add_subplot(1, 3, 1)
        ax2 = fig.add_subplot(1, 3, 3, sharey=ax1, sharex=ax1)
        ax3 = fig.add_subplot(1, 3, 2)

        # ttes
        ax1.plot(skiba_t, skiba_p, linestyle='-', color='tab:green', label="skiba")
        ax1.plot(hyd_t, hyd_p, linestyle='-', color='tab:orange', label="hyd")

        # recovery times
        ax2.plot(skiba_r, skiba_p, linestyle='-', color='tab:green', label="skiba")
        ax2.plot(hyd_r, hyd_p, linestyle='-', color='tab:orange', label="hyd")

        ax3.annotate("rec p: {} \nrec t: {}".format(round(rec_pow, 1), round(rec_t)), xy=(0.75, 0.5),
                     xytext=(0.25, 0.5), va="center", arrowprops=dict(arrowstyle="->"))
        ax3.set_axis_off()

        ax1.set_ylabel("power")
        ax1.set_xlabel("time (s)")
        ax2.set_xlabel("time (s)")

        ax1.set_title("expenditure")
        ax2.set_title("recovery")

        ax1.legend()

        plt.tight_layout()
        plt.show()
        plt.close(fig)

    plot_the_curves(0, 240)
    plot_the_curves(0, 360)
    plot_the_curves(0, 720)
    plot_the_curves(cp * 0.33, 360)
    plot_the_curves(cp * 0.66, 360)


def full_recovery_compare(skiba_agent, three_comp_agent):
    """
    compares full recovery as a detailed plot
    :param skiba_agent:
    :param three_comp_agent:
    :return:
    """
    w_p = skiba_agent.w_p
    cp = skiba_agent.cp

    p_4 = (w_p + 240 * cp) / 240

    def do_the_trials(agent, step_function, p_exp, p_rec):
        """
        complete the
        wb1 -> recovery -> wb2 procedure
        and return times
        """
        agent.reset()

        # WB1 Exhaust...
        agent.set_power(p_exp)
        steps = 0
        while not agent.is_exhausted() and steps < 20000:
            step_function(p_exp)
            steps += 1
        wb1_t = agent.get_time()

        # Recover...
        agent.set_power(p_rec)
        steps = 0
        while not agent.is_equilibrium() and steps < 20000:
            step_function(p_rec)
            steps += 1

        rec_t = agent.get_time()

        # return work bout results
        return wb1_t, rec_t

    def plot_the_curves(p_exp, p_rec):
        """
        The whole procedure of getting data and plotting it
        :param p_exp:
        :param p_rec:
        :return:
        """

        def skiba_step(power):
            """ commands to execute every step """
            s_times.append(skiba_agent.get_time())
            s_w_b_data.append(skiba_agent.get_w_p_balance())
            s_p_data.append(power)
            skiba_agent.perform_one_step()

        def three_comp_step(power):
            """ commands to execute every step """
            t_comp_times.append(three_comp_agent.get_time())
            t_comp_agent_data.append(three_comp_agent.get_w_p_ratio())
            t_comp_p_data.append(power)
            three_comp_agent.perform_one_step()

        s_p_data, s_times, s_w_b_data = [], [], []
        t_comp_p_data, t_comp_times, t_comp_agent_data = [], [], []

        measure_points = []
        measure_points += do_the_trials(skiba_agent, skiba_step, p_exp, p_rec)
        measure_points += do_the_trials(three_comp_agent, three_comp_step, p_exp, p_rec)

        # plot the data
        fig = plt.figure()

        # plot curve
        ax1 = fig.add_subplot(3, 1, 1)
        ax2 = fig.add_subplot(3, 1, 2, sharex=ax1)
        ax3 = fig.add_subplot(3, 1, 3, sharex=ax1)

        ax1.set_title("p_exp {} p_rec {}".format(round(p_exp, 1), round(p_rec, 1)))
        ax1.plot(s_times, s_w_b_data,
                 linestyle='-',
                 color='tab:green')
        ax1.axvline(measure_points[0])
        ax1.axvline(measure_points[1])
        ax1.text(measure_points[0] + (measure_points[1] - measure_points[0]) / 2, w_p / 2,
                 s=measure_points[1] - measure_points[0])

        ax2.plot(t_comp_times, t_comp_agent_data,
                 linestyle='-',
                 color='tab:orange')
        ax2.axvline(measure_points[2])
        ax2.axvline(measure_points[3])
        ax2.text(measure_points[2] + (measure_points[3] - measure_points[2]) / 2, 0.5,
                 s=round(measure_points[3] - measure_points[2], 1))
        ax2.set_ylim((0, 1.1))

        ax3.plot(s_times, s_p_data,
                 linestyle='-',
                 color='tab:green',
                 linewidth=3)
        ax3.plot(t_comp_times, t_comp_p_data,
                 linestyle='-',
                 color='tab:orange')

        # if no axis object was sent, display result
        plt.tight_layout()
        plt.show()
        plt.close(fig)

    # Three different overviews
    plot_the_curves(p_4, 0)
    plot_the_curves(p_4, cp * 0.33)
    plot_the_curves(p_4, cp * 0.66)


def expenditure_compare(skiba_agent, three_comp_agent):
    """
    compare skiba to three comp agent energy expenditure at different levels
    """
    w_p = skiba_agent.w_p
    cp = skiba_agent.cp

    # power level and recovery level estimations for the trials
    p_2 = (w_p + 120 * cp) / 120
    p_4 = (w_p + 240 * cp) / 240
    p_8 = (w_p + 480 * cp) / 480
    p_16 = (w_p + 960 * cp) / 960

    # create some comparison trials
    setups = [p_2, p_4, p_8, p_16]

    def plot_expenditure(p):
        """whole procedure to create detailed expenditure curves for given power level"""

        skiba_p_data = []
        skiba_times = []
        skiba_w_b_data = []

        three_comp_p_data = []
        three_comp_times = []
        three_comp_agent_data = []

        skiba_agent.reset()
        # Skiba exhaust...
        skiba_agent.set_power(p)
        steps = 0
        while not skiba_agent.is_exhausted() and steps < 20000:
            skiba_times.append(skiba_agent.get_time())
            skiba_w_b_data.append(skiba_agent.get_w_p_balance())
            skiba_p_data.append(skiba_agent.get_power())
            skiba_agent.perform_one_step()
            steps += 1

        three_comp_agent.reset()
        # three comp agent exhaust...
        three_comp_agent.set_power(p)
        steps = 0
        while not three_comp_agent.is_exhausted() and steps < 20000:
            three_comp_times.append(three_comp_agent.get_time())
            three_comp_agent_data.append(three_comp_agent.get_w_p_ratio())
            three_comp_p_data.append(three_comp_agent.get_power())
            three_comp_agent.perform_one_step()
            steps += 1

        # plot the data
        fig = plt.figure()

        # plot curve
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2, sharex=ax1)

        ax1.set_title("p_exp {}".format(round(p, 1)))
        ax1.plot(skiba_times, skiba_w_b_data,
                 linestyle='-',
                 color='tab:green',
                 label="".format(skiba_agent.get_name()))

        ax2.plot(three_comp_times, three_comp_agent_data,
                 linestyle='-',
                 color='tab:orange',
                 label="".format(three_comp_agent.get_name()))

        ax2.set_ylim((0, 1.1))

        # if no axis object was sent, display result
        plt.tight_layout()
        plt.show()
        plt.close(fig)

    for p in setups:
        plot_expenditure(p)


def trial_expenditure_compare(skiba_agent, three_comp_agent):
    """
    compare skiba to three comp agent by executing some WB1->REC->WB2 trials
    """
    w_p = skiba_agent.w_p
    cp = skiba_agent.cp

    # power level and recovery level estimations for the trials
    p_8 = (w_p + 480 * cp) / 480
    p_4 = (w_p + 240 * cp) / 240
    cp_33 = cp * 0.33
    cp_66 = cp * 0.66

    # create some comparison trials
    setups = [
        [p_8, cp_66, 360], [p_8, cp_66, 240],
        [p_4, cp_66, 360], [p_8, cp_33, 360],
        [p_4, 0, 360], [p_8, 0, 360]
    ]

    def plot_trial_setup(p_exp, p_rec, t_rec):
        """whole procedure to create WB1 -> REC -> WB2 plots"""

        skiba_p_data = []
        skiba_times = []
        skiba_w_b_data = []

        three_comp_p_data = []
        three_comp_times = []
        three_comp_agent_data = []

        def skiba_step():
            """ commands to execute every step """
            skiba_times.append(skiba_agent.get_time())
            skiba_w_b_data.append(skiba_agent.get_w_p_balance())
            skiba_p_data.append(skiba_agent.get_power())
            skiba_agent.perform_one_step()
            return True

        def three_comp_step():
            """ commands to execute every step """
            three_comp_times.append(three_comp_agent.get_time())
            three_comp_agent_data.append(three_comp_agent.get_w_p_ratio())
            three_comp_p_data.append(three_comp_agent.get_power())
            three_comp_agent.perform_one_step()
            return True

        measure_points = []

        logging.info("start skiba")
        # TODO: update with new simulator basis functions
        marks = SimulatorBasis.do_caen_trials(skiba_agent, p_exp, p_rec, t_rec, step_function=skiba_step)
        measure_points.append(marks[0])
        measure_points.append(marks[1])

        logging.info("start three comp expenditure")
        marks = SimulatorBasis.do_caen_trials(three_comp_agent, p_exp, p_rec, t_rec, step_function=three_comp_step)
        measure_points.append(marks[0])
        measure_points.append(marks[1])

        # plot the data
        fig = plt.figure(figsize=(9, 7))

        # plot curve
        ax1 = fig.add_subplot(3, 1, 1)
        ax2 = fig.add_subplot(3, 1, 2, sharex=ax1)
        ax3 = fig.add_subplot(3, 1, 3, sharex=ax1)

        ax1.set_title("p_exp {} p_rec {}".format(round(p_exp, 1), round(p_rec, 1)))
        ax1.plot(skiba_times, skiba_w_b_data,
                 linestyle='-',
                 color='tab:green',
                 label="{}".format(skiba_agent.get_name()))
        ax1.legend()
        ax1.axvline(measure_points[0])
        ax1.axvline(measure_points[1])
        # ax1.text(measure_points[0] + (measure_points[1] - measure_points[0]) / 2, w_p / 2,
        #          s=measure_points[1] - measure_points[0])

        ax2.plot(three_comp_times, three_comp_agent_data,
                 linestyle='-',
                 color='tab:orange',
                 label="{}".format(three_comp_agent.get_name()))
        ax2.legend()
        ax2.axvline(measure_points[2])
        ax2.axvline(measure_points[3])
        # ax2.text(measure_points[2] + (measure_points[3] - measure_points[2]) / 2, 0.5,
        #          s=round(measure_points[3] - measure_points[2], 1))
        ax2.set_ylim((0, 1.1))

        ax3.plot(skiba_times, skiba_p_data,
                 linestyle='-',
                 color='tab:green',
                 linewidth=3)
        ax3.plot(three_comp_times, three_comp_p_data,
                 linestyle='-',
                 color='tab:orange')
        ax3.axhline(cp, linestyle="--", color="tab:red")
        ax3.set_xlabel("time (s)")
        # ax3.set_ylim((0, max(skiba_p_data) + max(skiba_p_data) * 0.2))
        ax3.set_ylabel("exercise intensity")
        ax3.set_yticks([])

        ax2.set_yticks([])
        ax2.set_ylabel("tank fill levels")
        ax1.set_yticks([])
        ax1.set_ylabel("W' balance")

        # if no axis object was sent, display result
        plt.tight_layout()
        plt.show()
        plt.close(fig)

    # show the plots
    for setup in setups:
        plot_trial_setup(setup[0], setup[1], setup[2])


def trial_recovery_compare(w_p, cp, t_exps, p_recs, t_recs, three_comp_agent=None):
    """
    detailed recovery rate comparison for skiba agents with given w_p and cp to a hydraulic agent
    :param w_p:
    :param cp:
    :param three_comp_agent:
    :return:
    """

    if three_comp_agent is None:
        hz = 10
    else:
        hz = three_comp_agent.hz

    skiba2012_agent = CpAgentSkiba2012(w_p=w_p, cp=cp)
    bartram_agent = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
    skiba2015_agent = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)

    # determine exp intensities from given times
    p_exps = []
    p_exp_labels = []
    for t_exp in t_exps:
        p_exps.append((w_p + t_exp * cp) / t_exp)
        # create a nicely formatted label
        label = t_exp / 60.0
        label = int(label) if label % 1 == 0 else round(label, 2)
        p_exp_labels.append("P{}".format(label))

    # power level and recovery level estimations for the trials
    p_rec_labels = []
    for p_rec in p_recs:
        if p_rec == 20:
            p_rec_labels.append("20W")
        else:
            p_rec_labels.append("CP{:0>2}".format(round((p_rec / cp) * 100.0)))

    # create all the comparison trials
    powers = p_exps
    rec_ps = p_recs
    rec_ts = t_recs
    combs = list(itertools.product(rec_ps, powers))

    # perform the trials
    agents = [skiba2015_agent, bartram_agent, skiba2012_agent]
    if three_comp_agent is not None:
        agents.append(three_comp_agent)
    data = {}
    for agent in agents:
        agent_data = []
        for comb in combs:
            rec_times, rec_percent = [], []
            for rt in rec_ts:
                ratio = SimulatorBasis.get_recovery_ratio_caen(agent, comb[1], comb[0], rt)
                rec_times.append(rt)
                rec_percent.append(ratio)
            # one entry in agent_data corresponds to one power + rec_power setting
            agent_data.append([rec_times, rec_percent])
        # one entry in data corresponds to one agent
        data[agent.get_name()] = agent_data

    # set up the figure
    if len(p_exps) < 2:
        fig = plt.figure(figsize=(len(p_exps) * 5, len(p_recs) * 4))
    else:
        fig = plt.figure(figsize=(len(p_exps) * 4, len(p_recs) * 4))
    axes = []
    for i, comb in enumerate(combs):
        axes.append(fig.add_subplot(len(rec_ps), len(powers), i + 1))
        axes[i].set_title(r'${} \rightarrow {}$'.format(p_exp_labels[p_exps.index(comb[1])],
                                                        p_rec_labels[p_recs.index(comb[0])]))

    legend_handles = []

    # defines the order of the proxy legend handles
    plot_agents = [bartram_agent, skiba2015_agent, three_comp_agent, skiba2012_agent]
    # plot simulated differential agent data
    for agent in plot_agents:

        # three comp hyd agent might be None
        if agent is None:
            continue

        # default styles
        linestyle = '-'
        color = plot_colors[agent.get_name()]
        label = plot_labels[agent.get_name()]

        # proxy for the legend
        legend_handles.append(mlines.Line2D([], [], color=color, linestyle=linestyle, label=label))
        # actual plot
        for j, comb in enumerate(combs):
            axes[j].plot(data[agent.get_name()][j][0], data[agent.get_name()][j][1],
                         linestyle=linestyle,
                         color=color)

    # add ground truth observations where they are applicable
    for j, comb in enumerate(combs):
        name = "{} - {}".format(p_exp_labels[p_exps.index(comb[1])],
                                p_rec_labels[p_recs.index(comb[0])])

        # insert caen observations
        if name in caen_measures:
            axes[j].scatter(caen_measures[name][0], caen_measures[name][1],
                            color=plot_colors["ground_truth"],
                            label="caen observations")
            axes[j].legend()

        # insert ferguson observations
        if name in ferguson_measures:
            axes[j].scatter(ferguson_measures[name][0], ferguson_measures[name][1],
                            color=plot_colors["ground_truth"],
                            label="ferguson observations")
            axes[j].legend()

    # ticks only on the outside
    for i, ax in enumerate(axes):
        ax.set_ylim(0, 110)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_xticks(list(np.arange(0, max(rec_ts) + 1, 120)))
        ax.set_xlim(0, max(rec_ts) + 10)
        ax.xaxis.set_ticklabels([int(x / 60) for x in ax.get_xticks()])
        ax.grid(True, linestyle=':', alpha=0.3)
        if i % len(powers) != 0:
            ax.yaxis.set_ticklabels([])
        if i < len(powers) * (len(rec_ps) - 1):
            ax.xaxis.set_ticklabels([])

    # Create the legend
    fig.legend(handles=legend_handles,
               loc='upper center',
               ncol=4,
               labelspacing=0.)
    fig.text(0.5, 0.04, 'recovery duration (min)', ha='center')
    fig.text(0.01, 0.5, 'W\' recovery (%)', va='center', rotation='vertical')
    # plt.tight_layout()

    if (fig.get_size_inches() == (5, 4)).all():
        plt.subplots_adjust(left=0.14, bottom=0.15, top=0.8)
    elif (fig.get_size_inches() == (8, 4)).all():
        plt.subplots_adjust(left=0.08, bottom=0.18, right=0.97, top=0.8, wspace=0.1)
    elif (fig.get_size_inches() == (16, 4)).all():
        plt.subplots_adjust(left=0.05, bottom=0.18, right=0.97, top=0.81, wspace=0.08)
    elif (fig.get_size_inches() == (16, 8)).all():
        plt.subplots_adjust(left=0.05, bottom=0.11, right=0.97, top=0.9, wspace=0.07, hspace=0.18)

    plt.show()
