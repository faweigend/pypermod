import logging

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
    def simulate_chidnok_trials(w_p, cp, hyd_agent_configs, p6_p, sev, hig, med, low):
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
            agent_results = []
            for trial in trials:
                # 2700 steps of trial0 intervals of 30 interspaced with trial1 intervals of 60
                whole_test = ([trial[0]] * (60 * hz) + [trial[1]] * (30 * hz)) * 30
                bal = SimulatorBasis.simulate_course(agent=agent, course_data=whole_test)

                # look for the point of exhaustion
                try:
                    end_t = bal.index(0) / hz
                    agent_results.append(end_t)
                except ValueError:
                    # no exhaustion -> no observation added
                    continue

            # add to results dict if agent not simulated yet
            if agent.get_name() not in trial_results:
                trial_results[agent.get_name()] = agent_results
            else:
                # add index to agent name if another agent of same type was simulated before
                new_name = agent.get_name() + "_" + str(sum([agent.get_name() in s for s in list(trial_results.keys())]))
                trial_results[new_name] = agent_results

        return trial_results
