import logging
import os
import fitparse

import pandas as pd
from pypermod import config
from pypermod.data_structure.activities.type_classes.standard_bike import StandardBike



def strava_to_activity(datapath: os.path):
    # fields to check the fit file for
    required_fields = ['timestamp', 'cadence', 'power', 'speed', 'altitude']
    srm_final_fields = ['sec', 'timestamp', 'cadence', 'power', 'speed', 'altitude']

    # parse the file
    fit_file = fitparse.FitFile(datapath,
                                data_processor=fitparse.StandardUnitsDataProcessor())
    messages = fit_file.messages
    # transform parsed messages into own data format
    parsed_data = []
    for m in messages:
        # if message has no data -> skip
        if not hasattr(m, 'fields'):
            continue
        # check for important data types
        mdata = {}
        # fill mdata with all desired data that's available
        for field in m.fields:
            if field.name in required_fields:
                mdata[field.name] = field.value
        # skip if not all required fields are met
        if not all(elem in mdata for elem in required_fields):
            continue
        # otherwise add the row
        parsed_data.append(mdata)

    final_data = []
    # write the parsed data line by line
    for entry in parsed_data:
        new_row = [str(entry.get(k, '')) for k in srm_final_fields]
        new_row[srm_final_fields.index('sec')] = (
                entry['timestamp'] - parsed_data[0]['timestamp']).total_seconds()
        # add the bygone seconds as the initial value to the row
        final_data.append(new_row)

    # create dataframe with correct data types
    pd_data = pd.DataFrame(final_data, columns=srm_final_fields)
    for col in ['sec', 'cadence', 'power', 'speed', 'altitude']:
        pd_data[col] = pd.to_numeric(pd_data[col])
    pd_data["timestamp"] = pd.to_datetime(pd_data["timestamp"])

    # transform timestamp of first entry into datetime object
    dt = pd_data["timestamp"].iloc[0]

    # create activity
    new_activity = StandardBike(date_time=dt)
    new_activity.set_data(pd_data)
    return new_activity


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    datapath = os.path.join(config.paths["data_storage"],
                            "strava_data",
                            "athlete_0",
                            "race_0.fit")

    na = strava_to_activity(datapath)
    logging.info("created {}".format(na.id))
