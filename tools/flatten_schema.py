"""Flatten v1.2 schema $defs to remove $ref dependencies."""
import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent.parent / "spec"

with open(SCHEMA_DIR / 'v1.2.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Flatten: merge baseEntry properties into each $def
base_entry = schema['$defs']['baseEntry']
base_props = base_entry['properties']
flat_defs = {}

for name, defn in schema['$defs'].items():
    if name == 'baseEntry':
        continue

    # Start with baseEntry properties
    flat = {
        'type': 'object',
        'properties': dict(base_props),
        'required': []
    }

    # Merge type-specific properties from allOf
    if 'allOf' in defn:
        for part in defn['allOf']:
            if '$ref' in part:
                continue  # Skip $ref, we already have baseEntry
            if 'properties' in part:
                flat['properties'].update(part['properties'])
            if 'required' in part:
                flat['required'].extend(part['required'])

    flat_defs[name] = flat

# Save flattened entry schema
entry_schema = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'title': 'AgentSON v1.2 Entry Validator',
    'type': 'object',
    'oneOf': list(flat_defs.values())
}

with open(SCHEMA_DIR / 'v1.2-entries.json', 'w', encoding='utf-8') as f:
    json.dump(entry_schema, f, indent=2)

print(f'Flattened {len(flat_defs)} definitions')
for name, defn in flat_defs.items():
    print(f'  {name}: required={defn.get("required", [])}')
