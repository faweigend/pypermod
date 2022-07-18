import json
import logging
import os
import shutil

import numpy as np
from pypermod import utility

from pypermod.data_structure.activities.activity import Activity
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod.data_structure.helper.simple_constant_effort_measures import SimpleConstantEffortMeasures
from pypermod.fitter.cp_to_tte_fitter import CPMFits


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
        self.__cp_fittings = dict()

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
        # reset metadata to empty state
        self.save()

    def get_cp_fitting_of_type(self, a_type: ActivityTypes, min_tte: int = None) -> CPMFits:
        """
        Checks for TTEs of given type and returns the fitting object
        :param a_type: ActivityType to check for
        :return:
        """
        typename = a_type.name

        # store TTE time and power data for a CP fitting
        times, powers, ids = [], [], []
        for i, test in enumerate(self.iterate_activities_of_type_and_protocol(a_type, ProtocolTypes.TTE)):
            exercise_times = test.get_exercise_srm_data()["sec"]
            exercise_time_s = exercise_times.iloc[-1] - exercise_times.iloc[0]
            exercise_power = np.max(test.get_exercise_srm_data()["altitude"])
            if min_tte is not None:
                if exercise_time_s < min_tte:
                    continue
            times.append(exercise_time_s)
            powers.append(exercise_power)
            ids.append(test.id)

        # check if a fitting is already saved and can be returned
        if typename in self.__cp_fittings:
            if "ttes" in self.__cp_fittings[typename]:
                # only load existing fitting if id list is still similar
                if self.__cp_fittings[typename]["ttes"] == ids:
                    cpmf = self.__cp_fittings[typename]["fitting"]
                    logging.info("TTE ids are the same. Athlete {} loaded {} "
                                 "CP fitting from meta data".format(self.__id,
                                                                    typename))
                    return cpmf
                else:
                    logging.info("athlete {} stored list of TTEs of type {} changed. "
                                 "New CP fitting is estimated".format(self.__id,
                                                                      typename))

        # if not enough TTEs are available, return nothing
        if len(times) < 4:
            logging.warning("athlete {} not enough ({}) "
                            "TTEs of type {} to estimate CP fitting".format(self.__id,
                                                                            len(times),
                                                                            typename))
            return CPMFits()

        # create fitting, store in meta, and return object
        else:
            # conduct a CP fitting if enough data is available
            es = SimpleConstantEffortMeasures(times=times,
                                              measures=powers)

            # do a full cp fitting with the fitter object
            cpm_fits = CPMFits()
            cpm_fits.create_from_ttes(es=es)

            # store in meta data
            if typename not in self.__cp_fittings:
                self.__cp_fittings[typename] = {
                    "ttes": ids,
                    "fitting": cpm_fits
                }
            else:
                self.__cp_fittings[typename].update({
                    "ttes": ids,
                    "fitting": cpm_fits
                })

            logging.info("athlete {} created CP fitting for {}".format(self.__id, typename))
            # save created fitting
            self.save()
            # return created fitting
            return cpm_fits

    def set_hydraulic_fitting_of_type(self, config: list, a_type: ActivityTypes):
        """
        Stores a given hydraulic model fitting into metadata under given activity type.
        The activity type is the mode of exercise tests the hydraulic model was fitted to
        :param config: the hydraulic model configuration
        :param a_type: the activity type to store it under
        """
        typename = a_type.name
        if self.__meta_data is not None:
            if "threecomphyd_fitting" in self.__meta_data:
                self.__meta_data["threecomphyd_fitting"][typename] = config
            else:
                self.__meta_data["threecomphyd_fitting"] = {typename: config}
            self.save()
        else:
            raise UserWarning("trying to set hydraulic fitting for a model without meta data")

    def get_hydraulic_fitting_of_type(self, a_type: ActivityTypes):
        """
        Checks if a hydraulic fitting is stored in metadata and returns it if yes.
        """
        typename = a_type.name
        if self.__meta_data is not None:
            if "threecomphyd_fitting" in self.__meta_data:
                if typename in self.__meta_data["threecomphyd_fitting"]:
                    return self.__meta_data["threecomphyd_fitting"][typename]
                else:
                    logging.warning("no hydraulic model configuration for type {} assigned".format(a_type))
                    return None
            else:
                logging.warning("no hydraulic model configuration assigned")
                return None
        else:
            raise UserWarning("trying to get hydraulic fitting of a model without meta data")

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

        # store cp fittings as dictionaries
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
