import pandas as pd

from pypermod.data_structure.activities.type_classes.standard_bike_bbb_test import StandardBikeBbbTest


class SrmBbbTest(StandardBikeBbbTest):
    """
    A performance bike test on the SRM cycle ergometer (With the SRM resistance is altitude)
    coupled with breath-by-breath data collection with the Cosmed.
    """

    def set_data(self, data: pd.DataFrame):
        """
        Adds actual exercise data to the activity object
        :param data: the data to add
        """
        needed_cols = ['altitude']
        # check if mandatory columns exist
        if any(i not in data.columns for i in needed_cols):
            raise UserWarning("Given dataframe with {} does not "
                              "contain one of {}".format(data.columns, needed_cols))
        super().set_data(data)

    def update_meta_data(self):
        """
        Update meta data with power measured specific info
        """
        super().update_meta_data()

        if self.is_data_loaded():
            # because of the condition in set_data a column 'power' must exist
            self._metadata.update({
                "resistance": self.altitude_data.max()
            })
