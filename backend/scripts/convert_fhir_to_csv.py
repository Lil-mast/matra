"""
Convert Synthea FHIR JSON output to CSV format for synthetic maternal dataset generation.

Usage:
    python convert_fhir_to_csv.py --fhir-dir ./tools/output/fhir --csv-dir ./output/csv
"""

import argparse
import json
import os
import sys
from datetime import datetime
import pandas as pd


def extract_from_fhir(fhir_dir):
    """Extract patients, conditions, observations, and encounters from FHIR files."""
    
    patients_data = {}
    conditions_data = []
    observations_data = []
    encounters_data = []
    
    # Get file list
    try:
        json_files = [f for f in os.listdir(fhir_dir) if f.endswith('.json')]
        json_files.sort()
    except OSError as e:
        print(f"❌ Error reading directory {fhir_dir}: {e}")
        return patients_data, conditions_data, observations_data, encounters_data
    
    print(f"📂 Found {len(json_files)} FHIR files in {fhir_dir}\n")
    
    for idx, filename in enumerate(json_files):
        # Show progress every 100 files
        if (idx + 1) % 100 == 0:
            print(f"⏳ Processing... {idx + 1}/{len(json_files)}")
        
        filepath = os.path.join(fhir_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                bundle = json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError) as e:
            continue
        
        if bundle.get("resourceType") != "Bundle":
            continue
        
        # Extract resources from bundle
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            res_type = resource.get("resourceType")
            
            if res_type == "Patient":
                patient_id = resource.get("id")
                if patient_id:
                    birthdate = None
                    gender = None
                    
                    # Extract birthDate
                    if "birthDate" in resource:
                        birthdate = resource["birthDate"]
                    
                    # Extract gender and normalize to F/M
                    if "gender" in resource:
                        raw_gender = resource["gender"].strip().upper()
                        if raw_gender in {"FEMALE", "F"}:
                            gender = "F"
                        elif raw_gender in {"MALE", "M"}:
                            gender = "M"
                        else:
                            gender = raw_gender
                    
                    patients_data[patient_id] = {
                        "Id": patient_id,
                        "BIRTHDATE": birthdate,
                        "GENDER": gender,
                    }
            
            elif res_type == "Condition":
                condition_id = resource.get("id")
                patient_id = None
                description = None
                code = None
                encounter_ref = None

                # Extract patient reference
                if "subject" in resource:
                    subject = resource["subject"].get("reference", "")
                    if "Patient/" in subject:
                        patient_id = subject.split("/")[-1]
                    elif "urn:uuid:" in subject:
                        patient_id = subject.split(":")[-1]

                # Extract code and description
                if "code" in resource:
                    code_obj = resource["code"]
                    if "coding" in code_obj and code_obj["coding"]:
                        code = code_obj["coding"][0].get("code", "")
                    if "text" in code_obj:
                        description = code_obj["text"]

                # Extract encounter reference for parity calculation
                if "encounter" in resource and isinstance(resource["encounter"], dict):
                    encounter = resource["encounter"].get("reference", "")
                    if "Encounter/" in encounter:
                        encounter_ref = encounter.split("/")[-1]
                    elif "urn:uuid:" in encounter:
                        encounter_ref = encounter.split(":")[-1]

                if patient_id and description:
                    conditions_data.append({
                        "Id": condition_id,
                        "PATIENT": patient_id,
                        "DESCRIPTION": description,
                        "CODE": code,
                        "ENCOUNTER": encounter_ref,
                    })

            elif res_type == "Observation":
                observation_id = resource.get("id")
                patient_id = None
                code = None
                value = None

                # Extract patient reference
                if "subject" in resource:
                    subject = resource["subject"].get("reference", "")
                    if "Patient/" in subject:
                        patient_id = subject.split("/")[-1]
                    elif "urn:uuid:" in subject:
                        patient_id = subject.split(":")[-1]

                # Extract code (LOINC)
                if "code" in resource:
                    code_obj = resource["code"]
                    if "coding" in code_obj and code_obj["coding"]:
                        code = code_obj["coding"][0].get("code", "")

                # Extract value
                if "valueQuantity" in resource:
                    value = resource["valueQuantity"].get("value")

                if patient_id and code and value is not None:
                    observations_data.append({
                        "Id": observation_id,
                        "PATIENT": patient_id,
                        "CODE": code,
                        "VALUE": value,
                    })

            elif res_type == "Encounter":
                encounter_id = resource.get("id")
                patient_id = None
                description = None
                
                # Extract patient reference
                if "subject" in resource:
                    subject = resource["subject"].get("reference", "")
                    # Handle both Patient/ and urn:uuid: formats
                    if "Patient/" in subject:
                        patient_id = subject.split("/")[-1]
                    elif "urn:uuid:" in subject:
                        patient_id = subject.split(":")[-1]
                
                # Extract description from type or reason
                if "type" in resource and resource["type"]:
                    type_obj = resource["type"][0]
                    if "text" in type_obj:
                        description = type_obj["text"]
                    elif "coding" in type_obj and type_obj["coding"]:
                        description = type_obj["coding"][0].get("display", "")
                
                if patient_id:
                    encounters_data.append({
                        "Id": encounter_id,
                        "PATIENT": patient_id,
                        "DESCRIPTION": description or "Encounter",
                    })
    
    return patients_data, conditions_data, observations_data, encounters_data


