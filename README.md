![](./httpdocs/small_pypermod_title.png)

# pypermod

[![PyPI](https://img.shields.io/pypi/v/pypermod.svg?style=for-the-badge)](https://pypi.python.org/pypi/pypermod)

This python package provides various tools to predict energy expenditure and recovery dynamics of an athlete. The
name `pypermod` stands for __Python Performance Modeling__.

More details on the purpose of this package can be found in our manuscript __A hydraulic model outperforms work-balance
models for predicting recovery kinetics from intermittent exercise__. You can find the preprint
on [arXiv](https://arxiv.org/abs/2108.04510).

You may also want to check our detailed video presentation
at [STARS](https://www.clearinghouseforsport.gov.au/digital-media/conferences/2020/stars/modelling-energy-expenditure-and-recovery-investigation-and-validation-of-a-three-component-hydraulic-model)
. Or the more recent presentation at the [SFU Sports Analytics Seminar](https://www.youtube.com/watch?v=OGiv_frvM6g).

If you make use of this project, we would be grateful if you star the repository and/or cite our preprint.

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

### Setup

If you aim to use the package for your own analysis you may want to install it via `pip3 install pypermod` without the
need for a manual download.

If you aim to work on the source code you may clone the [GitHub_repository](https://github.com/faweigend/pypermod). You
can install the files from the repository by running `pip3 install -e <path_to_project_root>`.

### Usage

Please see the scripts in the `example_scripts`
folder of our [GitHub_repository](https://github.com/faweigend/pypermod) for example applications. Each subdirectory has
its own README.md with instructions. Available examples are

* [Recovery Study](example_scripts/recovery_study)
* [VO2 Study](example_scripts/vo2_study)