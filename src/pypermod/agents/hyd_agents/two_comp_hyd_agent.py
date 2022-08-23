from pypermod.agents.hyd_agents.hyd_agent_basis import HydAgentBasis


class TwoCompHydAgent(HydAgentBasis):

    def __init__(self, an: float, cp: float, phi: float, psi: float = 0.0, hz: int = 10):
        """
        :param an: capacity of An
        :param cp: maximal flow from Ae to An
        :param phi: phi (distance Ae to bottom)
        :param phi: psi (distance An to top)
        :param hz: calculations per second
        """
        super().__init__(hz=hz)

        if psi > 1 - phi:
            if abs(psi - (1 - phi)) < 0.001:
                psi = 1 - phi
            else:
                raise UserWarning("Top of An has to be above or at bottom of Ae (psi > 1 - phi must be False)")

        # constants
        self.__phi = phi  # bottom of Ae tank
        self.__psi = psi  # top of An tank
        self.__an = an  # capacity of An tank
        self.__cp = cp  # max flow from Ae to An

        # variable parameters
        self.__h = 0  # state of depletion of vessel W'
        self.__p_ae = 0  # flow from Ae

    @property
    def an(self):
        """:return cross sectional area of W'"""
        return self.__an

    @property
    def phi(self):
        """:return phi (distance Ae to bottom)"""
        return self.__phi

    @property
    def psi(self):
        """:return psi (distance W' to top)"""
        return self.__psi

    @property
    def cp(self):
        """:return max flow through R1"""
        return self.__cp

    def get_w_p_balance(self):
        """:return remaining energy in W' tank"""
        return (1.0 - self.psi - self.__h) / (1.0 - self.psi) * self.__an

    def get_h(self):
        """:return state of depletion of vessel P"""
        return self.__h

    def get_p_ae(self):
        """:return flow through R1"""
        return self.__p_ae

    def _estimate_possible_power_output(self):
        """
        Update internal capacity estimations by one step.
        :return: the amount of power that the athlete was able to put out
        """

        # the change on fill-level of An by flow from tap
        self.__h += (1.0 - self.psi) * self._pow / self.__an / self._hz

        # level An above pipe exit. Scale flow according to h level
        if (self.__h + self.__psi) <= (1.0 - self.__phi):
            self.__p_ae = self.__cp * (self.__h + self.__psi) / (1.0 - self.__phi)

        # at maximum rate because level h is below pipe exit of p_Ae
        else:
            self.__p_ae = self.__cp

        # consider hz (delta t)
        self.__p_ae = self.__p_ae / self._hz

        # due to psi there might be pressure on p_ae even though the tap is closed and An is full
        if self.__p_ae > self.get_w_p_balance():
            self.__p_ae = self.get_w_p_balance()

        # the change on fill-level of An by flow from Ae
        self.__h -= (1.0 - self.psi) * self.__p_ae / self.__an

        # also W' cannot be fuller than full
        if self.__h < 0:
            self.__h = 0
        # ...or emptier than empty
        elif self.__h > 1.0 - self.psi:
            self.__h = 1.0 - self.psi

        return self._pow

    def is_exhausted(self) -> bool:
        """
        exhaustion is reached when level in An cannot sustain power demand
        :return: simply returns the exhausted flag
        """
        return self.__h == 1.0 - self.psi

    def is_recovered(self) -> bool:
        """
        recovery is complete when An is full again
        :return: simply returns boolean flag
        """
        return self.__h == 0

    def is_equilibrium(self) -> bool:
        """
        equilibrium is reached when p_ae meets p
        :return: boolean flag
        """
        return abs(self.__p_ae - self._pow) < 0.01
