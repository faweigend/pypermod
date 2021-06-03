from w_pm_modeling.agents.wbal_agents.wbal_ode_agent_exponential import WbalODEAgentExponential


class WbalODEAgentWeigend(WbalODEAgentExponential):
    """
    The virtual agent model employing the 2 parameter CP model and exponential recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion. Depending on a fixed tau that's given.
    * depleted W' results in exhaustion
    """

    def _get_tau_to_dcp(self, dcp: float):
        """
        :return: tau estimation according to fitting created by Weigend et al. with measures derived from Caen et al.
        """
        return 2559.6395321524374 * pow(dcp, -0.46856788359687684) + 41.08002216973527
