from pypermod.agents.wbal_agents.wbal_ode_agent_exponential import WbalODEAgentExponential


class WbalODEAgentSkiba(WbalODEAgentExponential):
    """
    The virtual agent model employing the 2 parameter CP model and Skiba's 2015 recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion. Depending on difference to CP.
    * depleted W' results in exhaustion
    """

    def _get_tau_to_dcp(self, dcp: float):
        """
        :return: tau estimation according to Skiba et al. 2021
        """
        return self._w_p / dcp
