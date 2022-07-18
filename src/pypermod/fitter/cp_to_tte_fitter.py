import logging
from enum import Enum

import numpy as np
from pypermod.data_structure.helper.simple_constant_effort_measures import SimpleConstantEffortMeasures
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
from scipy import stats


class CPMTypes(Enum):
    """determines available CP models"""
    P2_1dTIME = "2p_1/time"
    P2_LINEAR = "2p_linear"
    P2_HYP = "2p_hyp"
    P3K = "3p_k"
    P3PMAX = "3p_pmax"


class CPMFits:
    """stores CPM fits to standardise storage and handling"""

    def __init__(self):
        """simple setup of the internal storage"""
        self.__param_dict = {"ttes_time:power": {}}

    def has_ttes(self):
        """
        simple check whether tte intensities and times were stored with the fitting
        :return: boolean
        """
        return bool(self.__param_dict["ttes_time:power"])

    def get_params(self, cpm_type: CPMTypes):
        """returns desired set of stored estimation results"""
        return self.__param_dict[cpm_type.value]

    def get_ttes(self) -> SimpleConstantEffortMeasures:
        """
        :return: used TTEs as a simple constant effort measures object
        """
        dict_tte = self.__param_dict["ttes_time:power"]
        return SimpleConstantEffortMeasures(times=list(dict_tte.keys()),
                                            measures=list(dict_tte.values()))

    def create_from_ttes(self, es: SimpleConstantEffortMeasures):
        """
        creates new fittings
        :param es:
        :return:
        """

        # save ttes
        self.__param_dict["ttes_time:power"] = es.as_dict()

        # fit all available models and store results in CPMFits instance
        w_p_m, cp_m, wp_see, cp_see, r2 = CpToTTEsFitter.fit_2p_linear(es)
        self.__param_dict.update({
            CPMTypes.P2_LINEAR.value: {"w_p": w_p_m,
                                       "cp": cp_m,
                                       "wp_see": wp_see,
                                       "cp_see": cp_see,
                                       "wp_see%": round(wp_see / w_p_m * 100, 1),
                                       "cp_see%": round(cp_see / cp_m * 100, 1),
                                       "r2": r2}
        })

        w_p, cp, wp_see, cp_see, r2 = CpToTTEsFitter.fit_2p_1dtime(es)
        self.__param_dict.update({
            CPMTypes.P2_1dTIME.value: {"w_p": w_p,
                                       "cp": cp,
                                       "wp_see": wp_see,
                                       "cp_see": cp_see,
                                       "wp_see%": round(wp_see / w_p * 100, 1),
                                       "cp_see%": round(cp_see / cp * 100, 1),
                                       "r2": r2}
        })

        w_p, cp, wp_see, cp_see, r2 = CpToTTEsFitter.fit_2p_hyp(es)
        self.__param_dict.update({
            CPMTypes.P2_HYP.value: {"w_p": w_p,
                                    "cp": cp,
                                    "wp_see": wp_see,
                                    "cp_see": cp_see,
                                    "wp_see%": round(wp_see / w_p * 100, 1),
                                    "cp_see%": round(cp_see / cp * 100, 1),
                                    "r2": r2}
        })

        w_p, cp, k, err, r2 = CpToTTEsFitter.fit_3_param_model_k(es)
        self.__param_dict.update({CPMTypes.P3K.value: {"w_p": w_p, "cp": cp, "k": k, "error": err.tolist(), "r2": r2}})

        # set cp *2 as the initial guess for max instantaneous power
        w_p, cp, p_max, err, r2 = CpToTTEsFitter.fit_3_param_model_p_max(es)
        self.__param_dict.update(
            {CPMTypes.P3PMAX.value: {"w_p": w_p, "cp": cp, "p_max": p_max, "error": err.tolist(), "r2": r2}})

    def get_best_2p_fit(self):
        """
        finds the 2p model fitting with the smallest sum of (W' SEE)/W' + (CP SEE)/CP. Recommended by Jones et al. 2019
        :return:  dict with entries {model, cp, w_p, wp_see%, cp_see, score}
        """
        checks = [CPMTypes.P2_1dTIME, CPMTypes.P2_LINEAR, CPMTypes.P2_HYP]
        score = 100
        best = None
        for chk in checks:
            vals = self.get_params(chk)
            w_p = vals["w_p"]
            cp = vals["cp"]
            wp_see = vals["wp_see"]
            cp_see = vals["cp_see"]
            s = (wp_see / w_p + cp_see / cp) * 100
            if s < score:
                score = s
                best = {
                    "model": chk.value,
                    "cp": cp,
                    "w_p": w_p,
                    "wp_see%": round(wp_see / w_p * 100, 1),
                    "cp_see%": round(cp_see / cp * 100, 1),
                    "score": score
                }
        self.__param_dict["best_2p"] = best
        return best

    def create_from_saved_dict(self, param_dict: dict):
        """sets input dict as internal storage"""
        for cpm_type in CPMTypes:
            if cpm_type.value in param_dict:
                self.__param_dict[cpm_type.value] = param_dict[cpm_type.value]

        # keep track of extra values (used to be more)
        extra_values = ["ttes_time:power", "best_2p"]
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
    def fit_2p_1dtime(ttes: SimpleConstantEffortMeasures):
        """
        Fits 2 parameter CP model using 1/time approach by Whipp et al. (1982)
        Uses given TTE times fit an estimate of W' (Anaerobic work capacity) and
        CP (Critical Power) using the two parameter model.
        :return: w' and critical power as two variables
        """
        # transform time frames to allow linear regression
        trans_times = [1 / x for x in ttes.times]

        # flip values: W' * 1/t + CP
        w_p, cp, wp_see, cp_see = CpToTTEsFitter.__linear_regression(trans_times, ttes.measures)

        # estimate the r2 score for comparison
        true = ttes.measures
        pred = []
        for time in trans_times:
            # W' * 1/t + cp
            pred.append(w_p * time + cp)
        r2 = r2_score(true, pred)

        return w_p, cp, wp_see, cp_see, r2

    @staticmethod
    def fit_2p_linear(ttes: SimpleConstantEffortMeasures):
        """
        Fits 2 linear parameter CP model using Monod & Scherrer (1965)
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
        cp, w_p, cp_see, wp_see = CpToTTEsFitter.__linear_regression(tte_times, w_lim)

        # estimate the r2 score for comparison
        true = w_lim
        pred = []
        for time in ttes.times:
            pred.append(cp * time + w_p)
        r2 = r2_score(true, pred)

        return w_p, cp, wp_see, cp_see, r2

    @staticmethod
    def fit_2p_hyp(ttes: SimpleConstantEffortMeasures, initial_guess: list = None):
        """
        Fits 2 parameter hyperbolic CP model using Moritani et. al. (1981)
        Uses given TTE times fit an estimate of W' (Anaerobic work capacity) and
        CP (Critical Power) using the two parameter model.
        :return: w' and critical power as two variables
        """
        if len(ttes) < 2:
            raise UserWarning("{} are not enough time frames to estimate W' and CP".format(len(ttes)))

        # apply non-linear regression
        guess = [15000, 50] if initial_guess is None else initial_guess

        if len(ttes) < 2:
            raise UserWarning("{} are not enough time frames to estimate W' and CP".format(len(ttes)))
        try:

            def func_2p_hyp(p, w_p, cp):
                """
                two parameter model
                :return: t_lim
                """
                return w_p / (p - cp)

            # The model function, f(x, ...).  It must take the independent
            # variable as the first argument and the parameters to fit as
            # separate remaining arguments.
            popt, pcov = curve_fit(func_2p_hyp,
                                   xdata=ttes.measures,
                                   ydata=ttes.times,
                                   p0=guess)

            # estimate the r2 score for comparison
            true = ttes.times
            pred = []
            for p in ttes.measures:
                pred.append(func_2p_hyp(p, popt[0], popt[1]))
            r2 = r2_score(true, pred)

            # standard error is sqrt of diag of cov matrix
            sees = np.sqrt(np.diag(pcov))
            # w_p, cp, k,
            return popt[0], popt[1], sees[0], sees[1], r2
        except RuntimeError:
            logging.warning("Optimal parameters not found")
            return -1, -1, -1, -1

    @staticmethod
    def fit_3_param_model_k(ttes: SimpleConstantEffortMeasures, initial_guess: list = None):
        """
        Uses collected mmp data to give an estimate of W' (Anaerobic work capacity) and
        CP (Critical Power) using the three parameter model
        :return: w' and critical power and p_max
        """
        guess = [9999, 99, -150] if initial_guess is None else initial_guess
        bounds = ([0, 0, -np.inf], [np.inf, np.inf, 0])

        def func_3p_k(p, w_p, cp, k):
            """
            three parameter model P(t_lim)
            :param p:
            :param w_p: Anaerobic power capacity
            :param k:
            :param cp: critical power
            :return: t_lim
            """
            if (p-cp == 0).any():
                raise UserWarning("Cannot fit to P=CP (division by 0) {}-{}={}".format(p, cp, p-cp))

            return w_p / (p - cp) + k

        w_p, cp, k, err, r2 = CpToTTEsFitter.__3_param_curve_fit(func_3p_k, ttes,
                                                                 guess, bounds)
        return w_p, cp, k, err, r2

    @staticmethod
    def fit_3_param_model_p_max(ttes: SimpleConstantEffortMeasures, initial_guess: list = None):
        """
        Uses collected mmp data to give an estimate of W' (Anaerobic work capacity) and
        CP (Critical Power) using the three parameter model
        :return: w' and critical power and p_max
        """
        guess = [9999, 99, 300] if initial_guess is None else initial_guess

        def func_3p_p_max(p, w_p, cp, p_max):
            """
            three parameter model P(t_lim)
            :param p:
            :param w_p: Anaerobic power capacity
            :param p_max:
            :param cp: critical power
            :return: t_lim
            """
            return w_p / (p - cp) + w_p / (cp - p_max)

        w_p, cp, p_max, err, r2 = CpToTTEsFitter.__3_param_curve_fit(func_3p_p_max,
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
        lm = stats.linregress(x, y)

        return lm.slope, lm.intercept, lm.stderr, lm.intercept_stderr

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
            popt, pcov = curve_fit(func,
                                   xdata=ttes.measures,
                                   ydata=ttes.times,
                                   p0=guess,
                                   bounds=bounds)

            # estimate the r2 score for comparison
            true = ttes.times
            pred = []
            for p in ttes.measures:
                pred.append(func(p, popt[0], popt[1], popt[2]))
            r2 = r2_score(true, pred)

            # w_p, cp, k, standard error is sqrt of cov matrix
            return popt[0], popt[1], popt[2], np.sqrt(np.diag(pcov)), r2
        except RuntimeError:
            logging.warning("Optimal parameters not found")
            return -1, -1, -1, -1
