"""
CO-RADS Chest CT Agent: COVID-19 Reporting and Data System for chest CT.
"""
__version__ = "2.0.0-PRO"

from .models import CORADSLevel, ChestCTFindings, CORADSResult, LobarInvolvement
from .engine import assess_corads, calculate_severity_score, LEVEL_INFO
