# CO-RADS Chest CT Agent

> **CO-RADS** COVID-19 Reporting and Data System for chest CT assessment.

## Overview

Implements CO-RADS (COVID-19 Reporting and Data System) for assessing chest CT findings and assigning probability levels for COVID-19 pneumonia. Includes CT severity scoring (0-25) based on lobar involvement.

## CO-RADS Levels

| Level | Label | Probability | Description |
|-------|-------|-------------|-------------|
| **1** | Very low | Very low | Normal or non-infectious finding |
| **2** | Low | Low | Findings consistent with other infection |
| **3** | Equivocal | Equivocal | Features compatible with COVID-19 but also other disease |
| **4** | High | High | GGO peripheral/posterior, bilateral, multifocal |
| **5** | Very high | Very high | Extensive bilateral GGO, crazy paving, posterior/peripheral |
| **6** | Confirmed | Confirmed | RT-PCR positive for COVID-19 |

## CT Severity Score

Lobar involvement scored 0-5 per lobe (total 0-25):
- 0: No involvement
- 1: <5% involvement
- 2: 5-25%
- 3: 26-50%
- 4: 51-75%
- 5: >75%

## Typical vs Atypical Features

**Typical COVID-19:**
- Ground-glass opacities (GGO)
- Peripheral/posterior distribution
- Bilateral, multifocal
- Crazy paving pattern
- Posterior consolidation

**Atypical (suggest other cause):**
- Tree-in-bud pattern
- Cavitation
- Lymphadenopathy
- Pleural effusion
- Upper lobe predominance

## CLI Usage

```bash
# Assess typical COVID-19 pattern
python cli.py assess --ggo --peripheral --posterior --bilateral --multifocal

# Assess with severity scoring
python cli.py assess --ggo --peripheral --posterior --bilateral --multifocal --crazy-paving --rum 3 --rmm 4 --rlm 5 --lum 3 --llm 4

# RT-PCR confirmed
python cli.py assess --rt-pcr-positive

# Calculate severity only
python cli.py severity --rum 3 --rmm 4 --rlm 5 --lum 3 --llm 4

# JSON output
python cli.py assess --ggo --peripheral --posterior --bilateral --multifocal --json

# Show level info
python cli.py info
python cli.py info 5
```

## Python API

```python
from corads_chest_ct_agent import ChestCTFindings, LobarInvolvement, assess_corads

findings = ChestCTFindings(
    ground_glass_opacities=True,
    ggo_peripheral_distribution=True,
    ggo_posterior_distribution=True,
    ggo_bilateral=True,
    ggo_multifocal=True,
    crazy_paving=True,
    lobar_involvement=LobarInvolvement(3, 4, 5, 3, 4),
)

result = assess_corads(findings)
print(f"CO-RADS {result.corads_level}: {result.corads_label}")
print(f"CT Severity: {result.ct_severity_score}/25")
```

## Testing

```bash
python -m pytest tests/ -v
```

## License

MIT License. See [LICENSE](LICENSE).
