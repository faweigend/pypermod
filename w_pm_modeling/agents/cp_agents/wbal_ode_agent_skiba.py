from w_pm_modeling.agents.cp_agents.wbal_ode_agent import WbalODEAgent


class WbalODEAgentSkiba(WbalODEAgent):
    """
    The virtual agent model employing the 2 parameter CP model and Skiba's 2015 recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion. Depending on difference to CP.
    * depleted W' results in exhaustion
    """

    def __init__(self, w_p: float, cp: float, hz: int = 1):
        """
        constructor with basic constants
        :param cp:
        :param w_p:
        """
        super().__init__(w_p=w_p, cp=cp, hz=hz)

    def _get_tau_to_dcp(self, dcp: float):
        """
        :return: tau estimation according to Skiba et al. 2021
        """
        return self._w_p / dcp
