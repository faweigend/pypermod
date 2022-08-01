from enum import Enum


class ProtocolTypes(Enum):
    """
    lists all possible protocol types
    """
    UNDEFINED = "undefined"
    RAMP = "ramp"
    TTE = "tte"
    RECOVERY = "recovery"
    ALL_OUT = "all-out"
    RAMP_ALL_OUT = "ramp_all-out"
    TRAINING = "training"
    TIME_TRIAL = "time_trial"
    RACE = "race"

    @classmethod
    def type_from_value(cls, value: str):
        """
        searches the Activity Type that corresponds to given string
        :param value:
        :return:
        """
        v_map = cls._value2member_map_
        if value not in v_map:
            return ProtocolTypes.UNDEFINED
        else:
            return v_map[value]
