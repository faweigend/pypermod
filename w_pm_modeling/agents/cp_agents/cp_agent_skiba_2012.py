import math

from w_pm_modeling.agents.cp_agents.cp_integral_agent_basis import CpIntegralAgentBasis


class CpAgentSkiba2012(CpIntegralAgentBasis):
    """
    The virtual agent model employing the 2 parameter CP model and Skiba's 2012 recovery kinetics.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover in exponential fashion.
    Depending on average difference to CP of the whole recovery bout.
    """

    def __init__(self, w_p: float, cp: float, hz: int):
        """
        constructor with basic constants
        :param cp: CP
        :param w_p: W'
        :param hz: the time steps per second the agent operates in
        """

        super().__init__(w_p=w_p, cp=cp, hz=hz)

    def _recover(self):
        """
        recovering happens for p < cp. It reduces W' exp and increases W' balance
        """
        # restore W' if some was expended
        if self._get_last_entry() < (self._w_p - 0.1):

            # EQ (3) in Skiba et al. 2012
            tau = 546 * pow(math.e, (-0.01 * self._dcp)) + 316
            # EQ (2) in Skiba et al. 2012
            # decrease expended W' according to time if power output is below cp
            w_exp = self._w_u * pow(math.e, -(self._hz_t - self._u) / tau)
        else:
            w_exp = 0

        # Update balance
        self._w_bal_hist.append(self._w_p - w_exp)
