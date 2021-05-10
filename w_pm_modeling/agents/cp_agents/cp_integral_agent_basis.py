import logging
from abc import abstractmethod

from w_pm_modeling.agents.integral_agent_basis import IntegralAgentBasis
import numpy as np


class CpIntegralAgentBasis(IntegralAgentBasis):
    """
    The virtual agent model employing the 2 parameter CP model for expenditure and providing a template
    for various recovery kinetics. Integral agents need the entire exercise to be known before estimations can be made.
    In the skiba2012 case that is because the recovery constant is estimated from the average recovery intensity
    of the whole exercise.
    * performance above CP drains W' in a linear fashion
    """

    def __init__(self, w_p: float, cp: float):
        """
        constructor with basic constants
        :param cp:
        :param w_p:
        """

        super().__init__()

        # constants
        self._w_p = w_p
        self._cp = cp

        # fully rested, balance equals w_p
        self._w_bal_hist = []
        self._data = []

        self._dcp = None
        self._w_u = None
        self._u = None

        self._t = 0

    def reset(self):
        """
        resets all parameters
        :return:
        """
        self._w_bal_hist = []
        self._data = []

        self._dcp = None
        self._w_u = None
        self._u = None

        self._t = 0

    def get_w_p_balance_history(self):
        """:return: """
        return self._w_bal_hist

    @property
    def hz(self):
        """:return: hz. Integral hz default to 1"""
        return 1

    @property
    def cp(self):
        """:return: critical power"""
        return self._cp

    @property
    def w_p(self):
        """:return: anaerobic capacity"""
        return self._w_p

    def get_recovery_ratio(self, p_exp: float, p_rec: float, t_rec: int):
        """
        run a recovery estimation trial
        :param p_exp:
        :param p_rec:
        :param t_rec:
        :return: ratio as a percentage of W'
        """
        dynamics = self.get_recovery_dynamics(p_rec)
        ratio = 100.0
        # no recovery if no recovery time
        if t_rec == 0:
            ratio = 0.0
        # if rec_time is not in dynamics recovery is already at 100%
        elif t_rec < len(dynamics):
            ratio = (dynamics[t_rec - 1] / self._w_p) * 100.0
        return ratio

    def get_expenditure_dynamics(self, p: float, w_bal: float = None):
        """
        returns expenditure dynamics given intensity p. Position 0 in the resulting array is time step 1.
        :param p:
        :param w_bal:
        :return: W'bal history starting with time step 1
        """

        # set start W' bal
        if w_bal is None:
            w_bal = self._w_p

        # no expenditure below or at CP
        if p <= self._cp:
            logging.warning("Not possible to model expenditure for p <= CP")
            return np.nan

        # reset internal params
        self.reset()

        # set parameters for expenditure estimation
        self._w_bal_hist = [w_bal]

        while self._get_last_entry() > 0:
            self._expend(p)

        # because it started with the initial time step using wp
        self._w_bal_hist = self._w_bal_hist[1:]
        return self._w_bal_hist

    def get_tte(self, p: float, w_bal: float = None):
        """
        estimates the time until exhaustion with given power
        :param p:
        :param w_bal: the W'bal to start with
        :return: tte in seconds
        """
        if w_bal is None:
            w_bal = self._w_p
        dynamics = self.get_expenditure_dynamics(p=p, w_bal=w_bal)
        return len(dynamics)

    def get_recovery_dynamics(self, p_rec: float, init_w_bal: float = None):
        """
        Returns recovery dynamics given recovery power p. Position 0 in the resulting array is the initial w'bal.
        The integral approach does not consider changes in p_rec during recovery estimations.
        :param p_rec: recovery bout intensity
        :param init_w_bal: the W'bal to start recovery from
        :return: W'bal history starting at second 0
        """
        # reset internal params
        self.reset()

        if p_rec >= self._cp:
            logging.warning("Not possible to model recovery for p >= CP")
            return np.nan

        # set needed parameters for recovery estimation
        if init_w_bal is None:
            self._w_bal_hist = [0.0]
        else:
            self._w_bal_hist = [init_w_bal]

        self._dcp = self._cp - p_rec
        self._u = self._t
        self._w_u = self._w_p - self._get_last_entry()

        while self._get_last_entry() < self._w_p:
            self._t += 1
            self._recover()

        # because it started with the initial time step using wp
        return self._w_bal_hist

    def estimate_w_p_bal_to_data(self, data):
        """
        simple setter for the data to be processed with a trigger to initiate processing
        :param data:
        :return resulting W'bal history
        """
        self.reset()
        self._data = data
        self._process_data()
        return self._w_bal_hist

    def _process_data(self):
        """
        walks through stored data and creates the corresponding W'bal history
        """
        np_data = np.array(self._data)
        self._dcp = self._cp - np.mean(np_data[(np_data - self._cp) < 0])
        self._w_bal_hist = []
        for i, tp in enumerate(self._data):
            # keep track of time (assumes 1 step per sec)
            self._t = i + 1

            if tp >= self._cp:
                # update u and w'u as long as energy is expended
                # self._dcp = None
                self._u = self._t
                self._expend(tp)
                self._w_u = self._w_p - self._w_bal_hist[-1]
            else:
                # otherwise use recovery procedure
                self._recover()

    def _get_last_entry(self):
        """
        :return: last W'bal history entry or W' as default
        """
        if len(self._w_bal_hist) == 0:
            return self._w_p
        else:
            return self._w_bal_hist[-1]

    def _expend(self, p):
        """
        draw energy from the W' capacity. Typically in a linear fashion.
        :param p: power demands
        """
        last = self._get_last_entry()
        # cannot drop further than 0 because agent is exhausted
        self._w_bal_hist.append(max(last - (p - self._cp), 0))

    @abstractmethod
    def _recover(self):
        """
        recovering happens for p < cp. It reduces W' exp and increases W' balance
        """
