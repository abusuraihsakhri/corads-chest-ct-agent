"""FastAPI interface for the canonical CO-RADS assessment engine."""
from typing import Optional

from .engine import assess_corads
from .models import ChestCTFindings, LobarInvolvement


def _build_app():
    from fastapi import FastAPI
    from pydantic import BaseModel, Field

    app = FastAPI(
        title="CO-RADS Chest CT Agent API",
        description=(
            "Structured, rule-based CO-RADS decision support. "
            "For educational/research use; radiologist interpretation is required."
        ),
        version="2.1.0",
    )

    class AssessmentRequest(BaseModel):
        ground_glass_opacities: bool = False
        ggo_peripheral_distribution: bool = False
        ggo_posterior_distribution: bool = False
        ggo_bilateral: bool = False
        ggo_multifocal: bool = False
        crazy_paving: bool = False
        consolidation: bool = False
        consolidation_posterior: bool = False
        tree_in_bud: bool = False
        cavitation: bool = False
        lymphadenopathy: bool = False
        pleural_effusion: bool = False
        diffuse_bilateral_ggo: bool = False
        unilateral: bool = False
        rt_pcr_positive: bool = False
        right_upper: Optional[int] = Field(default=None, ge=0, le=5)
        right_middle: Optional[int] = Field(default=None, ge=0, le=5)
        right_lower: Optional[int] = Field(default=None, ge=0, le=5)
        left_upper: Optional[int] = Field(default=None, ge=0, le=5)
        left_lower: Optional[int] = Field(default=None, ge=0, le=5)

    def _assess(req: AssessmentRequest):
        scores = (req.right_upper, req.right_middle, req.right_lower, req.left_upper, req.left_lower)
        lobar = None
        if any(score is not None for score in scores):
            lobar = LobarInvolvement(*[0 if score is None else score for score in scores])
        findings = ChestCTFindings(
            ground_glass_opacities=req.ground_glass_opacities,
            ggo_peripheral_distribution=req.ggo_peripheral_distribution,
            ggo_posterior_distribution=req.ggo_posterior_distribution,
            ggo_bilateral=req.ggo_bilateral,
            ggo_multifocal=req.ggo_multifocal,
            crazy_paving=req.crazy_paving,
            consolidation=req.consolidation,
            consolidation_posterior=req.consolidation_posterior,
            tree_in_bud=req.tree_in_bud,
            cavitation=req.cavitation,
            lymphadenopathy=req.lymphadenopathy,
            pleural_effusion=req.pleural_effusion,
            diffuse_bilateral_ggo=req.diffuse_bilateral_ggo,
            unilateral=req.unilateral,
            rt_pcr_positive=req.rt_pcr_positive,
            lobar_involvement=lobar,
        )
        return assess_corads(findings).to_dict()

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "corads-chest-ct-agent", "version": "2.1.0"}

    @app.post("/api/assess")
    def api_assess(req: AssessmentRequest):
        return _assess(req)

    @app.post("/api/audit", include_in_schema=False)
    def api_audit(req: AssessmentRequest):
        return _assess(req)

    return app


try:
    app = _build_app()
except ImportError:
    app = None


def create_app():
    """Return the FastAPI app, raising a clear error when API extras are absent."""
    if app is None:
        raise RuntimeError("FastAPI dependencies are not installed. Install with: pip install 'corads-chest-ct-agent[api]'")
    return app
