# paths to be used by all scripts that store or access data
import os

paths = {
    "data_storage": os.path.dirname(os.path.abspath(__file__)) + "/data_storage/"
}

# a flag to determine whether plot should be displayed in black and white or in color
black_and_white = False

# an additional constraint on the three component hydraulic model that limits the interval for phi
three_comp_phi_constraint = False