from pathlib import Path
import re
text = Path('doc_preprocessor_hybrid/rule_parser.py').read_text(encoding='utf-8')
print(re.findall(r"base\.description\.split\("".*?""\)", text))
