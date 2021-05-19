class IntegralAgentBasis:
    """
    This is an abstract class and defines the structure for all integral agents.
    Integral agents require full information about the whole course and cannot provide "on-the-fly+ estimations
    """

    def __init__(self, hz: int):
        """
        constructor
        :param hz: The steps per second this agent operates in
        """
        self._hz = hz

    def reset(self):
        """
        empty reset function
        :return:
        """
        pass

    def get_name(self):
        """
        :return: a descriptive name
        """
        return self.__class__.__name__

    @property
    def hz(self):
        """
        :return: number of obs per second
        """
        return self._hz
