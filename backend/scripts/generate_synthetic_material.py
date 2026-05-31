"""
Code to generate a synthetic maternal dataset from Synthea CSV output.

Reads Synthea CSV output and produces synthetic_maternal.csv
with the maternal intake schema used by the referral model.

Usage:
    python backend/scripts/generate_synthetic_material.py \
        --synthea-dir ./output/csv \
        --out ./backend/model/data/synthetic_maternal.csv

Requirements:
    pip install pandas
"""

import argparse
import os
import re
import pandas as pd
from datetime import datetime

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_OUT = os.path.join(REPO_ROOT, "backend", "model", "data", "synthetic_maternal.csv")

# ── LOINC codes we care about ─────────────────────────────────────────────────
LOINC_SYSTOLIC   = "8480-6"
LOINC_DIASTOLIC  = "8462-4"
LOINC_HEART_RATE = "8867-4"
LOINC_TEMP       = "8310-5"   # body temperature

# ── Condition keywords (SNOMED descriptions in Synthea) ───────────────────────
BLEEDING_KEYWORDS     = ["hemorrhage", "bleeding", "antepartum", "postpartum", "placenta previa",
                          "abruption", "blood loss"]
CONVULSION_KEYWORDS   = ["eclampsia", "seizure", "convulsion"]
ANEMIA_KEYWORDS       = ["anemia", "anaemia", "iron deficiency"]
FETAL_MVMT_KEYWORDS   = ["decreased fetal movement", "reduced fetal movement", "fetal movement"]

PREGNANCY_KEYWORDS    = ["pregnancy", "gravid", "prenatal", "antenatal",
                          "obstetric", "gestation", "trimester"]

# ── WHO-inspired referral rules ───────────────────────────────────────────────
def derive_label(row: dict) -> str:
    """
    Returns one of:
        emergency_referral  – life-threatening condition
        urgent_referral     – needs care within hours
        routine_referral    – scheduled follow-up
        no_referral         – manage at facility / home
    """
    # Emergency
    if row.get("convulsions"):
        return "emergency_referral"
    if row.get("bleeding") and (row.get("systolic_bp") or 0) > 160:
        return "emergency_referral"
    if row.get("bleeding"):
        return "emergency_referral"
    sbp = row.get("systolic_bp") or 0
    dbp = row.get("diastolic_bp") or 0
    if sbp >= 160 or dbp >= 110:
        return "emergency_referral"

    # Urgent
    if sbp >= 140 or dbp >= 90:
        return "urgent_referral"
    if row.get("fever") and row.get("anemia_signs"):
        return "urgent_referral"
    if row.get("reduced_fetal_movement"):
        return "urgent_referral"
    if row.get("anemia_signs"):
        return "urgent_referral"

    # Routine
    if row.get("fever"):
        return "routine_referral"

    return "no_referral"


def flag_keywords(text: str, keywords: list) -> bool:
    text = text.lower()
    return any(kw in text for kw in keywords)


def load_csv(path: str, label: str) -> pd.DataFrame:
    if not os.path.exists(path):
        print(f"  ⚠️  {label} not found at {path} — skipping.")
        return pd.DataFrame()
    print(f"  ✔  Loading {label} …")
    return pd.read_csv(path, low_memory=False)


