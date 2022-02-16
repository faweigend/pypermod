import logging
from enum import Enum

import numpy as np
from pypermod.data_structure.helper.simple_constant_effort_measures import SimpleConstantEffortMeasures
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
from scipy import stats


class CPMTypes(Enum):
    """determines available CP models"""
    P2WHIPP = "2p_whipp"
    P2MONOD = "2p_monod_and_scherrer"
    P2MORIT = "2p_moritani"
    P3K = "3p_k"
    P3PMAX = "3p_pmax"


class CPMFits:
    """stores CPM fits to standardise storage and handling"""

    def __init__(self):
        """simple setup of the internal storage"""
        self.__param_dict = {"tte_intensities": {}}

    def set_p2whipp(self, w_p, cp, err, r2):
        """setter for Whipp et. al. (1982) estimation results"""
        self.__param_dict.update({CPMTypes.P2WHIPP.value: {"w_p": w_p, "cp": cp, "error": err, "r2": r2}})

    def set_p2monod(self, w_p, cp, err, r2):
        """setter for Monod & Scherrer (1965) estimation results"""
        self.__param_dict.update({CPMTypes.P2MONOD.value: {"w_p": w_p, "cp": cp, "error": err, "r2": r2}})

    def set_p2morit(self, w_p, cp, err, r2):
        """setter for  Moritani et. al. (1981) estimation results"""
        self.__param_dict.update({CPMTypes.P2MORIT.value: {"w_p": w_p, "cp": cp, "error": err.tolist(), "r2": r2}})

    def set_p3k(self, w_p, cp, k, err, r2):
        """setter for Morton (1996) 3-p model with simple k parameter"""
        self.__param_dict.update({CPMTypes.P3K.value: {"w_p": w_p, "cp": cp, "k": k, "error": err.tolist(), "r2": r2}})

    def set_p3p_pmax(self, w_p, cp, p_max, err, r2):
        """setter for Morton (1996) 3-p model with dynamic p_max parameter"""
        self.__param_dict.update(
            {CPMTypes.P3PMAX.value: {"w_p": w_p, "cp": cp, "p_max": p_max, "error": err.tolist(), "r2": r2}})

    def has_ttes(self):
        """
        simple check whether tte intensities and times were stored with the fitting
        :return: boolean
        """
        return bool(self.__param_dict["tte_intensities"])

    def get_params(self, cpm_type: CPMTypes):
        """returns desired set of stored estimation results"""
        return self.__param_dict[cpm_type.value]

    def create_from_ttes(self, es: SimpleConstantEffortMeasures):
        """
        creates new fittings
        :param es:
        :return:
        """

        # save ttes
        self.__param_dict["tte_intensities"] = es.as_dict()

        # fit all available models and store results in CPMFits instance
        w_p_m, cp_m, err, r2 = CpToTTEsFitter.fit_2_param_model_monod_and_scherrer(es)
        self.set_p2monod(w_p=w_p_m, cp=cp_m, err=err, r2=r2)

        w_p, cp, err, r2 = CpToTTEsFitter.fit_2_param_model_whipp(es)
        self.set_p2whipp(w_p=w_p, cp=cp, err=err, r2=r2)

        w_p, cp, err, r2 = CpToTTEsFitter.fit_2_param_model_moritani(es, initial_guess=[300, 5000])
        self.set_p2morit(w_p=w_p, cp=cp, err=err, r2=r2)

        w_p, cp, k, err, r2 = CpToTTEsFitter.fit_3_param_model_k(es, initial_guess=[w_p_m, cp_m, -40])
        self.set_p3k(w_p=w_p, cp=cp, k=k, err=err, r2=r2)

        # set cp *2 as the initial guess for max instantaneous power
        w_p, cp, p_max, err, r2 = CpToTTEsFitter.fit_3_param_model_p_max(es, initial_guess=[w_p_m, cp_m, cp_m * 2])
        self.set_p3p_pmax(w_p=w_p, cp=cp, p_max=p_max, err=err, r2=r2)

    def create_from_saved_dict(self, param_dict: dict):
        """sets input dict as internal storage"""
        for cpm_type in CPMTypes:
            if cpm_type.value in param_dict:
                self.__param_dict[cpm_type.value] = param_dict[cpm_type.value]

        # keep track of extra values (used to be more)
        extra_values = ["tte_intensities"]
        for extra_value in extra_values:
            if extra_value in param_dict:
                self.__param_dict[extra_value] = param_dict[extra_value]
            else:
                self.__param_dict[extra_value] = {}

    def as_dict(self):
        """:return internal storage as dict"""
        return self.__param_dict


