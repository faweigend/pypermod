from w_pm_modeling.agents.cp_agents.wbal_ode_agent import WbalODEAgent


class WbalODEAgentFixTau(WbalODEAgent):
    """
    The virtual agent model employing the 2 parameter CP model and exponential recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion. Depending on a fixed tau that's given.
    * depleted W' results in exhaustion
    """

    def __init__(self, w_p: float, cp: float, hz: int = 1):
        """
        constructor with basic constants
        :param cp:
        :param w_p:
        """
        super().__init__(w_p=w_p, cp=cp, hz=hz)
        self._tau = 100

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

    def _get_tau(self):
        """
        This function is called by the parent's class _recovery method
        :return: stored tau
        """
        return self._tau
