class CpAgentBasis:
    """
    This is an abstract class and defines the structure for all agents.
    """

    def __init__(self, w_p: float, cp: float, hz: int = 1):
        """
        constructor
        :param hz: The steps per second this agent operates in
        """
        # constants
        self._hz = hz
        self._delta_t = float(1 / hz)
        self._w_p = w_p
        self._cp = cp

    @property
    def cp(self):
        """:return: critical power"""
        return self._cp

    @property
    def w_p(self):
        """:return: anaerobic capacity"""
        return self._w_p

    def reset(self):
        """
        empty reset function
        """
        pass

    def get_name(self) -> str:
        """
        :return: a descriptive name
        """
        return self.__class__.__name__

    @property
    def hz(self) -> int:
        """
        :return: number of obs per second
        """
        return self._hz
