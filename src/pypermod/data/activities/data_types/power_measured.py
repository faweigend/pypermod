from datetime import datetime
import pandas as pd

from pypermod.data.activities.activity import Activity


class PowerMeasured(Activity):
    """
    This activity class expects internal data to contain power output measurements.
    A power output measurement under the column 'power' is mandatory when adding
    input data with set_data function.
    """

    def __init__(self, date_time: datetime):
        """
        simply calls the parent classes constructor
        """
        super().__init__(date_time)

    def set_data(self, data: pd.DataFrame):
        """
        Adds actual exercise data to the activity object
        :param data:
        """
        # check if mandatory columns exist
        if 'power' not in data.columns:
            raise UserWarning("Given dataframe with {} does not "
                              "contain \'power\'".format(data.columns))
        super().set_data(data)

    @property
    def max_power(self):
        """
        :return: getter for max power output during this activity
        """
        return self.meta["max_power"]

    @property
    def power_data(self):
        """
        :return: power values
        """
        return self.data['power']

    def update_meta_data(self):
        """
        Update meta data with power measured specific info
        """
        super().update_meta_data()

        if self.is_data_loaded():
            # because of the condition in set_data a column 'power' must exist
            col = 'power'
            self._metadata.update({
                "{}_avr".format(col): float(self.data[col].mean()),
                "{}_max".format(col): float(self.data[col].max())
            })
