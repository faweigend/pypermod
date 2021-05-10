import pathlib
import setuptools

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setuptools.setup(
    name="performance_modeling",
    version="1.0.1",
    description="Performance modeling examples including Critical Power based agents "
                "and simulations on past recovery dynamic studies",
    long_description=README,
    long_description_content_type="text/x-rst",
    author="Fabian Weigend",
    author_email="fabian.weigend@westernsydney.edu.au",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python"
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3"
)