class CpToTTEsFitter:
    """
    provides functions and fitting for
    2 and 3 param critical power models
    """

    @staticmethod
    def func_3p_p_max(t_lim, w_p, cp, p_max):
        """
        three parameter model P(t_lim)
        :param t_lim:
        :param w_p: Anaerobic power capacity
        :param p_max:
        :param cp: critical power
        :return: P(t)
        """
        return w_p / (t_lim - (w_p / (cp - p_max))) + cp

    @staticmethod
    def func_3p_k(t_lim, w_p, cp, k):
        """
        three parameter model P(t_lim)
        :param t_lim:
        :param w_p: Anaerobic power capacity
        :param k:
        :param cp: critical power
        :return: P(t)
        """
        return w_p / (t_lim - k) + cp

    @staticmethod
    def func_2p_moritani(t_lim, w_p, cp):
        """
        two parameter model
        :param t_lim:
        :param w_p:
        :param cp:
        :return: P(t)
        """
        return (w_p / t_lim) + cp

    @staticmethod
    def fit_2_param_model_whipp(ttes: SimpleConstantEffortMeasures):
        """
        Fits 2 parameter CP model using Whipp et. al. (1982)
        Uses given TTE times fit an estimate of W' (Anaerobic work capacity) and
        CP (Critical Power) using the two parameter model.
        :return: w' and critical power as two variables
        """
        # transform time frames to allow linear regression
        trans_times = [1 / x for x in ttes.times]

        # flip values: W' * 1/t + CP
        w_p, cp, err = CpToTTEsFitter.__linear_regression(trans_times, ttes.measures)

        # estimate the r2 score for comparison
        true = ttes.measures
        pred = []
        for time in trans_times:
            # W' * 1/t + cp
            pred.append(w_p * time + cp)
        r2 = r2_score(true, pred)

        return w_p, cp, err, r2

    @staticmethod
    def fit_2_param_model_monod_and_scherrer(ttes: SimpleConstantEffortMeasures):
        """
        Fits 2 parameter CP model using Monod & Scherrer (1965)
        Uses given TTE times fit an estimate of W' (Anaerobic work capacity) and
        CP (Critical Power) using the two parameter model.
        :return: w' and critical power as two variables
        """
        # transform time to minutes
        tte_times = ttes.times
        # get W_lim (accumulated power)
        w_lim = []
        for i, x in enumerate(list(ttes.measures)):
            w_lim.append(float(x) * (tte_times[i]))

        # flip values: cp * t + W'
        cp, w_p, err = CpToTTEsFitter.__linear_regression(tte_times, w_lim)

        # estimate the r2 score for comparison
        true = w_lim
        pred = []
        for time in ttes.times:
            pred.append(cp * time + w_p)
        r2 = r2_score(true, pred)

        return w_p, cp, err, r2

    @staticmethod
    def fit_2_param_model_moritani(ttes: SimpleConstantEffortMeasures, initial_guess: list = None):
        """
        Fits 2 parameter CP model using Moritani et. al. (1981)
        Uses given TTE times fit an estimate of W' (Anaerobic work capacity) and
        CP (Critical Power) using the two parameter model.
        :return: w' and critical power as two variables
        """
        if len(ttes) < 2:
            raise UserWarning("{} are not enough time frames to estimate W' and CP".format(len(ttes)))

        # apply non-linear regression
        guess = [15000, 50] if initial_guess is None else initial_guess
        slope, intercept, err, r2 = CpToTTEsFitter.__2_param_curve_fit(
            CpToTTEsFitter.func_2p_moritani, ttes,
            guess)
        return slope, intercept, err, r2

    @staticmethod
    def fit_3_param_model_k(ttes: SimpleConstantEffortMeasures, initial_guess: list = None):
        """
        Uses collected mmp data to give an estimate of W' (Anaerobic work capacity) and
        CP (Critical Power) using the three parameter model
        :return: w' and critical power and p_max
        """
        guess = [150, 50, -40] if initial_guess is None else initial_guess
        bounds = ([0, 0, -np.inf], [np.inf, np.inf, 0])
        w_p, cp, k, err, r2 = CpToTTEsFitter.__3_param_curve_fit(CpToTTEsFitter.func_3p_k, ttes,
                                                                 guess, bounds)
        return w_p, cp, k, err, r2

    @staticmethod
    def fit_3_param_model_p_max(ttes: SimpleConstantEffortMeasures, initial_guess: list = None):
        """
        Uses collected mmp data to give an estimate of W' (Anaerobic work capacity) and
        CP (Critical Power) using the three parameter model
        :return: w' and critical power and p_max
        """
        guess = [150, 50, 300] if initial_guess is None else initial_guess
        w_p, cp, p_max, err, r2 = CpToTTEsFitter.__3_param_curve_fit(CpToTTEsFitter.func_3p_p_max,
                                                                     ttes, guess)
        return w_p, cp, p_max, err, r2

    @staticmethod
    def __linear_regression(x, y):
        """
        :param x:
        :param y:
        :return: slope, intercept and std err
        """
        if len(x) < 2:
            raise UserWarning("{} are not enough time frames to estimate W' and CP".format(len(x)))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return slope, intercept, std_err

    @staticmethod
    def __2_param_curve_fit(func, ttes: SimpleConstantEffortMeasures, guess: list):
        """
        base method for 3 param k or p_max fit
        :param func:
        :param ttes:
        :param guess:
        :return:
        """
        if len(ttes) < 2:
            raise UserWarning("{} are not enough time frames to estimate W' and CP".format(len(ttes)))
        try:
            # The model function, f(x, ...).  It must take the independent
            # variable as the first argument and the parameters to fit as
            # separate remaining arguments.
            popt, pcov = curve_fit(func, ttes.times, ttes.measures, guess)

            # estimate the r2 score for comparison
            true = ttes.measures
            pred = []
            for time in ttes.times:
                pred.append(func(time, popt[0], popt[1]))
            r2 = r2_score(true, pred)

            # w_p, cp, k, standard error is sqrt of cov matrix
            return popt[0], popt[1], np.sqrt(np.diag(pcov)), r2
        except RuntimeError:
            logging.warning("Optimal parameters not found")
            return -1, -1, -1, -1

    @staticmethod
    def __3_param_curve_fit(func, ttes: SimpleConstantEffortMeasures, guess: list, bounds=None):
        """
        base method for 3 param k or p_max fit
        :param func:
        :param ttes:
        :param guess:
        :return:
        """
        if len(ttes) < 2:
            raise UserWarning("{} are not enough time frames to estimate W' and CP".format(len(ttes)))
        try:
            if bounds is None:
                bounds = ([0, 0, 0], [np.inf, np.inf, np.inf])
            popt, pcov = curve_fit(func, ttes.times, ttes.measures, guess, bounds=bounds)

            # estimate the r2 score for comparison
            true = ttes.measures
            pred = []
            for time in ttes.times:
                pred.append(func(time, popt[0], popt[1], popt[2]))
            r2 = r2_score(true, pred)

            # w_p, cp, k, standard error is sqrt of cov matrix
            return popt[0], popt[1], popt[2], np.sqrt(np.diag(pcov)), r2
        except RuntimeError:
            logging.warning("Optimal parameters not found")
            return -1, -1, -1, -1
