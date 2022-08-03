import logging

from datetime import datetime

from pypermod.data_structure.activities.data_formats.time_series import TimeSeries
from pypermod.data_structure.activities.protocol_types import ProtocolTypes


class ProtocolTimeStamps(TimeSeries):
    """
    Protocol tests are a time series with a warmup and recovery time stamp
    """

    def __init__(self, date_time: datetime):
        """
        Constructor
        :param date_time:
        """
        # parent's constructor
        super().__init__(date_time=date_time)

        self._warmup = None
        self._recovery = None

    def update_meta_data(self):
        """ updates internal metadata """
        super().update_meta_data()
        # set the offset
        self._metadata["warmup"] = self._warmup
        self._metadata["recovery"] = self._recovery

    def _load_meta(self):
        """ sets internal data with info from loaded meta"""
        super()._load_meta()
        if "warmup" in self._metadata:
            self._warmup = self._metadata["warmup"]
        if "recovery" in self._metadata:
            self._recovery = self._metadata["recovery"]

    def filter_exercise_data(self, times, data):
        """
        :param times: time that each row of data was collected at
        :param data: data to filter
        :return: selection of input data that's within the time frame defined by warmup and recovery
        """
        sel_data = data.loc[(times >= self.get_warmup_end_timestamp()) &
                            (times <= self.get_recovery_start_timestamp())]
        # dataset is sliced. Indices have to be renewed
        sel_data = sel_data.reset_index(drop=True)
        return sel_data

    def get_warmup_end_timestamp(self):
        """
        Defines when warmup ends
        simple getter with availability check
        :return the warmup timestamp
        """
        if self._warmup is None:
            try:
                self._warmup = self.meta["warmup"]
                # might be stored as None
                if self._warmup is None:
                    raise KeyError
            except KeyError:
                logging.warning("activity {} has no warmup timestamp defined -> returning 0".format(self.id))
                return 0
        return self._warmup

    def get_recovery_start_timestamp(self):
        """
        Defines when recovery starts and exercise ends
        simple getter with availability check
        :return the recovery end timestamp
        """
        if self._recovery is None:
            try:
                self._recovery = self.meta["recovery"]
                # might be stored as None
                if self._recovery is None:
                    raise KeyError
            except KeyError:
                logging.warning("activity {} no recovery start timestamp defined -> "
                                "returning last observed time {}".format(self.id, self.time_data.iloc[-1]))
                return self.time_data.iloc[-1]
        return self._recovery

    def set_protocol_with_timestamps(self, prot_type: ProtocolTypes, warmup: float, exercise_end_time: float):
        """
        Sets timestamps according to protocol and measurement starts
        :param prot_type: defines the protocol type of the test
        :param warmup: Defines when warmup ends
        :param exercise_end_time: Defines when exercise ends and recovery starts
        """

        if self.data is None:
            raise UserWarning("please add data to activity before setting timestamps")

        # use activity base class method to set the protocol
        self.set_protocol(prot_type)

        # use additional setup specific time stamps for the rest
        self._warmup = warmup
        self._recovery = exercise_end_time

        # some checks to ensure sensible values are stored
        if warmup < 0:
            raise UserWarning("Warmup timestamp ({}) cannot be "
                              "smaller than exercise start (assumed to be 0)".format(warmup))
        if exercise_end_time > self.time_data.iloc[-1]:
            raise UserWarning("Recovery start timestamp ({}) cannot be "
                              "greater than last observed timestamp ({})".format(exercise_end_time,
                                                                                 self.time_data.iloc[-1]))

        self.update_meta_data()
