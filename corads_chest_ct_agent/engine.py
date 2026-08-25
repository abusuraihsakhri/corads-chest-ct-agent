"""
CO-RADS Engine: COVID-19 Reporting and Data System for chest CT.

Implements CO-RADS assessment levels for chest CT findings suggestive
of COVID-19 pneumonia.

Categories:
  CO-RADS 1: Very low probability (normal or non-infectious)
  CO-RADS 2: Low probability (infection other than COVID-19)
  CO-RADS 3: Equivocal/uncertain
  CO-RADS 4: High probability (typical COVID-19 pattern)
  CO-RADS 5: Very high probability (extensive typical pattern)
  CO-RADS 6: RT-PCR confirmed COVID-19

CT Severity Score: Lobar involvement 0-5 per lobe, total 0-25

Reference: CO-RADS (Dutch Radiological Society, 2020)
"""
from typing import List, Optional
from .models import CORADSLevel, ChestCTFindings, CORADSResult, LobarInvolvement


# Level metadata
LEVEL_INFO = {
    CORADSLevel.CO_RADS_1: {
        "label": "Very low probability",
        "description": "Normal or non-infectious finding.",
        "probability": "Very low",
    },
    CORADSLevel.CO_RADS_2: {
        "label": "Low probability",
        "description": "Findings consistent with infection other than COVID-19.",
        "probability": "Low",
    },
    CORADSLevel.CO_RADS_3: {
        "label": "Equivocal/uncertain",
        "description": "Features compatible with COVID-19 but also other disease.",
        "probability": "Equivocal",
    },
    CORADSLevel.CO_RADS_4: {
        "label": "High probability",
        "description": "Ground-glass opacities in peripheral/posterior distribution, bilateral, multifocal.",
        "probability": "High",
    },
    CORADSLevel.CO_RADS_5: {
        "label": "Very high probability",
        "description": "Extensive bilateral GGO with or without consolidation, crazy paving, posterior/peripheral predominance.",
        "probability": "Very high",
    },
    CORADSLevel.CO_RADS_6: {
        "label": "RT-PCR confirmed",
        "description": "COVID-19 confirmed by RT-PCR.",
        "probability": "Confirmed",
    },
}


def _count_typical_features(findings: ChestCTFindings) -> tuple:
    """Count typical and atypical COVID-19 features. Returns (typical_list, atypical_list)."""
    typical = []
    atypical = []

    # Typical features
    if findings.ground_glass_opacities:
        typical.append("Ground-glass opacities")
    if findings.ggo_peripheral_distribution:
        typical.append("Peripheral distribution")
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
    if findings.bronchial_wall_thickening:
        typical.append("Bronchial wall thickening")
    if findings.traction_bronchiectasis:
        typical.append("Traction bronchiectasis")
    if findings.subpleural_lines:
        typical.append("Subpleural lines")
    if findings.halo_sign:
        typical.append("Halo sign")

    # Atypical features
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


def _is_typical_covid_pattern(findings: ChestCTFindings) -> bool:
    """Check if findings match typical COVID-19 pattern."""
    # Typical: GGO + peripheral/posterior + bilateral + multifocal
    has_ggo = findings.ground_glass_opacities
    has_peripheral = findings.ggo_peripheral_distribution
    has_posterior = findings.ggo_posterior_distribution
    has_bilateral = findings.ggo_bilateral
    has_multifocal = findings.ggo_multifocal

    return has_ggo and (has_peripheral or has_posterior) and has_bilateral and has_multifocal


def _is_very_high_pattern(findings: ChestCTFindings) -> bool:
    """Check if findings match very high probability pattern."""
    typical = _is_typical_covid_pattern(findings)
    if not typical:
        return False

    # Very high: extensive + crazy paving or consolidation
    has_extensive = findings.crazy_paving or (findings.consolidation and findings.consolidation_posterior)
    has_posterior_periph = findings.ggo_posterior_distribution and findings.ggo_peripheral_distribution

    return has_extensive and has_posterior_periph


def _has_atypical_features(findings: ChestCTFindings) -> bool:
    """Check for features atypical for COVID-19."""
    return (findings.tree_in_bud or findings.cavitation or
            findings.lymphadenopathy or findings.pleural_effusion or
            findings.upper_lobe_predominance or findings.unilateral)


