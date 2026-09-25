"""Tests for the canonical CO-RADS chest CT assessment engine."""
import json

import pytest

from corads_chest_ct_agent.cli import main as cli_main
from corads_chest_ct_agent.engine import LEVEL_INFO, assess_corads, calculate_severity_score
from corads_chest_ct_agent.models import CORADSLevel, ChestCTFindings, LobarInvolvement


def test_corads_6_for_reported_positive_rt_pcr():
    result = assess_corads(ChestCTFindings(rt_pcr_positive=True))
    assert result.corads_level == 6
    assert result.probability == "Confirmed"


def test_corads_1_for_no_modeled_infectious_opacity():
    assert assess_corads(ChestCTFindings()).corads_level == 1


@pytest.mark.parametrize("findings", [ChestCTFindings(ground_glass_opacities=True, tree_in_bud=True), ChestCTFindings(ground_glass_opacities=True, cavitation=True), ChestCTFindings(consolidation=True)])
def test_corads_2_for_other_infectious_patterns(findings):
    assert assess_corads(findings).corads_level == 2


def test_corads_3_for_indeterminate_ggo():
    assert assess_corads(ChestCTFindings(ground_glass_opacities=True, ggo_bilateral=True)).corads_level == 3


def test_corads_3_for_diffuse_bilateral_ggo_without_typical_distribution():
    assert assess_corads(ChestCTFindings(diffuse_bilateral_ggo=True)).corads_level == 3


def test_corads_4_for_suspicious_nonclassic_pattern():
    findings = ChestCTFindings(ground_glass_opacities=True, ggo_peripheral_distribution=True, ggo_posterior_distribution=True, unilateral=True)
    result = assess_corads(findings)
    assert result.corads_level == 4
    assert result.probability == "High"


def test_corads_5_for_classic_bilateral_multifocal_peripheral_pattern():
    findings = ChestCTFindings(ground_glass_opacities=True, ggo_peripheral_distribution=True, ggo_bilateral=True, ggo_multifocal=True)
    result = assess_corads(findings)
    assert result.corads_level == 5
    assert result.probability == "Very high"


def test_corads_5_does_not_require_crazy_paving_or_consolidation():
    findings = ChestCTFindings(ground_glass_opacities=True, ggo_peripheral_distribution=True, ggo_posterior_distribution=True, ggo_bilateral=True, ggo_multifocal=True)
    assert assess_corads(findings).corads_level == 5


def test_atypical_cofindings_are_reported_with_classic_pattern():
    findings = ChestCTFindings(ground_glass_opacities=True, ggo_peripheral_distribution=True, ggo_bilateral=True, ggo_multifocal=True, pleural_effusion=True)
    result = assess_corads(findings)
    assert result.corads_level == 5
    assert "Pleural effusion" in result.atypical_features
    assert any("Atypical co-findings" in note for note in result.notes)


@pytest.mark.parametrize(("lobar", "expected"), [(LobarInvolvement(0,0,0,0,0),0), (LobarInvolvement(5,5,5,5,5),25), (LobarInvolvement(3,4,5,3,4),19)])
def test_ct_severity_score(lobar, expected):
    assert calculate_severity_score(lobar) == expected


def test_lobar_validation_rejects_out_of_range_and_non_integer_values():
    assert LobarInvolvement(6,0,0,0,0).validate()
    assert LobarInvolvement("3",0,0,0,0).validate()
    assert LobarInvolvement(True,0,0,0,0).validate()


def test_invalid_lobar_score_raises():
    with pytest.raises(ValueError):
        calculate_severity_score(LobarInvolvement(6,0,0,0,0))


def test_severity_is_included_in_assessment():
    findings = ChestCTFindings(ground_glass_opacities=True, lobar_involvement=LobarInvolvement(3,4,5,3,4))
    assert assess_corads(findings).ct_severity_score == 19


def test_result_to_dict_and_level_info_complete():
    data = assess_corads(ChestCTFindings(ground_glass_opacities=True)).to_dict()
    assert data["corads_level"] == 3
    assert "ct_severity_score" in data
    assert all(level in LEVEL_INFO for level in CORADSLevel)


def test_cli_assess_json(capsys):
    ret = cli_main(["assess","--ggo","--peripheral","--bilateral","--multifocal","--json"])
    assert ret == 0
    assert json.loads(capsys.readouterr().out)["corads_level"] == 5


def test_cli_severity(capsys):
    ret = cli_main(["severity","--rum","3","--rmm","4","--rlm","5","--lum","3","--llm","4"])
    assert ret == 0
    assert "19/25" in capsys.readouterr().out


def test_cli_info(capsys):
    assert cli_main(["info","5"]) == 0
    assert "Very high" in capsys.readouterr().out
