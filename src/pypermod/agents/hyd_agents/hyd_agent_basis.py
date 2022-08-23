from abc import abstractmethod


class HydAgentBasis:
    """
    Basis for Hydraulic Agents.
    This is an abstract class.
    Provided are functions for dynamic power outputs and commands for simulations.
    Hydraulic agents allow real time estimations.
    """

    def __init__(self, hz: int):
        """
        constructor
        :param hz: The steps per second this agent operates in
        """
        # simulation management parameters
        self._step = 0
        self._hz = hz
        self._hz_t = 0.0

        # power parameters
        self._pow = 0

    def get_name(self) -> str:
        """
        :return: a descriptive name
        """
        return self.__class__.__name__

    def set_power(self, power: float):
        """
        set power output directly
        :param power: power in Watts
        """
        self._pow = power

    def get_power(self) -> float:
        """
        :return: power in Watts
        """
        return self._pow

    @property
    def hz(self) -> int:
        """
        :return: number of obs per second
        """
        return self._hz

    def reset(self):
        """
        reset internal values to default
        """
        self._step = 0
        self._hz_t = 0.0
        # power output params
        self._pow = 0

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
    def is_exhausted(self) -> bool:
        """
        :return: simply returns the exhausted flag
        """

    @abstractmethod
    def is_recovered(self) -> bool:
        """
        :return: simply returns the recovered flag
        """

    @abstractmethod
    def is_equilibrium(self) -> bool:
        """
        :return: if energy storages are at a constant state
        """
