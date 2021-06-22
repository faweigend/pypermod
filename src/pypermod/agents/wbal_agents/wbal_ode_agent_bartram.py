from pypermod.agents.wbal_agents.wbal_ode_agent_exponential import WbalODEAgentExponential


class WbalODEAgentBartram(WbalODEAgentExponential):
    """
    The virtual agent model employing the 2 parameter CP model and Bartram's adjusted recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion. Depending on difference to CP.
    """

    def _get_tau_to_dcp(self, dcp: float):
        """
        :return: tau estimation according to Bartram et al.
        """
        return 2287.2 * pow(dcp, -0.688)
