import logging

import numpy as np
import pandas as pd


def time_dependant_rolling_average_center(seconds: pd.Series, values: pd.Series, time_radius: int):
    """
    Averages over time frames. This requires the addition of observation times.
    :param seconds:
    :param values:
    :param time_radius:
    :return: smoothed data
    """

    smoothed_data = np.zeros(values.shape)

    # iterate over every observation and
    # walk back and forth in time to add values within the time frame
    for i in range(len(seconds)):
        # create clean list
        avg = []
        for b_i in range(i):
            # avoid a doubled entry
            if b_i == 0:
                continue
            # walk back till radius is hit
            elif seconds.iloc[i - b_i] < (seconds.iloc[i] - time_radius):
                break
            # include value in average
            else:
                avg.append(values.iloc[i - b_i])
        for a_i in range(len(seconds) - i):
            # walk forward till radius or border is hit
            if seconds.iloc[i + a_i] > (seconds.iloc[i] + time_radius):
                break
            else:
                avg.append(values.iloc[i + a_i])

        # average extracted data window
        if len(avg) == 0:
            logging.warning("averaging window is empty!")
            smoothed_data[i] = 0
        else:
            smoothed_data[i] = np.average(avg)

    return smoothed_data


def rolling_average_center(column: pd.Series, radius: int = 8, ignore_zeros=False):
    """
    PADDING WITH ZEROS
    averages column values by a given window size.
    :param radius: smoothness factor determines smoothing window size
    :param column: a full column of values to be averaged
    :param ignore_zeros: zeros are not included in the mean calculations
    :return: power values
    """
    # add zero padding for averaging close to borders
    zero_border = np.full(len(column.index) + 2 * radius, np.nan)
    zero_border[radius:-radius] = column

    # target for averaged values
    smoothed_data = np.zeros(column.shape)

    # estimate averages and insert them into target
    for i in range(len(column)):
        # add +1 to have [radius][i][radius]
        window = zero_border[i:i + 2 * radius + 1]

        if np.isnan(window).any():
            smoothed_data[i] = np.nan
        else:
            if ignore_zeros is True:
                window = window[np.nonzero(window)]

            # average extracted window
            if window.size == 0:
                logging.info("averaging window is empty!")
                smoothed_data[i] = 0
            else:
                smoothed_data[i] = np.average(window)

    return smoothed_data


def rolling_average_right(column: pd.Series, window_size: int = 8, ignore_zeros=False):
    """
    PADDING WITH ZEROS
    averages column values by a given window size and inserts value on the right of the window.
    This corresponds to the pandas default rolling average implementation
    :param window_size: smoothness factor determines smoothing window size
    :param column: a full column of values to be averaged
    :param ignore_zeros: zeros are not included in the mean calculations
    :return: power values
    """
    # add zero padding for averaging close to borders
    zero_border = np.full(len(column.index) + window_size, np.nan)
    zero_border[window_size:] = column

    # target for averaged values
    smoothed_data = np.zeros(column.shape)

    # estimate averages and insert them into target
    for i in range(len(column.index)):
        # all the values to the left of current with given window size
        # the +1 is needed because we want write the value in the most right cell
        # of the window. Otherwise window_size would be the end and excluded
        window = zero_border[i + 1:i + window_size + 1]

        if np.nan in window:
            smoothed_data[i] = np.nan
        else:
            if ignore_zeros is True:
                window = window[np.nonzero(window)]

            # average extracted window
            if window.size == 0:
                logging.warning("averaging window is empty!")
                smoothed_data[i] = 0
            else:
                smoothed_data[i] = np.average(window)

    return smoothed_data


def time_dependant_rolling_average_right(seconds: pd.Series, values: pd.Series, window_size: int):
    """
    Averages over time frames. This requires the addition of observation times.
    :param seconds:
    :param values:
    :param window_size:
    :return: smoothed data
    """

    smoothed_data = np.zeros(values.shape)

    # iterate over every observation and
    # walk back and forth in time to add values within the time frame
    for i in range(len(seconds)):
        # create clean list
        avg = []
        for b_i in range(i):
            # walk back till radius is hit
            if seconds.iloc[i - b_i] <= (seconds.iloc[i] - window_size):
                break
            else:
                # include value in average
                avg.append(values.iloc[i - b_i])
        # average extracted data window
        if len(avg) == 0:
            logging.warning("averaging window is empty!")
            smoothed_data[i] = 0
        else:
            smoothed_data[i] = np.average(avg)

    return smoothed_data


def bin_data(data: pd.DataFrame, bin_size: int = 1):
    """
    Summarises data into bins of defined size. A whole time series is created and missing seconds are added:
    i.e. if no observations are made in a second, an empty row is added.
    i.e. if data occurs multiple times per second, data is summarised using the provided binning funcs and stored as one
    observation for this second.
    """
    # create a lookup for column positions
    columns = {}
    for i, c in enumerate(data.columns):
        columns[c] = int(i)

    # check for timestamps
    if 'sec' not in columns:
        raise UserWarning("No \'sec\' column available. Data cannot be binned if timestamps are missing.")

    # custom functions to bin observation types into seconds
    binning_funcs = {
        'power': (lambda x: np.average(x)),
        'hr': (lambda x: np.average(x)),
        'km': (lambda x: np.max(x)),
        'vel': (lambda x: np.average(x)),
        'vo2': (lambda x: np.average(x)),
        'acc': (lambda x: np.average(x)),
        'alt': (lambda x: np.max(x)),
        'speed': (lambda x: np.average(x)),
        'cadence': (lambda x: np.average(x)),
        'vco2': (lambda x: np.average(x)),
        'fat': (lambda x: np.average(x)),
        'cho': (lambda x: np.average(x)),
        'rer': (lambda x: np.average(x)),
        've': (lambda x: np.average(x))
    }

    def __bin_batch(batch: np.array, bin_sec):
        """
        helper function to summarise batch for data binning.
        """
        cols = [str(col) for col in columns.keys()]

        # empty row to be filled
        obs_row = [0] * len(cols)
        # handle seconds
        obs_row[columns["sec"]] = bin_sec
        cols.remove("sec")

        # finish remaining cols
        # if batch contains only one entry, no processing is needed
        if len(batch) == 1:
            for col in cols:
                obs_row[columns[col]] = batch[0, columns[col]]
        else:
            # apply assigned functions to obtain binning result
            for col in cols:
                obs_row[columns[col]] = binning_funcs[col](batch[:, columns[col]])

        return obs_row

    # list to append binned results into
    binned_data = []
    curr_sec = data['sec'].min()
    # start with second one
    cur_batch = []
    for _, row in data.iterrows():
        # update seconds if row doesn't match current batch
        while curr_sec < int(row['sec']):
            # estimate summary and insert into binned data
            if len(cur_batch) > 0:
                binned_data.append(__bin_batch(np.vstack(cur_batch), curr_sec))
                cur_batch = []
            else:
                # fill up empty rows with zeroes
                binned_data.append(__bin_batch(np.zeros((1, len(columns))), curr_sec))
            # update second
            curr_sec += bin_size

        # fill second batch
        if curr_sec >= int(row['sec']):
            cur_batch.append(row)

    # finish last batch
    if len(cur_batch) > 0:
        binned_data.append(__bin_batch(np.vstack(cur_batch), curr_sec))

    # cast into pd dataframe
    binned_data = pd.DataFrame(binned_data, columns=list(columns.keys()))

    return binned_data
