from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union


# --- XML用データクラス ---
@dataclass
class XmlParameter:
    key: str
    name: str
    type_name: str
    description: str

@dataclass
class XmlEntry:
    entry_type: str
    name: str
    category: Optional[str]
    title_jp: Optional[str]
    raw_return: Optional[str]
    return_description: Optional[str]
    params: List[XmlParameter]
    object_name: Optional[str]


# --- JSON用データクラス (新規追加) ---
@dataclass
class JsonParameter:
    key: str
    name: str
    type_name: str
    description: str
    order: int

@dataclass
class JsonEntry:
    entry_type: str
    name: str
    category: Optional[str] = None
    title_jp: Optional[str] = None
    raw_return: Optional[str] = None
    return_description: Optional[str] = None
    params: List[JsonParameter] = field(default_factory=list)
    object_name: Optional[str] = None


ENTRY_TYPE_MAP: Dict[str, str] = {
    "method": "function",
    "parameterObject": "parameter_object",
}


def sanitize_template_xml(text: str) -> str:
    """Fixes known formatting issues in api_template.xml before parsing."""
    def fix_block(tag: str, source: str) -> str:
        pattern = re.compile(rf"<{tag}>(?P<body>[\s\S]*?)<{tag}\s*/>")
        while True:
            match = pattern.search(source)
            if not match:
                break
            body = match.group("body")
            replacement = f"<{tag}>{body}</{tag}>"
            source = source[: match.start()] + replacement + source[match.end() :]
        return source

    text = fix_block("parameters", text)
    text = fix_block("attributes", text)
    text = re.sub(r"<parameters>\s*<parameters\s*/>", "<parameters/>", text)
    text = re.sub(r"<parameters>\s*</parameters>", "<parameters/>", text)
    text = re.sub(r"<attributes>\s*<attributes\s*/>", "<attributes/>", text)
    text = re.sub(r"<attributes>\s*</attributes>", "<attributes/>", text)
    return text


