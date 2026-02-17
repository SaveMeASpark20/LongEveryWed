"""
Time Series Window Processing Module

This module privides a set of classes for processing streaming time series data
using sliding windows. It' designed for real-time calculation like log returns
and lagged values, commonly used in financial data analysis.
"""

from abc import ABC, abstractmethod
from collections import deque
from typing import Optional, Deque
import numpy as np

class Tick(ABC):
    """
    Abstract base class for streaming data processors.

    All tick-based processor should inherit from this class and implement
    the on_tick method to handle incoming data points.
    """

    @abstractmethod
    def on_tick(self, x):
        """
        Process a single incoming data point.

        Args:
            x: The incoming data point (type depnds on implementation)

        Returns:
            Implementaion-specific return value
        """ 
        pass