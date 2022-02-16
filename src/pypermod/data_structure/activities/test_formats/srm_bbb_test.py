import pandas as pd
from pypermod.data_structure.activities.data_formats.protocol_time_stamps import ProtocolTimeStamps
from pypermod.data_structure.activities.data_formats.bbb_measured import BbbMeasured


class SRMBbbTest(ProtocolTimeStamps, BbbMeasured):
    """
    A performance bike test on the SRM cycle ergometer
    coupled with breath-by-breath data collection with the Cosmed.
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

    def update_meta_data(self):
        """
        Update meta data with power measured specific info
        """
        super().update_meta_data()

        if self.is_data_loaded():
            # because of the condition in set_data a column 'power' must exist
            self._metadata.update({
                "resistance": self.altitude_data.max()
            })

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
