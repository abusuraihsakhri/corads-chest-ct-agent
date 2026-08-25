"""
Data models for CO-RADS (COVID-19 Reporting and Data System).
Standard: CO-RADS (Dutch Radiological Society)
"""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Dict, Any


class CORADSLevel(IntEnum):
    """CO-RADS assessment levels 1-6."""
    CO_RADS_1 = 1
    CO_RADS_2 = 2
    CO_RADS_3 = 3
    CO_RADS_4 = 4
    CO_RADS_5 = 5
    CO_RADS_6 = 6


@dataclass
class LobarInvolvement:
    """CT severity scoring per lobe (0-5 scale)."""
    right_upper: int = 0  # 0-5
    right_middle: int = 0  # 0-5
    right_lower: int = 0  # 0-5
    left_upper: int = 0  # 0-5
    left_lower: int = 0  # 0-5

    def validate(self) -> List[str]:
        errors = []
        for name, val in [
            ("right_upper", self.right_upper),
            ("right_middle", self.right_middle),
            ("right_lower", self.right_lower),
            ("left_upper", self.left_upper),
            ("left_lower", self.left_lower),
        ]:
            if not 0 <= val <= 5:
                errors.append(f"{name} must be 0-5, got {val}")
        return errors

    @property
    def total_score(self) -> int:
        """Total CT severity score (0-25)."""
        return (self.right_upper + self.right_middle + self.right_lower +
                self.left_upper + self.left_lower)

    def to_dict(self) -> Dict[str, int]:
        return {
            "right_upper": self.right_upper,
            "right_middle": self.right_middle,
            "right_lower": self.right_lower,
            "left_upper": self.left_upper,
            "left_lower": self.left_lower,
            "total": self.total_score,
        }


@dataclass
class ChestCTFindings:
    """Findings on a chest CT for CO-RADS assessment."""
    # Typical COVID-19 features
    ground_glass_opacities: bool = False
    ggo_peripheral_distribution: bool = False
    ggo_posterior_distribution: bool = False
    ggo_bilateral: bool = False
    ggo_multifocal: bool = False
    crazy_paving: bool = False
    consolidation: bool = False
    consolidation_posterior: bool = False
    vascular_thickening: bool = False
    bronchial_wall_thickening: bool = False
    traction_bronchiectasis: bool = False
    subpleural_lines: bool = False
    halo_sign: bool = False

    # Atypical features
    tree_in_bud: bool = False
    cavitation: bool = False
    lymphadenopathy: bool = False
    pleural_effusion: bool = False
    pericardial_effusion: bool = False
    diffuse_bilateral_ggo: bool = False  # not COVID-typical pattern

    # Distribution
    upper_lobe_predominance: bool = False
    diffuse_distribution: bool = False
    unilateral: bool = False

    # Clinical
    rt_pcr_positive: bool = False  # confirmed COVID-19

    # Severity
    lobar_involvement: Optional[LobarInvolvement] = None

    notes: str = ""


@dataclass
class CORADSResult:
    """Result of a CO-RADS assessment."""
    corads_level: int  # 1-6
    corads_label: str
    description: str
    probability: str
    ct_severity_score: Optional[int] = None  # 0-25
    typical_features: List[str] = field(default_factory=list)
    atypical_features: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "corads_level": self.corads_level,
            "corads_label": self.corads_label,
            "description": self.description,
            "probability": self.probability,
            "ct_severity_score": self.ct_severity_score,
            "typical_features": self.typical_features,
            "atypical_features": self.atypical_features,
            "notes": self.notes,
        }
        return result