def normalize_whitespace(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.replace("\u3000", " ")
    normalized = re.sub(r"\s+", " ", normalized.strip())
    return normalized or None


def normalize_category(section: Optional[str]) -> Optional[str]:
    section = normalize_whitespace(section)
    if not section:
        return None
    suffixes = ["のメソッド", "のプロパティ", "のイベント", "の属性", "のパラメータ"]
    for suffix in suffixes:
        if section.endswith(suffix):
            section = section[: -len(suffix)]
            break
    return section or None


def extract_return_fields(text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    text = normalize_whitespace(text)
    if not text:
        return None, None
    cleaned = re.sub(r"^返り値[:：]\s*", "", text)
    return cleaned or None, cleaned or None


def split_type_and_description(text: Optional[str]) -> Tuple[str, str]:
    normalized = normalize_whitespace(text) or ""
    if not normalized:
        return "", ""
    parts = re.split(r"[:：]", normalized, maxsplit=1)
    if len(parts) == 1:
        return parts[0].strip(), ""
    type_name, description = parts[0].strip(), parts[1].strip()
    return type_name, description


def build_parameter_key(name: str, index: int) -> str:
    name = name.strip()
    return name or f"__index_{index}"


def parse_xml_template(path: Path) -> Dict[str, XmlEntry]:
    raw = path.read_text(encoding="utf-8")
    sanitized = sanitize_template_xml(raw)
    try:
        root = ET.fromstring(sanitized)
    except ET.ParseError as exc:
        raise ValueError(f"XMLの解析に失敗しました: {exc}") from exc

    entries: Dict[str, XmlEntry] = {}
    for element in root:
        entry_type_raw = element.tag
        entry_type = ENTRY_TYPE_MAP.get(entry_type_raw, entry_type_raw)
        name = element.get("name")
        if not name:
            continue
        category = normalize_category(element.get("section"))
        object_name = category
        title_jp, raw_return, return_description = None, None, None
        params: List[XmlParameter] = []

        for child in element:
            if child.tag == "title":
                title_jp = normalize_whitespace(child.text)
            elif child.tag == "return":
                raw_return, return_description = extract_return_fields(child.text)
            elif child.tag in {"parameters", "attributes"}:
                for param in child:
                    if param.tag != "parameter":
                        continue
                    param_name = normalize_whitespace(param.get("name") or "") or ""
                    type_name, description = split_type_and_description(param.text)
                    key = build_parameter_key(param_name, len(params))
                    params.append(
                        XmlParameter(key=key, name=param_name, type_name=type_name, description=description)
                    )
        entries[name] = XmlEntry(
            entry_type=entry_type, name=name, category=category, title_jp=title_jp,
            raw_return=raw_return, return_description=return_description,
            params=params, object_name=object_name,
        )
    return entries

# --- ▼▼▼ ここからが大幅な修正箇所 ▼▼▼ ---

def parse_neo4j_json(path: Path) -> Dict[str, JsonEntry]:
    """
    neo4j_data.jsonのグラフ構造を解析し、検証可能な形式に再構成する。
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes = {node['id']: node for node in data.get('nodes', [])}
    
    # 探索を効率化するため、リレーションシップをソースIDとターゲットIDで索引付け
    source_to_rels: Dict[str, List[Dict]] = {}
    for rel in data.get('relationships', []):
        source_id = rel.get('source')
        if source_id:
            source_to_rels.setdefault(source_id, []).append(rel)

    json_entries: Dict[str, JsonEntry] = {}
    method_nodes = [n for n in nodes.values() if n.get('type') == 'Method']

    for method_node in method_nodes:
        method_props = method_node.get('properties', {})
        method_name = method_props.get('name')
        if not method_name or not method_props:  # プロパティがないMethodノードは無視
            continue

        entry = JsonEntry(
            name=method_name,
            entry_type='function', # Methodノードはfunctionとして扱う
            title_jp=method_props.get('description')
        )

        method_rels = source_to_rels.get(method_node['id'], [])
        for rel in method_rels:
            target_id = rel.get('target')
            target_node = nodes.get(target_id)
            if not target_node:
                continue
            
            rel_type = rel.get('type')
            target_props = target_node.get('properties', {})

            if rel_type == 'BELONGS_TO':
                entry.object_name = target_props.get('name')
                entry.category = entry.object_name
            
            elif rel_type == 'HAS_RETURNS':
                entry.return_description = normalize_whitespace(target_props.get('description'))
                entry.raw_return = entry.return_description

            elif rel_type == 'HAS_PARAMETER':
                param_name = target_props.get('name', '')
                param_desc = target_props.get('description', '')
                param_order = target_props.get('order', 999)
                param_type = "不明"

                # パラメータの型を探す
                param_rels = source_to_rels.get(target_id, [])
                for param_rel in param_rels:
                    if param_rel.get('type') == 'HAS_TYPE':
                        type_node = nodes.get(param_rel.get('target'))
                        if type_node:
                            param_type = type_node.get('properties', {}).get('name', "不明")
                        break
                
                entry.params.append(JsonParameter(
                    key=build_parameter_key(param_name, len(entry.params)),
                    name=param_name, type_name=param_type,
                    description=param_desc, order=param_order,
                ))

        entry.params.sort(key=lambda p: p.order)
        json_entries[method_name] = entry
        
    return json_entries

# --- ▲▲▲ ここまでが大幅な修正箇所 ▲▲▲ ---

@dataclass
class Difference:
    name: str
    entry_type: str
    field: str
    expected: object
    actual: object


def compare_entries(xml_entry: XmlEntry, json_entry: JsonEntry) -> List[Difference]:
    differences: List[Difference] = []

    def record(field: str, expected: object, actual: object) -> None:
        # ホワイトスペースを正規化して比較
        norm_expected = normalize_whitespace(str(expected)) if isinstance(expected, str) else expected
        norm_actual = normalize_whitespace(str(actual)) if isinstance(actual, str) else actual
        if norm_expected != norm_actual:
            differences.append(
                Difference(name=xml_entry.name, entry_type=xml_entry.entry_type, field=field, expected=expected, actual=actual)
            )

    record("title_jp", xml_entry.title_jp, json_entry.title_jp)
    record("return_description", xml_entry.return_description, json_entry.return_description)
    record("object_name", xml_entry.object_name, json_entry.object_name)

    xml_params: Dict[str, XmlParameter] = {p.key: p for p in xml_entry.params}
    json_params: Dict[str, JsonParameter] = {p.key: p for p in json_entry.params}

    for key in sorted(set(xml_params) - set(json_params)):
        param = xml_params[key]
        differences.append(
            Difference(name=xml_entry.name, entry_type=xml_entry.entry_type, field=f"params[{param.name or key}]",
                       expected={"type": param.type_name, "description": param.description}, actual="(JSONに無し)")
        )
    for key in sorted(set(json_params) - set(xml_params)):
        param = json_params[key]
        differences.append(
            Difference(name=xml_entry.name, entry_type=xml_entry.entry_type, field=f"params[{param.name or key}]",
                       expected="(XMLに無し)", actual={"type": param.type_name, "description": param.description})
        )
    for key in sorted(set(xml_params) & set(json_params)):
        xml_param = xml_params[key]
        json_param = json_params[key]
        record(f"params[{xml_param.name or key}].type", xml_param.type_name, json_param.type_name)
        record(f"params[{xml_param.name or key}].description", xml_param.description, json_param.description)

    return differences


def compare_collections(
    xml_entries: Dict[str, XmlEntry], json_entries: Dict[str, JsonEntry]
) -> Tuple[List[str], List[str], List[Difference]]:
    xml_keys = set(xml_entries.keys())
    json_keys = set(json_entries.keys())
    
    xml_only = sorted(xml_keys - json_keys)
    json_only = sorted(json_keys - xml_keys)

    diffs: List[Difference] = []
    for name in sorted(xml_keys & json_keys):
        diffs.extend(compare_entries(xml_entries[name], json_entries[name]))

    return xml_only, json_only, diffs


def format_differences(
    xml_only: Iterable[str], json_only: Iterable[str], diffs: Iterable[Difference], limit: Optional[int] = 20
) -> str:
    lines: List[str] = []
    xml_only_list, json_only_list, diff_list = list(xml_only), list(json_only), list(diffs)

    def trim(items: List) -> Tuple[List, bool]:
        if limit is None or len(items) <= limit:
            return items, False
        return items[:limit], True

    if xml_only_list:
        subset, more = trim(xml_only_list)
        lines.append(f"[XMLのみ] {', '.join(subset)}")
        if more: lines.append(f"  ...他 {len(xml_only_list) - len(subset)} 件")
    if json_only_list:
        subset, more = trim(json_only_list)
        lines.append(f"[JSONのみ] {', '.join(subset)}")
        if more: lines.append(f"  ...他 {len(json_only_list) - len(subset)} 件")
    if diff_list:
        lines.append("[差分あり]")
        subset, more = trim(diff_list)
        for diff in subset:
            expected = f'"{diff.expected}"' if diff.expected is not None else "(空)"
            actual = f'"{diff.actual}"' if diff.actual is not None else "(空)"
            lines.append(f"- {diff.name} | {diff.field:<30} | 期待値: {expected:<40} | 実際値: {actual}")
        if more: lines.append(f"  ...他 {len(diff_list) - len(subset)} 件の差分")

    return "\n".join(lines) if lines else "差分は検出されませんでした。"


def write_report_document(
    report_path: Path, xml_path: Path, json_path: Path, xml_only: List[str],
    json_only: List[str], diffs: List[Difference], report_text: str, exit_code: int
) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    outcome = "差分なし (exit 0)" if exit_code == 0 else "差分あり (exit 1)"
    xml_count = len(xml_only) + len(diffs) + len(set(json_only) ^ (set(json_only) | set(xml_only)))
    json_count = len(json_only) + len(diffs) + len(set(xml_only) ^ (set(json_only) | set(xml_only)))

    summary_lines = [
        f"# structured_api 検証ログ ({timestamp})", "",
        f"- XML: `{xml_path.name}`",
        f"- JSON: `{json_path.name}`",
        f"- 結果: {outcome}",
        f"- XMLエントリ数: {xml_count}",
        f"- JSONエントリ数: {json_count}",
        f"- XMLのみ: {len(xml_only)}件 / JSONのみ: {len(json_only)}件 / 差分: {len(diffs)}件",
        "", "## レポート", "```", report_text, "```",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def run_validation(xml_path: Path, json_path: Path, report_path: Path) -> int:
    try:
        xml_entries = parse_xml_template(xml_path)
        # 修正：新しいJSONパーサーを呼び出す
        json_entries = parse_neo4j_json(json_path)
    except (ValueError, FileNotFoundError) as e:
        print(f"エラー: ファイルの読み込みまたは解析に失敗しました。\n{e}", file=sys.stderr)
        return 2

    xml_only, json_only, diffs = compare_collections(xml_entries, json_entries)
    report = format_differences(xml_only, json_only, diffs)
    print(report)

    full_report = format_differences(xml_only, json_only, diffs, limit=None)
    exit_code = 1 if xml_only or json_only or diffs else 0
    write_report_document(report_path, xml_path, json_path, xml_only, json_only, diffs, full_report, exit_code)

    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="api_template.xml と neo4j_data.json の整合性検証")
    parser.add_argument(
        "--xml", type=Path, default=Path("api_template.xml"), help="APIテンプレートXMLのパス"
    )
    parser.add_argument(
        "--json", type=Path, default=Path("neo4j_data.json"), help="Neo4jグラフ構造JSONのパス"
    )
    parser.add_argument(
        "--report", type=Path, default=Path("validation_report.md"), help="検証結果を書き出すMarkdownファイルのパス"
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.xml.exists():
        print(f"XMLファイルが見つかりません: {args.xml}", file=sys.stderr)
        return 2
    if not args.json.exists():
        print(f"JSONファイルが見つかりません: {args.json}", file=sys.stderr)
        return 2

    return run_validation(args.xml, args.json, args.report)


if __name__ == "__main__":
    sys.exit(main())