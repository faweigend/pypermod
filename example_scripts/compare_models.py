import logging
import math

import pandas as pd
from example_scripts.simulate_bartram_trials import simulate_bartram
from example_scripts.simulate_caen_2021_trials import simulate_caen_2021
from example_scripts.simulate_chidnok_trials import simulate_chidnok
from example_scripts.simulate_ferguson_trials import simulate_ferguson
from example_scripts.simulate_weigend_trials import simulate_weigend
from w_pm_modeling.performance_modeling_utility import PlotLayout


def to_latex(df, caption, label, study_descr):
    bart = PlotLayout.get_plot_label("WbalODEAgentBartram")
    skib = PlotLayout.get_plot_label("WbalODEAgentSkiba")
    weig = PlotLayout.get_plot_label("WbalODEAgentWeigend")
    hydr = PlotLayout.get_plot_label("ThreeCompHydAgent")
    grtr = PlotLayout.get_plot_label("ground_truth")

    # the table header
    latex_str = "\\begin{table}\n" \
                + "\\centering" \
                + "\\label{" + label + "}\n" \
                + "{\\footnotesize" \
                + "\\begin{tabular}{\n" \
                + "S[table-format=3.0]S[table-format=3.0]\n" \
                + "S[table-format=3.0]S[table-format=2.1]\n" \
                + "S[table-format=2.1]S[table-format=2.1]\n" \
                + "S[table-format=2.1]S[table-format=2.1]\n" \
                + "}\n" \
                + "\\hline\n" \
                + "\\multicolumn{4}{c|}{" + study_descr + "}&\\multicolumn{4}{|c}{Predicted $W'_{bal}$ Recovery (\%)} \\\\\n" \
                + "\\hline\n" \
                + "\\multicolumn{1}{l}{" + r'$P_{exp}$' + "}&\\multicolumn{1}{l}{" + r'$P_{rec}$' + "}&\n" \
                + "\\multicolumn{1}{l}{" + r'$T_{rec}$' + "}&\\multicolumn{1}{l|}{ground truth}&\n" \
                + "\\multicolumn{1}{|l}{" + bart + "}&\\multicolumn{1}{l}{" + skib + "}&\n" \
                + "\\multicolumn{1}{l}{" + weig + "}&\\multicolumn{1}{l}{" + hydr + "}\\\\\n" \
                + "\\hline\n"

    # now add the data into the table
    for index, row in df.iterrows():
        # stop when RMSE is reached
        if index == "RMSE":
            break
        latex_str += str(int(row[PlotLayout.get_plot_label("p_exp")])) + "&" \
                     + str(int(row[PlotLayout.get_plot_label("p_rec")])) + "&" \
                     + str(int(row[PlotLayout.get_plot_label("t_rec")])) + "&" \
                     + str(round(row[grtr], 1)) + "&" \
                     + str(round(row[bart], 1)) + "&" \
                     + str(round(row[skib], 1)) + "&" \
                     + str(round(row[weig], 1)) + "&" \
                     + str(round(row[hydr], 1)) + "\\\\\n"

    # add the RMSE
    rmse_row = df.loc[["RMSE"]]
    latex_str += "\\hline\n" \
                 + "\\hline\n" \
                 + "\\multicolumn{3}{r}{}&\n" \
                 + "\\multicolumn{1}{c}{RMSE}&\n" \
                 + str(round(rmse_row[bart][0], 1)) + "&" \
                 + str(round(rmse_row[skib][0], 1)) + "&" \
                 + str(round(rmse_row[weig][0], 1)) + "&" \
                 + str(round(rmse_row[hydr][0], 1)) + "\\\\\n"

    # finish the table
    latex_str += "\\end{tabular}\n" \
                 + "}" \
                 + "\\caption{" + caption + "}\n" \
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
    merged = pd.concat([bart_res, caen_res, chid_res, ferg_res], sort=False)

    texts = [("Extracted data from~\\cite{weigend_new_2021} and~\\cite{caen_reconstitution_2019} " \
              + "together with model predictions and RMSE estimate.",
              "tab:weigend_comp",
              "From~\\cite{weigend_new_2021} and~\\cite{caen_reconstitution_2019}"),
             ("Extracted data from~\\cite{bartram_accuracy_2018} " \
              + "together with model predictions and RMSE estimate. The " + bart + " predictions " \
              + "are the ground truth and therefore not compared.",
              "tab:bart_comp",
              "From~\\cite{bartram_accuracy_2018}"),
             ("Extracted data from~\\cite{caen_w_2021} " \
              + "together with model predictions and RMSE estimate.",
              "tab:caen_comp",
              "From~\\cite{caen_w_2021}"),
             ("Extracted data from~\\cite{chidnok_exercise_2012} " \
              + "together with model predictions and RMSE estimate.",
              "tab:chid_comp",
              "From~\\cite{chidnok_exercise_2012}"),
             ("Extracted data from~\\cite{ferguson_effect_2010} " \
              + "together with model predictions and RMSE estimate.",
              "tab:ferg_comp",
              "From~\\cite{ferguson_effect_2010}")]
    all_data = [weig_res, bart_res, caen_res, chid_res, ferg_res]
    for i, x in enumerate(all_data):
        rmse_row = []
        for col in cols:
            rmse_row.append(((x[grtr] - x[col]) ** 2).mean() ** 0.5)
        new_row = pd.DataFrame([rmse_row], index=["RMSE"], columns=cols)
        data_err = x.append(new_row, sort=False)
        print(data_err.to_string())
        capt = texts[i][0]
        labe = texts[i][1]
        tite = texts[i][2]
        to_latex(data_err, capt, labe, tite)

    # now the AICc computations
    total_merged = pd.concat([weig_res, bart_res, caen_res, chid_res, ferg_res], sort=False)
    for agent in [hydr, weig]:
        rss_n = ((total_merged[grtr] - total_merged[agent]) ** 2).mean()
        k = 8 if agent == hydr else 3
        n = len(total_merged.index)
        aic_c = n * math.log(rss_n) + 2 * k + ((2 * k * (k + 1)) / (n - k - 1))
        print(agent, aic_c)
