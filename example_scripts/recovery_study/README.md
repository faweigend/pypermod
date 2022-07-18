# Recovery Study

This directory contains scripts related to our publication:
```
@misc{weigend2021hydraulic,
      title={A hydraulic model outperforms work-balance models for predicting recovery kinetics from intermittent exercise}, 
      author={Fabian C. Weigend and David C. Clarke and Oliver Obst and Jason Siegler},
      year={2021},
      eprint={2108.04510},
      archivePrefix={arXiv},
      primaryClass={cs.OH}
}
```
Three types of scripts are available:

#### Compare models to data or to each other

Scripts that have a name that starts with `compare_[last name]_dataset` recreate comparison plots of the [paper](https://arxiv.org/abs/2108.04510). 
You may use them to investigate the data we extracted from other studies or to see examples for how to use `pypermod` agents to predict recovery ratios.

`compare_all` recreates the big comparison table from the [paper](https://arxiv.org/abs/2108.04510).

`comparison_significance_test` tests for statistical differences in prediction error distributions of two models as done in our [paper](https://arxiv.org/abs/2108.04510). 

`compare_p_work_effec` recreates the plot 4.1 of our paper [paper](https://arxiv.org/abs/2108.04510)

#### Fitting Tau

Scripts that have a name that starts with `fitting` recreate the fitting process of time constants for W'bal-weig and Chidnok comparisons in our [paper](https://arxiv.org/abs/2108.04510). 
You may use them to further investigate our approaches to derive these time constants and how fitted models perform.

#### Simulate

__note:__ the `simulate` script has been moved to the directory above as it is relevant for all data.

Scripts that have a name that starts with `simulate` use one or several models to simulate energy dynamics of an athlete during exercise. 
Use these scripts as examples for how to use `pypermod` for predictions.