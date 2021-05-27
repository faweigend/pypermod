from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2015 import CpAgentSkiba2015


class CpAgentBartram(CpAgentSkiba2015):
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
        # quote Sreedhara: Dcp is the difference between CP and average power output
        # during intervals below CP
        dcp = sum(self._dcp_history) / len(self._dcp_history)
        return 2287.2 * pow(dcp, -0.688)
