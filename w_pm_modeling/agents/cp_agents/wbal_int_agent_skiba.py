import math

from w_pm_modeling.agents.cp_agents.wbal_int_agent import WbalIntAgent


class WbalIntAgentSkiba(WbalIntAgent):
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

    def _get_tau_to_dcp(self, dcp: float):
        """
        Applies Eq 3 from Skiba et al. 2012 to estimate tau from given dcp
        :param dcp: Average difference to CP during recovery bouts
        :return: Tau
        """
        return 546 * pow(math.e, (-0.01 * dcp)) + 316
