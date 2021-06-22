from pypermod.agents.wbal_agents.wbal_ode_agent_exponential import WbalODEAgentExponential


class WbalODEAgentFixTau(WbalODEAgentExponential):
    """
    The virtual agent model employing the 2 parameter CP model and exponential recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion. Depending on a fixed tau that's given.
    * depleted W' results in exhaustion
    """

    def __init__(self, w_p: float, cp: float, hz: int = 1, tau: float = 100.0):
        """
        constructor with basic constants
        :param cp: critical power in watts
        :param w_p: W' in Joules
        :param tau: time constant that affects recovery speed
        :param hz: computations per second (delta t)
        """
        super().__init__(w_p=w_p, cp=cp, hz=hz)
        self._tau = tau

    def get_tau(self):
        """
        getter for time constant tau
        """
        return self._tau

    def set_tau(self, new_tau):
        """
        setter for tau
        :param new_tau:
        """
        self._tau = new_tau

    def _get_tau_to_dcp(self, dcp: float):
        """
        Ignores dcp and returns fix tau
        :return: stored tau
        """
        return self._tau
