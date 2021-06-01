import logging
import math

import numpy as np
from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2012 import CpAgentSkiba2012
from w_pm_modeling.agents.cp_agents.cp_integral_agent_basis import CpIntegralAgentBasis


class CpAgentIntDynTau(CpAgentSkiba2012):
    """
    The virtual agent model employing Skiba's 2012 Equation for expenditure and recovery kinetics.
    Depending on average difference to CP of the whole recovery bout.
    """

    def __init__(self, w_p: float, cp: float, hz: int):
        """
        constructor with basic constants
        :param cp: CP
        :param w_p: W'
        :param hz: the time steps per second the agent operates in
        """
        super().__init__(w_p=w_p, cp=cp, hz=hz)

    @staticmethod
    def _estimate_tau(dcp: float):
        """
        Applies Eq 3 from Skiba et al. 2012 to estimate tau from given dcp
        :param dcp: Average difference to CP during recovery bouts
        :return: Tau
        """
        # EQ (3) in Skiba et al. 2012
        return 2287.2 * pow(dcp, -0.688)