"""
Data models for CO-RADS chest CT assessment and a five-lobe CT severity score.
"""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional


class CORADSLevel(IntEnum):
    CO_RADS_1 = 1
    CO_RADS_2 = 2
    CO_RADS_3 = 3
    CO_RADS_4 = 4
    CO_RADS_5 = 5
    CO_RADS_6 = 6


@dataclass
class LobarInvolvement:
    """Ordinal involvement score for each lobe (0-5; total 0-25)."""

    right_upper: int = 0
    right_middle: int = 0
    right_lower: int = 0
    left_upper: int = 0
    left_lower: int = 0

    def validate(self) -> List[str]:
        errors: List[str] = []
        for name, value in (
            ("right_upper", self.right_upper),
            ("right_middle", self.right_middle),
            ("right_lower", self.right_lower),
            ("left_upper", self.left_upper),
            ("left_lower", self.left_lower),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"{name} must be an integer from 0 to 5, got {value!r}")
            elif not 0 <= value <= 5:
                errors.append(f"{name} must be 0-5, got {value}")
        return errors

    @property
    def total_score(self) -> int:
        return (
            self.right_upper
            + self.right_middle
            + self.right_lower
            + self.left_upper
            + self.left_lower
        )

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
    tree_in_bud: bool = False
    cavitation: bool = False
    lymphadenopathy: bool = False
    pleural_effusion: bool = False
    pericardial_effusion: bool = False
    diffuse_bilateral_ggo: bool = False
    upper_lobe_predominance: bool = False
    diffuse_distribution: bool = False
    unilateral: bool = False
    rt_pcr_positive: bool = False
    lobar_involvement: Optional[LobarInvolvement] = None
    notes: str = ""


@dataclass
class CORADSResult:
    corads_level: int
    corads_label: str
    description: str
    probability: str
    ct_severity_score: Optional[int] = None
    typical_features: List[str] = field(default_factory=list)
    atypical_features: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "corads_level": self.corads_level,
            "corads_label": self.corads_label,
            "description": self.description,
            "probability": self.probability,
            "ct_severity_score": self.ct_severity_score,
            "typical_features": self.typical_features,
            "atypical_features": self.atypical_features,
            "notes": self.notes,
        }
