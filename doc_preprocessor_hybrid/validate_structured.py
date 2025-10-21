from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


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
            source = source[: match.start()] + replacement + source[match.end():]
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

        title_jp = None
        raw_return = None
        return_description = None
        params: List[XmlParameter] = []

        for child in element:
            if child.tag == "title":
                title_jp = normalize_whitespace(child.text)
            elif child.tag == "return":
                raw_return, return_description = extract_return_fields(child.text)
            elif child.tag in {"parameters", "attributes"}:
                for idx, param in enumerate(child):
                    if param.tag != "parameter":
                        continue
                    param_name = normalize_whitespace(param.get("name") or "") or ""
                    type_name, description = split_type_and_description(param.text)
                    key = build_parameter_key(param_name, len(params))
                    params.append(
                        XmlParameter(
                            key=key,
                            name=param_name,
                            type_name=type_name,
                            description=description,
                        )
                    )

        entries[name] = XmlEntry(
            entry_type=entry_type,
            name=name,
            category=category,
            title_jp=title_jp,
            raw_return=raw_return,
            return_description=return_description,
            params=params,
            object_name=object_name,
        )

    return entries


def normalize_json_entry(entry: Dict[str, object]) -> Tuple[str, Dict[str, object]]:
    name = str(entry.get("name", ""))
    data: Dict[str, object] = {
        "entry_type": entry.get("entry_type"),
        "category": normalize_whitespace(entry.get("category")),
        "title_jp": normalize_whitespace(entry.get("title_jp")),
        "raw_return": normalize_whitespace(entry.get("raw_return")),
        "return_description": normalize_whitespace(
            (entry.get("returns") or {}).get("description")
            if isinstance(entry.get("returns"), dict)
            else None
        ),
        "object_name": normalize_whitespace(entry.get("object_name")),
    }

    params = []
    for param in entry.get("params", []) or []:
        param_name = param.get("name")
        param_desc = param.get("description")
        params.append(
            {
                "name": param_name or "",
                "description": normalize_whitespace(param_desc) or "",
                "type": normalize_whitespace(param.get("type")) or "",
            }
        )
    data["params"] = params
    return name, data