def assess_corads(findings: ChestCTFindings) -> CORADSResult:
    """
    Perform a CO-RADS assessment based on chest CT findings.

    Decision logic:
    1. RT-PCR positive -> CO-RADS 6
    2. Normal/non-infectious -> CO-RADS 1
    3. Atypical features suggesting other infection -> CO-RADS 2
    4. Very high probability pattern -> CO-RADS 5
    5. Typical COVID-19 pattern -> CO-RADS 4
    6. Equivocal -> CO-RADS 3
    """
    notes: List[str] = []
    typical, atypical = _count_typical_features(findings)

    # Calculate CT severity score if lobar involvement provided
    ct_severity = None
    if findings.lobar_involvement is not None:
        errors = findings.lobar_involvement.validate()
        if errors:
            raise ValueError(f"Invalid lobar involvement: {'; '.join(errors)}")
        ct_severity = findings.lobar_involvement.total_score

    # CO-RADS 6: RT-PCR confirmed
    if findings.rt_pcr_positive:
        info = LEVEL_INFO[CORADSLevel.CO_RADS_6]
        return CORADSResult(
            corads_level=6,
            corads_label=info["label"],
            description=info["description"],
            probability=info["probability"],
            ct_severity_score=ct_severity,
            typical_features=typical,
            atypical_features=atypical,
            notes=["COVID-19 confirmed by RT-PCR."],
        )

    # CO-RADS 1: Normal or non-infectious
    if not findings.ground_glass_opacities and not findings.consolidation and not findings.crazy_paving:
        info = LEVEL_INFO[CORADSLevel.CO_RADS_1]
        return CORADSResult(
            corads_level=1,
            corads_label=info["label"],
            description=info["description"],
            probability=info["probability"],
            ct_severity_score=ct_severity,
            typical_features=typical,
            atypical_features=atypical,
            notes=notes + ["No GGO, consolidation, or crazy paving identified."],
        )

    # CO-RADS 2: Atypical features suggesting other infection
    if _has_atypical_features(findings) and not _is_typical_covid_pattern(findings):
        # If there are atypical features and it doesn't look like COVID
        if findings.tree_in_bud or findings.cavitation:
            info = LEVEL_INFO[CORADSLevel.CO_RADS_2]
            return CORADSResult(
                corads_level=2,
                corads_label=info["label"],
                description=info["description"],
                probability=info["probability"],
                ct_severity_score=ct_severity,
                typical_features=typical,
                atypical_features=atypical,
                notes=notes + ["Atypical features suggest non-COVID infection."],
            )

    # CO-RADS 5: Very high probability
    if _is_very_high_pattern(findings):
        info = LEVEL_INFO[CORADSLevel.CO_RADS_5]
        return CORADSResult(
            corads_level=5,
            corads_label=info["label"],
            description=info["description"],
            probability=info["probability"],
            ct_severity_score=ct_severity,
            typical_features=typical,
            atypical_features=atypical,
            notes=notes,
        )

    # CO-RADS 4: High probability (typical pattern)
    if _is_typical_covid_pattern(findings):
        info = LEVEL_INFO[CORADSLevel.CO_RADS_4]
        return CORADSResult(
            corads_level=4,
            corads_label=info["label"],
            description=info["description"],
            probability=info["probability"],
            ct_severity_score=ct_severity,
            typical_features=typical,
            atypical_features=atypical,
            notes=notes,
        )

    # CO-RADS 3: Equivocal - has some features but not clearly COVID
    if findings.ground_glass_opacities:
        info = LEVEL_INFO[CORADSLevel.CO_RADS_3]
        return CORADSResult(
            corads_level=3,
            corads_label=info["label"],
            description=info["description"],
            probability=info["probability"],
            ct_severity_score=ct_severity,
            typical_features=typical,
            atypical_features=atypical,
            notes=notes + ["GGO present but pattern not clearly typical for COVID-19."],
        )

    # Default: CO-RADS 1 if nothing else matches
    info = LEVEL_INFO[CORADSLevel.CO_RADS_1]
    return CORADSResult(
        corads_level=1,
        corads_label=info["label"],
        description=info["description"],
        probability=info["probability"],
        ct_severity_score=ct_severity,
        typical_features=typical,
        atypical_features=atypical,
        notes=notes,
    )


def calculate_severity_score(lobar: LobarInvolvement) -> int:
    """Calculate CT severity score (0-25) from lobar involvement."""
    errors = lobar.validate()
    if errors:
        raise ValueError(f"Invalid lobar involvement: {'; '.join(errors)}")
    return lobar.total_score
