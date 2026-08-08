import os
from pathlib import Path
import logging

from datetime import datetime

time_now = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"

makethispath = os.path.join(os.getcwd(), "log")
os.makedirs(makethispath, exist_ok=True)

# or
# os.makedirs(os.path.join(os.getcwd ,"logs"),exist_ok=True)

final_version = os.path.join(makethispath, time_now)

logging.basicConfig(
    level=logging.INFO,
    filename=final_version,
    format="[%(asctime)s] %(lineno)d %(name)s - %(levelname)s - %(message)s",
)
