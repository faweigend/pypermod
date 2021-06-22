import logging
import math

import numpy as np
from threecomphyd.agents.three_comp_hyd_agent import ThreeCompHydAgent
from pypermod import utility
from pypermod.agents.wbal_agents.wbal_int_agent_skiba import WbalIntAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_bartram import WbalODEAgentBartram
from pypermod.agents.wbal_agents.wbal_ode_agent_skiba import WbalODEAgentSkiba
from pypermod.agents.wbal_agents.wbal_ode_agent_weigend import WbalODEAgentWeigend
from pypermod.simulator.simulator_basis import SimulatorBasis


class StudySimulator(SimulatorBasis):
    """
    An extension of the standard simulator that adds convenience functions to recreate trials of studies
    that investigated W' recovery dynamics
    """

    @staticmethod
    def get_standard_error_measures(w_p: float, cp: float,
                                    hyd_agent_configs: list, hz: int,
                                    ground_truth_t: list,
                                    ground_truth_v: list,
                                    ground_truth_p_exp: list,
                                    ground_truth_p_rec: list):
        """
        compares agent results with ground truth and prints estimated RMSE and AIC
        :param w_p:
        :param cp:
        :param hyd_agent_configs:
        :param ground_truth_t: ground truth times
        :param ground_truth_v: ground truth values
        :param ground_truth_p_exp:
        :param ground_truth_p_rec:
        :param hz:
        :return:
        """

        agent_skiba_2015 = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
        agent_bartram = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
        agent_skiba_2012 = WbalIntAgentSkiba(w_p=w_p, cp=cp, hz=hz)
        agent_fit_caen = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)

        agents = [agent_bartram, agent_skiba_2015, agent_fit_caen]  # agent_skiba_2012]

        # create the hydraulic agents
        for p in hyd_agent_configs:
            agents.append(
                ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                  the=p[5], gam=p[6], phi=p[7]))

        error_summary = {}
        # plot simulated agent data
        for agent in agents:
            # two  lists to be filled with expected and actual values
            exp, act = [], []
            for i in range(len(ground_truth_t)):
                # get simulated value
                ratio = SimulatorBasis.get_recovery_ratio_caen(agent,
                                                               p_exp=ground_truth_p_exp[i],
                                                               p_rec=ground_truth_p_rec[i],
                                                               t_rec=ground_truth_t[i])
                exp.append(ground_truth_v[i])
                act.append(ratio)

            # define number of free parameters according to agent type
            if isinstance(agent, WbalODEAgentBartram):
                k = 2
            elif isinstance(agent, WbalODEAgentSkiba):
                k = 1
            elif isinstance(agent, WbalODEAgentWeigend):
                k = 3
            elif isinstance(agent, ThreeCompHydAgent):
                k = 8
            else:
                k = 1

            # add error summary into dict
            error_summary[agent.get_name()] = StudySimulator.__apply_error_measure(exp=exp, act=act, k=k)
        print(error_summary)

    @staticmethod
    def __apply_error_measure(exp: list, act: list, k: int):
        """
        simply applies established error measures using both input lists
        :param exp: a list containing the expected values
        :param act: a list containing the actual values
        :param k: number of parameters for AIC and BIC
        :return: 
        """
        se = []  # squared errors
        for i, ex in enumerate(exp):
            se.append(math.pow(ex - act[i], 2))

        # RSS (residual sum of squares)
        rss = sum(se)
        n = len(se)

        # estimate used error measures
        rmse = math.sqrt(rss / len(se))
        aic = n * math.log(rss / n) + 2 * k + ((2 * k * (k + 1)) / (n - k - 1))
        bic = n * math.log(rss / n) + k * math.log(n)
        return rmse, aic, bic

    @staticmethod
    def standard_comparison(agents, p_exp: float, p_rec: float, rec_times: np.ndarray):
        """
        This function employs the WB1 -> RB -> WB2 protocol proposed by Caen et al. to estimate recovery ratios.
        Recovery dynamics after a given intensity, at a given recovery intensity, and over a given time are estimated.
        :param agents: list of agents to compare
        :param p_exp: intensity that leads to exhaustion
        :param p_rec: recovery intensity
        :param rec_times: recovery times to estimate
        :return: simulation results in a dictionary
        """

        # add agents dict to results
        trial_results = {}

        # estimate recovery ratios with Caen protocol
        for agent in agents:
            agent_data = []

            # get recovery ratio for every time frame to be considered
            for t_rec in rec_times:
                ratio = SimulatorBasis.get_recovery_ratio_caen(agent,
                                                               p_exp=p_exp,
                                                               p_rec=p_rec,
                                                               t_rec=t_rec)
                agent_data.append(ratio)

            # make use of insert function to not overwrite saved data
            trial_results = utility.insert_with_key_enumeration(agent=agent,
                                                                agent_data=agent_data,
                                                                results=trial_results)
            # update about progress
            logging.info("{} simulation done".format(agent.get_name()))

        return trial_results

    @staticmethod
    def simulate_chidnok_trials(w_p: float, cp: float, hyd_agent_configs: list, p6_p: float,
                                sev: float, hig: float, med: float, low: float, hz: int):
        """
        Simulates the trials made by Chidnok et al. 2012.
        It utilises the intensities p6_p, sev, hig, med, low to create their trial setup of 60 sec and 30 sec intervals
        :param w_p: W' to use
        :param cp: CP to use
        :param hyd_agent_configs: configs for fitted hydraulic agents
        :param p6_p: exercise intensity p6plus
        :param sev: severe rec intensity
        :param hig: high rec intensity
        :param med: medium rec intensity
        :param low: low rec intensity
        :param hz: time steps per second for the agents
        :return: simulation results in a dict
        """

        # results dict
        trial_results = {}

        agent_skiba_2015 = WbalODEAgentSkiba(w_p=w_p, cp=cp, hz=hz)
        agent_bartram = WbalODEAgentBartram(w_p=w_p, cp=cp, hz=hz)
        agent_fit_caen = WbalODEAgentWeigend(w_p=w_p, cp=cp, hz=hz)

        agents = [agent_bartram, agent_skiba_2015, agent_fit_caen]

        # create the hydraulic agents
        for p in hyd_agent_configs:
            agents.append(
                ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1],
                                  m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                  the=p[5], gam=p[6], phi=p[7]))

        # experimental trials
        trials = [(p6_p, sev), (p6_p, hig), (p6_p, med), (p6_p, low)]

        # simulate all trials for all created agents
        for agent in agents:
            agent_data = []
            for trial in trials:
                # 1800 steps of trial0 intervals of 60 interspaced with trial1 intervals of 30
                whole_test = ([trial[0]] * (60 * hz) + [trial[1]] * (30 * hz)) * 20
                bal = SimulatorBasis.simulate_course(agent=agent, course_data=whole_test)

                # look for the point of exhaustion
                try:
                    end_t = bal.index(0) / hz
                    agent_data.append(end_t)
                except ValueError:
                    # no exhaustion -> no observation added
                    continue

            # make use of insert function to not overwrite saved data
            trial_results = utility.insert_with_key_enumeration(agent=agent,
                                                                agent_data=agent_data,
                                                                results=trial_results)

        return trial_results
