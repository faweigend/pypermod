import logging
import os
import shutil
import time
from datetime import datetime

import numpy as np
import pandas as pd

from pypermod.data_structure.activities.test_formats.srm_bbb_test import SRMBbbTest
from pypermod.data_structure.activities.activity import Activity
from pypermod.data_structure.activities.activity_types import ActivityTypes
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod.data_structure.athlete import Athlete
from pypermod.fitter.cp_to_tte_fitter import CPMFits, CPMTypes

import config


def add_four_undefined_activities_to_athlete(athlete: Athlete):
    """
    adds four made-up TTE tests to given athlete
    """

    # create dt object without microseconds
    dt = datetime.utcnow()
    dt = dt.replace(microsecond=0)
    dt = dt.replace(minute=0)

    # 1800 secs for 18km with constant power of 50 and heart rate of 90
    new_training = Activity(date_time=dt)
    new_training.set_data(pd.DataFrame({
        'sec': np.arange(0, 1800),
        'km': np.arange(0, 18, 0.01),
        'power': np.full_like(np.ones(1800), 50),
        'hr': np.full_like(np.ones(1800), 90)}
    ))

    # add activity to athlete
    athlete.add_and_save_activity(new_training)

    # change time fro next session
    dt = dt.replace(minute=1)

    # 1800 secs observed in 10Hz for 18km with saw blade power curve of 50 to 100 and heart rate of 90
    new_training = Activity(date_time=dt)
    # power curve is a saw blade increasing in steps of 5 until it reaches 100
    power = np.ones(18000)
    for i in range(0, 18000, 10):
        power[i:i + 10] = np.arange(50, 100, 5)
    new_training.set_data(pd.DataFrame({
        'sec': np.arange(0, 1800, 0.1),
        'km': np.arange(0, 180, 0.01),
        'power': power,
        'hr': np.full_like(np.ones(18000), 90)}))

    # add activity to athlete
    athlete.add_and_save_activity(new_training)

    # change time fro next session
    dt = dt.replace(minute=3)
    new_training = Activity(date_time=dt)
    # power curve is set to 300 for 500 sec
    power = np.full_like(np.ones(1800), 50)
    power[500:1000] = np.full_like(np.ones(500), 100)
    new_training.set_data(pd.DataFrame({
        'sec': np.arange(0, 1800, 1),
        'km': np.arange(0, 180, 0.1),
        'power': power,
        'hr': np.full_like(np.ones(1800), 90)}))

    # add activity to athlete
    athlete.add_and_save_activity(new_training)

    # change time fro next session
    dt = dt.replace(minute=2)
    new_training = Activity(date_time=dt)
    # power curve is set to 300 for 500 sec
    power = np.full_like(np.ones(1800), 50)
    power[500:600] = np.full_like(np.ones(100), 300)
    new_training.set_data(pd.DataFrame({
        'sec': np.arange(0, 1800, 1),
        'km': np.arange(0, 180, 0.1),
        'power': power,
        'hr': np.full_like(np.ones(1800), 90)}))

    # add activity to athlete
    athlete.add_and_save_activity(new_training)

    athlete.save()
    return athlete


def add_srm_test_ttes_to_athlete(athlete, combs):
    for i, comb in enumerate(combs):
        # create srm test according to power duration combination
        dt = datetime.utcnow()
        new_tte = SRMBbbTest(date_time=dt)
        new_tte.set_data(pd.DataFrame({
            'sec': np.arange(0, comb[1]),
            'speed': np.full_like(np.ones(comb[1]), 14),
            'cadence': np.full_like(np.ones(comb[1]), 50),
            'power': np.full_like(np.ones(comb[1]), comb[0]),
            'altitude': np.full_like(np.ones(comb[1]), comb[0])}
        ))
        new_tte.set_bbb_data(
            pd.DataFrame({
                'sec': np.arange(0, comb[1], step=3),
                've': np.arange(0, comb[1], step=3),
                'vo2': np.arange(0, comb[1], step=3),
                'hr': np.arange(0, comb[1], step=3),
                'vco2': np.arange(0, comb[1], step=3),
                'fat': np.arange(0, comb[1], step=3),
                'cho': np.arange(0, comb[1], step=3),
                'rer': np.arange(0, comb[1], step=3)
            }), 0)
        new_tte.set_protocol_with_timestamps(
            ProtocolTypes.TTE,
            warmup=0,
            exercise_end_time=comb[1] - 1)
        # save to athlete
        athlete.add_and_save_activity(new_tte)


