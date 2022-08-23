import logging
import random

import numpy as np
from matplotlib import pyplot as plt

from compare_all import grand_comparison


def mae_error_func(group_a, group_b) -> float:
    """error function to estimate difference in MAEs of two groups"""
    mae_a = np.mean(np.abs(group_a))
    mae_b = np.mean(np.abs(group_b))
    return mae_a - mae_b


def rmse_error_func(group_a, group_b) -> float:
    """error function to estimate difference in RMSEs of two groups"""
    rmse_a = np.sqrt(np.mean(np.power(group_a, 2)))
    rmse_b = np.sqrt(np.mean(np.power(group_b, 2)))
    return rmse_a - rmse_b


def bootstrap(group_a, group_b, error_func, niter: int = 1500000, plot: bool = False) -> float:
    """
    a bootstrap test to test for a significant difference between two distributions
    :param group_a: first distribution
    :param group_b: second distribution
    :param error_func: function to estimate the test statistic
    :param niter: number of produced bootstrap samples
    :param plot: whether a plot should be displayed that shows the test statistic distribution
    return: p-value
    """

    # drop all rows with nan values
    group_a = group_a.dropna()
    group_b = group_b.dropna()

    # test statistic
    t = error_func(group_a, group_b)

    # pool all observations
    pool = group_a.tolist() + group_b.tolist()

    # count times the bootstrapped test statistic is >= t
    sumv = 0
    # store results for plot
    ms = []
    # bootstrap n times
    for _ in range(niter):
        # get random groups with replace
        rand_a = random.choices(pool, k=len(group_a))
        rand_b = random.choices(pool, k=len(group_b))

        # bootstrapped test statistic
        diff = error_func(rand_a, rand_b)

        # check for p value
        sumv += int(abs(diff) >= abs(t))
        ms.append(diff)

    # this optional plot shows the test statistic results distribution
    if plot:
        fig, ax = plt.subplots()
        ax.hist(ms, bins=50)
        ax.axvline(t)
        ax.axvline(-t)
        plt.show()

    # p value
    return sumv / niter


if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    # first, run all simulations and use values from results table
    total = grand_comparison(hz=10)
    # drop metric results
    total = total.drop(["MAE", "SD", "RMSE", "AIC"])

    # now conduct all bootstrap tests on error distributions
    print("MAE between W'bal_bart and hyd_weig")
    p = bootstrap(total[2], total[3], error_func=mae_error_func)
    print("  p-value: {}".format(p))

    print("MAE between W'bal_skib and hyd_weig")
    p = bootstrap(total[4], total[6], error_func=mae_error_func)
    print("  p-value: {}".format(p))

    print("MAE between W'bal_weig and hyd_weig")
    p = bootstrap(total[5], total[6], error_func=mae_error_func)
    print("  p-value: {}".format(p))

    print("RMSE between W'bal_bart and hyd_weig")
    p = bootstrap(total[2], total[3], error_func=rmse_error_func)
    print("  p-value: {}".format(p))

    print("RMSE between W'bal_skib and hyd_weig")
    p = bootstrap(total[4], total[6], error_func=rmse_error_func)
    print("  p-value: {}".format(p))

    print("RMSE between W'bal_weig and hyd_weig")
    p = bootstrap(total[5], total[6], error_func=rmse_error_func)
    print("  p-value: {}".format(p))
