import datetime
import json
import logging
import os

import pandas as pd

import config
import utility

from sportsparsing.activities.protocol_types import ProtocolTypes


class Activity:
    """
    Provides the setup to store and load activity objects
    according to established convention
    """

    def __init__(self, date_time: datetime,
                 protocol_type: ProtocolTypes = ProtocolTypes.UNDEFINED):
        """
        Set up the basic structure
        :param date_time:
        :param protocol_type:
        """
        self._dt_string = utility.date_to_string(date_time)
        self._datetime = date_time
        self._protocol_type = protocol_type

        # to be updated by set_data method
        self._metadata = None
        self.__data = None

        # name combines datetime and type
        self._id = "{}A{}".format(self.typename, self._dt_string)

        # filepaths can be set if an athlete is assigned
        self._obj_dir = None
        self._file_path = None

    @property
    def id(self):
        """ :return: name """
        return self._id

    @property
    def typename(self):
        """ :return: simple getter for activity type """
        return str(self.__class__.__name__)

    @property
    def protocol(self):
        """ :return: """
        return self._protocol_type

    @property
    def date_time_string(self):
        """:return: date time in string format"""
        return self._dt_string

    @property
    def date_time(self):
        """ :return: a datetime object containing the activities date time """
        return self._datetime

    @property
    def data(self):
        """ :return: activity data if data is loaded or stored """
        if self.__data is None:
            self.__load_data()
        return self.__data

    def set_data(self, data: pd.DataFrame):
        """
        Adds actual exercise data to the activity object
        :param data:
        """
        self.__data = data
        # update meta data to new data
        self.update_meta_data()

    @property
    def meta(self):
        """ :return: Internal meta data """
        # load meta from file if not existent
        if self._metadata is None or len(self._metadata) == 0:
            self._load_meta()
        return self._metadata

    @property
    def directory(self):
        """
        :return: Path to directory were contents are stored
        """
        return self._obj_dir

    def set_protocol(self, prot_type: ProtocolTypes):
        """
        Simply sets the internal protocol variable and writes it to meta data
        :param prot_type:
        :return:
        """
        self._protocol_type = prot_type
        self.update_meta_data()

    def is_data_loaded(self):
        """
        :return: simple flag if data is in memory
        """
        return self.__data is None

    def assign_athlete(self, athlete_id: str):
        """
        Assigns athlete to activity. This allows to create it's full filepath
        :param athlete_id:
        :return:
        """
        self._obj_dir = os.path.join(config.paths["data_storage"], athlete_id, self.typename)
        self._file_path = os.path.join(self._obj_dir, self._id)

    def update_meta_data(self):
        """
        Update meta data with loaded data
        :return:
        """
        # try to load metadata if none is assigned
        if self._metadata is None:
            try:
                self._load_meta()
            except (FileNotFoundError, UserWarning):
                self._metadata = dict()

        # most general info
        self._metadata.update({"activity": self.typename,
                               "protocol": self._protocol_type.value,
                               "datetime": str(self._datetime)})

        if self.__data is not None:
            # add averages and means of available columns
            for col in self.__data.columns:
                if col in ['sec']:
                    continue
                self._metadata.update({"{}_avr".format(col): float(self.__data[col].mean()),
                                       "{}_max".format(col): float(self.__data[col].max())})

    def free_memory(self):
        """
        If the activity object has te be kept but you want to free RAM from loaded data
        :return:
        """
        self.__data = None

    def save(self):
        """
        stores meta and data to local files
        """
        if self._file_path is None:
            raise UserWarning("Activity {} has to be assigned to an athlete to be saved".format(self._id))

        # check if data is available
        if self.__data is None:
            logging.warning("saving empty activity {}".format(self._dt_string))

        # create directories if not existent yet
        if not os.path.exists(os.path.dirname(self._file_path)):
            os.makedirs(os.path.dirname(self._file_path))

        # store data
        if self.__data is not None:
            self.__data.to_pickle(self._file_path)

        self._save_meta()

    def _save_meta(self):
        """
        saves metadata
        :return:
        """
        # write meta info to json
        try:
            with open("{}.json".format(self._file_path), 'w') as fp:
                json.dump(self._metadata, fp, indent=4)
        except TypeError as e:
            print(self._metadata)
            logging.warning("Metadata is corrupted for object {}: {}".format(self._dt_string, e))

    def load(self):
        """
        loads data and meta from file
        """
        self.__load_data()
        self._load_meta()

    def _load_meta(self):
        """
        loads only meta data from file
        """
        if self._file_path is None:
            raise UserWarning(
                "Activity {} has to be assigned to an athlete to determine full file path".format(self._id))

        # load meta
        with open("{}.json".format(self._file_path), 'rb') as fp:
            self._metadata = json.load(fp)
            # assign internal vars according to stored metadata strings
            self._protocol_type = ProtocolTypes.type_from_value(self._metadata["protocol"])

    def __load_data(self):
        """
        loads only data from file
        """
        if self._file_path is None:
            logging.warning(
                "Activity {} has to be assigned to an athlete to determine full file path".format(self._id))
        else:
            self.__data = pd.read_pickle(self._file_path)
