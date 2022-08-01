from pypermod.agents.cp_agent_basis import CpAgentBasis


class CpODEAgentBasisLinear(CpAgentBasis):
    """
    This class defines the structure for all differential agents.
    Provided are functions for dynamic power outputs and commands for simulations.
    Differential agents allow real time estimations.

    The most basic virtual agent model employing the 2 parameter CP model.
    Characteristics:
    * performance above CP drains W' in a linear fashion
    * performance below CP allows W' to recover linear fashion.
    * depleted W' results in exhaustion
    """

    def __init__(self, w_p: float, cp: float, hz: int = 1):
        """
        constructor with basic constants
        :param cp:
        :param w_p:
        """
        super().__init__(hz=hz, w_p=w_p, cp=cp)

        # fully rested, balance equals w_p
        self._w_bal = w_p

        # simulation management parameters
        self._step = 0
        self._hz_t = 0.0
        self._pow = 0.0

    def is_equilibrium(self) -> bool:
        """
        Checks if W'bal is at a steady state.
        In case of a CP agent this is either:
            1) when the athlete works exactly at CP
            2) works below CP and W'bal is full
        :return: boolean
        """
        return self._pow == self._cp or (self._pow < self._cp and self._w_bal >= (self._w_p * 0.01))

    def is_exhausted(self) -> bool:
        """
        simple exhaustion check using W' balance
        :return: boolean
        """
        return self._w_bal == 0

    def is_recovered(self) -> bool:
        """
        simple recovery check using W' expended
        :return: boolean
        """
        return self._w_bal >= (self._w_p * 0.01)

    def get_time(self) -> float:
        """
        :return: time in seconds considering the agent's hz setting
        """
        return self._hz_t

    def perform_one_step(self) -> float:
        """
        Updates power output and internal W' balance parameters.
        :return: expended power
        """
        # increase time counter
        self._step = self._step + 1
        self._hz_t = float(self._step / self._hz)

        # use updated instantaneous power to update internal capacities
        self._pow = self._estimate_possible_power_output()

        # final instantaneous power output
        return self._pow

    def reset(self):
        """
        reset internal values to default
        """
        self._step = 0
        self._hz_t = 0.0
        self._pow = 0.0
        self._w_bal = self._w_p

    def set_power(self, power: float):
        """
        set power output directly to skip acceleration phases
        :param power: power in Watts
        """
        self._pow = power

    def get_power(self) -> float:
        """
        :return: power in Watts
        """
        return self._pow

    def get_w_p_balance(self) -> float:
        """
        :return: current W'bal
        """
        return self._w_bal

    def set_w_p_balance(self, w_bal: float):
        """
        sets internal wbal parameter and ensures it's in-between 0 and W'
        """
        if w_bal < 0 or w_bal > self.w_p:
            raise UserWarning(
                "W'balance ({}) has an illegal value. "
                "It must be between 0 and W' ({})".format(w_bal, self.w_p)
            )
        self._w_bal = w_bal

    def _estimate_possible_power_output(self) -> float:
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

    def _spend_capacity(self, p: float) -> float:
        """
        Capacity is spent for p > cp. It updates W'bal and returns the
        achieved power output
        :param p: power demand in watts
        :return: possible power in watts
        """

        # determine aerobic power considering hz
        anaer_p = (self._pow - self._cp) * self._delta_t

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
        if self._w_bal < self._w_p - 0.01:
            diff = (self._cp - p) * self._delta_t
            self._w_bal += diff
            # cannot be more recovered than w'
            self._w_bal = min(self._w_p, self._w_bal)
        else:
            self._w_bal = self._w_p
