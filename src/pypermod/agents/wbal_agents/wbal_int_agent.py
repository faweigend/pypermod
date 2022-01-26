import logging
import math
from abc import abstractmethod

import numpy as np
from pypermod.agents.cp_agent_basis import CpAgentBasis


class WbalIntAgent(CpAgentBasis):
    """
    The virtual agent model. Integral agents need the entire exercise to be
    known before estimations can be made. A convolutional integral is applied.
    """

    @abstractmethod
    def _get_tau_to_dcp(self, dcp: float):
        """
        Estimate tau from given dcp
        :param dcp: Average difference to CP during recovery bouts
        :return: Tau
        """

    def get_expenditure_dynamics(self, p_exp, dcp: float = None):
        """
        Returns expenditure dynamics given intensity p.
        :param p_exp: constant exercise intensity
        :param dcp: (optional) average difference to CP used for the determination of tau
        :return: W'bal history. Position 0 in the resulting array is time step 1.
        """

        # no expenditure below or at CP
        if p_exp <= self._cp:
            logging.warning("Not possible to model expenditure for p <= CP")
            return np.nan

        # a custom DCP might be set to experiment with behaviour...
        if dcp is None:
            # ... if not, DCP is 0 in this case because it is a TTE
            dcp = 0

        tau = self._get_tau_to_dcp(dcp)

        # Now that tau is known, use internal _get_expenditure_dynamics method
        return self._get_expenditure_dynamics(p_exp=p_exp, tau=tau)

    def get_tte(self, p_exp: float):
        """
        estimates the time until exhaustion at given constant exercise intensity in Watts
        :param p_exp: constant exercise intensity in Watts
        :return: tte in seconds
        """
        dynamics = self.get_expenditure_dynamics(p_exp=p_exp)
        # dynamics skip time step 0. Therefore, total time in seconds conforms to length of dynamics
        return len(dynamics)

    def get_recovery_dynamics(self, p_rec: float, max_steps: int):
        """
        Returns recovery dynamics given recovery power p. Position 0 in the resulting array is the initial w'bal of 0.
        The integral approach does not consider changes in p_rec during recovery estimations.
        :param p_rec: recovery bout intensity in Watts
        :param max_steps: when to stop
        :return: W'bal history. Position 0 in the resulting array is the initial W'bal of 0 at time step 0.
        """

        if p_rec >= self._cp:
            logging.warning("Not possible to model recovery for p >= CP")
            return np.nan

        dcp = self._cp - p_rec
        tau = self._get_tau_to_dcp(dcp)

        # at initial time step 0 the agent is fully exhausted
        w_bal_hist = [0]
        w_exp = self._w_p

        # EQ (2) in Skiba et al. 2012
        t = 1
        while t <= max_steps and w_bal_hist[-1] < self._w_p:
            sum_t = w_exp * pow(math.e, -t / tau)

            # apply limits
            sum_t = min(sum_t, self._w_p)
            w_bal = self._w_p - sum_t
            w_bal_hist.append(w_bal)
            t += 1

        # skip time step 0 to conform to equation by Skiba and Clarke (2021)
        return w_bal_hist[1:]

    def estimate_w_p_bal_to_data(self, data):
        """
        initiate processing data and kick off W'bal history estimation
        :param data:
        :return resulting W'bal history
        """
        np_data = np.array(data)
        # dcp only works if power demand is below CP at any point
        if np.any((np_data - self._cp) < 0):
            dcp = self._cp - np.mean(np_data[(np_data - self._cp) < 0])
        else:
            logging.warning("No recovery found in data. DCP set to 0")
            dcp = 0
        tau = self._get_tau_to_dcp(dcp)
        # now that tau is known, use internal _process_data method
        return self._process_data(data, tau)

    def _process_data(self, data: np.array, tau: float):
        """
        walks through data and creates the corresponding W'bal history
        :param data: power demand data to simulate
        :param tau: recovery time constant to use
        :return: W'bal history. Pos 0 is time step 1
        """

        # ensure type
        np_data = np.array(data)
        w_bal_hist = [self._w_p]  # starts with time step 0

        # Wexp is the expended energy above CP or 0 if below CP
        np_exp = np.where((np_data - self._cp) > 0, np_data - self._cp, 0)

        # EQ (2) in Skiba et al. 2012
        for t in range(0, len(np_data)):
            sum_t = 0.0
            for u in range(0, t + 1):
                sum_t += np_exp[u] * pow(math.e, -(t - u) / tau)

            # apply limits
            sum_t = min(sum_t, self._w_p)
            w_bal_hist.append(self._w_p - sum_t)

        # skip time step 0 to conform to equation by Skiba and Clarke (2021)
        return w_bal_hist[1:]

    def _get_expenditure_dynamics(self, p_exp: float, tau: float):
        """
        returns expenditure dynamics given intensity p.
        :param p_exp: constant exercise intensity in Watts
        :return: W'bal history. Pos 0 is time step 1
        """
        # Wexp is the expended energy above CP (here a constant)
        np_exp = p_exp - self._cp

        #  at time step 0, W'balance is at max
        w_bal_hist = [self._w_p]
        t = 0

        max_steps = 5000
        # EQ (2) in Skiba et al. 2012
        while w_bal_hist[-1] > 0 and t < max_steps:
            sum_t = 0.0
            for u in range(0, t + 1):
                sum_t += np_exp * pow(math.e, -(t - u) / tau)

            # apply limits and append
            sum_t = min(sum_t, self._w_p)
            w_bal_hist.append(self._w_p - sum_t)
            t += 1

        if t >= max_steps:
            raise UserWarning("exhaustion not reached")

        # skip time step 0 to conform to equation by Skiba and Clarke (2021)
        return w_bal_hist[1:]
