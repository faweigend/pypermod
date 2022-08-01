import pandas as pd

from pypermod.data_structure.activities.activity import Activity


class TimeSeries(Activity):
    """
    This activity class expects internal data to be a time series.
    Increasing time measurements under the column 'sec' are mandatory when adding
    input data with set_data function.
    Adds steps and duration to metadata.
    """

    def set_data(self, data: pd.DataFrame):
        """
        Adds actual exercise data to the activity object
        :param data:
        """
        # check if mandatory columns exist
        if 'sec' not in data.columns:
            raise UserWarning("Given dataframe with {} does not "
                              "contain \'sec\'".format(data.columns))
        super().set_data(data)

    def update_meta_data(self):
        """
        Update meta data with time series specific info
        """
        super().update_meta_data()

        if self.is_data_loaded():
            # because of the condition in set_data a column 'sec' must exist
            # get max seconds and num taken steps
            seconds = int(self.data['sec'].max())
            steps = int(self.data.shape[0])

            self._metadata.update({"steps": steps,
                                   "duration": seconds})

    @property
    def duration(self):
        """ simple getter """
        return self.meta["duration"]

    @property
    def time_data(self):
        """:return: seconds column"""
        return self.data['sec']
