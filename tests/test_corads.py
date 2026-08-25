"""
Tests for CO-RADS chest CT assessment engine.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from corads_chest_ct_agent.models import CORADSLevel, ChestCTFindings, CORADSResult, LobarInvolvement
from corads_chest_ct_agent.engine import assess_corads, calculate_severity_score, LEVEL_INFO
from cli import main as cli_main


# ── CO-RADS 6 (Confirmed) Tests ────────────────────────────────────

class TestCORADS6:
    def test_rt_pcr_positive(self):
        findings = ChestCTFindings(rt_pcr_positive=True)
        r = assess_corads(findings)
        assert r.corads_level == 6
        assert r.probability == "Confirmed"

    def test_rt_pcr_with_ggo(self):
        findings = ChestCTFindings(rt_pcr_positive=True, ground_glass_opacities=True)
        r = assess_corads(findings)
        assert r.corads_level == 6


# ── CO-RADS 1 (Very Low) Tests ─────────────────────────────────────

class TestCORADS1:
    def test_normal_ct(self):
        findings = ChestCTFindings()
        r = assess_corads(findings)
        assert r.corads_level == 1

    def test_no_ggo_no_consolidation(self):
        findings = ChestCTFindings(pleural_effusion=True)
        r = assess_corads(findings)
        assert r.corads_level == 1


# ── CO-RADS 2 (Low) Tests ──────────────────────────────────────────

class TestCORADS2:
    def test_tree_in_bud_pattern(self):
        """Tree-in-bud suggests non-COVID infection."""
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            tree_in_bud=True,
        )
        r = assess_corads(findings)
        assert r.corads_level == 2

    def test_cavitation_pattern(self):
        """Cavitation suggests non-COVID infection."""
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            cavitation=True,
        )
        r = assess_corads(findings)
        assert r.corads_level == 2


# ── CO-RADS 3 (Equivocal) Tests ────────────────────────────────────

class TestCORADS3:
    def test_ggo_not_typical_pattern(self):
        """GGO present but not in typical COVID distribution."""
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            ggo_bilateral=True,
            # Missing peripheral/posterior or multifocal
        )
        r = assess_corads(findings)
        assert r.corads_level == 3

    def test_ggo_unilateral(self):
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            ggo_peripheral_distribution=True,
            unilateral=True,
        )
        r = assess_corads(findings)
        assert r.corads_level == 3


# ── CO-RADS 4 (High) Tests ─────────────────────────────────────────

class TestCORADS4:
    def test_typical_covid_pattern(self):
        """GGO + peripheral + posterior + bilateral + multifocal = CO-RADS 4."""
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            ggo_peripheral_distribution=True,
            ggo_posterior_distribution=True,
            ggo_bilateral=True,
            ggo_multifocal=True,
        )
        r = assess_corads(findings)
        assert r.corads_level == 4
        assert r.probability == "High"

    def test_typical_without_crazy_paving(self):
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            ggo_peripheral_distribution=True,
            ggo_posterior_distribution=True,
            ggo_bilateral=True,
            ggo_multifocal=True,
        )
        r = assess_corads(findings)
        assert r.corads_level == 4


# ── CO-RADS 5 (Very High) Tests ────────────────────────────────────

class TestCORADS5:
    def test_extensive_with_crazy_paving(self):
        """Typical pattern + crazy paving + posterior/peripheral = CO-RADS 5."""
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            ggo_peripheral_distribution=True,
            ggo_posterior_distribution=True,
            ggo_bilateral=True,
            ggo_multifocal=True,
            crazy_paving=True,
        )
        r = assess_corads(findings)
        assert r.corads_level == 5
        assert r.probability == "Very high"

    def test_extensive_with_consolidation(self):
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            ggo_peripheral_distribution=True,
            ggo_posterior_distribution=True,
            ggo_bilateral=True,
            ggo_multifocal=True,
            consolidation=True,
            consolidation_posterior=True,
        )
        r = assess_corads(findings)
        assert r.corads_level == 5


# ── CT Severity Score Tests ─────────────────────────────────────────

class TestSeverityScore:
    def test_zero_score(self):
        lobar = LobarInvolvement(0, 0, 0, 0, 0)
        assert calculate_severity_score(lobar) == 0

    def test_max_score(self):
        lobar = LobarInvolvement(5, 5, 5, 5, 5)
        assert calculate_severity_score(lobar) == 25

    def test_partial_score(self):
        lobar = LobarInvolvement(3, 4, 5, 3, 4)
        assert calculate_severity_score(lobar) == 19

    def test_lobar_to_dict(self):
        lobar = LobarInvolvement(2, 3, 4, 1, 2)
        d = lobar.to_dict()
        assert d["total"] == 12
        assert d["right_upper"] == 2

    def test_lobar_validation(self):
        lobar = LobarInvolvement(6, 0, 0, 0, 0)
        errors = lobar.validate()
        assert len(errors) == 1

    def test_severity_in_result(self):
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            ggo_peripheral_distribution=True,
            ggo_posterior_distribution=True,
            ggo_bilateral=True,
            ggo_multifocal=True,
            lobar_involvement=LobarInvolvement(3, 4, 5, 3, 4),
        )
        r = assess_corads(findings)
        assert r.ct_severity_score == 19

    def test_severity_none_when_not_provided(self):
        findings = ChestCTFindings(ground_glass_opacities=True)
        r = assess_corads(findings)
        assert r.ct_severity_score is None


# ── Feature Tracking Tests ──────────────────────────────────────────

class TestFeatureTracking:
    def test_typical_features_listed(self):
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            ggo_peripheral_distribution=True,
            ggo_bilateral=True,
        )
        r = assess_corads(findings)
        assert "Ground-glass opacities" in r.typical_features
        assert "Peripheral distribution" in r.typical_features

    def test_atypical_features_listed(self):
        findings = ChestCTFindings(
            ground_glass_opacities=True,
            tree_in_bud=True,
            cavitation=True,
        )
        r = assess_corads(findings)
        assert "Tree-in-bud pattern" in r.atypical_features
        assert "Cavitation" in r.atypical_features


# ── Result Model Tests ──────────────────────────────────────────────

class TestResultModel:
    def test_to_dict(self):
        findings = ChestCTFindings(ground_glass_opacities=True)
        r = assess_corads(findings)
        d = r.to_dict()
        assert "corads_level" in d
        assert "ct_severity_score" in d

    def test_level_info_complete(self):
        for level in CORADSLevel:
            assert level in LEVEL_INFO


# ── CLI Tests ───────────────────────────────────────────────────────

class TestCLI:
    def test_assess_ggo(self, capsys):
        ret = cli_main(["assess", "--ggo", "--peripheral", "--posterior", "--bilateral", "--multifocal"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "CO-RADS" in out

    def test_assess_json(self, capsys):
        ret = cli_main(["assess", "--ggo", "--json"])
        assert ret == 0
        import json
        data = json.loads(capsys.readouterr().out)
        assert "corads_level" in data

    def test_severity_command(self, capsys):
        ret = cli_main(["severity", "--rum", "3", "--rmm", "4", "--rlm", "5", "--lum", "3", "--llm", "4"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "19/25" in out

    def test_info_command(self, capsys):
        ret = cli_main(["info"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "CO-RADS" in out

    def test_info_specific(self, capsys):
        ret = cli_main(["info", "5"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "Very high" in out
