import json
import logging
import os
import shutil

from pypermod import utility, config

from pypermod.data.activities.activity import Activity
from pypermod.data.activities.activity_types import ActivityTypes
from pypermod.data.activities.protocol_types import ProtocolTypes


class Athlete:
    """
    An athlete stores all information needed for performance of an
    athlete. Following these design principles:
    - Metadata of an athlete are their summarised properties.
    - An athlete performs activities.
    - Activities are test data assigned to an athlete under an ActivityType and ProtocolType.
    """

    def __init__(self, id_num: str):
        """
        constructor
        :param id_num: identification string of the athlete
        """
        self.__id = id_num
        # storage for all activities of type ActivityTypes
        self.__activities = dict()
        self.__meta_data = dict()
        self.__cp_fittings = dict()
        self.__dir_path = os.path.join(config.paths["data_storage"], self.__id)

    @property
    def dir_path(self):
        """:return: os path to directory where meta and activity data is stored """
        return self.__dir_path

    @property
    def id(self):
        """
        :return: athlete id
        """
        return self.__id

    def remove_activity(self, act: Activity):
        """
        clears activity from internal storage
        :param act:
        """
        self.__activities[act.typename][act.protocol].remove(act)

    def remove_activity_by_id(self, id_str: str):
        """
        removes activity from internal storage
        :param id_str: ID of activity to remove
        """
        for act in self.iterate_activities_all():
            if act.id == id_str:
                self.remove_activity(act)

    def remove_activities_by_id_list(self, id_str_list: list):
        """
        removes a list of activities from internal storage
        :param id_str_list: list of activity IDs to remove
        """
        for id_str in id_str_list:
            self.remove_activity_by_id(id_str)

    def free_memory(self):
        """
        iterates through all activities and frees data from memory
        """
        for act in self.iterate_activities_all():
            act.free_memory()

    def iterate_activities_all(self):
        """
        iterates through all stored activities
        :return: activity object
        """
        for _, ats in self.__activities.items():
            for _, ps in ats.items():
                for act in ps:
                    yield act

    def iterate_activities_of_type_and_protocol(self, a_type: ActivityTypes, p_type: ProtocolTypes):
        """
        Generator that returns stored training sessions one by one.
        Iterates through all stored protocols
        :return: activity object
        """
        # check if activities of type are stored
        if a_type.value.__name__ in self.__activities:
            # check if given protocol is stored
            if p_type in self.__activities[a_type.value.__name__]:
                # iterate through stored activities
                for act in self.__activities[a_type.value.__name__][p_type]:
                    yield act

    def list_activity_ids(self, a_type: ActivityTypes, p_type: ProtocolTypes, as_sorted: bool = False):
        """
        WARNING! list is not guaranteed to be sorted, use parameter flag to force an additional sorting
        :param a_type: type of activity to be listed
        :param p_type: protocol type to look for
        :param as_sorted: Per default, data is not guaranteed to be sorted. If this is true, it is sorted before return
        :return: A list with all stored training_sessions
        """
        # only sort list if required to. This action can be computationally
        # expensive and therefore is optional
        if as_sorted is True:
            # sort activities according to date time
            acts = self.__activities[a_type.value.__name__][p_type]
            return [y.id for y in sorted(acts, key=lambda x: x.date_time)]
        return [y.id for y in self.__activities[a_type.value.__name__][p_type]]

    def add_and_save_activity(self, activity):
        """
        Adds activity to corresponding internal list, assigns athlete id to it and saves it as a file.
        :param activity:
        :return:
        """

        if not ActivityTypes.has_value(type(activity)):
            raise UserWarning("activity of type {} is not a legal type".format(activity.typename))

        # create new entry for type and protocol
        if activity.typename not in self.__activities:
            self.__activities[activity.typename] = {activity.protocol: [activity]}
        elif activity.protocol not in self.__activities[activity.typename]:
            self.__activities[activity.typename][activity.protocol] = [activity]
        else:
            self.__activities[activity.typename][activity.protocol].append(activity)

        # assign self to newly stored activity
        activity.assign_athlete(self.__id)
        activity.save()
        logging.info("Added and saved {} activity under {} protocol and ID {}".format(activity.typename,
                                                                                      activity.protocol,
                                                                                      activity.id))

    def get_activity_by_type_and_id(self, a_id: str, a_type: ActivityTypes, p_type: ProtocolTypes):
        """
        Loads activity with given name from list
        :param a_type: type of activity to load
        :param p_type: protocol that selected activity is stored under
        :param a_id: ID of activity
        :return:
        """

        if type(a_id) is not str:
            raise UserWarning("Activity ID {} seems to be in the wrong format".format(a_id))

        for act in self.__activities[a_type.value.__name__][p_type]:
            if act.id == a_id:
                return act

        raise UserWarning("Activity with ID {} of type {} "
                          "and with protocol {} doesn't exist".format(a_id, a_type, p_type))

    def clear_all_data(self):
        """
        Clears everything that's stored
        """
        # clear old and create new directory
        if os.path.exists(self.__dir_path):
            # clear whole folder
            shutil.rmtree(self.__dir_path)
        os.makedirs(self.__dir_path)
        # empty stored activities
        self.__activities.clear()
        # reset metadata to empty state
        self.save()

    def save(self):
        """
        Saves athlete data to meta.json
        """
        # produce json output
        json_dict = {"id": self.__id}
        # write number of activities categorised by type and protocol
        for atn, atv in self.__activities.items():
            json_dict[atn] = {}
            for ptn, ptv in atv.items():
                json_dict[atn][ptn.value] = [x.date_time_string for x in ptv]

        # add meta data to json
        json_dict["meta_data"] = self.__meta_data

        # store sp fittings as dictionaries
        json_dict["cp_fittings"] = {}
        for cpn, cpv in self.__cp_fittings.items():
            json_dict["cp_fittings"][cpn] = {"ttes": cpv["ttes"],
                                             "fitting": cpv["fitting"].as_dict()}

        # write everything into a file
        with open(os.path.join(self.__dir_path, 'meta.json'), 'w') as fp:
            json.dump(json_dict, fp, indent=4)

    def load(self):
        """
        loads meta.json and creates activity objects
        """
        # write meta info to json
        with open(os.path.join(self.__dir_path, 'meta.json'), 'rb') as fp:
            meta = json.load(fp)
            # verify the meta json
            if meta["id"] != self.__id:
                logging.warning(
                    "athlete ID {} and meta.json ID {} do "
                    "not match. Wrong file?".format(self.__id, meta["id"]))

            self.__meta_data = meta["meta_data"]

            # create training activity objects
            self.__activities = dict()

            # check all Activity Types
            for at in ActivityTypes:
                atn = at.value.__name__
                if atn in meta:

                    # check all Protocol Types
                    for pt in ProtocolTypes:
                        ptn = pt.value
                        if ptn in meta[atn]:

                            # create all stored activities
                            for dt in meta[atn][ptn]:
                                a_inst = at.value(date_time=utility.string_to_date(dt))
                                a_inst.assign_athlete(self.__id)
                                a_inst.load()
                                self.add_and_save_activity(a_inst)
