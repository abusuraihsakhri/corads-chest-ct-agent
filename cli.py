"""Compatibility wrapper for the installed CO-RADS CLI."""
from corads_chest_ct_agent.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
