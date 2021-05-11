import logging
from collections import defaultdict

from w_pm_modeling.agents.cp_agents.cp_agent_bartram import CpAgentBartram
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2012 import CpAgentSkiba2012
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2015 import CpAgentSkiba2015
from w_pm_modeling.simulation.simulator_basis import SimulatorBasis


class StudySimulator(SimulatorBasis):

    @staticmethod
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
