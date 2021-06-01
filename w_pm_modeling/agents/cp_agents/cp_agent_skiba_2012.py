import logging
import math

import numpy as np
from w_pm_modeling.agents.cp_agents.cp_integral_agent_basis import CpIntegralAgentBasis


class CpAgentSkiba2012(CpIntegralAgentBasis):
    """
    The virtual agent model employing Skiba's 2012 Equation for expenditure and recovery kinetics.
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

    @staticmethod
    def _estimate_tau(dcp: float):
        """
        Applies Eq 3 from Skiba et al. 2012 to estimate tau from given dcp
        :param dcp: Average difference to CP during recovery bouts
        :return: Tau
        """
        # EQ (3) in Skiba et al. 2012
        return 546 * pow(math.e, (-0.01 * dcp)) + 316

    def get_expenditure_dynamics(self, p_exp, dcp: float = None):
        """
        returns expenditure dynamics given intensity p. Position 0 in the resulting array is time step 1.
        :param p_exp: constant exercise intensity
        :param dcp: average difference to CP used for the determination of tau
        :return: W'bal history
        """
        # no expenditure below or at CP
        if p_exp <= self._cp:
            logging.warning("Not possible to model expenditure for p <= CP")
            return np.nan

        # a custom DCP might be set to experiment with behaviour...
        if dcp is None:
            # ... if not, DCP is 0 in this case because it is a TTE
            dcp = 0

        tau = self._estimate_tau(dcp)

        # use parent class method
        return self._get_expenditure_dynamics(p_exp=p_exp, tau=tau)

    def get_recovery_dynamics(self, p_rec: float, max_steps: int):
        """
        Returns recovery dynamics given recovery power p. Position 0 in the resulting array is the initial w'bal.
        The integral approach does not consider changes in p_rec during recovery estimations.
        :param p_rec: recovery bout intensity
        :param max_steps: when to stop
        :return: W'bal history
        """
        dcp = self._cp - p_rec
        tau = self._estimate_tau(dcp)
        # use parent class method
        return self._get_recovery_dynamics(p_rec=p_rec, max_steps=max_steps, tau=tau)

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
        tau = self._estimate_tau(dcp)
        # use parent class method
        return self._process_data(data, tau)
