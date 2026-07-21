"""Freqtrade 2026.6 compatibility adapter for the frozen Supertrend source."""

import math as _stdlib_math
import numpy.lib as _numpy_lib
import pandas as _pandas

# NumPy 2 removed the unused ``numpy.lib.math`` compatibility export used by
# the source.  Supplying the stdlib module changes no strategy calculation.
_numpy_lib.math = _stdlib_math
# Pandas 3 otherwise infers Arrow strings and rejects the source's neutral
# numeric fill value.  Object strings preserve the pre-Pandas-3 behavior:
# neutral remains neither ``up`` nor ``down``.
_pandas.options.future.infer_string = False

from original_source import Supertrend as _OriginalSupertrend


class Supertrend(_OriginalSupertrend):
    pass
