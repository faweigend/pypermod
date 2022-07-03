import os

import fitparse
import pandas as pd
import pytz
from pypermod import config
from pypermod.data_structure.activities.activity import Activity

datapath = os.path.join(config.paths["data_storage"],
                        "strava_data",
                        "athlete_0")
file = "race_0.fit"

# some timezone info
UTC = pytz.UTC
CST = pytz.timezone('Australia/Sydney')

# fields to check the fit file for
required_fields = ['timestamp', 'cadence', 'power', 'speed', 'altitude']
srm_final_fields = ['sec', 'timestamp', 'cadence', 'power', 'speed', 'altitude']

# parse the file
fit_file = fitparse.FitFile(os.path.join(datapath, file),
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
            if field.name == 'timestamp':
                mdata[field.name] = UTC.localize(field.value).astimezone(CST)
            else:
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

pd_data = pd.DataFrame(final_data)
print(pd_data)


