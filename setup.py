
from setuptools import setup, find_packages

setup(
    name="DiamondPricePrediction",
    version="0.0.1",
    author="Ansh",
    package_dir={"": "src"},
    packages =find_packages(where="src"),
    install_requires=[
        "pandas",
        "numpy",
        "seaborn",
        "scipy",
        "scikit-learn",
    ]

)

