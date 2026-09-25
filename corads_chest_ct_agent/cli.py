"""Command-line interface for the CO-RADS chest CT assessment helpers."""
import argparse
import json
import sys

from .engine import LEVEL_INFO, assess_corads, calculate_severity_score
from .models import CORADSLevel, ChestCTFindings, LobarInvolvement


def _lobar_from_args(args: argparse.Namespace) -> LobarInvolvement:
    return LobarInvolvement(
        right_upper=args.rum,
        right_middle=args.rmm,
        right_lower=args.rlm,
        left_upper=args.lum,
        left_lower=args.llm,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="corads-chest-ct-agent",
        description=(
            "Rule-based CO-RADS chest CT assessment helper. "
            "For educational/research use; radiologist interpretation is required."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_assess = subparsers.add_parser("assess", help="Assess structured chest CT findings")
    p_assess.add_argument("--ggo", action="store_true", help="Ground-glass opacities present")
    p_assess.add_argument("--peripheral", action="store_true", help="Peripheral/subpleural distribution")
    p_assess.add_argument("--posterior", action="store_true", help="Posterior distribution")
    p_assess.add_argument("--bilateral", action="store_true", help="Bilateral involvement")
    p_assess.add_argument("--multifocal", action="store_true", help="Multifocal involvement")
    p_assess.add_argument("--crazy-paving", action="store_true", help="Crazy paving pattern")
    p_assess.add_argument("--consolidation", action="store_true", help="Consolidation present")
    p_assess.add_argument(
        "--consolidation-posterior",
        action="store_true",
        help="Posterior consolidation",
    )
    p_assess.add_argument("--tree-in-bud", action="store_true", help="Tree-in-bud pattern")
    p_assess.add_argument("--cavitation", action="store_true", help="Cavitation")
    p_assess.add_argument("--lymphadenopathy", action="store_true", help="Lymphadenopathy")
    p_assess.add_argument("--pleural-effusion", action="store_true", help="Pleural effusion")
    p_assess.add_argument(
        "--diffuse-bilateral-ggo",
        action="store_true",
        help="Diffuse bilateral GGO without a classic peripheral pattern",
    )
    p_assess.add_argument("--unilateral", action="store_true", help="Predominantly unilateral distribution")
    p_assess.add_argument(
        "--rt-pcr-positive",
        action="store_true",
        help="SARS-CoV-2 RT-PCR reported positive",
    )
    for flag, label in (
        ("rum", "Right upper lobe"),
        ("rmm", "Right middle lobe"),
        ("rlm", "Right lower lobe"),
        ("lum", "Left upper lobe"),
        ("llm", "Left lower lobe"),
    ):
        p_assess.add_argument(f"--{flag}", type=int, default=0, help=f"{label} score (0-5)")
    p_assess.add_argument("--json", action="store_true", help="Output JSON")

    p_severity = subparsers.add_parser("severity", help="Calculate the five-lobe CT severity score")
    for flag, label in (
        ("rum", "Right upper lobe"),
        ("rmm", "Right middle lobe"),
        ("rlm", "Right lower lobe"),
        ("lum", "Left upper lobe"),
        ("llm", "Left lower lobe"),
    ):
        p_severity.add_argument(f"--{flag}", type=int, required=True, help=f"{label} score (0-5)")

    p_info = subparsers.add_parser("info", help="Show CO-RADS level information")
    p_info.add_argument("level", nargs="?", type=int, default=None, help="Level (1-6)")

    args = parser.parse_args(argv)

    if args.command == "assess":
        lobar = _lobar_from_args(args)
        findings = ChestCTFindings(
            ground_glass_opacities=args.ggo,
            ggo_peripheral_distribution=args.peripheral,
            ggo_posterior_distribution=args.posterior,
            ggo_bilateral=args.bilateral,
            ggo_multifocal=args.multifocal,
            crazy_paving=args.crazy_paving,
            consolidation=args.consolidation,
            consolidation_posterior=args.consolidation_posterior,
            tree_in_bud=args.tree_in_bud,
            cavitation=args.cavitation,
            lymphadenopathy=args.lymphadenopathy,
            pleural_effusion=args.pleural_effusion,
            diffuse_bilateral_ggo=args.diffuse_bilateral_ggo,
            unilateral=args.unilateral,
            rt_pcr_positive=args.rt_pcr_positive,
            lobar_involvement=lobar,
        )
        try:
            result = assess_corads(findings)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
            return 0

        print("=" * 64)
        print(f"CO-RADS {result.corads_level} — {result.corads_label}")
        print(f"Suspicion: {result.probability}")
        print(result.description)
        if result.ct_severity_score is not None:
            print(f"CT severity score: {result.ct_severity_score}/25")
        if result.typical_features:
            print("Typical/suspicious features: " + ", ".join(result.typical_features))
        if result.atypical_features:
            print("Atypical features: " + ", ".join(result.atypical_features))
        for note in result.notes:
            print(f"Note: {note}")
        print("=" * 64)
        return 0

    if args.command == "severity":
        try:
            score = calculate_severity_score(_lobar_from_args(args))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"CT Severity Score: {score}/25")
        return 0

    if args.command == "info":
        if args.level is not None:
            try:
                level = CORADSLevel(args.level)
            except ValueError:
                print(f"Invalid level: {args.level}. Must be 1-6.", file=sys.stderr)
                return 2
            info = LEVEL_INFO[level]
            print(f"CO-RADS {level.value}: {info['label']}")
            print(f"  {info['description']}")
            print(f"  Suspicion: {info['probability']}")
            return 0

        for level in CORADSLevel:
            info = LEVEL_INFO[level]
            print(f"CO-RADS {level.value}: {info['label']}")
            print(f"  {info['description']}")
            print(f"  Suspicion: {info['probability']}")
            print()
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
