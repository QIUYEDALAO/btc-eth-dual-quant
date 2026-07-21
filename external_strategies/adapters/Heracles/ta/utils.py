"""Import-compatible ``ta.utils`` subset required by frozen Heracles."""

import pandas as pd


def dropna(dataframe: pd.DataFrame) -> pd.DataFrame:
    return dataframe.replace([float("inf"), float("-inf")], float("nan")).dropna()
