from pypermod import config

from pypermod.agents.hyd_agents.hyd_agent_basis import HydAgentBasis


class ThreeCompHydAgent(HydAgentBasis):
    """
    Implementation of the more abstract hydraulic model by Weigend et al. which they derived from Morton's generalised
    three component model of human bioenergetics. ODEs by Morton and numeric procedures by Sundström were used and
    adapted to develop the equations in _estimate_possible_power_output. We added extra limitations to handle extreme
    values. Please, see the Appendix of the document "A New Pathway to Approximate Energy Expenditure and Recovery of
    an Athlete" by Weigend et al. for a detailed rationale for procedures in _estimate_power_output.
    """

    def __init__(self, hz, lf, ls, m_u, m_ls, m_lf, the, gam, phi):
        """
        :param hz: calculations per second
        :param lf: cross sectional area of LF
        :param ls: cross sectional area of LS
        :param m_u: maximal flow from U to LF
        :param m_ls: maximal flow from LS to LF
        :param m_lf: maximal flow from LF to LS
        :param the: theta (distance top -> top LS)
        :param gam: gamma (distance bottom -> bottom LS)
        :param phi: phi (distance bottom -> bottom U)
        """
        super().__init__(hz=hz)

        # constants
        self.__theta, self.__gamma, self.__phi = the, gam, phi
        # height of vessel LS
        self.__height_ls = 1 - self.__theta - self.__gamma

        # the LS tank has to have a positive size
        if self.__height_ls <= 0:
            raise UserWarning("LS has negative height: Theta {} Gamma {} Phi {}".format(the, gam, phi))

        # the optional LS tank constraint that corresponds to 1 - phi > theta
        # described as "hitting the wall" constraint that says glycogen can be depleted below VO2 MAX
        if config.three_comp_phi_constraint is True:
            if self.__phi > self.__gamma:
                raise UserWarning("phi not smaller gamma")

        # vessel areas
        self.__lf = lf  # area of vessel LF
        self.__ls = ls  # area of LS

        # max flows
        self.__m_u = m_u  # max flow from U to LF
        self.__m_ls = m_ls  # max flow from LS to LF
        self.__m_lf = m_lf  # max flow from LF to LS

        # self.__w_m = 100  # max instantaneous power (not in use yet)

        # variable parameters
        self.__h = 0.0  # state of depletion of vessel LF
        self.__g = 0.0  # state of depletion of vessel LS
        self.__p_u = 0.0  # flow from U to LF
        self.__p_l = 0.0  # flow from LS to LF (bi-directional)
        self.__m_flow = 0.0  # maximal flow through pg according to liquid diffs

    def __str__(self):
        """
        print function
        :return: parameter overview
        """
        return "Three Component Hydraulic Agent \n" \
               "LF, LS, M_U, M_LS, M_LF, theta, gamma, phi \n " \
               "{}".format([self.__lf, self.__ls, self.__m_u, self.__m_ls,
                            self.__m_lf, self.__theta, self.__gamma, self.__phi])

    def __raise_detailed_error_report(self):
        """
        raises a UserWarning exception with info about configuration, fill states, and power demands
        """
        raise UserWarning("Unhandled tank fill-level state \n"
                          "gamma:  {} \n "
                          "theta:  {} \n "
                          "phi:    {} \n "
                          "LF:    {} \n "
                          "LS:    {} \n "
                          "g:      {} \n "
                          "h:      {} \n "
                          "m_u:   {} \n"
                          "m_ls:  {} \n"
                          "m_lf:  {} \n"
                          "p_U:   {} \n"
                          "p_L:   {} \n"
                          "pow:    {} \n".format(self.__gamma,
                                                 self.__theta,
                                                 self.__phi,
                                                 self.__lf,
                                                 self.__ls,
                                                 self.__g,
                                                 self.__h,
                                                 self.__m_u,
                                                 self.__m_ls,
                                                 self.__m_lf,
                                                 self.__p_u,
                                                 self.__p_l,
                                                 self._pow))

    def _estimate_possible_power_output(self):
        """
        Estimates liquid flow to meet set power demands. Exhaustion flag is set and internal tank fill levels and
        pipe flows are updated.
        :return: power output
        """

        # step 1: drop level in LF according to power demand
        # estimate h_{t+1}: scale to hz (delta t) and drop the level of LF
        self.__h += self._pow / self.__lf / self._hz

        # step 2: determine tank flows to respond to change in h_{t+1}

        # step 2 a: determine oxygen energy flow (P_U)
        # level LF above pipe exit. Scale contribution according to h level
        if 0 <= self.__h < (1 - self.__phi):
            # contribution from U scales with maximal flow capacity
            self.__p_u = self.__m_u * self.__h / (1 - self.__phi)
        # at maximum rate because level h of LF is below pipe exit of U
        elif (1 - self.__phi) <= self.__h:
            # max contribution R1 = m_u
            self.__p_u = self.__m_u
        else:
            self.__raise_detailed_error_report()

        # multiply with delta t1
        self.__p_u = self.__p_u / self._hz

        # step 2 b: determine the slow component energy flow (P_U)
        # [no change] LS full and level LF above level LS
        if self.__h <= self.__theta and self.__g == 0:
            self.__p_l = 0.0
        # [no change] LS empty and level LF below pipe exit
        elif self.__h >= (1 - self.__gamma) and self.__g == self.__height_ls:
            self.__p_l = 0.0
        # [no change] h at equal with g
        elif self.__h == (self.__g + self.__theta):
            self.__p_l = 0.0
        else:
            # [restore] if level LF above level LS and LS is not full
            if self.__h < self.__g + self.__theta and self.__g > 0:
                # see EQ (16) in Morton (1986)
                self.__p_l = -self.__m_lf * (self.__g + self.__theta - self.__h) / (1 - self.__gamma)
            # [utilise] if level LS above level LF and level LF above pipe exit of LS
            elif (self.__g + self.__theta) < self.__h < (1 - self.__gamma):
                # EQ (9) in Morton (1986)
                self.__p_l = self.__m_ls * (self.__h - self.__g - self.__theta) / self.__height_ls
            # [utilise max] if level LF below or at LS pipe exit and LS not empty
            elif (1 - self.__gamma) <= self.__h and self.__g < self.__height_ls:
                # the only thing that affects flow is the amount of remaining liquid (pressure)
                # EQ (20) Morton (1986)
                self.__p_l = self.__m_ls * (self.__height_ls - self.__g) / self.__height_ls
            else:
                self.__raise_detailed_error_report()

            # This check is added to handle cases where the flow causes level height swaps between LS and LF
            self.__m_flow = ((self.__h - (self.__g + self.__theta)) / (
                    (1 / self.__ls) + (1 / self.__lf)))

            # consider delta t before extreme values get capped
            self.__p_l = self.__p_l / self._hz

            # Cap flow according to estimated limits
            if self.__p_l < 0:
                self.__p_l = max(self.__p_l, self.__m_flow)
                # don't refill more than there is capacity
                self.__p_l = max(self.__p_l, -self.__g * self.__ls)
            elif self.__p_l > 0:
                self.__p_l = min(self.__p_l, self.__m_flow)
                # don't drain more than is available in LS
                self.__p_l = min(self.__p_l, (self.__height_ls - self.__g) * self.__ls)

        # level LS is adapted to estimated change
        # g increases as liquid flows into LF
        self.__g += self.__p_l / self.__ls
        # refill or deplete LF according to LS flow and Power demand
        # h rises as p_u and p_l flow into LF
        self.__h -= (self.__p_u + self.__p_l) / self.__lf

        # step 3: account for rounding errors and set exhaustion flag
        self._exhausted = self.__h >= 1.0
        # apply limits so that tanks cannot be fuller than full or emptier than empty
        self.__g = max(self.__g, 0.0)
        self.__g = min(self.__g, self.__height_ls)
        self.__h = max(self.__h, 0.0)
        self.__h = min(self.__h, 1.0)

        return self._pow

    def is_exhausted(self) -> bool:
        """
        exhaustion is reached when level in LF cannot sustain power demand
        :return: simply returns the exhausted boolean
        """
        return bool(self.__h >= 1.0)

    def is_recovered(self) -> bool:
        """
        recovery is estimated according to w_p ratio
        :return: simply returns the recovered boolean
        """
        return self.get_w_p_ratio() == 1.0

    def is_equilibrium(self) -> bool:
        """
        equilibrium is reached when ph meets pow and LS does not contribute or drain
        :return: boolean
        """
        return abs(self.__p_u - self._pow) < 0.1 and abs(self.__p_l) < 0.1

    def reset(self):
        """power parameters"""
        super().reset()
        # variable parameters
        self.__h = 0  # state of depletion of vessel LF
        self.__g = 0  # state of depletion of vessel LS
        self.__p_u = 0  # flow from U to LF
        self.__p_l = 0  # flow from LS to LF

    def get_w_p_ratio(self):
        """
        :return: wp estimation between 0 and 1 for comparison to CP models
        """
        return 1.0 - self.__h

    def get_fill_lf(self):
        """
        :return: fill level of LF between 0 - 1
        """
        return 1 - self.__h

    def get_fill_ls(self):
        """
        :return:fill level of LS between 0 - 1
        """
        return (self.__height_ls - self.__g) / self.__height_ls

    @property
    def phi_constraint(self):
        """
        getter for phi_constraint flag
        :return boolean ture or false
        """
        return config.three_comp_phi_constraint

    @property
    def lf(self):
        """
        :return cross sectional area of LF
        """
        return self.__lf

    @property
    def ls(self):
        """
        :return cross sectional area of LS
        """
        return self.__ls

    @property
    def theta(self):
        """
        :return theta (distance top -> top LS)
        """
        return self.__theta

    @property
    def gamma(self):
        """
        :return gamma (distance bottom -> bottom LS)
        """
        return self.__gamma

    @property
    def phi(self):
        """
        :return phi (distance bottom -> bottom U)
        """
        return self.__phi

    @property
    def height_ls(self):
        """
        :return height of vessel LS
        """
        return self.__height_ls

    @property
    def m_u(self):
        """
        :return maximal flow from U to LF
        """
        return self.__m_u

    @property
    def m_ls(self):
        """
        :return maximal flow from LS to LF
        """
        return self.__m_ls

    @property
    def m_lf(self):
        """
        :return maximal flow from LF to LS
        """
        return self.__m_lf

    def get_m_flow(self):
        """
        :return maximal flow through pg from liquid height diffs
        """
        return self.__m_flow

    def get_g(self):
        """
        :return state of depletion of vessel LS
        """
        return self.__g

    def set_g(self, g):
        """
        setter for state of depletion of vessel AnS
        """
        self.__g = g

    def get_h(self):
        """
        :return state of depletion of vessel LF
        """
        return self.__h

    def set_h(self, h):
        """
        setter for state of depletion of vessel AnF
        """
        self.__h = h

    def get_p_u(self):
        """
        :return flow from U to LF
        """
        return self.__p_u

    def get_p_l(self):
        """
        :return flow from LS to LF
        """
        return self.__p_l
