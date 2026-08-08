import os
import pandas as pd
import pytest

from DiamondPricePrediction.component.data_ingestion import DataIngestion


def test_data_ingestion():

    obj = DataIngestion()

    train_path, test_path = obj.initiate_data_ingestion()

    # Check files exist

    assert os.path.exists(train_path)

    assert os.path.exists(test_path)

    # Read generated files

    train_data = pd.read_csv(train_path)

    test_data = pd.read_csv(test_path)

    # Check data is not empty

    assert train_data.shape[0] > 0

    assert test_data.shape[0] > 0

    # Check total rows maintained

    total_rows = train_data.shape[0] + test_data.shape[0]

    original_data = pd.read_csv("notebook/train.csv")

    assert total_rows == original_data.shape[0]

    # Check split ratio approximately 80/20

    train_ratio = train_data.shape[0] / total_rows

    test_ratio = test_data.shape[0] / total_rows

    assert round(train_ratio, 1) == 0.8

    assert round(test_ratio, 1) == 0.2
