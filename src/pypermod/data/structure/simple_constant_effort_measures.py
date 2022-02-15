class SimpleConstantEffortMeasures:
    """
    Used to standardise collections of constant time-to-exhaustion efforts.
    This is mostly intended for the use of CP and W' fittings
    """

    def __init__(self, times, measures, name: str = "ConstantEffortMeasures"):
        """
        constructor
        :param times:
        :param measures:
        """
        # ensure it's cast into the right format from e.g. read json files
        self.__times = [float(x) for x in list(times)]
        self.__measures = [float(x) for x in list(measures)]
        self.__name = name

    def __len__(self):
        """length definition"""
        return len(self.__times)

    def __str__(self):
        """
        print function
        :return: stored values as a stringified dict
        """
        return str(dict(zip(self.__times, self.__measures)))

    def as_dict(self):
        """:return: a dict with powers as keys and times as values"""
        return dict(zip(self.__times, self.__measures))

    @property
    def name(self):
        """:return: name"""
        return self.__name

    @property
    def times(self):
        """:return: stored time values as list"""
        return self.__times

    @property
    def measures(self):
        """:return: stored power values as list"""
        return self.__measures

    def iterate_pairs(self):
        """generator for time/measure pairs"""
        for i in range(len(self.__times)):
            yield self.__times[i], self.__measures[i]
