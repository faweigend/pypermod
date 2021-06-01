from w_pm_modeling.agents.differential_agent_basis import DifferentialAgentBasis


class CpDifferentialAgentBasis(DifferentialAgentBasis):
    """
    The most basic virtual agent model employing the 2 parameter CP model.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover linear fashion.
    * depleted W' results in exhaustion
    """

    def __init__(self, w_p: float, cp: float, hz: int):
        """
        constructor with basic constants
        :param cp:
        :param w_p:
        """

        super().__init__(hz=hz)
        # constants
        self._w_p = w_p
        self._cp = cp
        # fully rested, balance equals w_p
        self._w_bal = w_p

    def get_w_p_balance(self):
        """:return: """
        return self._w_bal

    @property
    def cp(self):
        """:return: critical power"""
        return self._cp

    @property
    def w_p(self):
        """:return: anaerobic capacity"""
        return self._w_p

    def reset(self):
        """resets capacity, time and power parameters"""
        super().reset()
        self._w_bal = self._w_p

    def _estimate_possible_power_output(self):
        """
        Update internal capacity estimations by one step.
        :return: the amount of power that the athlete was able to put out
        """
        p = self._pow
        # update W exp and power output
        if p < self._cp:
            self._recover(p)
        else:
            p = self._spend_capacity(p)
        # return possible power output
        return p

    def is_equilibrium(self):
        """
        Checks if W'bal is at a steady state.
        In case of a CP agent this is either:
            1) when the athlete works exactly at CP
            2) works below CP and W'bal is full
        """
        return self._pow == self._cp or (self._pow < self._cp and self._w_bal >= (self._w_p * 0.01))

    def is_exhausted(self):
        """simple exhaustion check using W' balance"""
        return bool(self._w_bal == 0)

    def is_recovered(self):
        """simple recovery check using W' expended"""
        return self._w_bal >= (self._w_p * 0.01)

    def _spend_capacity(self, p: float):
        """
        Capacity is spent for p > cp. It updates W'bal and returns the
        achieved power output
        """

        # determine aerobic power considering hz
        anaer_p = (self._pow - self._cp) / self._hz

        if self._w_bal < anaer_p:
            # not enough balance to perform on requested power
            p = self._w_bal + self._cp
            self._w_bal = 0.0
        else:
            # increase expended W'
            self._w_bal -= anaer_p
            # Update balance
            self._w_bal = min(self._w_p, self._w_bal)
            self._w_bal = max(0.0, self._w_bal)

        return p

    def _recover(self, p: float):
        """
        linear recovery happens for p < cp. It reduces W' exp and increases W' balance
        """

        # nothing to do if fully recovered
        if self._w_bal < (self._w_p * 0.01):
            diff = (self._cp - self._pow) / self._hz
            self._w_bal += diff
            # cannot be more recovered than w'
            self._w_bal = min(self._w_p, self._w_bal)
        else:
            self._w_bal = self._w_p
