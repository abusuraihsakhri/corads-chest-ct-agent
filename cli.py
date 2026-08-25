"""
CLI for CO-RADS Chest CT Agent: COVID-19 Reporting and Data System tool.
"""
import argparse
import json
import sys
from corads_chest_ct_agent.models import ChestCTFindings, LobarInvolvement, CORADSLevel
from corads_chest_ct_agent.engine import assess_corads, calculate_severity_score, LEVEL_INFO


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="corads-chest-ct-agent",
        description="CO-RADS chest CT assessment tool for COVID-19 probability.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # assess command
    p_assess = subparsers.add_parser("assess", help="Assess chest CT findings")
    p_assess.add_argument("--ggo", action="store_true", help="Ground-glass opacities present")
    p_assess.add_argument("--peripheral", action="store_true", help="Peripheral distribution")
    p_assess.add_argument("--posterior", action="store_true", help="Posterior distribution")
    p_assess.add_argument("--bilateral", action="store_true", help="Bilateral involvement")
    p_assess.add_argument("--multifocal", action="store_true", help="Multifocal involvement")
    p_assess.add_argument("--crazy-paving", action="store_true", help="Crazy paving pattern")
    p_assess.add_argument("--consolidation", action="store_true", help="Consolidation present")
    p_assess.add_argument("--consolidation-posterior", action="store_true", help="Posterior consolidation")
    p_assess.add_argument("--tree-in-bud", action="store_true", help="Tree-in-bud pattern (atypical)")
    p_assess.add_argument("--cavitation", action="store_true", help="Cavitation (atypical)")
    p_assess.add_argument("--lymphadenopathy", action="store_true", help="Lymphadenopathy (atypical)")
    p_assess.add_argument("--pleural-effusion", action="store_true", help="Pleural effusion (atypical)")
    p_assess.add_argument("--rt-pcr-positive", action="store_true", help="RT-PCR confirmed COVID-19")
    p_assess.add_argument("--rum", type=int, default=0, help="Right upper lobe involvement (0-5)")
    p_assess.add_argument("--rmm", type=int, default=0, help="Right middle lobe involvement (0-5)")
    p_assess.add_argument("--rlm", type=int, default=0, help="Right lower lobe involvement (0-5)")
    p_assess.add_argument("--lum", type=int, default=0, help="Left upper lobe involvement (0-5)")
    p_assess.add_argument("--llm", type=int, default=0, help="Left lower lobe involvement (0-5)")
    p_assess.add_argument("--json", action="store_true", help="Output as JSON")

    # severity command
    p_severity = subparsers.add_parser("severity", help="Calculate CT severity score only")
    p_severity.add_argument("--rum", type=int, required=True, help="Right upper lobe (0-5)")
    p_severity.add_argument("--rmm", type=int, required=True, help="Right middle lobe (0-5)")
    p_severity.add_argument("--rlm", type=int, required=True, help="Right lower lobe (0-5)")
    p_severity.add_argument("--lum", type=int, required=True, help="Left upper lobe (0-5)")
    p_severity.add_argument("--llm", type=int, required=True, help="Left lower lobe (0-5)")

    # info command
    p_info = subparsers.add_parser("info", help="Show CO-RADS level information")
    p_info.add_argument("level", nargs="?", type=int, default=None, help="Level (1-6)")

    args = parser.parse_args(argv)

    if args.command == "assess":
        lobar = LobarInvolvement(
            right_upper=args.rum,
            right_middle=args.rmm,
            right_lower=args.rlm,
            left_upper=args.lum,
            left_lower=args.llm,
        )
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
            rt_pcr_positive=args.rt_pcr_positive,
            lobar_involvement=lobar,
        )
        result = assess_corads(findings)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print("=" * 60)
            print(f"  CO-RADS Assessment")
            print("=" * 60)
            print(f"  CO-RADS Level: {result.corads_level} - {result.corads_label}")
            print(f"  Probability:   {result.probability}")
            print(f"  Description:   {result.description}")
            if result.ct_severity_score is not None:
                print(f"  CT Severity:   {result.ct_severity_score}/25")
            if result.typical_features:
                print(f"\n  Typical features:")
                for f in result.typical_features:
                    print(f"    + {f}")
            if result.atypical_features:
                print(f"\n  Atypical features:")
                for f in result.atypical_features:
                    print(f"    - {f}")
            if result.notes:
                print(f"\n  Notes:")
                for n in result.notes:
                    print(f"    * {n}")
            print("=" * 60)
        return 0

    elif args.command == "severity":
        lobar = LobarInvolvement(
            right_upper=args.rum,
            right_middle=args.rmm,
            right_lower=args.rlm,
            left_upper=args.lum,
            left_lower=args.llm,
        )
        score = calculate_severity_score(lobar)
        print(f"CT Severity Score: {score}/25")
        print(f"  Right upper:   {args.rum}/5")
        print(f"  Right middle:  {args.rmm}/5")
        print(f"  Right lower:   {args.rlm}/5")
        print(f"  Left upper:    {args.lum}/5")
        print(f"  Left lower:    {args.llm}/5")
        return 0

    elif args.command == "info":
        if args.level:
            try:
                level = CORADSLevel(args.level)
            except ValueError:
                print(f"Invalid level: {args.level}. Must be 1-6.", file=sys.stderr)
                return 1
            info = LEVEL_INFO[level]
            print(f"CO-RADS {level.value}: {info['label']}")
            print(f"  {info['description']}")
            print(f"  Probability: {info['probability']}")
        else:
            for level in CORADSLevel:
                info = LEVEL_INFO[level]
                print(f"CO-RADS {level.value}: {info['label']}")
                print(f"  {info['description']}")
                print(f"  Probability: {info['probability']}")
                print()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
