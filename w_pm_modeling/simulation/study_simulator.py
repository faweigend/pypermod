import logging
from collections import defaultdict

from w_pm_hydraulic.agents.three_comp_hyd_agent import ThreeCompHydAgent
from w_pm_modeling.agents.cp_agents.cp_agent_bartram import CpAgentBartram
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2012 import CpAgentSkiba2012
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2015 import CpAgentSkiba2015
from w_pm_modeling.simulation.simulator_basis import SimulatorBasis


class StudySimulator(SimulatorBasis):

    @staticmethod
    def standard_comparison(w_p, cp, hyd_agent_configs, p_exp, p_rec, rec_times):
        """
        :param cp_agents:
        :param hyd_agetns:
        :param p_exp:
        :param p_rec:
        :param rec_times:
        :return:
        """

        # add agents dict to results
        trial_results = {}

        hz = 10
        agent_skiba_2015 = CpAgentSkiba2015(w_p=w_p, cp=cp, hz=hz)
        agent_bartram = CpAgentBartram(w_p=w_p, cp=cp, hz=hz)
        agent_skiba_2012 = CpAgentSkiba2012(w_p=w_p, cp=cp)

        agents = [agent_bartram, agent_skiba_2015, agent_skiba_2012]

        # create the agents
        three_comp_hyd_agents = []
        for p in hyd_agent_configs:
            three_comp_hyd_agents.append(
                ThreeCompHydAgent(hz=hz, a_anf=p[0], a_ans=p[1], m_ae=p[2], m_ans=p[3], m_anf=p[4],
                                  the=p[5], gam=p[6], phi=p[7]))

        # estimate recovery ratios for CP agents
        for agent in agents:
            agent_data = []
            for t_rec in rec_times:
                # get recovery dynamics via the caen protocol
                ratio = SimulatorBasis.get_recovery_ratio_caen(agent,
                                                               p_exp=p_exp,
                                                               p_rec=p_rec,
                                                               t_rec=t_rec)
                agent_data.append(ratio)
            trial_results[agent.get_name()] = agent_data
            logging.info("{} simulation done".format(agent.get_name()))

        # add each hydraulic agent with an individual number
        for i, hyd_agent in enumerate(three_comp_hyd_agents):
            agent_data = []
            for t_rec in rec_times:
                ratio = SimulatorBasis.get_recovery_ratio_caen(hyd_agent,
                                                               p_exp=p_exp,
                                                               p_rec=p_rec,
                                                               t_rec=t_rec)
                agent_data.append(ratio)
            trial_results["{}_{}".format(hyd_agent.get_name(), i)] = agent_data
            logging.info("{} simulation done".format(hyd_agent.get_name()))

        return trial_results

    @staticmethod
    def simulate_bartram_trials(agent_three_comp_list,
                                w_p: float,
                                cp: float,
                                prec: float,
                                times: list):
        """
        Simulates bartram recovery ratio comparison with all established models
        :param agent_three_comp_list: a list of three comp agents to simulate
        :param w_p: skiba agent parameter to compare to
        :param cp: skiba agent parameter to compare to
        :param prec: recovery intensity
        :param times: the times of comparison
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
        recovery_times = times

        # collection of simulated recovery ratios
        trial_results = defaultdict(dict)

        # estimate recovery ratios for CP agents
        for agent in agents:
            agent_data = []
            for t_rec in recovery_times:
                # get recovery dynamics via the caen protocol
                ratio = SimulatorBasis.get_recovery_ratio_caen(agent,
                                                               p_exp=p_exp,
                                                               p_rec=p_rec,
                                                               t_rec=t_rec)
                agent_data.append(ratio)
            trial_results[agent.get_name()] = agent_data
            logging.info("{} simulation done".format(agent.get_name()))

        # add each hydraulic agent with an individual number
        for i, hyd_agent in enumerate(agent_three_comp_list):
            agent_data = []
            for t_rec in recovery_times:
                ratio = SimulatorBasis.get_recovery_ratio_caen(hyd_agent,
                                                               p_exp=p_exp,
                                                               p_rec=p_rec,
                                                               t_rec=t_rec)
                agent_data.append(ratio)
            trial_results["{}_{}".format(hyd_agent.get_name(), i)] = agent_data
            logging.info("{} simulation done".format(hyd_agent.get_name()))

        return trial_results
