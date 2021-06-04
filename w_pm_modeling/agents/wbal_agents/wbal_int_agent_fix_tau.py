from w_pm_modeling.agents.wbal_agents.wbal_int_agent import WbalIntAgent


class WbalIntAgentFixTau(WbalIntAgent):
    """
    The virtual agent model employing Skiba's 2012 Equation for expenditure and recovery kinetics.
    This agent version allows to set a fix tau different from the fitted tau/dcp relationship from Skiba 2012
    """

    def __init__(self, w_p: float, cp: float, tau: float = 100.0, hz: int = 1):
        """
        constructor with basic constants
        :param cp: CP
        :param w_p: W'
        :param tau: the recovery time constant tau used by this agent
        :param hz: the time steps per second the agent operates in
        """
        super().__init__(w_p=w_p, cp=cp, hz=hz)
        self._tau = tau

    @property
    def tau(self):
        """
        getter for time constant tau
        """
        return self._tau

    @tau.setter
    def tau(self, new_tau):
        """
        setter for tai
        :param new_tau:
        """
        self._tau = new_tau

    def _get_tau_to_dcp(self, dcp: float):
        """
        Ignores given DCP and returns fix tau
        :param dcp: Average difference to CP during recovery bouts
        :return: Tau
        """
        return self._tau
