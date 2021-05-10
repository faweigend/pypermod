import math
from abc import abstractmethod


class IntegralAgentBasis:
    """
    This is an abstract class and defines the structure for all integral agents.
    Integral agents require full information about the whole course and cannot provide "on-the-fly+ estimations
    """

    def __init__(self):
        """
        constructor
        """

    def get_name(self):
        """
        :return: a descriptive name
        """
        return self.__class__.__name__