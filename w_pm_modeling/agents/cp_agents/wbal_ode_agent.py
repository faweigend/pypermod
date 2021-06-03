import math
from abc import abstractmethod

from w_pm_modeling.agents.cp_agents.cp_differential_agent_basis import CpDifferentialAgentBasis


class WbalODEAgent(CpDifferentialAgentBasis):
    """
    The most basic virtual agent model employing the 2 parameter CP model and ODE
    recovery according to Skiba et al 2021.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in a curvelinear fashion according to tau.
    * depleted W' results in exhaustion
    """

    def __init__(self, w_p: float, cp: float, hz: int = 1):
        """
        constructor with basic constants
        :param cp:
        :param w_p:
        """
        super().__init__(w_p=w_p, cp=cp, hz=hz)

    @abstractmethod
    def _get_tau_to_dcp(self, dcp: float):
        """
        :return: tau estimation according using DCP
        """

    def _recover(self, p: float):
        """
        recovering happens for p < cp. It reduces W' exp and increases W' balance
        """

        # restore W' if some was expended
        if self._w_bal < self._w_p - 0.1:
            dcp = self._cp - p
            tau = self._get_tau_to_dcp(dcp=dcp)
            # according to Eq 12 in Skiba 2021
            self._w_bal = self._w_p - ((self._w_p - self._w_bal) * pow(math.e, (- self.hz / tau)))
        else:
            self._w_bal = self._w_p
