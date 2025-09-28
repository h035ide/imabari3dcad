import json
from pathlib import Path
from collections import defaultdict

structured_path = Path('doc_preprocessor_hybrid/out/structured_api.json')
with structured_path.open('r', encoding='utf-8') as f:
    structured = json.load(f)
entries = structured.get('api_entries', [])
structured_methods = {entry['name']: entry for entry in entries}

triples_path = Path('extracted_triples_20250928_181150.json')
with triples_path.open('r', encoding='utf-8') as f:
    triples_data = json.load(f)
triples = triples_data['sources']['api_specifications']['triples']
method_nodes = {t['source'] for t in triples if t.get('source_type') == 'Method'}

structured_only = sorted(set(structured_methods) - method_nodes)
triples_only = sorted(method_nodes - set(structured_methods))

structured_params = {
    name: {p.get('name') for p in entry.get('parameters', []) if p.get('name')}
    for name, entry in structured_methods.items()
}
triples_params = defaultdict(set)
for t in triples:
    if t.get('label') == 'HAS_PARAMETER':
        source = t.get('source')
        target = t.get('target')
        if not source or not target:
            continue
        if source not in method_nodes:
            continue
        param_name = target.split('_', 1)[-1]
        triples_params[source].add(param_name)

differences = []
for name in structured_methods:
    s = structured_params.get(name, set())
    t = triples_params.get(name, set())
    missing = sorted(s - t)
    extra = sorted(t - s)
    if missing or extra:
        differences.append((name, missing, extra))

print('structured_method_count', len(structured_methods))
print('triple_method_count', len(method_nodes))
print('structured_only_count', len(structured_only))
print('structured_only_sample', structured_only[:10])
print('triples_only_count', len(triples_only))
print('triples_only_sample', triples_only[:10])
print('param_mismatch_count', len(differences))
for name, missing, extra in differences[:10]:
    print('diff', name, 'missing', missing[:5], 'extra', extra[:5])
