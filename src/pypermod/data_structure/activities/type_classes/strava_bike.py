import pandas as pd
from pypermod.data_structure.activities.data_formats.time_series import TimeSeries


class StravaBike(TimeSeries):
    """
    Straba Bike data
    """

    def set_data(self, data: pd.DataFrame):
        """
        Adds actual exercise data to the activity object
        :param data: the data to add
        """
        needed_cols = ['power', 'speed', 'cadence', 'altitude']
        # check if mandatory columns exist
        if any(i not in data.columns for i in needed_cols):
            raise UserWarning("Given dataframe with {} does not "
                              "contain one of {}".format(data.columns, needed_cols))
        super().set_data(data)

    @property
    def max_power(self):
        """
        :return: getter for max power output during this activity
        """
        return self.meta["max_power"]

    @property
    def power_data(self):
        """
        :return: power values
        """
        return self.data['power']

    @property
    def speed_data(self):
        """simple getter"""
        return self.data['speed']

    @property
    def cadence_data(self):
        """simple getter"""
        return self.data['cadence']

    @property
    def altitude_data(self):
        """simple getter"""
        return self.data['altitude']
