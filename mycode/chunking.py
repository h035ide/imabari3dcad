# mycode/chunking.py
"""
This module handles the "chunking" of the proprietary api.txt format.
In this context, "chunking" means parsing the file into structured
documents, where each document represents a single API method.
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document

# --- Constants ---

DATA_DIR = Path("data")

API_TXT_CANDIDATES = [
    DATA_DIR / "src" / "api.txt",
    Path("/mnt/data/api.txt"),
    Path("api.txt"),
    DATA_DIR / "api.txt",
]

API_ARG_TXT_CANDIDATES = [
    DATA_DIR / "src" / "api_arg.txt",
    Path("/mnt/data/api_arg.txt"),
    Path("api_arg.txt"),
    DATA_DIR / "api_arg.txt",
]

# --- Public API ---


def get_api_documents() -> List[Document]:
    """
    Reads and parses api.txt and returns a list of LangChain Documents.

    This is the main entry point for this module. Each Document represents
    one API method, with its content being a structured representation
    of the method's details and metadata containing the object and method name.
    """
    api_text = _read_api_text()
    api_entries = _parse_api_specs(api_text)

    docs: List[Document] = []
    for entry in api_entries:
        content_parts = [
            f"オブジェクト: {entry['object']}",
            f"メソッド名: {entry['name']}",
            f"説明: {entry['title_jp']}",
            f"返り値: {entry['return_desc']}",
        ]
        if entry['params']:
            param_texts = [f"- {p['name']} ({p['type']}): {p['description']}" for p in entry['params']]
            content_parts.append("パラメータ:\n" + "\n".join(param_texts))

        content = "\n".join(content_parts)

        # Create a unique ID for each document to ensure consistency
        doc_id = f"{entry['object']}_{entry['name']}"

        metadata = {
            "object": entry['object'],
            "method_name": entry['name'],
            "doc_id": doc_id
        }

        docs.append(Document(page_content=content, metadata=metadata))

    return docs


def get_api_entries() -> List[Dict[str, Any]]:
    """Reads and parses api.txt into a list of structured dictionaries."""
    api_text = _read_api_text()
    return _parse_api_specs(api_text)


def get_type_descriptions() -> Dict[str, str]:
    """Reads and parses api_arg.txt into a dictionary of type descriptions."""
    api_arg_text = _read_api_arg_text()
    return _parse_data_type_descriptions(api_arg_text)


# --- Internal Helper Functions (previously in ingest.py) ---

def _read_api_text() -> str:
    """Reads api.txt from candidate paths."""
    for p in API_TXT_CANDIDATES:
        if p.exists():
            return _normalize_text(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("api.txt could not be found.")


def _read_api_arg_text() -> str:
    """Reads api_arg.txt from candidate paths."""
    for p in API_ARG_TXT_CANDIDATES:
        if p.exists():
            return _normalize_text(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("api_arg.txt could not be found.")


def _normalize_text(text: str) -> str:
    """Normalizes whitespace, newlines, and removes BOM."""
    text = text.replace("\ufeff", "")  # BOM
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = text.replace("\t", " ")
    text = re.sub(r"[ \u00A0\u3000]+", " ", text)
    return text


def _to_object_id_from_header(header: str) -> str:
    """'■Partオブジェクトのメソッド' -> 'Part'"""
    s = header.strip()
    s = re.sub(r"^■", "", s)
    s = s.replace("のメソッド", "")
    s = s.replace("オブジェクト", "")
    return s.strip()


def _guess_return_type_from_desc(desc: str) -> str:
    """Infers return type from its description string."""
    d = desc or ""
    if re.search(r"\bID\b", d, flags=re.IGNORECASE) or ("要素ID" in d):
        return "ID"
    return "不明"


def _parse_api_specs(text: str) -> List[Dict[str, Any]]:
    """
    Parses the content of api.txt into a list of structured dictionaries.
    """
    # --- Local regex helpers ---
    lines = text.split("\n")
    closing_pat = re.compile(r"\)\s*;?(?:\s*//.*)?$")
    param_pat = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,?\s*//\s*([^:：]+)\s*[:：]\s*(.*)$")
    method_start_pat = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\($")
    header_pat = re.compile(r"^■.+のメソッド$")
    title_pat = re.compile(r"^〇(.+)$")
    ret_pat = re.compile(r"^返り値[:：]\s*(.+)$")

    def is_header(line: str) -> bool:
        return bool(header_pat.match(line))

    def parse_header(line: str) -> str:
        return _to_object_id_from_header(line)

    def is_title(line: str) -> Optional[str]:
        m = title_pat.match(line)
        return m.group(1).strip() if m else None

    def is_return(line: str) -> Optional[str]:
        m = ret_pat.match(line)
        return m.group(1).strip() if m else None

    def is_method_start(line: str) -> Optional[str]:
        m = method_start_pat.match(line)
        return m.group(1) if m else None

    def try_parse_param_line(line: str) -> Optional[Dict[str, str]]:
        m = param_pat.match(line)
        if not m:
            return None
        pname, ptype, pdesc = m.groups()
        return {"name": pname, "type": ptype.strip(), "description": pdesc.strip()}

    def try_parse_trailing_param_on_close(line: str) -> Optional[Dict[str, str]]:
        if not closing_pat.search(line):
            return None
        idx_close = line.rfind(")")
        before = line[:idx_close]
        token = before.split(",")[-1].strip()
        token = re.sub(r"[;,\s]+$", "", token)
        comment = line.split("//", 1)[1].strip() if "//" in line else ""
        synth = f"{token} // {comment}" if comment else token
        m = param_pat.match(synth)
        if not m:
            return None
        pname, ptype, pdesc = m.groups()
        return {"name": pname, "type": ptype.strip(), "description": pdesc.strip()}

    # --- State ---
    current_object = None
    current_title = None
    current_return_desc = None
    collecting_params = False
    current_entry: Optional[Dict[str, Any]] = None
    entries: List[Dict[str, Any]] = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()

        # Header line
        if is_header(line):
            current_object = parse_header(line)
            current_title = None
            current_return_desc = None
            i += 1
            continue

        # Title and optional return line
        title_text = is_title(line)
        if title_text is not None:
            current_title = title_text
            i += 1
            if i < n:
                ret_text = is_return(lines[i].strip())
                if ret_text is not None:
                    current_return_desc = ret_text
                    i += 1
            continue

        # Method start
        method_name = is_method_start(line)
        if method_name is not None:
            current_entry = {
                "object": current_object or "Object",
                "title_jp": current_title or "",
                "name": method_name,
                "return_desc": current_return_desc or "",
                "return_type": _guess_return_type_from_desc(current_return_desc or ""),
                "params": [],
            }
            collecting_params = True
            i += 1
            continue

        # Parameter block
        if collecting_params and current_entry is not None:
            parsed = try_parse_param_line(line)
            if parsed is not None:
                current_entry["params"].append(parsed)
                if closing_pat.search(line):
                    entries.append(current_entry)
                    current_entry = None
                    collecting_params = False
                i += 1
                continue

            # handle last-line-with-closing-paren case
            trailing = try_parse_trailing_param_on_close(line)
            if trailing is not None:
                current_entry["params"].append(trailing)
                entries.append(current_entry)
                current_entry = None
                collecting_params = False
                i += 1
                continue

            i += 1
            continue

        i += 1
    return entries


def _parse_data_type_descriptions(text: str) -> Dict[str, str]:
    """
    Parses the content of api_arg.txt into a dictionary of data type descriptions.
    """
    descriptions = {}
    current_type = None
    current_desc_lines = []

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("■"):
            if current_type and current_desc_lines:
                descriptions[current_type] = "\n".join(current_desc_lines).strip()

            current_type = line.replace("■", "").strip()
            current_desc_lines = []
        elif current_type:
            current_desc_lines.append(line)

    if current_type and current_desc_lines:
        descriptions[current_type] = "\n".join(current_desc_lines).strip()

    return descriptions
