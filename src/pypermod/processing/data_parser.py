import csv
import logging
import os
from datetime import datetime

import fitparse
import numpy as np
import pandas as pd
import pytz
from pypermod.data_structure.activities.protocol_types import ProtocolTypes
from pypermod.data_structure.activities.type_classes.srm_bbb import SrmBbb

import config
from pypermod.data_structure.activities.type_classes.standard_bike import StandardBike
from pypermod.data_structure.activities.type_classes.standard_bike_bbb import StandardBikeBbb


class DataParser():

    @staticmethod
    def datetime_from_fit_file(fit_file):
        """
        read date-time from fit file with messages that have a timestamp field
        :param fit_file: full file path
        :return: datetime object
        """

        # some timezone info
        UTC = pytz.UTC

        # fields to check the fit file for
        required_fields = ['timestamp', 'cadence', 'power', 'speed']

        # parse the file and read through messages
        fit_file = fitparse.FitFile(fit_file, data_processor=fitparse.StandardUnitsDataProcessor())
        messages = fit_file.messages

        # transform parsed messages into own data format
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
                        mdata[field.name] = UTC.localize(field.value)
                    else:
                        mdata[field.name] = field.value
            # skip if not all required fields are met
            if not all(elem in mdata for elem in required_fields):
                continue
            else:
                # this is the first valid message. Use the timestamp to determine activity time
                return mdata['timestamp']

        raise UserWarning("Could not find timestamp field in {}".format(fit_file))

    @staticmethod
    def datetime_from_prot_file(prot_file):
        """
        read date-time from protocol csv file
        :param prot_file: full file path
        :return: datetime object
        """
        df = pd.read_csv(prot_file)
        return datetime.strptime(df['datetime'].iloc[0], '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def datetime_from_bbb_file(bbb_file):
        """
        read date-time from cosmed BBB excel file
        :param bbb_file: full file path
        :return: datetime object
        """
        # date and time information is written in column 4
        df = pd.read_excel(bbb_file, sheet_name="Data", header=None, usecols=[4])
        date = df.iloc[0, 0]
        timestamp = df.iloc[1, 0]
        try:
            dt = datetime.strptime(" ".join([date, timestamp]), '%d/%m/%Y %I:%M:%S %p')
        except ValueError:
            dt = datetime.strptime(" ".join([date, timestamp]), '%d/%m/%Y %I:%M %p')
        return dt

    @staticmethod
    def parse_srm_bbb_activity(prot_file, srm_file, bbb_file):

        # parse BBB data
        cosmed_data = DataParser.parse_cosmed_bbb_file(bbb_file)

        # parse SRM data
        if srm_file.split(".")[-1] == "fit":
            srm_data = DataParser.parse_srm_fit_file(srm_file)
        elif srm_file.split(".")[-1] == "csv":
            srm_data = DataParser.parse_golden_cheetah_csv_file(srm_file)
        else:
            raise UserWarning("Cannot handle SRM data of file type {} (must be csv or fit)".format(srm_file))

        prot = DataParser.parse_protocol_file(prot_file)

        if "datetime" in prot:
            dt = DataParser.datetime_from_prot_file(prot_file)
        else:
            dt = DataParser.datetime_from_bbb_file(bbb_file)

        new_activity = SrmBbb(date_time=dt)
        new_activity.set_data(srm_data)
        new_activity.set_protocol_with_timestamps(prot_type=ProtocolTypes.type_from_value(prot["type"]),
                                                  warmup=prot["warmup"],
                                                  exercise_end_time=prot["exercise_end"])
        new_activity.set_bbb_data(cosmed_data, offset=prot["bbb_start"])
        return new_activity

    @staticmethod
    def parse_zwift_race(bike_file: os.path):

        dt = DataParser.datetime_from_fit_file(bike_file)
        bike_data = DataParser.parse_bike_fit_file(bike_file)

        new_activity = StandardBike(date_time=dt)
        new_activity.set_protocol(prot_type=ProtocolTypes.RACE)
        new_activity.set_data(bike_data)

        return new_activity

    @staticmethod
    def parse_bike_bbb_activity(prot_file: os.path, bike_file: os.path, bbb_file: os.path):

        # parse BBB data
        cosmed_data = DataParser.parse_cosmed_bbb_file(bbb_file)

        # parse SRM data
        if bike_file.split(".")[-1] == "fit":
            bike_data = DataParser.parse_bike_fit_file(bike_file)
        elif bike_file.split(".")[-1] == "csv":
            bike_data = DataParser.parse_golden_cheetah_csv_file(bike_file)
        else:
            raise UserWarning("Cannot handle SRM data of file type {} (must be csv or fit)".format(bike_file))

        prot = DataParser.parse_protocol_file(prot_file)

        if "datetime" in prot:
            dt = DataParser.datetime_from_prot_file(prot_file)
        else:
            dt = DataParser.datetime_from_bbb_file(bbb_file)

        new_activity = StandardBikeBbb(date_time=dt)
        new_activity.set_data(bike_data)
        new_activity.set_protocol_with_timestamps(prot_type=ProtocolTypes.type_from_value(prot["type"]),
                                                  warmup=prot["warmup"],
                                                  exercise_end_time=prot["exercise_end"])
        new_activity.set_bbb_data(cosmed_data, offset=prot["bbb_start"])
        return new_activity

    @staticmethod
    def create_protocol_file(activity_dir):
        prot_csv_filename = "{}_prot.csv".format(os.path.basename(activity_dir))
        pd_prot = pd.read_csv(os.path.join(activity_dir, prot_csv_filename))
        return pd_prot.iloc[0].to_dict()

    @staticmethod
    def parse_protocol_file(prot_file):
        if prot_file.split(".")[-1] == "prot" or prot_file.split(".")[-1] == "csv":
            pd_prot = pd.read_csv(prot_file)
        else:
            raise UserWarning("Cannot handle Protocol data of file type {} (must be prot or csv)".format(prot_file))
        return pd_prot.iloc[0].to_dict()

    @staticmethod
    def parse_cosmed_bbb_file(full_file_path):

        if not full_file_path.split(".")[-1] == "xlsx":
            raise UserWarning("Cannot handle Cosmed BBB data of file type {} (must be xlsx)".format(full_file_path))

        df = pd.read_excel(full_file_path, sheet_name="Data")

        df = df.iloc[2:]

        data = pd.DataFrame({
            "sec": df["t"].apply(lambda t: (t.hour * 60 + t.minute) * 60 + t.second),
            "hr": df["HR"],
            "ve": df["VE"],
            "vo2": df["VO2"],
            "vco2": df["VCO2"],
            "fat": df["FAT"],
            "cho": df["CHO"],
            "phases": df["Phase"],
            "rer": df["VCO2"] / df["VO2"]
        })

        return data

    @staticmethod
    def parse_golden_cheetah_csv_file(full_file_path):
        """
        The software tool Golden Cheetah can be used to gather data from cycle ergometers. It also allows to export the
        data as a .csv file. This function parses the CSV file into a standardised pandas DataFrame
        """

        ergo_data = pd.DataFrame()
        with open(os.path.join(full_file_path), 'r') as srm_file:
            reader_gc = csv.reader(srm_file)
            # first row is header info
            gc_fields = next(reader_gc)
            for gc_row in reader_gc:
                pd_ergo_row = pd.DataFrame({
                    "sec": [float(gc_row[gc_fields.index('secs')])],
                    "cadence": [float(gc_row[gc_fields.index('cad')])],
                    "power": [float(gc_row[gc_fields.index('watts')])],
                    "speed": [float(gc_row[gc_fields.index('kph')])],
                    "altitude": [float(gc_row[gc_fields.index('alt')])]
                })
                ergo_data = pd.concat([ergo_data, pd_ergo_row])

        return ergo_data

    @staticmethod
    def parse_bike_fit_file(full_file_path):
        """
        Strava fit files into a standardised Pandas DataFrame.
        """

        # some timezone info
        UTC = pytz.UTC

        # fields to check the fit file for
        required_fields = ['timestamp', 'cadence', 'power', 'speed']

        # parse the file
        fit_file = fitparse.FitFile(full_file_path,
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
                        mdata[field.name] = UTC.localize(field.value)
                    else:
                        mdata[field.name] = field.value
            # skip if not all required fields are met
            if not all(elem in mdata for elem in required_fields):
                continue
            # otherwise add the row
            parsed_data.append(mdata)

        bike_data = pd.DataFrame()

        # write the parsed data line by line
        for entry in parsed_data:
            pd_ergo_row = pd.DataFrame({
                "sec": [float((entry['timestamp'] - parsed_data[0]['timestamp']).total_seconds())],
                "cadence": [float(entry.get('cadence', 0))],
                "power": [float(entry.get('power', 0))],
                "speed": [float(entry.get('speed', 0))],
                "altitude": [float(entry.get('altitude', 0))]
            })
            bike_data = pd.concat([bike_data, pd_ergo_row])

        return bike_data

    @staticmethod
    def parse_srm_fit_file(full_file_path):
        """
        The SRM cycle ergometer software stores exercise data as a .fit file. This function parses such a fit file into
        a standardised Pandas DataFrame.

        SRM files report resistance settings as altitude
        """

        # some timezone info
        UTC = pytz.UTC
        CST = pytz.timezone('Australia/Sydney')

        # fields to check the fit file for
        required_fields = ['timestamp', 'cadence', 'power', 'speed', 'altitude']

        # parse the file
        fit_file = fitparse.FitFile(full_file_path,
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

        srm_data = pd.DataFrame()

        # write the parsed data line by line
        for entry in parsed_data:
            pd_ergo_row = pd.DataFrame({
                "sec": [float((entry['timestamp'] - parsed_data[0]['timestamp']).total_seconds())],
                "cadence": [float(entry.get('cadence', 0))],
                "power": [float(entry.get('power', 0))],
                "speed": [float(entry.get('speed', 0))],
                "altitude": [float(entry.get('altitude', 0))]
            })
            srm_data = pd.concat([srm_data, pd_ergo_row])

        # post-process SRM data
        # when during a test the skip button was pressed, the protocol jumps forwart to the time of the next
        # exercise bout. It's necessary to erase these time jumps for a continuous power output
        skips = []
        np_secs = np.array(srm_data["sec"])
        for i in range(1, len(np_secs)):
            if abs(np_secs[i - 1] - np_secs[i]) > 3:
                skips.append((i - 1, i))

        if len(skips) >= 1:
            for skip in skips:
                np_secs[skip[1]:] -= (np_secs[skip[1]] - np_secs[skip[0]] - 1)
                logging.info(
                    "skip between {} and {} found and processed".format(srm_data["sec"].iloc[skip[0]],
                                                                        srm_data["sec"].iloc[skip[1]]))
        srm_data["sec"] = np_secs

        return srm_data


if __name__ == "__main__":
    # dat_dir = os.path.join(config.paths["external_data"],"strava_study/athlete_0/20220728")
    dat_dir = os.path.join(config.paths["external_data"], "strava_study/athlete_0/20220728")
    DataParser.parse_bike_bbb_activity(prot_file=os.path.join(dat_dir, "prot.prot"),
                                       bike_file=os.path.join(dat_dir, "pow.csv"),
                                       bbb_file=os.path.join(dat_dir, "bbb.xlsx"))

    dat_dir = os.path.join(config.paths["external_data"], "strava_study/athlete_0/20220804")
    DataParser.parse_bike_bbb_activity(prot_file=os.path.join(dat_dir, "prot.csv"),
                                       bike_file=os.path.join(dat_dir, "pow.fit"),
                                       bbb_file=os.path.join(dat_dir, "bbb.xlsx"))