def save_to_csv(csv_dir, patients_data, conditions_data, observations_data, encounters_data):
    """Save extracted data to CSV files."""
    
    os.makedirs(csv_dir, exist_ok=True)
    
    # Save patients
    if patients_data:
        df_patients = pd.DataFrame(list(patients_data.values()))
        df_patients.to_csv(os.path.join(csv_dir, "patients.csv"), index=False)
        print(f"✅ Saved {len(df_patients)} patients to patients.csv")
    
    # Save conditions
    if conditions_data:
        df_conditions = pd.DataFrame(conditions_data)
        df_conditions.to_csv(os.path.join(csv_dir, "conditions.csv"), index=False)
        print(f"✅ Saved {len(df_conditions)} conditions to conditions.csv")
    
    # Save observations
    if observations_data:
        df_observations = pd.DataFrame(observations_data)
        df_observations.to_csv(os.path.join(csv_dir, "observations.csv"), index=False)
        print(f"✅ Saved {len(df_observations)} observations to observations.csv")
    
    # Save encounters
    if encounters_data:
        df_encounters = pd.DataFrame(encounters_data)
        df_encounters.to_csv(os.path.join(csv_dir, "encounters.csv"), index=False)
        print(f"✅ Saved {len(df_encounters)} encounters to encounters.csv")


def main(fhir_dir, csv_dir):
    print(f"\n🔄 Converting FHIR JSON to CSV format…\n")
    
    patients_data, conditions_data, observations_data, encounters_data = extract_from_fhir(fhir_dir)
    
    print(f"\n📊 Extracted:")
    print(f"   - {len(patients_data)} patients")
    print(f"   - {len(conditions_data)} conditions")
    print(f"   - {len(observations_data)} observations")
    print(f"   - {len(encounters_data)} encounters")
    
    save_to_csv(csv_dir, patients_data, conditions_data, observations_data, encounters_data)
    
    print(f"\n✅ FHIR conversion complete! CSV files saved to {csv_dir}")
    print(f"   Next step: python generate_synthetic_material.py --synthea-dir {csv_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Synthea FHIR JSON to CSV format")
    parser.add_argument("--fhir-dir", default="./tools/output/fhir",
                        help="Path to Synthea's output/fhir directory")
    parser.add_argument("--csv-dir", default="./output/csv",
                        help="Output CSV directory")
    args = parser.parse_args()
    main(args.fhir_dir, args.csv_dir)
