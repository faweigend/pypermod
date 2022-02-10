from datetime import datetime

import pandas as pd
from pypermod.data.activities.data_types.power_measured import PowerMeasured
from pypermod.data.activities.data_types.protocol_test import ProtocolTest
from pypermod.data.activities.data_types.bbb_measured import BbbMeasured


class SRMBbBTest(ProtocolTest, PowerMeasured, BbbMeasured):
    """
    A performance bike test on the SRM device
    coupled with breath-by-breath data collection with the Cosmed.
    """

    def __init__(self, date_time: datetime):
        """
        Constructor
        :param date_time:
        """
        # parent's constructor
        super().__init__(date_time=date_time)

    def set_data(self, data: pd.DataFrame):
        """
        Adds actual exercise data to the activity object
        :param data: the data to add
        """
        needed_cols = ['speed', 'cadence', 'altitude']
        # check if mandatory columns exist
        if any(i not in data.columns for i in needed_cols):
            raise UserWarning("Given dataframe with {} does not "
                              "contain one of {}".format(data.columns, needed_cols))
        super().set_data(data)

    def get_exercise_srm_data(self):
        """
        :return: selection of srm data that's within the time frame defined by warmup and recovery
        """
        return self.filter_exercise_data(self.time_data, self.data)

    def get_exercise_bbb_data(self):
        """
        :return: selection of bbb data that's within the time frame defined by warmup and recovery
        """
        return self.filter_exercise_data(self.bbb_time_data, self.bbb_data)

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
