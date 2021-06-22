import logging
import math

import pandas as pd
from example_scripts.simulate_bartram_trials import simulate_bartram
from example_scripts.simulate_caen_2021_trials import simulate_caen_2021
from example_scripts.simulate_chidnok_trials import simulate_chidnok
from example_scripts.simulate_ferguson_trials import simulate_ferguson
from example_scripts.simulate_weigend_trials import simulate_weigend
from pypermod.utility import PlotLayout


def to_latex(df, caption, label, study_descr):
    # create a list of available model estimations
    columns = []
    bart = PlotLayout.get_plot_label("WbalODEAgentBartram")
    skib = PlotLayout.get_plot_label("WbalODEAgentSkiba")
    weig = PlotLayout.get_plot_label("WbalODEAgentWeigend")
    hydr = PlotLayout.get_plot_label("ThreeCompHydAgent")
    check_cols = [bart, skib, weig, hydr]
    for check_col in check_cols:
        if check_col in df.columns:
            columns.append(check_col)

    grtr = PlotLayout.get_plot_label("ground_truth")

    # the table header
    latex_str = "\\begin{table}\n" \
                + "\\centering" \
                + "{\\footnotesize" \
                + "\\begin{tabular}{\n" \
                + "S[table-format=3.0]S[table-format=3.0]\n" \
                + "S[table-format=3.0]S[table-format=2.1]\n"

    # add according to available columns
    for _ in range(len(columns)):
        latex_str += "S[table-format=2.1]\n"

    latex_str += "}\n" \
                 + "\\hline\n" \
                 + "\\multicolumn{4}{c|}{" + study_descr + "}&\\multicolumn{" + str(len(columns)) + "}{c}{Predicted " \
                 + "$W'_{bal}$ Recovery (\%)} \\\\\n" \
                 + "\\hline\n" \
                 + "\\multicolumn{1}{c}{" + r'$P_{exp}$' + "}&\\multicolumn{1}{c}{" + r'$P_{rec}$' + "}&\n" \
                 + "\\multicolumn{1}{c}{" + r'$T_{rec}$' + "}&\\multicolumn{1}{c|}{ground truth} \n"

    # add title of available columns
    for c in columns:
        latex_str += "&\\multicolumn{1}{c}{" + c + "}"
    # finish row
    latex_str += "\\\\\n \\hline\n"

    # now add the data into the table
    for index, row in df.iterrows():
        # stop when RMSE is reached
        if index == "RMSE":
            break
        # study params are always there
        latex_str += str(int(row[PlotLayout.get_plot_label("p_exp")])) + "&" \
                     + str(int(row[PlotLayout.get_plot_label("p_rec")])) + "&" \
                     + str(int(row[PlotLayout.get_plot_label("t_rec")])) + "&" \
                     + str(round(row[grtr], 1))
        # add values of available columns
        for c in columns:
            latex_str += "&" + str(round(row[c], 1))
        # finish row
        latex_str += "\\\\\n"

    # add the RMSE
    rmse_row = df.loc[["RMSE"]]
    latex_str += "\\hline\n" \
                 + "\\hline\n" \
                 + "\\multicolumn{3}{r}{}&\n" \
                 + "\\multicolumn{1}{c}{RMSE:}\n"

    # add values of available columns
    for c in columns:
        latex_str += "&" + str(round(rmse_row[c][0], 1))

    # finish RMSE row
    latex_str += "\\\\\n"

    # finish the table
    latex_str += "\\end{tabular}\n" \
                 + "}" \
                 + "\\caption{" + caption + "}\n" \
                 + "\\label{" + label + "}\n" \
                 + "\\end{table}"
    print(latex_str)


