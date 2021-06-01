from w_pm_modeling.agents.cp_agents.wbal_ode_agent import WbalODEAgent


class WbalODEAgentBartram(WbalODEAgent):
    """
    The virtual agent model employing the 2 parameter CP model and Bartram's adjusted recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion. Depending on difference to CP.
    """

    def _get_tau(self):
        """
        :return: tau estimation according to Bartram et al.
        """
        dcp = self._cp - self._pow
        return 2287.2 * pow(dcp, -0.688)
