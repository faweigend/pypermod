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
        self._w_exp = 0
        # expenditure at last utilisation
        self._w_u = 0

        # time since w_p was last utilised
        self._u = 0

        # e.g. used for skiba2015. The average of all past DCPs is used for the recovery slope estimations
        self._dcp_history = []

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
        self._w_exp = 0
        self._w_u = 0
        self._u = 0

    def _estimate_possible_power_output(self):
        """
        Update internal capacity estimations by one step.
        :return: the amount of power that the athlete was able to put out
        """
        p = self._pow

        # update W exp and power output
        if p < self._cp:

            # the dcp history is used for recovery speed estimations by skiba et al.
            if self._w_bal != self._w_p:
                self._dcp_history.append(self._cp - p)
            self._recover(p)
        else:

            # clear history when recovery is over
            if len(self._dcp_history) > 0:
                self._dcp_history.clear()

            # update u to current time
            self._u = self._hz_t
            p = self._spend_capacity(p)
            # update expenditure at u
            self._w_u = self._w_exp

        # return possible power output
        return p

    def is_equilibrium(self):
        """
        Checks if W'bal is at a steady state.
        In case of a CP agent this is either:
            1) when the athlete works exactly at CP
            2) works below CP and W'bal is full
        """
        return self._pow == self._cp or (self._pow < self._cp and self._w_exp <= (self._w_p * 0.01))

    def is_exhausted(self):
        """simple exhaustion check using W' balance"""
        return bool(self._w_bal == 0)

    def is_recovered(self):
        """simple recovery check using W' expended"""
        return self._w_exp <= (self._w_p * 0.01)

    def _spend_capacity(self, p: float):
        """
        Capacity is spent for p > cp. It updates W'exp and W' bal and returns the
        achieved power output
        """

        # determine aerobic power considering hz
        anaer_p = (self._pow - self._cp) / self._hz

        if self._w_bal < anaer_p:
            # not enough balance to perform on requested power
            p = self._w_bal + self._cp
            self._w_bal = 0
            self._w_exp = self._w_p
        else:
            # increase expended W'
            self._w_exp += anaer_p
            # expended W' cannot exceed W'
            self._w_exp = min(self._w_p, self._w_exp)
            # Update balance
            self._w_bal = self._w_p - self._w_exp

        return p

    def _recover(self, p: float):
        """
        linear recovery happens for p < cp. It reduces W' exp and increases W' balance
        """

        # nothing to do if fully recovered
        if self._w_exp > 0:
            diff = (self._cp - self._pow) / self._hz
            self._w_exp -= diff
            # cannot be less expended than 0
            self._w_exp = max(self._w_exp, 0)

        # Update balance
        self._w_bal = self._w_p - self._w_exp
