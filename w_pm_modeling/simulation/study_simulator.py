import logging

import numpy as np
from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.agents.cp_agents.cp_agent_bartram import CpAgentBartram
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2012 import CpAgentSkiba2012
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2015 import CpAgentSkiba2015
from w_pm_modeling.simulation.simulator_basis import SimulatorBasis


class StudySimulator(SimulatorBasis):

    @staticmethod
    def standard_comparison(w_p: float, cp: float, hyd_agent_configs: list, p_exp: float,
                            p_rec: float, rec_times: np.ndarray, hz: int):
        """

        :param w_p:
        :param cp:
        :param hyd_agent_configs:
        :param p_exp:
        :param p_rec:
        :param rec_times:
        :param hz:
        :return:
        """

        # add agents dict to results
        trial_results = {}

        agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
        agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
        agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

        agents = [agent_bartram, agent_skiba_2015, agent_skiba_2012]

        # create the hydraulic agents
        for p in hyd_agent_configs:
            agents.append(
                ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                  the=p[5], gam=p[6], phi=p[7]))

        # estimate recovery ratios with Caen protocol
        for agent in agents:
            agent_data = []

            # get recovery ratio for every time frame to be considered
            for t_rec in rec_times:
                ratio = SimulatorBasis.get_recovery_ratio_caen(agent, p_exp=p_exp, p_rec=p_rec, t_rec=t_rec)
                agent_data.append(ratio)

            # make use of insert function to not overwrite saved data
            trial_results = StudySimulator.__insert_with_enumeration(agent=agent, agent_data=agent_data,
                                                                     results=trial_results)
            # update about progress
            logging.info("{} simulation done".format(agent.get_name()))

        return trial_results

    @staticmethod
    def simulate_chidnok_trials(w_p: float, cp: float, hyd_agent_configs: list, p6_p: float,
                                sev: float, hig: float, med: float, low: float):
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
        :return: trial results in a dict
        """

        # results dict
        trial_results = {}

        # integral agents have to work with 1hz
        hz = 1
        agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
        agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
        agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

        agents = [agent_bartram, agent_skiba_2015, agent_skiba_2012]

        # create the hydraulic agents
        for p in hyd_agent_configs:
            agents.append(
                ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                  the=p[5], gam=p[6], phi=p[7]))

        # experimental trials
        trials = [(p6_p, sev), (p6_p, hig), (p6_p, med), (p6_p, low)]

        # simulate all trials for all created agents
        for agent in agents:
            agent_data = []
            for trial in trials:
                # 2700 steps of trial0 intervals of 30 interspaced with trial1 intervals of 60
                whole_test = ([trial[0]] * (60 * hz) + [trial[1]] * (30 * hz)) * 30
                bal = SimulatorBasis.simulate_course(agent=agent, course_data=whole_test)

                # look for the point of exhaustion
                try:
                    end_t = bal.index(0) / hz
                    agent_data.append(end_t)
                except ValueError:
                    # no exhaustion -> no observation added
                    continue

            # make use of insert function to not overwrite saved data
            trial_results = StudySimulator.__insert_with_enumeration(agent=agent, agent_data=agent_data,
                                                                     results=trial_results)

        return trial_results

    @staticmethod
    def simulate_skiba_2014_trials(w_p: int, cp: int, hyd_agent_configs: list,
                                   trials: list, hz: int):
        """
        Simulates trials from the skiba 2014 publication Effect of Work and Recovery Durations on W'
        Reconstitution during Intermittent Exercise. https://insights.ovid.com/crossref?an=00005768-201407000-00020
        :param w_p: skiba agent parameter to compare to
        :param cp: skiba agent parameter to compare to
        :param hyd_agent_configs: three comp agent configurations
        :param trials: a list expected to consist of pairs that indicate [(t_exp, t_rec), ...]
        :param hz: hz for all agents
        :return: results in a dict
        """

        agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)
        agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
        agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)

        agents = [agent_skiba_2012, agent_skiba_2015, agent_bartram]

        # create the hydraulic agents
        for p in hyd_agent_configs:
            agents.append(
                ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                  the=p[5], gam=p[6], phi=p[7]))

        # p4 equals p6+, which is p6 plus 50% diff p6 and cp
        p4 = (w_p / 240) + cp
        # recovery is simply at 20 Watts
        p_rec = 20

        # dict to store all simulation results into
        results = {}

        for agent in agents:

            # stores all results for current agent
            agent_ts = []

            # iterate through trials
            for trial in trials:
                # search for the number of bouts that results in W'exp of ~50%
                balance = w_p
                num_of_intervals = 0

                # Derive the optimal amount of work and recovery bouts (W'exp of ~50%) according to skiba2012
                while True:
                    # set up the total test with the increasing number of work and recovery bouts
                    num_of_intervals += 1
                    total_test = ([p4] * trial[0] + [p_rec] * trial[1]) * num_of_intervals
                    bal_hist = agent_skiba_2012.estimate_w_p_bal_to_data(total_test)

                    # check balance
                    balance_before = balance
                    balance = bal_hist[-1]

                    if balance <= w_p / 2:
                        # use the other opt if balance shrunk by too much
                        if abs(balance - w_p / 2) > abs(balance_before - w_p / 2):
                            # print("balance: ", balance, abs(balance - w_p / 2), " 50%: ", w_p / 2, "BALANCE_BEFORE: ",
                            #       balance_before, abs(balance_before - w_p / 2))
                            num_of_intervals -= 1
                        # else:
                        #     print("BALANCE: ", balance, abs(balance - w_p / 2), " 50%: ", w_p / 2, "balance_before: ",
                        #           balance_before, abs(balance_before - w_p / 2))
                        break

                # now assemble whole protocol
                p_intervals = ([p4] * trial[0] + [p_rec] * trial[1]) * num_of_intervals
                p_exhaust = [p4] * 3000
                p_total = p_intervals + p_exhaust

                # get W'bal history from agent
                bal_hist = SimulatorBasis.simulate_course(agent, p_total)

                # find point of exhaustion
                t_end = bal_hist.index(0)
                agent_ts.append(t_end)

            # make use of insert function to not overwrite saved data
            results = StudySimulator.__insert_with_enumeration(agent, agent_ts, results)

        return results

    @staticmethod
    def simulate_sreedhara_trials(w_p: float, cp: float, hyd_agent_configs: list,
                                  p_rec: float, p_exp: float, t_exp: int,
                                  rec_times: np.ndarray, hz: int):
        """
        Simulates trials done by Ferguson et al. with all available recovery agents
        :param w_p:
        :param cp:
        :param hyd_agent_configs:
        :param p_rec:
        :param p_exp:
        :param t_exp:
        :param rec_times:
        :param hz:
        :return:
        """

        results = {}

        agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
        agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
        agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

        agents = [agent_bartram, agent_skiba_2015, agent_skiba_2012]

        # create the hydraulic agents
        for p in hyd_agent_configs:
            agents.append(
                ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                  the=p[5], gam=p[6], phi=p[7]))

        # get the recovery dynamics for every agent
        for agent in agents:

            agent_data = []
            for t_rec in rec_times:
                # get recovery dynamics via the Sreedhara protocol
                ratio = SimulatorBasis.get_recovery_ratio_sreedhara(agent, p_exp=p_exp, t_exp=t_exp,
                                                                    p_rec=p_rec, t_rec=t_rec)
                agent_data.append(ratio)

            # make use of insert function to not overwrite saved data
            results = StudySimulator.__insert_with_enumeration(agent, agent_data, results)

        return results

    @staticmethod
    def __insert_with_enumeration(agent, agent_data, results):
        """
        Checks if agent with the same name has stored data already and enumerates in case
        :param agent: agent that produced data
        :param agent_data: simulated data
        :param results: dict to store data into
        :return: dict with inserted data/name pair
        """
        # add to results dict and don't double agent names
        if agent.get_name() not in results:
            results[agent.get_name()] = agent_data
        else:
            # add index to agent name if another agent of same type was simulated before
            new_name = agent.get_name() + "_" + str(
                sum([agent.get_name() in s for s in list(results.keys())]))
            results[new_name] = agent_data
        return results