def test_save_load_activity(athlete):
    acts = []
    for act in athlete.iterate_activities_of_type_and_protocol(ActivityTypes.UNDEFINED,
                                                               ProtocolTypes.UNDEFINED):
        acts.append(act)
    assert len(acts) == 4

    # verify that none of SRM TEST type are found
    no_acts = []
    for act in athlete.iterate_activities_of_type_and_protocol(ActivityTypes.SRM_BBB_TEST,
                                                               ProtocolTypes.UNDEFINED):
        no_acts.append(act)
    assert len(no_acts) == 0

    # verify that all corresponds to stored training activities
    all_acts = []
    for act in athlete.iterate_activities_all():
        all_acts.append(act.id)

    assert len(all_acts) == len(acts)
    # check ID list functions
    id_list_unsorted = athlete.list_activity_ids(ActivityTypes.UNDEFINED, ProtocolTypes.UNDEFINED, False)
    id_list_sorted = athlete.list_activity_ids(ActivityTypes.UNDEFINED, ProtocolTypes.UNDEFINED, True)

    assert id_list_unsorted != id_list_sorted
    assert id_list_unsorted[2] == id_list_sorted[3]
    assert id_list_unsorted[3] == id_list_sorted[2]

    # a simple check if this function throws an error
    # athlete.update_meta_data()
    athlete.free_memory()

    # verify getter function
    for id_str in id_list_unsorted:
        act = athlete.get_activity_by_type_and_id(id_str,
                                                  ActivityTypes.UNDEFINED,
                                                  ProtocolTypes.UNDEFINED)
        assert act.id == id_str

    # verify delete functions
    athlete.remove_activity_by_id(id_list_unsorted[0])
    id_list_unsorted_smaller = athlete.list_activity_ids(ActivityTypes.UNDEFINED, ProtocolTypes.UNDEFINED, False)

    assert len(id_list_unsorted) == (len(id_list_unsorted_smaller) + 1)
    assert id_list_unsorted[0] not in id_list_unsorted_smaller

    # check the clean function
    athlete.clear_all_data()
    clean_acts = []
    for act in athlete.iterate_activities_all():
        clean_acts.append(act.id)
    assert len(clean_acts) == 0


if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    if os.path.exists(os.path.join(config.paths["data_storage"], "test_athlete")):
        shutil.rmtree(os.path.join(config.paths["data_storage"], "test_athlete"))

    # create an athlete of own type
    athlete = Athlete(os.path.join(
        config.paths["data_storage"],
        "test_athlete")
    )
    athlete.clear_all_data()

    # test general activity functions
    add_four_undefined_activities_to_athlete(athlete=athlete)

    # basic tests for save and load with protocol type and activity type
    test_save_load_activity(athlete)
    logging.info("PASSED activity save and load tests")

    # Now create specific SRM_BBB_TESTS
    combs = [(90, 600), (120, 300), (180, 150), (240, 75)]
    add_srm_test_ttes_to_athlete(athlete, combs)
    athlete.save()

    # load a fitting
    cpm1 = athlete.get_cp_fitting_of_type(ActivityTypes.SRM_BBB_TEST)
    assert type(cpm1) is CPMFits

    # double check W' and CP values
    assert cpm1.get_params(CPMTypes.P2_LINEAR)["w_p"] == 15096.0
    assert cpm1.get_params(CPMTypes.P2_LINEAR)["cp"] == 66.0
    logging.info("PASSED first SRM BBB TTE fitting")

    # clear one TTE and see if fitting is updated
    tte_ids = athlete.list_activity_ids(ActivityTypes.SRM_BBB_TEST, ProtocolTypes.TTE)
    athlete.remove_activity_by_id(tte_ids[0])

    # no fitting possible because only three tests remain
    cpm2 = athlete.get_cp_fitting_of_type(ActivityTypes.SRM_BBB_TEST)
    assert cpm2 != cpm1
    assert cpm2.has_ttes() == False
    logging.info("PASSED changed TTEs test")

    # add new ttes
    combs2 = [(100, 500), (190, 130)]
    add_srm_test_ttes_to_athlete(athlete, combs2)
    tte_list = athlete.list_activity_ids(ActivityTypes.SRM_BBB_TEST,
                                         ProtocolTypes.TTE)
    assert len(tte_list) == 5

    cpm3 = athlete.get_cp_fitting_of_type(ActivityTypes.SRM_BBB_TEST)

    assert cpm2 != cpm1 != cpm3

    # double check W' and CP values
    assert cpm3.get_params(CPMTypes.P2_LINEAR)["w_p"] == 14475.303501945524
    assert cpm3.get_params(CPMTypes.P2_LINEAR)["cp"] == 71.73346303501945

    # nothing changed -> should be loaded
    cpm4 = athlete.get_cp_fitting_of_type(ActivityTypes.SRM_BBB_TEST)
    assert cpm4 == cpm3

    logging.info("PASSED changed TTEs test 2")

    athlete.save()
    athlete.load()
    tte_list = athlete.list_activity_ids(ActivityTypes.SRM_BBB_TEST,
                                         ProtocolTypes.TTE)
    assert len(tte_list) == 5

    logging.info("PASSED save/load test")

    # check if a new object indeed loads the same data
    athlete2 = Athlete(os.path.join(
        config.paths["data_storage"],
        athlete.id)
    )
    cpm5 = athlete2.get_cp_fitting_of_type(ActivityTypes.SRM_BBB_TEST)
    tte_list = athlete2.list_activity_ids(ActivityTypes.SRM_BBB_TEST,
                                          ProtocolTypes.TTE)
    assert len(tte_list) == 5

    assert cpm5.get_params(CPMTypes.P2_LINEAR)["w_p"] == 14475.303501945524
    assert cpm5.get_params(CPMTypes.P2_LINEAR)["cp"] == 71.73346303501945

    logging.info("PASSED 2 athletes 1 ID tests")

    hyd_conf = [12627.151127290388, 38502.21530457119,
                216.63752756838872, 77.153935498425,
                11.586559865141686, 0.7718471321983202,
                0.011210584001550252, 0.21310297838308895]

    athlete.set_hydraulic_fitting_of_type(hyd_conf, ActivityTypes.SRM_BBB_TEST)
    test_conf = athlete.get_hydraulic_fitting_of_type(ActivityTypes.SRM_BBB_TEST)

    assert test_conf == hyd_conf

    logging.info("PASSED hyd conf setting tests")

    # clean up
    athlete.clear_all_data()
    shutil.rmtree(os.path.join(
        config.paths["data_storage"],
        "test_athlete")
    )
