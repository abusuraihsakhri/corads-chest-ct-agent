# CO-RADS Chest CT Agent

A small, deterministic implementation of structured CO-RADS decision support plus a five-lobe CT severity score (0–25).

> **Important:** CO-RADS is a radiologist reporting scheme. This repository provides a simplified rule-based approximation for research, education, and software testing. It is not a diagnostic device and does not replace CT interpretation, microbiologic testing, or clinical judgment.

## What it provides

- CO-RADS 1–5 structured suspicion categories with CO-RADS 6 for reported RT-PCR confirmation.
- Five-lobe semiquantitative CT severity scoring from 0 to 25.
- Python API and command-line interface.
- Optional FastAPI service.
- Static browser application that performs calculations locally and is suitable for GitHub Pages.
- Automated tests across supported Python versions.

The CO-RADS rules are based on the original Dutch Radiological Society publication by Prokop et al. The browser and Python implementations intentionally use the same limited structured feature set; they cannot represent every morphology or distributional nuance in the original scheme.

## Browser application

Open `web/index.html` directly in a modern browser, or serve the `web/` directory with any static HTTP server. No server-side Python is required and no data is transmitted by the application itself.

Do not enter patient identifiers. The browser interface intentionally contains no patient-identity fields.

## Python CLI

```bash
python -m pip install .
corads-chest-ct-agent info
corads-chest-ct-agent assess --ggo --peripheral --bilateral --multifocal
corads-chest-ct-agent severity --rum 3 --rmm 4 --rlm 5 --lum 3 --llm 4
```

JSON output:

```bash
corads-chest-ct-agent assess --ggo --peripheral --bilateral --multifocal --json
```

## Python API

```python
from corads_chest_ct_agent import ChestCTFindings, assess_corads

findings = ChestCTFindings(
    ground_glass_opacities=True,
    ggo_peripheral_distribution=True,
    ggo_bilateral=True,
    ggo_multifocal=True,
)

result = assess_corads(findings)
print(result.to_dict())
```

## Optional REST API

```bash
python -m pip install ".[api]"
uvicorn corads_chest_ct_agent.server:app --host 127.0.0.1 --port 8000
```

Endpoints:

- `GET /health`
- `POST /api/assess`
- `GET /docs`

Docker is also supported:

```bash
docker build -t corads-chest-ct-agent .
docker run --rm -p 8000:8000 corads-chest-ct-agent
```

## Development and testing

```bash
python -m pip install -e ".[api,test]"
python -m pytest -q
python -m compileall -q .
```

The optional legacy `agents/` subsystem uses an in-memory HMAC audit chain. Set `AUDIT_SECRET_KEY` before using that subsystem. Its identifier-pattern guard is a narrow screening utility, **not** a HIPAA de-identification implementation.

## CT severity score

Each lobe is scored 0–5 by estimated involvement:

- 0: none
- 1: <5%
- 2: 5–25%
- 3: 26–50%
- 4: 51–75%
- 5: >75%

The five lobar scores are summed to a total from 0 to 25.

## References

- Prokop M, et al. *CO-RADS: A Categorical CT Assessment Scheme for Patients Suspected of Having COVID-19—Definition and Evaluation.* Radiology. 2020;296(2):E97-E104. doi:10.1148/radiol.2020201473.
- Francone M, et al. *Chest CT score in COVID-19 patients: correlation with disease severity and short-term prognosis.* Eur Radiol. 2020.

## Browser compatibility

The static application uses standard HTML, CSS, and JavaScript and is intended for current versions of Chrome, Edge, Firefox, and Safari.

## License

MIT. See [LICENSE](LICENSE).
