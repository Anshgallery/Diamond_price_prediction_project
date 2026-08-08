import os
from pathlib import Path

package_name = "DiamondPricePrediction"

list = [
    ".github/workflows/.gitkeep",
    f"src/{package_name}/component/__init__.py",
    f"src/{package_name}/component/data_ingestion.py",
    f"src/{package_name}/component/model_training.py",
    f"src/{package_name}/pipeline/__init__.py",
    f"src/{package_name}/pipeline/training.py",
    f"src/{package_name}/pipeline/prediction.py",
    "requirements.txt",
    "setup.py",
    "notebook/research.ipynb",
]

for i in list:
    fullpath = Path(i)
    dir, file = os.path.split(fullpath)

    if dir != "":
        os.makedirs(dir, exist_ok=True)

    if not os.path.exists(fullpath):
        with open(fullpath, "w") as f:
            pass
