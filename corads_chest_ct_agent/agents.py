"""
Compatibility helpers around the canonical CO-RADS assessment engine.

These small classes preserve the historical import names without maintaining a
second, divergent clinical algorithm.
"""
from typing import Any, Dict, Optional

from .engine import assess_corads, calculate_severity_score
from .models import ChestCTFindings


class GGOFeatureExtractorAgent:
    def audit(self, findings: ChestCTFindings) -> Dict[str, Any]:
        result = assess_corads(findings)
        return {"typical_features": result.typical_features, "atypical_features": result.atypical_features}


class CORADSCategorizerAgent:
    def audit(self, findings: ChestCTFindings) -> Dict[str, Any]:
        return assess_corads(findings).to_dict()


class CTSeverityIndexCalculatorAgent:
    def audit(self, findings: ChestCTFindings) -> Optional[int]:
        if findings.lobar_involvement is None:
            return None
        return calculate_severity_score(findings.lobar_involvement)


class ChestCTCoordinator:
    def __init__(self) -> None:
        self.case_registry: Dict[str, Dict[str, Any]] = {}

    def process_case(self, findings: ChestCTFindings, case_id: Optional[str] = None) -> Dict[str, Any]:
        result = assess_corads(findings).to_dict()
        if case_id:
            self.case_registry[case_id] = result
        return result

    def query_supervisory_chat(self, user_query: str) -> str:
        query = user_query.strip().lower()
        if "standard" in query or "guideline" in query:
            return "CO-RADS follows the Dutch Radiological Society scheme published by Prokop et al. (Radiology 2020; doi:10.1148/radiol.2020201473)."
        return "This package provides deterministic structured CO-RADS decision support; it does not replace radiologist interpretation."
