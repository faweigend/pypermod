from w_pm_modeling.agents.cp_agents.cp_agent_skiba_2015 import CpAgentSkiba2015


class CpAgentFitCaen(CpAgentSkiba2015):
    """
    The virtual agent model employing the 2 parameter CP model and exponential recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion. Depending on a fixed tau that's given.
    * depleted W' results in exhaustion
    """

    def _get_tau(self):
        """
        :return: tau estimation according to fitting to measures by Caen et al.
        """
        dcp = sum(self._dcp_history) / len(self._dcp_history)
        # tau = 850.822466610013 * pow(math.e, (-0.02542815195305181 * dcp)) + 261.82954131635853 # skiba fit result
        # tau = 2559.6395321524374 * pow(dcp, -0.46856788359687684) + 41.08002216973527  # bart fit result
        tau = 2199.656151360503 * pow(dcp, - 0.4071892025253823)  # bart fit with two param
        return tau
