# Synthea Integration Guidell

This guide explains how to generate synthetic maternal health records using Synthea, transform outputs into a CSV matching this project's intake schema, and integrate the synthetic data into the model training and tests.

## Overview

Synthea is an open-source synthetic patient generator that produces realistic, but non-identifiable, clinical records. Use it to create sample maternal health datasets for development, demoing triage logic, and training lightweight models without needing real PHI.

## Prerequisites

- Java 11+ installed
- `git` and `unzip` available
- Python 3.8+ and project `requirements.txt` installed for transformation scripts

## Steps

1. Download Synthea

```bash
# from project root
mkdir -p tools
cd tools
wget https://github.com/synthetichealth/synthea/releases/latest/download/synthea-with-dependencies.jar -O synthea.jar
```

2. Generate synthetic patients with pregnancy module

Run Synthea with a population size. Example: 1000 patients.

```bash
java -jar synthea.jar -p 1000
```

Synthea outputs `output/fhir` and `output/csv` directories (FHIR resources + CSVs).

3. Extract pregnancy-related records

Synthea's pregnancy module encodes pregnancy-related encounters and conditions. Use the FHIR outputs or CSV exports. We recommend using `output/csv/observations.csv` and `output/csv/conditions.csv` along with `patients.csv` and `encounters.csv`.

4. Map fields to intake schema

Create a mapping between Synthea fields and your intake fields:

- `age` ← calculate from `birthdate` in `patients.csv`
- `parity` ← approximate from pregnancy `conditions`/`encounters` or use generated `pregnancy` events count
- `blood_pressure_systolic` / `blood_pressure_diastolic` ← filter `observations.csv` for LOINC codes for blood pressure
- `pulse` ← heart rate observations
- `temperature` / `fever` ← temperature observations
- `bleeding`, `convulsions`, `reduced_fetal_movement`, `anemia_signs` ← infer from `conditions.csv` or keywords in condition codes
- `gestational_age_weeks` ← if available from pregnancy encounters; otherwise infer or leave null

5. Convert to CSV toy schema

Write a Python script to read Synthea CSVs and emit `synthetic_maternal.csv` with schema:

```
patient_id,age,parity,gestational_age_weeks,systolic_bp,diastolic_bp,pulse,temperature,bleeding,fever,convulsions,reduced_fetal_movement,anemia_signs,referral_label
```

For `referral_label`, you can derive labels using WHO-like rules (e.g., any severe bleeding->`emergency_referral`).

6. Use dataset in repo

- Place `synthetic_maternal.csv` in `backend/model/data/`.
- Update `backend/model/train.py` to read `backend/model/data/synthetic_maternal.csv` when present.
- Add a small unit test under `backend/tests/` to assert the generator script produces expected columns.

## Tuning and realistic distributions

- Adjust Synthea configuration for local context and prevalence (Synthea allows configuration of modules and demographic distributions).
- For small hackathon runs, 500–2,000 patients is sufficient.

## Notes on ethics and documentation

- Document in `DATA_README.md` that this dataset is synthetic and not derived from any real patient's PHI.
- Explain mapping decisions, limitations, and where clinical judgement is required.

## Troubleshooting

- If Synthea fails due to Java version, ensure Java 11+ is used.
- For missing pregnancy codes, enable the pregnancy module explicitly in Synthea config or use a larger population to increase events.

---

Next steps: run Synthea, run the transformation script at `backend/scripts/generate_synthetic_material.py`, and integrate the generated CSV into `backend/model/train.py`. If you want, I can add the generator script and wiring to `backend/model/train.py` now.