def main(synthea_dir: str, out_path: str):
    print("\n🔄  Loading Synthea CSVs …")

    patients    = load_csv(f"{synthea_dir}/patients.csv",    "patients.csv")
    conditions  = load_csv(f"{synthea_dir}/conditions.csv",  "conditions.csv")
    encounters  = load_csv(f"{synthea_dir}/encounters.csv",  "encounters.csv")
    observations= load_csv(f"{synthea_dir}/observations.csv","observations.csv")

    if patients.empty:
        raise FileNotFoundError(f"patients.csv missing in {synthea_dir}")

    # ── Step 1: Age ───────────────────────────────────────────────────────────
    print("\n📅  Calculating age …")
    today = datetime.today()
    patients["BIRTHDATE"] = pd.to_datetime(patients["BIRTHDATE"], errors="coerce")
    patients["age"] = ((today - patients["BIRTHDATE"]).dt.days / 365.25).round().astype("Int64")

    if "GENDER" in patients.columns:
        patients["GENDER"] = patients["GENDER"].astype(str).str.upper()
        patients = patients[patients["GENDER"].isin({"F", "FEMALE"})]

    patients = patients[patients["age"].between(15, 48)]
    patient_ids = set(patients["Id"])

    # ── Step 2: Parity (count distinct pregnancy conditions/encounters) ────────
    print("🤰  Estimating parity …")
    parity_map = {}

    if not conditions.empty and "DESCRIPTION" in conditions.columns:
        preg_conds = conditions[
            conditions["DESCRIPTION"].str.lower().str.contains(
                "|".join(PREGNANCY_KEYWORDS), na=False
            )
        ]
        if "ENCOUNTER" in preg_conds.columns:
            parity_map.update(
                preg_conds.groupby("PATIENT")["ENCOUNTER"].nunique().clip(upper=8).to_dict()
            )
        else:
            parity_map.update(
                preg_conds.groupby("PATIENT")["Id"].nunique().clip(upper=8).to_dict()
            )

    if not encounters.empty and "DESCRIPTION" in encounters.columns:
        preg_enc = encounters[
            encounters["DESCRIPTION"].str.lower().str.contains(
                "|".join(PREGNANCY_KEYWORDS), na=False
            )
        ]
        for pid, cnt in preg_enc.groupby("PATIENT")["Id"].nunique().items():
            parity_map[pid] = max(parity_map.get(pid, 0), min(cnt, 8))

    # ── Step 3: Observations (BP, HR, Temp) ───────────────────────────────────
    print("🩺  Extracting observations …")

    def obs_mean(code: str) -> pd.Series:
        if observations.empty or "CODE" not in observations.columns:
            return pd.Series(dtype=float)
        subset = observations[observations["CODE"].astype(str) == code]
        subset = subset.copy()
        subset["VALUE"] = pd.to_numeric(subset["VALUE"], errors="coerce")
        return subset.groupby("PATIENT")["VALUE"].mean()

    systolic_map  = obs_mean(LOINC_SYSTOLIC).to_dict()
    diastolic_map = obs_mean(LOINC_DIASTOLIC).to_dict()
    hr_map        = obs_mean(LOINC_HEART_RATE).to_dict()
    temp_map      = obs_mean(LOINC_TEMP).to_dict()

    # ── Step 4: Condition flags ───────────────────────────────────────────────
    print("🔍  Flagging conditions …")

    def condition_flag(keywords: list) -> dict:
        if conditions.empty or "DESCRIPTION" not in conditions.columns:
            return {}
        mask = conditions["DESCRIPTION"].str.lower().str.contains(
            "|".join(keywords), na=False
        )
        return conditions[mask].groupby("PATIENT").size().gt(0).to_dict()

    bleeding_map  = condition_flag(BLEEDING_KEYWORDS)
    convulse_map  = condition_flag(CONVULSION_KEYWORDS)
    anemia_map    = condition_flag(ANEMIA_KEYWORDS)
    fetal_mv_map  = condition_flag(FETAL_MVMT_KEYWORDS)

    # ── Step 5: Gestational age (if present in observations) ─────────────────
    # LOINC 49051-6 = gestational age in weeks
    gest_map = obs_mean("49051-6").to_dict()

    # ── Step 6: Assemble rows ─────────────────────────────────────────────────
    print("🧩  Assembling final dataset …")
    rows = []
    for _, pat in patients.iterrows():
        pid = pat["Id"]
        sbp  = systolic_map.get(pid)
        dbp  = diastolic_map.get(pid)
        pulse = hr_map.get(pid)
        temp = temp_map.get(pid)

        if sbp is None:
            sbp = 115.0
        if dbp is None:
            dbp = 75.0
        if pulse is None:
            pulse = 82.0
        if temp is None:
            temp = 36.7

        fever = bool(temp and temp > 38.0)

        row = {
            "patient_id":             pid,
            "age":                    pat["age"],
            "parity":                 min(parity_map.get(pid, 0), 8),
            "gestational_age_weeks":  round(gest_map[pid], 1) if pid in gest_map else None,
            "systolic_bp":            round(sbp,  1),
            "diastolic_bp":           round(dbp,  1),
            "pulse":                  round(pulse, 1),
            "temperature":            round(temp, 1),
            "bleeding":               int(bleeding_map.get(pid, False)),
            "fever":                  int(fever),
            "convulsions":            int(convulse_map.get(pid, False)),
            "reduced_fetal_movement": int(fetal_mv_map.get(pid, False)),
            "anemia_signs":           int(anemia_map.get(pid, False)),
        }
        row["referral_label"] = derive_label(row)
        rows.append(row)

    df = pd.DataFrame(rows, columns=[
        "patient_id", "age", "parity", "gestational_age_weeks",
        "systolic_bp", "diastolic_bp", "pulse", "temperature",
        "bleeding", "fever", "convulsions", "reduced_fetal_movement",
        "anemia_signs", "referral_label"
    ])

    # ── Step 7: Save ──────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\n✅  Done! {len(df)} patients → {out_path}")
    print(df["referral_label"].value_counts().to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthea-dir", default="./output/csv",
                        help="Path to Synthea's output/csv directory")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="Output CSV path")
    args = parser.parse_args()
    main(args.synthea_dir, args.out)
