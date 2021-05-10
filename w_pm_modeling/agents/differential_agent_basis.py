from abc import abstractmethod


class DifferentialAgentBasis:
    """
    This is an abstract class and defines the structure for all differential agents.
    Provided are functions for dynamic power outputs and commands for simulations.
    Differential agents allow real time estimations.
    """

    def __init__(self, hz: int):
        """
        constructor
        :param hz: The steps per second this agent operates in
        """
        # simulation management parameters
        self._step = 0
        self._hz = hz
        self._hz_t = 0

        # power parameters
        self._pow = 0

    def get_name(self):
        """
        :return: a descriptive name
        """
        return self.__class__.__name__

    def set_power(self, power: float):
        """
        set power output directly to skip acceleration phases
        :param power: power in Watts
        """
        self._pow = power

    def get_power(self):
        """
        :return: power in Watts
        """
        return self._pow

    @property
    def hz(self):
        """
        :return: number of obs per second
        """
        return self._hz

    def reset(self):
        """
        reset internal values to default
        """
        self._step = 0
        self._hz_t = 0
        # power output params
        self._pow = 0

    def get_time(self):
        """
        :return: time in seconds considering the agent's hz setting
        """
        return self._hz_t

    def perform_one_step(self):
        """
        Updates power output and internal W' balance parameters.
        :return: expended power
        """
        # increase time counter
        self._step = self._step + 1
        self._hz_t = self._step / self._hz

        # use updated instantaneous power to update internal capacities
        self._pow = self._estimate_possible_power_output()

        # final instantaneous power output
        return self._pow

    @abstractmethod
    def _estimate_possible_power_output(self):
        """
        Update internal capacity estimations by one step.
        :return: the amount of power that the athlete was able to put out
        """

    @abstractmethod
    def is_exhausted(self):
        """
        :return: simply returns the exhausted flag
        """

    @abstractmethod
    def is_recovered(self):
        """
        :return: simply returns the recovered flag
        """

    @abstractmethod
    def is_equilibrium(self):
        """
        returns if energy storages are at a constant state
        :return:
        """
