import math

from w_pm_modeling.agents.cp_agents.cp_differential_agent_basis import CpDifferentialAgentBasis


class CpAgentSkiba2015(CpDifferentialAgentBasis):
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

    def _get_tau(self):
        """
        :return: tau estimation according to Skiba et al. 2015
        """
        # quote Sreedhara: Dcp is the difference between CP and average power output
        # during intervals below CP
        dcp = sum(self._dcp_history) / len(self._dcp_history)
        return self._w_p / dcp

    def _recover(self, p: float):
        """
        recovering happens for p < cp. It reduces W' exp and increases W' balance
        """

        # restore W' if some was expended
        if self._w_exp_t > 0.1:
            # use internal method to get tau (can be updated by subclasses)
            tau = self._get_tau()

            # EQ (4) in Clarke and Skiba et. al. 2015
            # decrease expended W' according to time if power output is below cp
            new_exp = self._w_exp_u * pow(math.e, ((-(self._hz_t - self._u)) / tau))
            self._w_exp_t = new_exp
        else:
            self._w_exp_t = 0

        # Update balance
        self._w_bal = self._w_p - self._w_exp_t
