import datetime
import logging
import os

import pandas as pd

from pypermod.data_structure.activities.data_formats.time_series import TimeSeries


class BbbMeasured(TimeSeries):
    """
    This activity class adds Breath-by-Breath observations typically collected with COSMED to TimeSeries data.
    Considered COSMED measures are 'vo2', 'hr', 'vco2', 'fat', 'cho', 'rer'.
    Such Breath-by-Breath observations are characterised by irregular time steps.
    This class offers binning as one way to align irregular time steps with other observations.
    """

    def __init__(self, date_time: datetime):
        """
        Set up the basic structure
        :param date_time:
        """
        # create save/load structure
        super().__init__(date_time=date_time)
        self._bbb_data = None
        self._binned_bbb_data = None

        # bbb measures are a separate data set.
        # Thus, they don't start at the same time the data of the parent activity starts at.
        # this offset variable sets the time difference between the first bbb measure
        # and time point of the first observation in activity data to align both data sets.
        self._bbb_offset = None

    def update_meta_data(self):
        """
        Update meta data with bbb specific info
        """
        super().update_meta_data()

        if self.__is_bbb_data_loaded() and self._metadata is not None:

            # set the offset
            self._metadata["bbb_offset"] = self._bbb_offset

            # add averages and means of available bbb columns
            col = "vo2"
            self._metadata.update({"{}_avr".format(col): float(self._bbb_data[col].mean()),
                                   "{}_max".format(col): float(self._bbb_data[col].max())})

            # store or update total activity duration since bbb data has an effect on total time
            if "duration" in self._metadata:
                self._metadata["duration"] = max(self._metadata["duration"], self.bbb_time_data.values[-1])
            else:
                self._metadata["duration"] = self.bbb_time_data.values[-1]

    def set_bbb_data(self, bbb_data: pd.DataFrame, offset: float):
        """
        Adds breath-by-breath observations to activity and stores them as a pd dataframe
        :param bbb_data:
        :param offset:
        """
        needed_cols = ['ve', 'sec', 'vo2', 'hr', 'vco2', 'fat', 'cho', 'rer']
        # check if mandatory columns exist
        if any(i not in bbb_data.columns for i in needed_cols):
            raise UserWarning("Given dataframe with {} does not "
                              "contain one of {}".format(bbb_data.columns, needed_cols))

        self._bbb_data = bbb_data
        # add offset to seconds measure
        self._bbb_data['sec'] += offset
        self._bbb_offset = offset
        self.update_meta_data()

    def save(self):
        """
        stores meta and data to local files
        """
        super().save()
        if self._bbb_data is None:
            logging.warning("bbb save called with no data bbb data available")
        else:
            self._bbb_data.to_csv(
                os.path.join(self._dir_path, "{}-bbb.csv".format(self.id)),
                index=False
            )

    def get_bbb_offset(self):
        """
        simple getter with double-check in metadata check
        """
        if self._bbb_offset is None:
            try:
                self._bbb_offset = self._metadata["bbb_offset"]
            except KeyError:
                logging.warning("asked for bbb offset with no offset available")
                return None
        return self._bbb_offset

    def set_bbb_offset(self, offset: float):
        """
        :param offset:
        """
        if self.has_bbb_data():
            self._bbb_offset = offset
            # offset is stored in metadata
            self.update_meta_data()

    def free_memory(self):
        """
        If the activity object has te be kept but you want to free RAM from loaded data
        :return:
        """
        super().free_memory()
        self._bbb_data = None

    def load(self):
        """
        Adds bbb data to load list
        :return:
        """
        super().load()
        self.__load_bbb_data()

    def _load_meta(self):
        """
        sets internal data with info from loaded meta
        """
        super()._load_meta()
        if "bbb_offset" in self._metadata:
            self._bbb_offset = self._metadata["bbb_offset"]

    def __is_bbb_data_loaded(self):
        """
        simple check
        """
        return self._bbb_data is not None

    def __load_bbb_data(self):
        """
        loads bbb data from file
        :return:
        """
        fname = os.path.join(self._dir_path,
                             "{}-bbb.csv".format(self.id))
        if not os.path.isfile(fname):
            return False
        # set offset from stored metadata
        self._bbb_offset = self.meta["bbb_offset"]
        # read data from pickle file
        self._bbb_data = pd.read_csv(fname)
        return True

    def has_bbb_data(self):
        """
        check if breath-by-breath values were stored
        :return:
        """
        return self.bbb_data is not None

    @property
    def bbb_data(self):
        """
        Loads bbb data it if not loaded yet
        :return: bbb data as pandas dataframe
        """
        if self._bbb_data is None:
            if self.__load_bbb_data() is False:
                return None
        return self._bbb_data

    @property
    def bbb_time_data(self):
        """:return: seconds column"""
        return self.bbb_data['sec']

    @property
    def ve_data(self):
        """simple getter with defined column name"""
        return self.bbb_data['ve']

    @property
    def vo2_data(self):
        """simple getter with defined column name"""
        return self.bbb_data['vo2']

    @property
    def vco2_data(self):
        """simple getter with defined column name"""
        return self.bbb_data['vco2']

    @property
    def hr_data(self):
        """simple getter with defined column name"""
        return self.bbb_data['hr']

    @property
    def fat_data(self):
        """simple getter with defined column name"""
        return self.bbb_data['fat']

    @property
    def cho_data(self):
        """simple getter with defined column name"""
        return self.bbb_data['cho']

    @property
    def rer_data(self):
        """simple getter with defined column name"""
        return self.bbb_data['rer']
