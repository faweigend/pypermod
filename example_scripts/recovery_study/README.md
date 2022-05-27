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
Two types of scripts are available:

#### Compare to Data

Scripts that have a name that starts with `compare` recreate comparison plots of the [manuscript](https://arxiv.org/abs/2108.04510). You may use them to investigate the data we extracted from other studies or to see examples for how to use `pypermod` agents to predict recovery ratios.

#### Fitting Tau

Scripts that have a name that starts with `fitting` recreate the fitting process of time constants for W'bal-weig and Chidnok comparisons in our [manuscript](https://arxiv.org/abs/2108.04510). You may use them to further investigate our approaches to derive these time constants and how fitted models perform.

#### Simulate

Scripts that have a name that starts with `simulate` use one or several models to simulate energy dynamics of an athlete during exercise. Use these scripts as examples for how to use `pypermod` for predictions.