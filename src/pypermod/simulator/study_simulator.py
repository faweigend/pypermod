import logging
import numpy as np
from pypermod import utility
from pypermod.simulator.simulator_basis import SimulatorBasis


class StudySimulator(SimulatorBasis):
    """
    An extension of the standard simulator that adds convenience functions to recreate trials of studies
    that investigated W' recovery dynamics
    """

    @staticmethod
    def standard_comparison(agents, p_work: float, p_rec: float, rec_times: np.ndarray):
        """
        This function employs the WB1 -> RB -> WB2 protocol proposed by Caen et al. to estimate recovery ratios.
        Recovery dynamics after a given intensity, at a given recovery intensity, and over a given time are estimated.
        :param agents: list of agents to compare
        :param p_work: intensity that leads to exhaustion
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
                ratio = SimulatorBasis.get_recovery_ratio_wb1_wb2(agent,
                                                                  p_work=p_work,
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
