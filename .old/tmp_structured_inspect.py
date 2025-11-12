import json
from pathlib import Path
structured_path = Path('doc_preprocessor_hybrid/out/structured_api.json')
with structured_path.open('r', encoding='utf-8') as f:
    data = json.load(f)
print(type(data))
print(data.keys())
entries = data.get('entries', [])
print(len(entries))
if entries:
    first = entries[0]
    print(first.keys())
    print(first.get('name'))
    params = first.get('parameters')
    if params:
        print(params[0])