def parse_structured_json(path: Path) -> Dict[str, Dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries: Dict[str, Dict[str, object]] = {}
    for entry in data.get("api_entries", []) or []:
        name, normalized = normalize_json_entry(entry)
        if not name:
            continue
        entries[name] = normalized
    return entries


@dataclass
class Difference:
    name: str
    entry_type: str
    field: str
    expected: object
    actual: object


@dataclass
class AccuracyMetrics:
    """正答率計算用のメトリクス"""
    # ⑴関数名・引数定義名の総数に対する割合
    function_names_total: int
    function_names_correct: int
    function_names_accuracy: float

    # ⑵引数パラメータの総数に対する割合
    parameters_total: int
    parameters_correct: int
    parameters_accuracy: float

    # ⑶各オブジェクト名の総数に対する割合
    object_names_total: int
    object_names_correct: int
    object_names_accuracy: float

    # ⑷descriptionの総数に対する割合（完全一致）
    descriptions_total: int
    descriptions_correct: int
    descriptions_accuracy: float


def compare_entries(
    xml_entry: XmlEntry, json_entry: Dict[str, object]
) -> List[Difference]:
    differences: List[Difference] = []

    def record(field: str, expected: object, actual: object) -> None:
        if expected != actual:
            differences.append(
                Difference(
                    name=xml_entry.name,
                    entry_type=xml_entry.entry_type,
                    field=field,
                    expected=expected,
                    actual=actual,
                )
            )

    record("entry_type", xml_entry.entry_type, json_entry.get("entry_type"))
    record("category", xml_entry.category, json_entry.get("category"))
    record("title_jp", xml_entry.title_jp, json_entry.get("title_jp"))
    record("raw_return", xml_entry.raw_return, json_entry.get("raw_return"))
    record(
        "return_description",
        xml_entry.return_description,
        json_entry.get("return_description"),
    )
    record("object_name", xml_entry.object_name, json_entry.get("object_name"))

    xml_params: Dict[str, XmlParameter] = {
        param.key: param for param in xml_entry.params
    }
    json_params_raw: Dict[str, Dict[str, str]] = {}
    for idx, param in enumerate(json_entry.get("params", [])):
        key = build_parameter_key(param.get("name", ""), idx)
        json_params_raw[key] = param

    for key in sorted(set(xml_params) - set(json_params_raw)):
        param = xml_params[key]
        differences.append(
            Difference(
                name=xml_entry.name,
                entry_type=xml_entry.entry_type,
                field=f"params[{param.name or key}]",
                expected={"type": param.type_name, "description": param.description},
                actual="(JSONに無し)",
            )
        )
    for key in sorted(set(json_params_raw) - set(xml_params)):
        param = json_params_raw[key]
        differences.append(
            Difference(
                name=xml_entry.name,
                entry_type=xml_entry.entry_type,
                field=f"params[{param.get('name') or key}]",
                expected="(XMLに無し)",
                actual={
                    "type": param.get("type"),
                    "description": param.get("description"),
                },
            )
        )

    for key in sorted(set(xml_params) & set(json_params_raw)):
        xml_param = xml_params[key]
        json_param = json_params_raw[key]
        record(
            f"params[{xml_param.name or key}].type",
            xml_param.type_name,
            json_param.get("type", ""),
        )
        record(
            f"params[{xml_param.name or key}].description",
            xml_param.description,
            json_param.get("description", ""),
        )

    return differences


def compare_collections(
    xml_entries: Dict[str, XmlEntry], json_entries: Dict[str, Dict[str, object]]
) -> Tuple[List[str], List[str], List[Difference]]:
    xml_only = sorted(set(xml_entries) - set(json_entries))
    json_only = sorted(set(json_entries) - set(xml_entries))

    diffs: List[Difference] = []
    for name in sorted(set(xml_entries) & set(json_entries)):
        diffs.extend(compare_entries(xml_entries[name], json_entries[name]))

    return xml_only, json_only, diffs


def calculate_denominators(
    xml_entries: Dict[str, XmlEntry], json_entries: Dict[str, Dict[str, object]]
) -> Tuple[int, int, int, int]:
    """
    各評価指標の分母を計算する

    Returns:
        Tuple[int, int, int, int]: (関数名総数, パラメータ総数, オブジェクト名総数, description総数)
    """
    # ⑴関数名・引数定義名の総数
    # XMLとJSONの両方に存在するエントリ数を分母とする
    common_entries = set(xml_entries.keys()) & set(json_entries.keys())
    function_names_total = len(common_entries)

    # ⑵引数パラメータの総数
    parameters_total = 0
    for name in common_entries:
        xml_entry = xml_entries[name]
        json_entry = json_entries[name]
        # XMLとJSONの両方のパラメータ数を合計
        parameters_total += len(xml_entry.params) + len(json_entry.get("params", []))

    # ⑶各オブジェクト名の総数
    object_names_total = 0
    for name in common_entries:
        xml_entry = xml_entries[name]
        json_entry = json_entries[name]
        # オブジェクト名が存在する場合にカウント
        if xml_entry.object_name:
            object_names_total += 1
        if json_entry.get("object_name"):
            object_names_total += 1

    # ⑷descriptionの総数
    descriptions_total = 0
    for name in common_entries:
        xml_entry = xml_entries[name]
        json_entry = json_entries[name]

        # パラメータのdescription
        for param in xml_entry.params:
            if param.description:
                descriptions_total += 1
        for param in json_entry.get("params", []):
            if param.get("description"):
                descriptions_total += 1

        # 戻り値のdescription
        if xml_entry.return_description:
            descriptions_total += 1
        if json_entry.get("return_description"):
            descriptions_total += 1

    return function_names_total, parameters_total, object_names_total, descriptions_total


def calculate_numerators(
    xml_entries: Dict[str, XmlEntry], json_entries: Dict[str, Dict[str, object]]
) -> Tuple[int, int, int, int]:
    """
    各評価指標の分子（正解数）を計算する

    Returns:
        Tuple[int, int, int, int]: (関数名正解数, パラメータ正解数, オブジェクト名正解数, description正解数)
    """
    # ⑴関数名・引数定義名の正解数
    # XMLとJSONの両方に存在するエントリで、nameが一致するものの数
    common_entries = set(xml_entries.keys()) & set(json_entries.keys())
    function_names_correct = len(common_entries)  # 共通エントリは全て正解とする

    # ⑵引数パラメータの正解数
    parameters_correct = 0
    for name in common_entries:
        xml_entry = xml_entries[name]
        json_entry = json_entries[name]

        # パラメータのマッピングを作成
        xml_params = {param.key: param for param in xml_entry.params}
        json_params = {}
        for idx, param in enumerate(json_entry.get("params", [])):
            key = build_parameter_key(param.get("name", ""), idx)
            json_params[key] = param

        # 共通のパラメータで一致するものをカウント
        common_params = set(xml_params.keys()) & set(json_params.keys())
        for key in common_params:
            xml_param = xml_params[key]
            json_param = json_params[key]
            # name, type, descriptionが一致する場合を正解とする
            if (xml_param.name == json_param.get("name", "") and
                    xml_param.type_name == json_param.get("type", "") and
                    xml_param.description == json_param.get("description", "")):
                parameters_correct += 1

    # ⑶各オブジェクト名の正解数
    object_names_correct = 0
    for name in common_entries:
        xml_entry = xml_entries[name]
        json_entry = json_entries[name]

        # オブジェクト名が一致する場合を正解とする
        if (xml_entry.object_name and
                json_entry.get("object_name") and
                xml_entry.object_name == json_entry.get("object_name")):
            object_names_correct += 1

    # ⑷descriptionの正解数（完全一致）
    descriptions_correct = 0
    for name in common_entries:
        xml_entry = xml_entries[name]
        json_entry = json_entries[name]

        # パラメータのdescription
        xml_params = {param.key: param for param in xml_entry.params}
        json_params = {}
        for idx, param in enumerate(json_entry.get("params", [])):
            key = build_parameter_key(param.get("name", ""), idx)
            json_params[key] = param

        common_params = set(xml_params.keys()) & set(json_params.keys())
        for key in common_params:
            xml_param = xml_params[key]
            json_param = json_params[key]
            if (xml_param.description and
                    json_param.get("description") and
                    xml_param.description == json_param.get("description")):
                descriptions_correct += 1

        # 戻り値のdescription
        if (xml_entry.return_description and
                json_entry.get("return_description") and
                xml_entry.return_description == json_entry.get("return_description")):
            descriptions_correct += 1

    return function_names_correct, parameters_correct, object_names_correct, descriptions_correct


def calculate_accuracy_metrics(
    xml_entries: Dict[str, XmlEntry], json_entries: Dict[str, Dict[str, object]]
) -> AccuracyMetrics:
    """
    正答率メトリクスを計算する

    Returns:
        AccuracyMetrics: 各評価指標の総数、正解数、正答率
    """
    # 分母を計算
    (function_names_total, parameters_total,
     object_names_total, descriptions_total) = calculate_denominators(xml_entries, json_entries)

    # 分子を計算
    (function_names_correct, parameters_correct,
     object_names_correct, descriptions_correct) = calculate_numerators(xml_entries, json_entries)

    # 正答率を計算（ゼロ除算を避ける）
    function_names_accuracy = (function_names_correct / function_names_total
                               if function_names_total > 0 else 0.0)
    parameters_accuracy = (parameters_correct / parameters_total
                           if parameters_total > 0 else 0.0)
    object_names_accuracy = (object_names_correct / object_names_total
                             if object_names_total > 0 else 0.0)
    descriptions_accuracy = (descriptions_correct / descriptions_total
                             if descriptions_total > 0 else 0.0)

    return AccuracyMetrics(
        function_names_total=function_names_total,
        function_names_correct=function_names_correct,
        function_names_accuracy=function_names_accuracy,
        parameters_total=parameters_total,
        parameters_correct=parameters_correct,
        parameters_accuracy=parameters_accuracy,
        object_names_total=object_names_total,
        object_names_correct=object_names_correct,
        object_names_accuracy=object_names_accuracy,
        descriptions_total=descriptions_total,
        descriptions_correct=descriptions_correct,
        descriptions_accuracy=descriptions_accuracy,
    )


def format_differences(
    xml_only: Iterable[str],
    json_only: Iterable[str],
    diffs: Iterable[Difference],
    limit: Optional[int] = 20,
) -> str:
    lines: List[str] = []
    xml_only_list = list(xml_only)
    json_only_list = list(json_only)

    def trim(items: List[str]) -> Tuple[List[str], bool]:
        if limit is None:
            return items, False
        return items[:limit], len(items) > limit

    if xml_only_list:
        subset, more = trim(xml_only_list)
        lines.append("[XMLのみ]" + ", ".join(subset))
        if more:
            lines.append(f"... ({len(xml_only_list) - len(subset)} more)")
    if json_only_list:
        subset, more = trim(json_only_list)
        lines.append("[JSONのみ]" + ", ".join(subset))
        if more:
            lines.append(f"... ({len(json_only_list) - len(subset)} more)")

    diff_list = list(diffs)
    if diff_list:
        lines.append("[差分]")
        subset, more = trim(diff_list)
        for diff in subset:
            expected = diff.expected if diff.expected not in [None, ""] else "(空)"
            actual = diff.actual if diff.actual not in [None, ""] else "(空)"
            lines.append(
                f"- {diff.entry_type}:{diff.name} {diff.field} -> 期待: {expected} / 実際: {actual}"
            )
        if more:
            lines.append(f"... ({len(diff_list) - len(subset)} more differences)")

    if not lines:
        return "差分は検出されませんでした。"
    return "\n".join(lines)


def write_report_document(
    report_path: Path,
    xml_path: Path,
    json_path: Path,
    xml_only: List[str],
    json_only: List[str],
    diffs: List[Difference],
    report_text: str,
    exit_code: int,
    accuracy_metrics: Optional[AccuracyMetrics] = None,
) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ファイル名に日時情報を追加
    if not report_path.suffix:
        report_path = report_path.with_suffix('.md')

    # 専用フォルダ（reports/）に出力
    reports_dir = report_path.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # ファイル名に日時情報を追加
    timestamped_filename = f"{report_path.stem}_{timestamp_filename}{report_path.suffix}"
    timestamped_report_path = reports_dir / timestamped_filename

    outcome = "差分なし (exit 0)" if exit_code == 0 else "差分あり (exit 1)"
    summary_lines = [
        f"# structured_api 検証ログ ({timestamp})",
        "",
        f"- XML: `{xml_path.as_posix()}`",
        f"- JSON: `{json_path.as_posix()}`",
        f"- 結果: {outcome}",
        f"- XMLエントリ数: {len(xml_only) + len(diffs) + len(set(json_only) & set(xml_only)) if xml_only or json_only else len(set(xml_only) | set(json_only))}",  # noqa: E501
        f"- JSONエントリ数: {len(json_only) + len(diffs) + len(set(xml_only) & set(json_only)) if xml_only or json_only else len(set(xml_only) | set(json_only))}",  # noqa: E501
        f"- XMLのみ: {len(xml_only)}件 / JSONのみ: {len(json_only)}件 / 差分: {len(diffs)}件",
        "",
    ]

    # 正答率情報を追加
    if accuracy_metrics:
        summary_lines.extend([
            "## 正答率メトリクス",
            "",
            "### ⑴関数名・引数定義名の正答率",
            f"- 総数: {accuracy_metrics.function_names_total}",
            f"- 正解数: {accuracy_metrics.function_names_correct}",
            f"- 正答率: {accuracy_metrics.function_names_accuracy:.2%}",
            "",
            "### ⑵引数パラメータの正答率",
            f"- 総数: {accuracy_metrics.parameters_total}",
            f"- 正解数: {accuracy_metrics.parameters_correct}",
            f"- 正答率: {accuracy_metrics.parameters_accuracy:.2%}",
            "",
            "### ⑶各オブジェクト名の正答率",
            f"- 総数: {accuracy_metrics.object_names_total}",
            f"- 正解数: {accuracy_metrics.object_names_correct}",
            f"- 正答率: {accuracy_metrics.object_names_accuracy:.2%}",
            "",
            "### ⑷descriptionの正答率（完全一致）",
            f"- 総数: {accuracy_metrics.descriptions_total}",
            f"- 正解数: {accuracy_metrics.descriptions_correct}",
            f"- 正答率: {accuracy_metrics.descriptions_accuracy:.2%}",
            "",
        ])

    summary_lines.extend([
        "## レポート",
        "```",
        report_text,
        "```",
    ])
    # タイムスタンプ付きファイルに書き込み
    timestamped_report_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    # 元のファイルパスにも同じ内容を書き込み（後方互換性のため）
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    # タイムスタンプ付きファイルのパスを出力
    print(f"\nレポートが保存されました: {timestamped_report_path.as_posix()}")


def run_validation(xml_path: Path, json_path: Path, report_path: Path) -> int:
    xml_entries = parse_xml_template(xml_path)
    json_entries = parse_structured_json(json_path)

    xml_only, json_only, diffs = compare_collections(xml_entries, json_entries)
    report = format_differences(xml_only, json_only, diffs)
    print(report)

    # 正答率を計算
    accuracy_metrics = calculate_accuracy_metrics(xml_entries, json_entries)

    # 正答率をコンソールに表示
    print("\n=== 正答率メトリクス ===")
    print(f"⑴関数名・引数定義名の正答率: {accuracy_metrics.function_names_correct}/{accuracy_metrics.function_names_total} ({accuracy_metrics.function_names_accuracy:.2%})")  # noqa: E501
    print(f"⑵引数パラメータの正答率: {accuracy_metrics.parameters_correct}/{accuracy_metrics.parameters_total} ({accuracy_metrics.parameters_accuracy:.2%})")  # noqa: E501
    print(f"⑶各オブジェクト名の正答率: {accuracy_metrics.object_names_correct}/{accuracy_metrics.object_names_total} ({accuracy_metrics.object_names_accuracy:.2%})")  # noqa: E501
    print(f"⑷descriptionの正答率: {accuracy_metrics.descriptions_correct}/{accuracy_metrics.descriptions_total} ({accuracy_metrics.descriptions_accuracy:.2%})")  # noqa: E501

    full_report = format_differences(xml_only, json_only, diffs, limit=None)
    exit_code = 0 if not (xml_only or json_only or diffs) else 1
    write_report_document(
        report_path,
        xml_path,
        json_path,
        xml_only,
        json_only,
        diffs,
        full_report,
        exit_code,
        accuracy_metrics,
    )

    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="api_template.xml と structured_api.json の整合性検証",
    )
    parser.add_argument(
        "--xml",
        type=Path,
        default=Path("doc_preprocessor_hybrid/out/api_template.xml"),
        help="APIテンプレートXMLのパス",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=Path("doc_preprocessor_hybrid/out/structured_api.json"),
        help="構造化API JSONのパス",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("doc_preprocessor_hybrid/out/validate_structured_report.md"),
        help="検証結果を書き出すMarkdownファイルのパス（日時情報付きでreports/フォルダに保存）",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.xml.exists():
        print(f"XMLテンプレートが見つかりません: {args.xml}", file=sys.stderr)
        return 2
    if not args.json.exists():
        print(f"JSONデータが見つかりません: {args.json}", file=sys.stderr)
        return 2

    return run_validation(args.xml, args.json, args.report)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(main())