if __name__ == "__main__":
    # set logging level to highest level
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s %(levelname)-5s %(name)s - %(message)s. [file=%(filename)s:%(lineno)d]")

    hz = 1

    # run all simulations...
    bart_res = simulate_bartram(hz=hz)
    bart_res = pd.DataFrame.from_dict(bart_res, orient='index')

    weig_res = simulate_weigend(hz=hz)
    weig_res = pd.DataFrame.from_dict(weig_res, orient='index')

    caen_res = simulate_caen_2021(hz=hz)
    caen_res = pd.DataFrame.from_dict(caen_res, orient='index')

    chid_res = simulate_chidnok(hz=hz)
    chid_res = pd.DataFrame.from_dict(chid_res, orient='index')

    ferg_res = simulate_ferguson(hz=hz)
    ferg_res = pd.DataFrame.from_dict(ferg_res, orient='index')

    # add error measures
    bart = PlotLayout.get_plot_label("WbalODEAgentBartram")
    skib = PlotLayout.get_plot_label("WbalODEAgentSkiba")
    weig = PlotLayout.get_plot_label("WbalODEAgentWeigend")
    hydr = PlotLayout.get_plot_label("ThreeCompHydAgent")
    grtr = PlotLayout.get_plot_label("ground_truth")
    cols = [bart, skib, weig, hydr]

    # ... and combine data for total RMSE
    bart_error_est = pd.concat([caen_res, chid_res, ferg_res], sort=False)
    wbal_error_est = pd.concat([bart_res, caen_res, chid_res, ferg_res], sort=False)

    texts = {
        "bart": ("Extracted data from~\\cite{bartram_accuracy_2018} (left part oft the table) " \
                 + "together with model predictions using the defined recovery estimation protocol " \
                 + "and RMSE estimates (right part oft the table). Predictions of " + bart + " are " \
                 + "the ground truth and therefore not compared.",
                 "tab:bart_comp",
                 "\\gls{cp}: 393   \\gls{w'}: 23300"),
        "caen": ("Extracted data from~\\cite{caen_w_2021} (left part oft the table) " \
                 + "together with model predictions using the defined recovery estimation protocol " \
                 + "and RMSE estimates (right part oft the table).",
                 "tab:caen_comp",
                 "\\gls{cp}: 269   \\gls{w'}: 19200"),
        "chid": ("Extracted data from~\\cite{chidnok_exercise_2012} (left part oft the table) " \
                 + "together with model predictions using the defined recovery estimation protocol " \
                 + "and RMSE estimates (right part oft the table).",
                 "tab:chid_comp",
                 "\\gls{cp}: 241   \\gls{w'}: 21100"),
        "ferg": ("Extracted data from~\\cite{ferguson_effect_2010} (left part oft the table) " \
                 + "together with model predictions using the defined recovery estimation protocol " \
                 + "and RMSE estimates (right part oft the table).",
                 "tab:ferg_comp",
                 "\\gls{cp}: 212   \\gls{w'}: 21600"),
        "weig": ("Extracted data from~\\cite{weigend_new_2021} and~\\cite{caen_reconstitution_2019} " \
                 + "(left part oft the table) " \
                 + "together with model predictions using the defined recovery estimation protocol " \
                 + "and RMSE estimates (right part oft the table). Both " + weig + " and " + hydr + " were " \
                 + "fitted to these ground truth values and are therefore not compared.",
                 "tab:weigend_comp",
                 "\\gls{cp}: 248   \\gls{w'}: 18200")
    }

    # DON'T CHANGE THESE ORDERS
    all_text = ["bart", "caen", "chid", "ferg", "weig"]
    all_data = [bart_res, caen_res, chid_res, ferg_res, weig_res]
    err_data = []
    for i, x in enumerate(all_data):
        rmse_row = []
        row_cols = []
        # go through all defined models
        for col in cols:
            # check if model estimations exist in dataset
            if col in x.columns:
                row_cols.append(col)
                rmse_row.append(((x[grtr] - x[col]) ** 2).mean() ** 0.5)
        new_row = pd.DataFrame([rmse_row], index=["RMSE"], columns=row_cols)
        x_err = x.append(new_row, sort=False)

        # print the whole data frame
        err_data.append(x_err)
        # print(x_err.to_string())

        capt = texts[all_text[i]][0]
        labl = texts[all_text[i]][1]
        tite = texts[all_text[i]][2]
        to_latex(x_err, capt, labl, tite)

        print("\n\n\n")

    # Estimate mean RMSEs
    bart_m_rmse = (err_data[all_text.index("caen")][bart][-1] +
                   err_data[all_text.index("chid")][bart][-1] +
                   err_data[all_text.index("ferg")][bart][-1]) / 3

    bart_hyd_m_rmse = (err_data[all_text.index("caen")][hydr][-1] +
                       err_data[all_text.index("chid")][hydr][-1] +
                       err_data[all_text.index("ferg")][hydr][-1]) / 3

    skib_m_rmse = (err_data[all_text.index("bart")][skib][-1] +
                   err_data[all_text.index("caen")][skib][-1] +
                   err_data[all_text.index("chid")][skib][-1] +
                   err_data[all_text.index("ferg")][skib][-1]) / 4

    weig_m_rmse = (err_data[all_text.index("bart")][weig][-1] +
                   err_data[all_text.index("caen")][weig][-1] +
                   err_data[all_text.index("chid")][weig][-1] +
                   err_data[all_text.index("ferg")][weig][-1]) / 4

    hydr_m_rmse = (err_data[all_text.index("bart")][hydr][-1] +
                   err_data[all_text.index("caen")][hydr][-1] +
                   err_data[all_text.index("chid")][hydr][-1] +
                   err_data[all_text.index("ferg")][hydr][-1]) / 4

    print("Mean RMSEs: \n"
          " bart: {0:.2f}\n"
          " bart_hyd: {4:.2f}\n"
          " skib: {1:.2f}\n"
          " weig: {2:.2f}\n"
          " hydr: {3:.2f}".format(bart_m_rmse,
                                  skib_m_rmse,
                                  weig_m_rmse,
                                  hydr_m_rmse,
                                  bart_hyd_m_rmse))

    # now the AICc computations
    total_merged = pd.concat([bart_res, caen_res, chid_res, ferg_res, weig_res], sort=False)
    for agent in [hydr, weig]:
        rss_n = ((total_merged[grtr] - total_merged[agent]) ** 2).mean()
        k = 8 if agent == hydr else 3
        n = len(total_merged.index)
        aic_c = n * math.log(rss_n) + 2 * k + ((2 * k * (k + 1)) / (n - k - 1))
        print("AIC for {0} is {1:.2f}".format(agent, aic_c))
