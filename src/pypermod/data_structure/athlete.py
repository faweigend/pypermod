import json
import logging
import os
import shutil

from pypermod import utility

from pypermod.data_structure.activities.activity import Activity
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod.fitter.cp_model_fit import CPMFits


class Athlete:
    """
    An athlete stores all information needed for performance of an
    athlete. We follow these design principles:
    - Metadata of an athlete are their summarised properties.
    - An athlete performs activities.
    - Activities are test data assigned to an athlete under an ActivityType and ProtocolType.
    """

    def __init__(self, path: os.path):
        """
        constructor
        :param path: location where athlete data is stored. Athlete ID is the folder name
        """
        self.__id = os.path.basename(path)
        self.__dir_path = path

        # internal data is structured in dicts
        self.__activities = dict()
        self.__meta_data = dict()

        # load data if some exists
        if os.path.exists(os.path.join(self.__dir_path, 'meta.json')):
            self.load()
        else:
            logging.info("No data available - created empty athlete object {}".format(self.__dir_path))

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

    def set_save_dir(self, new_path: os.path, clear_old: bool = True):
        """
        Changes the athlete id to the new base directory and saves
        all athlete data under the new path.
        :param new_path: new athlete save location as a string
        :param clear_old: whether old location should be deleted
        """

        if clear_old is True:
            shutil.rmtree(self.__dir_path)

        self.__id = os.path.basename(new_path)
        self.__dir_path = new_path

        # update athlete ID for all stored activities
        for act in self.iterate_activities_all():
            act.assign_athlete(self.__id)
            act.save()
            logging.info("Re assigned {} activity under ID {}".format(act.typename, self.__id))

        self.save()

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

    def get_activities(self, a_type: ActivityTypes, p_type: ProtocolTypes, as_sorted: bool = False) -> list:
        """
        WARNING! list is not guaranteed to be sorted, use parameter flag to force an additional sorting
        :param a_type: type of activity to be listed
        :param p_type: protocol type to look for
        :param as_sorted: Per default, data is not guaranteed to be sorted. If this is true, it is sorted before return
        :return: A list with all stored activity objects
        """
        # only sort list if required to. This action can be computationally
        # expensive and therefore is optional
        acts = self.__activities[a_type.value.__name__][p_type]
        if as_sorted is True:
            # sort activities according to date time
            return sorted(acts, key=lambda x: x.date_time)
        return acts

    def list_activity_ids(self, a_type: ActivityTypes, p_type: ProtocolTypes, as_sorted: bool = False) -> list:
        """
        WARNING! list is not guaranteed to be sorted, use parameter flag to force an additional sorting
        :param a_type: type of activity to be listed
        :param p_type: protocol type to look for
        :param as_sorted: Per default, data is not guaranteed to be sorted. If this is true, it is sorted before return
        :return: A list with all activity IDs
        """
        acts = self.get_activities(a_type=a_type, p_type=p_type, as_sorted=as_sorted)
        return [y.id for y in acts]

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
        activity_dir_path = os.path.join(self.dir_path, activity.typename)
        activity.set_dir_path(activity_dir_path)
        activity.save()
        # logging.info("Added and saved {} activity under {} protocol and ID {}".format(activity.typename,
        #                                                                               activity.protocol,
        #                                                                               activity.id))

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
        self.__meta_data.clear()
        # reset metadata to empty state
        self.save()

    def set_cp_fitting_of_type_and_protocol(self, cpmf: CPMFits, a_type: ActivityTypes, p_type: ProtocolTypes):
        """
        Stores CPMFits object as dictionary in metadata to save and load with athlete
        """
        tpname = "{}_{}".format(a_type.value.__name__, p_type.name)
        if "cp_fittings" in self.__meta_data:
            self.__meta_data["cp_fittings"][tpname] = cpmf.as_dict()
        else:
            self.__meta_data["cp_fittings"] = {tpname: cpmf.as_dict()}
        self.save()

    def get_cp_fitting_of_type_and_protocol(self, a_type: ActivityTypes, p_type: ProtocolTypes) -> CPMFits:
        """
        Checks whether a fitting was stored in the metadata
        :param a_type: ActivityType to check for
        :param p_type: ProtocolType, e.g., TTE or TT
        :return:
        """
        if "cp_fittings" in self.__meta_data:
            tpname = "{}_{}".format(a_type.value.__name__, p_type.name)
            if tpname in self.__meta_data["cp_fittings"]:
                cpmf = CPMFits()
                cpmf.create_from_saved_dict(self.__meta_data["cp_fittings"][tpname])
                return cpmf
        else:
            logging.info("athlete {} has no stored CP fittings for {} {} activities".format(self.__id,
                                                                                            a_type.name,
                                                                                            p_type.name))
            return CPMFits()

    def set_hydraulic_fitting_of_type_and_protocol(self, config: list, a_type: ActivityTypes, p_type: ProtocolTypes):
        """
        Stores a given hydraulic model fitting into metadata under given activity type.
        The activity type is the mode of exercise tests the hydraulic model was fitted to
        :param config: the hydraulic model configuration
        :param a_type: the activity type to store it under
        :param p_type: the protocol type to store it under
        """
        tpname = "{}_{}".format(a_type.value.__name__, p_type.name)
        if "threecomphyd_fitting" in self.__meta_data:
            self.__meta_data["threecomphyd_fitting"][tpname] = config
        else:
            self.__meta_data["threecomphyd_fitting"] = {tpname: config}
        self.save()

    def get_hydraulic_fitting_of_type_and_protocol(self, a_type: ActivityTypes, p_type: ProtocolTypes):
        """
        Checks if a hydraulic fitting is stored in metadata and returns it if yes.
        """
        if "threecomphyd_fitting" in self.__meta_data:
            tpname = "{}_{}".format(a_type.value.__name__, p_type.name)
            if tpname in self.__meta_data["threecomphyd_fitting"]:
                return self.__meta_data["threecomphyd_fitting"][tpname]
            else:
                logging.warning("no hydraulic model configuration for {} assigned".format(tpname))
                return None
        else:
            logging.warning("no hydraulic model configuration assigned")
            return None

    def save(self):
        """
        Saves athlete data to meta.json
        """
        if not os.path.exists(self.__dir_path):
            os.makedirs(self.__dir_path)

        # produce json output
        json_dict = {"id": self.__id}
        # write number of activities categorised by type and protocol
        for atn, atv in self.__activities.items():
            json_dict[atn] = {}
            for ptn, ptv in atv.items():
                json_dict[atn][ptn.value] = [x.date_time_string for x in ptv]

        # add meta data to json
        json_dict["meta_data"] = self.__meta_data

        # write everything into a file
        with open(os.path.join(self.__dir_path, 'meta.json'), 'w') as fp:
            json.dump(json_dict, fp, indent=4)

    def get_num_activities(self):
        """
        returns activity count
        """
        a_count = 0
        for _, ats in self.__activities.items():
            for _, pts in ats.items():
                a_count += len(pts)
        return a_count

    def load(self):
        """
        loads meta.json and creates activity objects
        """
        # write meta info to json
        with open(os.path.join(self.__dir_path, 'meta.json'), 'rb') as fp:
            json_dict = json.load(fp)
            # verify the meta json
            if json_dict["id"] != self.__id:
                raise UserWarning(
                    "athlete ID {} and meta.json ID {} do "
                    "not match. Wrong file?".format(self.__id, json_dict["id"]))

            self.__meta_data = json_dict["meta_data"]

            # create training activity objects
            self.__activities = dict()

            a_count = 0

            # check all Activity Types
            for at in ActivityTypes:
                atn = at.value.__name__
                if atn in json_dict:

                    # check all Protocol Types
                    for pt in ProtocolTypes:
                        ptn = pt.value
                        if ptn in json_dict[atn]:

                            # create all stored activities
                            for dt in json_dict[atn][ptn]:
                                a_inst = at.value(date_time=utility.string_to_date(dt))
                                # assign self to load stored activity
                                activity_path = os.path.join(self.dir_path, a_inst.typename)
                                a_inst.set_dir_path(activity_path)
                                a_inst.load()
                                self.add_and_save_activity(a_inst)
                                a_count += 1

        logging.info("loaded athlete {} with {} activities".format(os.path.abspath(self.__dir_path), a_count))
