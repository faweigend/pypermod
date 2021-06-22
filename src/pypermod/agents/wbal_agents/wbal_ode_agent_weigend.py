import numpy as np
from pypermod.agents.wbal_agents.wbal_ode_agent_exponential import WbalODEAgentExponential


class WbalODEAgentWeigend(WbalODEAgentExponential):
    """
    The virtual agent model employing the 2 parameter CP model and exponential recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion. Depending on a fixed tau dcp relationship
    fitted to measures by Weigend et al. 2021
    * depleted W' results in exhaustion
    """

    def _get_tau_to_dcp(self, dcp: float):
        """
        tau estimation according to fitting created by Weigend et al. 2021
        with measures derived from Caen et al. 2019
        :return: value for tau
        """
        return 1274.4492469669608 * np.exp(dcp * -0.030807662658070646) + 266.64757177314107
