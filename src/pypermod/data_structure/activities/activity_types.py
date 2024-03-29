from enum import Enum

from pypermod.data_structure.activities.activity import Activity
from pypermod.data_structure.activities.type_classes.srm_bbb import SrmBbb
from pypermod.data_structure.activities.type_classes.standard_bike import StandardBike
from pypermod.data_structure.activities.type_classes.standard_bike_bbb import StandardBikeBbb


class ActivityTypes(Enum):
    """
    lists all possible activity types
    """
    UNDEFINED = Activity
    SRM_BBB_TEST = SrmBbb  # srm data to be linked with breath by breath data
    STANDARD_BIKE = StandardBike
    STANDARD_BIKE_BBB = StandardBikeBbb

    @classmethod
    def has_name(cls, name):
        """check if a name exists"""
        return name in cls._member_names_

    @classmethod
    def has_value(cls, value):
        """check if value exists"""
        return value in cls._value2member_map_

    @classmethod
    def type_from_value(cls, value: str):
        """
        searches the Activity Type that corresponds to given string
        :param value:
        :return:
        """
        v_map = cls._value2member_map_

        if value not in v_map:
            return ActivityTypes.UNDEFINED
        else:
            return v_map[value]
