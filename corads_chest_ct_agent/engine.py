"""
Rule-based CO-RADS chest CT assessment helpers.

CO-RADS is a radiologist reporting scheme, not an autonomous diagnostic
algorithm. This module provides a deterministic approximation for educational,
research, and software-testing use from a limited set of structured findings.

Primary reference:
    Prokop M, et al. Radiology. 2020;296(2):E97-E104.
    doi:10.1148/radiol.2020201473
"""
from typing import List, Tuple

from .models import CORADSLevel, ChestCTFindings, CORADSResult, LobarInvolvement


LEVEL_INFO = {
    CORADSLevel.CO_RADS_1: {
        "label": "Very low suspicion",
        "description": "Normal CT or findings considered non-infectious.",
        "probability": "Very low",
    },
    CORADSLevel.CO_RADS_2: {
        "label": "Low suspicion",
        "description": "Pulmonary findings typical of infection other than COVID-19.",
        "probability": "Low",
    },
    CORADSLevel.CO_RADS_3: {
        "label": "Equivocal",
        "description": "Indeterminate findings compatible with COVID-19 and other causes.",
        "probability": "Equivocal",
    },
    CORADSLevel.CO_RADS_4: {
        "label": "High suspicion",
        "description": "Suspicious COVID-19 pattern that is not fully typical for CO-RADS 5.",
        "probability": "High",
    },
    CORADSLevel.CO_RADS_5: {
        "label": "Very high suspicion",
        "description": "Typical bilateral multifocal peripheral/subpleural COVID-19 pattern.",
        "probability": "Very high",
    },
    CORADSLevel.CO_RADS_6: {
        "label": "RT-PCR confirmed",
        "description": "SARS-CoV-2 infection confirmed by RT-PCR.",
        "probability": "Confirmed",
    },
}


def _count_features(findings: ChestCTFindings) -> Tuple[List[str], List[str]]:
    typical: List[str] = []
    atypical: List[str] = []

    if findings.ground_glass_opacities:
        typical.append("Ground-glass opacities")
    if findings.ggo_peripheral_distribution:
        typical.append("Peripheral/subpleural distribution")
    if findings.ggo_posterior_distribution:
        typical.append("Posterior distribution")
    if findings.ggo_bilateral:
        typical.append("Bilateral involvement")
    if findings.ggo_multifocal:
        typical.append("Multifocal involvement")
    if findings.crazy_paving:
        typical.append("Crazy paving pattern")
    if findings.consolidation and findings.consolidation_posterior:
        typical.append("Posterior consolidation")
    if findings.vascular_thickening:
        typical.append("Vascular thickening")
    if findings.traction_bronchiectasis:
        typical.append("Traction bronchiectasis")
    if findings.subpleural_lines:
        typical.append("Subpleural lines")
    if findings.halo_sign:
        typical.append("Halo sign")

    if findings.tree_in_bud:
        atypical.append("Tree-in-bud pattern")
    if findings.cavitation:
        atypical.append("Cavitation")
    if findings.lymphadenopathy:
        atypical.append("Lymphadenopathy")
    if findings.pleural_effusion:
        atypical.append("Pleural effusion")
    if findings.pericardial_effusion:
        atypical.append("Pericardial effusion")

    return typical, atypical


def _is_corads5_pattern(findings: ChestCTFindings) -> bool:
    """Approximate the mandatory CO-RADS 5 distributional pattern.

    The structured model uses ``ggo_peripheral_distribution`` as the available
    proxy for opacities close to visceral pleural surfaces.
    """
    return (
        findings.ground_glass_opacities
        and findings.ggo_peripheral_distribution
        and findings.ggo_bilateral
        and findings.ggo_multifocal
        and not findings.unilateral
    )


def _is_corads4_pattern(findings: ChestCTFindings) -> bool:
    """Approximate a suspicious but not fully typical CO-RADS 4 pattern."""
    if not findings.ground_glass_opacities or _is_corads5_pattern(findings):
        return False

    supportive = sum(
        bool(value)
        for value in (
            findings.ggo_peripheral_distribution,
            findings.ggo_posterior_distribution,
            findings.ggo_bilateral,
            findings.ggo_multifocal,
            findings.crazy_paving,
            findings.consolidation_posterior,
        )
    )
    return supportive >= 2


def _is_corads2_pattern(findings: ChestCTFindings) -> bool:
    """Findings more characteristic of another pulmonary infection."""
    if findings.tree_in_bud or findings.cavitation:
        return True
    # The current data model cannot distinguish lobar from organizing-pneumonia
    # consolidation. Isolated consolidation is therefore treated conservatively
    # as a non-COVID infectious pattern.
    return (
        findings.consolidation
        and not findings.ground_glass_opacities
        and not findings.crazy_paving
    )


def assess_corads(findings: ChestCTFindings) -> CORADSResult:
    """Return a deterministic CO-RADS approximation from structured findings.

    This function is decision support only. The original CO-RADS scheme requires
    interpretation of CT morphology and distribution by a radiologist; this
    simplified implementation cannot encode every pattern described by Prokop
    et al.
    """
    typical, atypical = _count_features(findings)
    notes: List[str] = [
        "Rule-based approximation from structured findings; radiologist review is required."
    ]

    ct_severity = None
    if findings.lobar_involvement is not None:
        errors = findings.lobar_involvement.validate()
        if errors:
            raise ValueError(f"Invalid lobar involvement: {'; '.join(errors)}")
        ct_severity = findings.lobar_involvement.total_score

    if findings.rt_pcr_positive:
        level = CORADSLevel.CO_RADS_6
        notes.append("SARS-CoV-2 infection reported as RT-PCR confirmed.")
    elif _is_corads5_pattern(findings):
        level = CORADSLevel.CO_RADS_5
        if atypical:
            notes.append(
                "Atypical co-findings are present; consider mixed or alternative pathology."
            )
    elif _is_corads4_pattern(findings):
        level = CORADSLevel.CO_RADS_4
        if atypical:
            notes.append(
                "Atypical co-findings reduce specificity and require clinical correlation."
            )
    elif _is_corads2_pattern(findings):
        level = CORADSLevel.CO_RADS_2
        notes.append("Pattern contains features more typical of another infection.")
    elif (
        findings.ground_glass_opacities
        or findings.diffuse_bilateral_ggo
        or findings.crazy_paving
        or findings.consolidation
    ):
        level = CORADSLevel.CO_RADS_3
        notes.append("Pulmonary opacity pattern is indeterminate in this structured model.")
    else:
        level = CORADSLevel.CO_RADS_1
        notes.append("No modeled infectious opacity pattern identified.")

    info = LEVEL_INFO[level]
    return CORADSResult(
        corads_level=level.value,
        corads_label=info["label"],
        description=info["description"],
        probability=info["probability"],
        ct_severity_score=ct_severity,
        typical_features=typical,
        atypical_features=atypical,
        notes=notes,
    )


def calculate_severity_score(lobar: LobarInvolvement) -> int:
    """Calculate the five-lobe CT severity score (0-25)."""
    errors = lobar.validate()
    if errors:
        raise ValueError(f"Invalid lobar involvement: {'; '.join(errors)}")
    return lobar.total_score
