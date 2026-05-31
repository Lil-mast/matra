import json

fhir_file = r"tools\output\fhir\Abe604_Dickinson688_c626fb0f-4c05-7690-9e55-837ac32e7dbd.json"
f = json.load(open(fhir_file))

print("=== CONDITION SAMPLE ===")
for e in f.get('entry',[]):
    res = e.get('resource',{})
    if res.get('resourceType') == 'Condition':
        print(json.dumps(res, indent=2)[:800])
        break

print("\n=== OBSERVATION SAMPLE ===")
for e in f.get('entry',[]):
    res = e.get('resource',{})
    if res.get('resourceType') == 'Observation':
        print(json.dumps(res, indent=2)[:800])
        break

print("\n=== ENCOUNTER SAMPLE ===")
for e in f.get('entry',[]):
    res = e.get('resource',{})
    if res.get('resourceType') == 'Encounter':
        print(json.dumps(res, indent=2)[:800])
        break
