import logging
import math

import numpy as np
import pandas as pd

from example_scripts.recovery_study.compare_bartram_dataset import compare_bartram_dataset
from example_scripts.recovery_study.compare_caen_2021_dataset import compare_caen_2021_dataset
from example_scripts.recovery_study.compare_chidnok_dataset import compare_chidnok_dataset
from example_scripts.recovery_study.compare_ferguson_dataset import compare_ferguson_dataset
from example_scripts.recovery_study.compare_weigend_dataset import compare_weigend_dataset
from pypermod.utility import PlotLayout

# set logging level to highest level for info about simulation progress
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

# simulation precision
hz = 10  # 10 hz is a dt of 0.1

# run all simulations...
bart_res = compare_bartram_dataset(hz=hz)
bart_res = pd.DataFrame.from_dict(bart_res, orient='index')

weig_res = compare_weigend_dataset(hz=hz)
weig_res = pd.DataFrame.from_dict(weig_res, orient='index')

caen_res = compare_caen_2021_dataset(hz=hz)
caen_res = pd.DataFrame.from_dict(caen_res, orient='index')

chid_res = compare_chidnok_dataset(hz=hz)
chid_res = pd.DataFrame.from_dict(chid_res, orient='index')

ferg_res = compare_ferguson_dataset(hz=hz)
ferg_res = pd.DataFrame.from_dict(ferg_res, orient='index')

# get column labels
bart = PlotLayout.get_plot_label("WbalODEAgentBartram")
skib = PlotLayout.get_plot_label("WbalODEAgentSkiba")
weig = PlotLayout.get_plot_label("WbalODEAgentWeigend")
hydr = PlotLayout.get_plot_label("ThreeCompHydAgent")
grtr = PlotLayout.get_plot_label("ground_truth")

# all data for bartram comparison
pred_error_1 = pd.concat([caen_res, chid_res, ferg_res])
# get all required data rows for skiba and weigend comparison
pred_error_2 = pd.concat([bart_res, caen_res, chid_res, ferg_res])
# all required rows for AIC comparison
aic_eval = pd.concat([bart_res, caen_res, chid_res, ferg_res, weig_res])

# assemble big table of prediction errors
total = pd.concat([
    # AIC
    aic_eval[weig] - aic_eval[grtr],
    aic_eval[hydr] - aic_eval[grtr],
    # pred 1
    pred_error_1[bart] - pred_error_1[grtr],
    pred_error_1[hydr] - pred_error_1[grtr],
    # pred 2
    pred_error_2[skib] - pred_error_2[grtr],
    pred_error_2[weig] - pred_error_2[grtr],
    pred_error_2[hydr] - pred_error_2[grtr]
], axis=1)

# AIC data were in front to get the order right. Rearrange
total = total[total.columns[-5:].append(total.columns[:2])]

# MAE scores
me_row = pd.DataFrame([["{0:.2f}".format(total[x].abs().mean()) for x in total.columns]],
                      index=["MAE"],
                      columns=total.columns)
me_row.iloc[0, -2:] = np.nan

# SD scores
sd_row = pd.DataFrame([["\\pm {0:.2f}".format(total[x].abs().std()) for x in total.columns]],
                      index=["SD"],
                      columns=total.columns)
sd_row.iloc[0, -2:] = np.nan

# RMSE scores
rmse_row = pd.DataFrame([["{0:.2f}".format(np.sqrt(np.mean(total[x] ** 2))) for x in total.columns]],
                        index=["RMSE"],
                        columns=total.columns)
rmse_row.iloc[0, -2:] = np.nan

# now the AICc scores
aics = []
for agent in [weig, hydr]:
    rss_n = ((aic_eval[grtr] - aic_eval[agent]) ** 2).mean()
    k = 8 if agent == hydr else 3
    n = len(aic_eval.index)
    aic_c = n * math.log(rss_n) + 2 * k + ((2 * k * (k + 1)) / (n - k - 1))
    aics.append(aic_c)
aic_row = pd.DataFrame([[np.nan] * 5 + aics],
                       index=["AIC"],
                       columns=total.columns)

# add to total dataframe
total = total.append([me_row, sd_row, rmse_row, aic_row], sort=False)
print(total.to_string())
