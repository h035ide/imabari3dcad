from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .config import PipelineConfig
from .logging_config import get_logger
from .schemas import (
    ApiBundle,
    ApiEntry,
    Parameter,
    ReturnSpec,
    TypeDefinition,
    SourceFragment,
)


HEADER_RE = re.compile(r"^■(.+?)(?:のメソッド)?$")
TITLE_RE = re.compile(r"^〇(.+)$")
RETURN_RE = re.compile(r"^\s*返り値[:：]\s*(.+)$")
# パラメータ改行型: 末尾が '(' で改行してパラメータが続く
METHOD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\($")
# パラメータ無しの同一行型: 例) Quit() / Create3DDocument()
ZERO_PARAM_METHOD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*;?$")
PARAM_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,?\s*//\s*([^:：]+)[:：]\s*(.+)$")
# コロンなしコメント形式にも対応する緩和版（例: pOpt) // STLパラメータオブジェクト）
PARAM_RE_LOOSE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*,?\s*//\s*(.+)$")
ARRAY_MARKERS = ("(配列)", "[]", "(array)")

# 閉じ括弧直前のパラメータ + コメント形式（例: bShow ) // bool: 表示する時はTrue）
FLEXIBLE_PARAM_RE = re.compile(
    r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*//\s*([^:：]+)[:：]\s*(.+)$"
)

TYPE_CANONICAL_MAP: dict[str, tuple[str, str]] = {
    "文字列": ("string", "str"),
    "浮動小数点": ("float", "float"),
    "bool": ("bool", "bool"),
    "整数": ("integer", "int"),
    "長さ": ("length", "str"),
    "角度": ("angle", "str"),
    "数値": ("number", "str"),
    "範囲": ("range", "str"),
    "点": ("point", "str"),
    "方向": ("direction", "str"),
    "平面": ("plane", "str"),
    "変数単位": ("unit", "str"),
    "要素グループ": ("element_group", "str"),
    "材料": ("material", "str"),
    "スイープ方向": ("direction", "str"),
    "厚み付けタイプ": ("thicken_type", "str"),
    "モールド位置": ("mold_position", "str"),
    "オペレーションタイプ （ボディ）": ("operation_body", "str"),
    "関連設定": ("relationship", "str"),
    "形状タイプ": ("shape_type", "str"),
    "形状パラメータ": ("shape_parameter", "str"),
    "要素": ("element", "str"),
}


ENUM_DESCRIPTION_SUFFIX_NAMES = {"長さ", "角度", "数値"}

TYPE_ONE_OF_MAP: dict[str, List[str]] = {
    "長さ": ["millimeter_literal", "variable_reference", "expression"],
    "角度": ["degree_literal", "variable_reference", "expression"],
    "数値": ["numeric_literal", "variable_reference", "expression"],
    "点": ["cartesian_point", "variable_reference", "expression"],
    "範囲": ["comma_delimited_range", "variable_reference", "expression"],
    "要素": [
        "element_id",
        "element_group",
        "element_reference",
        "element_array",
    ],
}


# ---- logging helpers -----------------------------------------------------
LOG_SNIPPET_LENGTH = 200


def _log_snippet(text: str) -> str:
    """Return a truncated single-line snippet for debug logs.

    This avoids flooding logs with very long source lines.
    """
    if text is None:
        return ""
    one_line = text.replace("\n", " ")
    return (
        one_line
        if len(one_line) <= LOG_SNIPPET_LENGTH
        else one_line[:LOG_SNIPPET_LENGTH] + "…"
    )


def _build_source_fragment(
    lines: List[str], start_idx: int, end_idx: int, path: Path | None
) -> SourceFragment | None:
    if path is None:
        return None
    if not lines:
        return None
    start = max(0, min(start_idx, len(lines) - 1))
    end = max(start, min(end_idx, len(lines) - 1))
    snippet = "\n".join(lines[start:end + 1])
    # 簡略化されたsource形式（textのみ）
    return SourceFragment(
        path="",
        start_line=0,
        end_line=0,
        text=snippet,
        checksum="",
    )


def _is_closing_line(raw_line: str) -> bool:
    code_part = raw_line.split("//", 1)[0].rstrip()
    if not code_part:
        return False
    code_part = code_part.rstrip(";").rstrip()
    return code_part.endswith(")")


def _normalize_type_definition_description(name: str, description: str) -> str:
    description = (description or "").strip()
    if not description:
        return ""
    lines = [line.strip() for line in description.split("\n") if line.strip()]
    if not lines:
        return ""

    # 句読点の統一処理
    normalized_lines = []
    for line in lines:
        # 全角句読点を半角に統一
        line = line.replace("、", ",").replace("。", ".")
        # 複数のスペースを単一スペースに統一
        line = re.sub(r"\s+", " ", line)
        # 句読点の前後のスペースを調整
        line = re.sub(r"\s*,\s*", ", ", line)
        line = re.sub(r"\s*\.\s*", ". ", line)
        # 引用符内の句読点を統一
        line = re.sub(r'"([^"]*)"', lambda m: f'"{m.group(1).replace(",", "、").replace(".", "。")}"', line)
        normalized_lines.append(line)

    if name in ENUM_DESCRIPTION_SUFFIX_NAMES:
        first = normalized_lines[0].rstrip(".")
        if "のいずれか" not in first:
            first = f"{first}のいずれか"
        if not first.endswith("."):
            first = f"{first}."
        normalized_lines[0] = first

    return "\n".join(normalized_lines)


def _refine_element_definition(type_def: TypeDefinition) -> None:
    type_def.description = (
        "モデル内の要素を参照する識別子を受け取ります。\n"
        "- element_id: 既存要素を一意に識別する ID（例: ID@...）。\n"
        "- element_group: 要素グループ名。複数要素をまとめて参照します。\n"
        "- element_reference: 操作対象の単一要素を指すラベルや名称。\n"
        "- element_array: 面リストや辺リストなど、複数要素を配列で指定するケース。"
    )


DEFAULT_POINT_EXAMPLES: Tuple[Tuple[str, ...], ...] = (
    ("100.0", "50.0", "0.0"),
    ("FRM1", "0.0", "1000.0"),
)
POINT_COMPONENT_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?$|^[A-Za-z_][A-Za-z0-9_]*$")


def _unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for value in values:
        if value in seen:
            continue
        ordered.append(value)
        seen.add(value)
    return ordered


def _tokenize_point_example(example: str) -> List[str]:
    if not example:
        return []
    cleaned = example.strip()
    if (
        cleaned.startswith(("'", '"'))
        and cleaned.endswith(("'", '"'))
        and len(cleaned) >= 2
    ):
        cleaned = cleaned[1:-1].strip()
    tokens = [token.strip() for token in cleaned.split(",")]
    normalized: List[str] = []
    for token in tokens:
        if not token:
            continue
        if POINT_COMPONENT_PATTERN.match(token):
            normalized.append(token)
        else:
            return []
    return normalized


def _parse_point_examples(examples: List[str]) -> List[List[str]]:
    parsed: List[List[str]] = []
    for example in examples:
        tokens = _tokenize_point_example(example)
        if tokens and tokens not in parsed:
            parsed.append(tokens)
    return parsed


def _examples_to_strings(
    parsed_examples: List[List[str]], *, limit: int | None = None
) -> List[str]:
    formatted: List[str] = []
    for tokens in parsed_examples:
        if limit is not None and len(tokens) < limit:
            continue
        subset = tokens if limit is None else tokens[:limit]
        formatted.append(",".join(subset))
    return _unique_preserve_order(formatted)


def _fallback_point_examples(components: int) -> List[str]:
    values = [
        ",".join(example[:components])
        for example in DEFAULT_POINT_EXAMPLES
        if len(example) >= components
    ]
    if not values:
        head = DEFAULT_POINT_EXAMPLES[0]
        values = [",".join(head[:components])]
    return _unique_preserve_order(values)


def _apply_type_metadata(type_def: TypeDefinition) -> None:
    type_def.description = _normalize_type_definition_description(
        type_def.name, type_def.description
    )
    # categoryフィールドを追加
    type_def.category = "型定義"
    meta = TYPE_CANONICAL_MAP.get(type_def.name)
    if meta:
        type_def.canonical_type, type_def.py_type = meta
    one_of = TYPE_ONE_OF_MAP.get(type_def.name)
    if one_of:
        # one_ofをオブジェクト配列形式に変換（より具体的な説明）
        one_of_descriptions = {
            "millimeter_literal": "mm単位の数値リテラル",
            "variable_reference": "変数要素名",
            "expression": "四則演算などの式",
            "integer_literal": "整数リテラル",
            "float_literal": "浮動小数点リテラル",
            "string_literal": "文字列リテラル",
            "boolean_literal": "真偽値リテラル",
        }
        type_def.one_of = [
            {"id": item, "description": one_of_descriptions.get(item, f"{item}の説明")}
            for item in one_of
        ]
    if type_def.name == "要素":
        _refine_element_definition(type_def)
    if type_def.name == "点":
        type_def.description = "モデル座標系の点を表す値を指定します。数値リテラルのほか、変数参照や式を利用できます。"
        parsed_examples = _parse_point_examples(type_def.examples)
        if not parsed_examples:
            parsed_examples = [list(example) for example in DEFAULT_POINT_EXAMPLES]
        type_def.examples = _examples_to_strings(parsed_examples)


def _build_point_variants(base: TypeDefinition) -> List[TypeDefinition]:
    parsed_examples = _parse_point_examples(base.examples)
    if not parsed_examples:
        parsed_examples = [list(example) for example in DEFAULT_POINT_EXAMPLES]
    base.examples = _examples_to_strings(parsed_examples)
    base_summary = base.description.split("\n")[0] if base.description else base.name
    base_summary = base_summary.rstrip("。").rstrip("．")
    variants: List[TypeDefinition] = []
    for dim, token, components in (
        ("2D", "cartesian_2d", 2),
        ("3D", "cartesian_3d", 3),
    ):
        examples = _examples_to_strings(parsed_examples, limit=components)
        if not examples:
            examples = _fallback_point_examples(components)
        desc = f"{base_summary}（{dim} 座標）"
        variant = TypeDefinition(
            name=f"{base.name}({dim})",
            description=f"{desc}。",
            examples=examples,
            category="型定義",
            canonical_type="point",
            py_type="str",
            one_of=[
                {"id": token, "description": f"{token}の説明"},
                {"id": "variable_reference", "description": "変数要素名"},
                {"id": "expression", "description": "四則演算などの式"},
            ],
            source=base.source,
        )
        variants.append(variant)
    return variants


def _augment_type_definitions(
    definitions: List[TypeDefinition],
) -> List[TypeDefinition]:
    augmented: List[TypeDefinition] = []
    for definition in definitions:
        augmented.append(definition)
        if definition.name == "点":
            augmented.extend(_build_point_variants(definition))
    return augmented


VECTOR_PARAM_LIMIT = 6
FALLBACK_PARAM_DESCRIPTION = "No description provided"


def _normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # 全角スペースを半角へ
    text = text.replace("\u3000", " ")
    # 句読点の正規化
    text = text.replace("、", ",")
    text = text.replace("。", ".")
    text = text.replace("（", "(")
    text = text.replace("）", ")")
    text = text.replace("「", "\"")
    text = text.replace("」", "\"")
    text = text.replace("『", "\"")
    text = text.replace("』", "\"")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _clean_type_name(raw: str) -> Tuple[str, bool]:
    name = raw.strip()
    # COM/IDL 属性の除去と代表型の正規化
    name = re.sub(r"\[[^\]]*\]", "", name).strip()  # [in], [out] など
    name = (
        name.replace("BSTR", "string")
        .replace("LPWSTR", "string")
        .replace("LPSTR", "string")
    )
    # 2D/3D注記など括弧内は後で落とす（dimension抽出は別）
    is_array = any(marker in name for marker in ARRAY_MARKERS)
    if is_array:
        for marker in ARRAY_MARKERS:
            name = name.replace(marker, "")
        name = name.replace("(配列)", "")
    name = re.sub(r"\s*\(.+\)$", "", name).strip()
    mapping = {
        "string": "文字列",
        "text": "文字列",
        "str": "文字列",
        "float": "浮動小数点",
        "double": "浮動小数点",
        "number": "浮動小数点",
        "int": "整数",
        "integer": "整数",
        "bool": "bool",
        "boolean": "bool",
        "真偽値": "bool",
        "論理値": "bool",
    }

    key = name.lower()
    name = mapping.get(key, name)
    return name, is_array


def _is_required(desc: str) -> bool:
    desc = desc or ""
    if "空欄不可" in desc or "必須" in desc:
        return True
    if "空欄可" in desc or "任意" in desc:
        return False
    return False


def _build_parameter(
    name: str, raw_type: str, description: str, position: int
) -> Parameter:
    cleaned, is_array = _clean_type_name(raw_type)
    # 次元(2D/3D)抽出
    dim: str | None = None
    if "(2D)" in raw_type:
        dim = "2D"
    elif "(3D)" in raw_type:
        dim = "3D"
    param = Parameter(
        name=name,
        type=cleaned,
        description=description.strip(),
        is_required=_is_required(description),
        position=position,
        raw_type=raw_type.strip(),
        dimension=dim,
    )
    if dim:
        param.type = f"{param.type}({dim})"
    if is_array:
        # 配列型の表記を統一: [] -> (配列)
        param.type = f"{param.type}(配列)"
    return param


def _guess_return_type(desc: str) -> str:
    desc = desc or ""
    if not desc.strip():
        return "void"
    if "なし" in desc:
        return "void"
    if re.search(r"\bID\b", desc, flags=re.IGNORECASE) or "要素ID" in desc:
        return "ID"
    return "不明"


def _guess_return_is_array(desc: str) -> bool:
    desc = desc or ""
    return ("配列" in desc) or ("の配列" in desc)


def _parse_bare_param(candidate: str) -> Tuple[str, str] | None:
    """コメント無しのパラメータ表記をヒューリスティックに解析する。
    例: "[in] BSTR plane" → name=plane, type="[in] BSTR"
    """
    if not candidate:
        return None
    # 末尾のカンマを除去、全角スペース→半角
    cand = candidate.strip().rstrip(",").replace("\u3000", " ")
    # 括弧内属性はそのまま型側に残す
    tokens = re.split(r"\s+", cand)
    if not tokens:
        return None
    pname = tokens[-1]
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", pname):
        # 末尾が識別子でない場合は放棄
        return None

    # 型推論の改善
    ptype = " ".join(tokens[:-1]).strip()
    if not ptype:
        # パラメータ名から型を推論
        if pname.startswith("b") and pname[1:2].isupper():
            # bUpdate, bShow など -> bool
            ptype = "bool"
        elif pname.startswith("n") and pname[1:2].isupper():
            # nDegree, nCount など -> 整数
            ptype = "整数"
        elif pname.startswith("f") and pname[1:2].isupper():
            # fValue, fLength など -> 浮動小数点
            ptype = "浮動小数点"
        elif pname.startswith("p") and pname[1:2].isupper():
            # pElement, pParam など -> 要素
            ptype = "要素"
        elif pname.endswith("Name") or pname.endswith("Name"):
            # Name, FileName など -> 文字列
            ptype = "文字列"
        elif pname.endswith("Group"):
            # ElementGroup など -> 要素グループ
            ptype = "要素グループ"
        elif pname.endswith("Method"):
            # ReferMethod など -> 関連設定
            ptype = "関連設定"
        else:
            ptype = "不明"

    return pname, ptype


def parse_type_definitions(
    text: str, *, path: Path | None = None
) -> List[TypeDefinition]:
    logger = get_logger("rule_parser.parse_type_definitions")
    logger.debug(f"Begin parse_type_definitions: source={path}")
    definitions: List[TypeDefinition] = []
    normalized = _normalize_text(text)
    lines = normalized.split("\n")
    logger.debug(f"Total lines: {len(lines)}")

    current_name: str | None = None
    current_lines: List[str] = []
    current_start: int | None = None
    current_end: int | None = None

    def finalize() -> None:
        nonlocal current_name, current_lines, current_start, current_end
        if not current_name or not current_lines:
            current_name = None
            current_lines = []
            current_start = None
            current_end = None
            return
        type_def = TypeDefinition(
            name=current_name,
            description="\n".join(current_lines),
            category="型定義"
        )
        fragment = None
        if current_start is not None:
            end_idx = current_end if current_end is not None else current_start
            fragment = _build_source_fragment(lines, current_start, end_idx, path)
        if fragment:
            type_def.source = fragment
        definitions.append(type_def)
        current_name = None
        current_lines = []
        current_start = None
        current_end = None

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if idx < 5 or idx % 50 == 0:
            # 先頭数行と50行毎に軽量スニペットを出力
            logger.debug(f"[type:{idx}] {_log_snippet(raw_line)}")
        if not line:
            continue
        if line.startswith("■"):
            finalize()
            current_name = line.replace("■", "", 1).strip()
            logger.info(f"[type] section start: name='{current_name}' at line={idx}")
            current_lines = []
            current_start = idx
            current_end = idx
            continue
        if current_name:
            if current_name == "bool" and line.startswith("以下のタイプ"):
                continue
            current_lines.append(line)
            current_end = idx

    finalize()

    refined: List[TypeDefinition] = []
    for type_def in definitions:
        _apply_type_metadata(type_def)
        logger.debug(
            f"[type] built: name='{type_def.name}', desc_snippet='{_log_snippet(type_def.description)}'"
        )
        refined.append(type_def)
    return _augment_type_definitions(refined)


def _finalize_entry(entry: ApiEntry, entries: List[ApiEntry]) -> None:
    if entry.returns is None:
        entry.returns = ReturnSpec()
    entries.append(entry)


def parse_api_specs(text: str, *, path: Path | None = None) -> List[ApiEntry]:
    logger = get_logger("rule_parser.parse_api_specs")
    logger.debug(f"Begin parse_api_specs: source={path}")
    entries: List[ApiEntry] = []
    normalized = _normalize_text(text)
    lines = normalized.split("\n")
    logger.debug(f"Total lines: {len(lines)}")
    current_object = ""
    current_title = ""
    current_return = ""
    collecting = False
    current_entry: ApiEntry | None = None
    param_index = 0
    block_start_idx: int | None = None
    entry_start_idx: int | None = None
    entry_end_idx: int | None = None

    # パラメータオブジェクトの検出パターン
    PARAM_OBJECT_PATTERN = re.compile(r"^\s*〇(.+パラメータオブジェクト)(?:の作成)?$")
    PARAM_OBJECT_NAMES = [
        "BracketParam", "FacePlateParam", "LinearSweepParam", "LoftParam",
        "ProfileParam", "RotationalSweepParam", "STLParameter", "SlotParam", "SweepParam"
    ]

    # 以前は日本語→英語マッピングを用意していたが、評価照合の都合により未使用

    def attach_source(
        entry: ApiEntry | None, start_idx: int | None, end_idx: int | None
    ) -> None:
        if not entry or start_idx is None or end_idx is None:
            return
        fragment = _build_source_fragment(lines, start_idx, end_idx, path)
        if fragment:
            entry.source = fragment

    def _consume_param(pname: str, ptype: str, pdesc: str) -> None:
        """現在のエントリにパラメータを追加し、必要なら即時クローズする。"""
        nonlocal current_entry, collecting, param_index, entry_end_idx, entry_start_idx, i
        if not current_entry:
            return
        parameter = _build_parameter(pname, ptype, pdesc, param_index)
        current_entry.params.append(parameter)
        param_index += 1
        entry_end_idx = i
        if _is_closing_line(raw_line):
            logger.debug(f"[api] entry close detected at line={i}")
            attach_source(current_entry, entry_start_idx, entry_end_idx)
            _finalize_entry(current_entry, entries)
            current_entry = None
            collecting = False
            entry_start_idx = None
            entry_end_idx = None
        i += 1

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        if i < 5 or i % 50 == 0:
            logger.debug(f"[api:{i}] {_log_snippet(raw_line)}")
        if not line:
            i += 1
            continue
        header_match = HEADER_RE.match(line)
        if header_match:
            logger.info(
                f"[api] HEADER matched: object='{header_match.group(1).strip()}' at line={i}"
            )
            current_object = header_match.group(1).strip()
            block_start_idx = None
            i += 1
            continue

        # パラメータオブジェクトの検出（タイトル検出より前に実行）
        param_obj_match = PARAM_OBJECT_PATTERN.match(line)
        if param_obj_match:
            logger.info(
                f"[api] PARAM_OBJECT matched: name='{param_obj_match.group(1).strip()}' "
                f"at line={i}"
            )
            param_obj_jp_name = param_obj_match.group(1).strip()
            # 日本語名から英語名にマッピング（現在は未使用／将来の拡張用）
            # param_obj_name = PARAM_OBJECT_MAPPING.get(param_obj_jp_name, param_obj_jp_name)

            # パラメータオブジェクトを独立したエントリとして追加
            param_entry = ApiEntry(
                entry_type="object",
                # 評価の照合に合わせて name は原文（日本語）を使用
                name=param_obj_jp_name,
                description=f"{param_obj_jp_name}のパラメータ定義",
                category=current_object,
                object_name=current_object,
                title_jp=param_obj_jp_name,
                raw_return="",
                returns=ReturnSpec(
                    type="void", description="", is_array=False
                ),
            )
            start_idx = block_start_idx if block_start_idx is not None else i

            # 直後の属性定義をpropertiesとして収集
            j = i + 1
            # 属性ラベル行をスキップ
            if j < len(lines) and lines[j].strip().startswith("属性"):
                j += 1

            prop_index = 0
            last_idx = i
            while j < len(lines):
                raw_prop_line = lines[j]
                stripped_prop = raw_prop_line.strip()
                if not stripped_prop:
                    # 空行はスキップして継続
                    j += 1
                    continue
                # セクション開始や次のブロック検出で打ち切り
                if (
                    HEADER_RE.match(stripped_prop)
                    or TITLE_RE.match(stripped_prop)
                    or METHOD_RE.match(stripped_prop)
                    or ZERO_PARAM_METHOD_RE.match(stripped_prop)
                ):
                    break

                # 型:説明 形式を優先
                pm = PARAM_RE.match(stripped_prop)
                if pm:
                    pname, ptype, pdesc = pm.groups()
                    parameter = _build_parameter(pname, ptype, pdesc, prop_index)
                    param_entry.properties.append(parameter)
                    prop_index += 1
                    last_idx = j
                    j += 1
                    continue

                # コロン無しコメント形式
                pm_loose = PARAM_RE_LOOSE.match(stripped_prop)
                if pm_loose:
                    pname, comment = pm_loose.groups()
                    if ":" in comment or "：" in comment:
                        raw2 = re.split(r"[:：]", comment, maxsplit=1)
                        ptype = raw2[0].strip()
                        pdesc = raw2[1].strip() if len(raw2) > 1 else ""
                    else:
                        ptype = comment.strip()
                        pdesc = ""
                    parameter = _build_parameter(pname, ptype, pdesc, prop_index)
                    param_entry.properties.append(parameter)
                    prop_index += 1
                    last_idx = j
                    j += 1
                    continue

                # 属性解釈不可 -> ブロック終了
                break

            # ソース範囲（属性を含む）を付与
            end_for_source = last_idx if prop_index > 0 else i
            attach_source(param_entry, start_idx, end_for_source)
            _finalize_entry(param_entry, entries)
            block_start_idx = None
            i = j
            continue

        # 既知のパラメータオブジェクト名の検出
        for param_name in PARAM_OBJECT_NAMES:
            if line.strip() == f"〇{param_name}":
                logger.info(
                    f"[api] KNOWN_PARAM_OBJECT matched: name='{param_name}' "
                    f"at line={i}"
                )
                param_entry = ApiEntry(
                    entry_type="object",
                    name=param_name,
                    description=f"{param_name}のパラメータ定義",
                    category=current_object,
                    object_name=current_object,
                    title_jp=param_name,
                    raw_return="",
                    returns=ReturnSpec(
                        type="void", description="", is_array=False
                    ),
                )
                start_idx = block_start_idx if block_start_idx is not None else i
                attach_source(param_entry, start_idx, i)
                _finalize_entry(param_entry, entries)
                block_start_idx = None
                i += 1
                break
        else:
            # パラメータオブジェクトが見つからなかった場合、通常の処理を続行
            pass

        # タイトルの検出
        title_match = TITLE_RE.match(line)
        if title_match:
            logger.info(
                f"[api] TITLE matched: title='{title_match.group(1).strip()}' at line={i}"
            )
            current_title = title_match.group(1).strip()
            current_return = ""
            block_start_idx = i
            i += 1
            if i < len(lines):
                ret_line = lines[i].strip()
                ret_match = RETURN_RE.match(ret_line)
                if ret_match:
                    logger.debug(
                        f"[api] RETURN matched: '{_log_snippet(ret_line)}' at line={i}"
                    )
                    current_return = ret_match.group(1).strip()
                    i += 1
            continue

        zero_match = ZERO_PARAM_METHOD_RE.match(line)
        if zero_match:
            logger.info(
                f"[api] ZERO-PARAM METHOD matched: name='{zero_match.group(1)}' at line={i}"
            )
            method_name = zero_match.group(1)
            entry = ApiEntry(
                entry_type="function",
                name=method_name,
                description=current_title,
                category=current_object,
                object_name=current_object,
                title_jp=current_title,
                raw_return=current_return,
                returns=ReturnSpec(
                    type=_guess_return_type(current_return),
                    description=current_return,
                    is_array=_guess_return_is_array(current_return),
                ),
            )
            start_idx = block_start_idx if block_start_idx is not None else i
            attach_source(entry, start_idx, i)
            _finalize_entry(entry, entries)
            block_start_idx = None
            i += 1
            continue

        method_match = METHOD_RE.match(line)
        if method_match:
            logger.info(
                f"[api] METHOD start matched: name='{method_match.group(1)}' at line={i}"
            )
            method_name = method_match.group(1)
            entry_start_idx = block_start_idx if block_start_idx is not None else i
            entry_end_idx = i
            current_entry = ApiEntry(
                entry_type="function",
                name=method_name,
                description=current_title,
                category=current_object,
                object_name=current_object,
                title_jp=current_title,
                raw_return=current_return,
                returns=ReturnSpec(
                    type=_guess_return_type(current_return),
                    description=current_return,
                    is_array=_guess_return_is_array(current_return),
                ),
            )
            collecting = True
            param_index = 0
            block_start_idx = None
            i += 1
            continue
        if collecting and current_entry:
            processed_line = re.sub(r"\s*\)\s*(?=//)", "", line)
            param_match = PARAM_RE.match(processed_line)
            if param_match:
                logger.debug(
                    f"[api] PARAM matched: name='{param_match.group(1)}', "
                    f"raw='{_log_snippet(processed_line)}' at line={i}"
                )
                pname, ptype, pdesc = param_match.groups()
                _consume_param(pname, ptype, pdesc)
                continue

            # より柔軟なパラメータ解析を追加
            # 例: "bShow ) // bool: 表示する時はTrue"
            flexible_param_match = FLEXIBLE_PARAM_RE.match(line)
            if flexible_param_match:
                logger.debug(
                    f"[api] FLEXIBLE_PARAM matched: name='{flexible_param_match.group(2)}', "
                    f"raw='{_log_snippet(line)}' at line={i}"
                )
                pname = flexible_param_match.group(2)
                ptype = flexible_param_match.group(3).strip()
                pdesc = flexible_param_match.group(4).strip()
                _consume_param(pname, ptype, pdesc)
                continue

            loose_match = PARAM_RE_LOOSE.match(line)
            if loose_match:
                logger.debug(
                    f"[api] PARAM_LOOSE matched: name='{loose_match.group(1)}', raw='{_log_snippet(line)}' at line={i}"
                )
                pname, comment = loose_match.groups()
                if ":" in comment or "：" in comment:
                    raw = re.split(r"[:：]", comment, maxsplit=1)
                    ptype = raw[0].strip()
                    pdesc = raw[1].strip() if len(raw) > 1 else ""
                else:
                    ptype = comment.strip()
                    pdesc = ""
                _consume_param(pname, ptype, pdesc)
                continue
            bare = raw_line
            comment = ""
            if ")" in bare:
                bare = bare.split(")", 1)[0]
            if "//" in bare:
                parts = bare.split("//", 1)
                bare = parts[0]
                comment = parts[1].strip()
            pname_ptype = _parse_bare_param(bare)
            if pname_ptype:
                logger.debug(
                    f"[api] BARE_PARAM matched: raw='{_log_snippet(bare)}' at line={i}"
                )
                pname, ptype = pname_ptype
                _consume_param(pname, ptype, comment)
                continue
            if _is_closing_line(raw_line):
                idx_close = raw_line.rfind(")")
                before = raw_line[:idx_close]
                if "," in before:
                    candidate = before.split(",")[-1].strip()
                else:
                    candidate = before.strip()
                candidate = candidate.rstrip(")")
                comment = ""
                if "//" in raw_line:
                    comment = raw_line.split("//", 1)[1].strip()
                synthetic = candidate
                if comment:
                    synthetic = f"{candidate} // {comment}"
                matched = False
                pm2 = PARAM_RE.match(synthetic)
                if pm2:
                    logger.debug(
                        f"[api] SYNTHETIC PARAM matched: name='{pm2.group(1)}', "
                        f"raw='{_log_snippet(synthetic)}' at line={i}"
                    )
                    pname, ptype, pdesc = pm2.groups()
                    _consume_param(pname, ptype, pdesc)
                    matched = True
                else:
                    pm2_loose = PARAM_RE_LOOSE.match(synthetic)
                    if pm2_loose:
                        logger.debug(
                            f"[api] SYNTHETIC PARAM_LOOSE matched: "
                            f"name='{pm2_loose.group(1)}', "
                            f"raw='{_log_snippet(synthetic)}' at line={i}"
                        )
                        pname, comment2 = pm2_loose.groups()
                        if ":" in comment2 or "：" in comment2:
                            raw2 = re.split(r"[:：]", comment2, maxsplit=1)
                            ptype = raw2[0].strip()
                            pdesc = raw2[1].strip() if len(raw2) > 1 else ""
                        else:
                            ptype = comment2.strip()
                            pdesc = ""
                        _consume_param(pname, ptype, pdesc)
                        matched = True
                    else:
                        logger.debug(
                            f"[api] TRY BARE after close: raw='{_log_snippet(candidate)}' at line={i}"
                        )
                        bare_parsed = _parse_bare_param(candidate)
                        if bare_parsed:
                            pname, ptype = bare_parsed
                            _consume_param(pname, ptype, "")
                            matched = True
                if not matched and current_entry:
                    entry_end_idx = i
                    attach_source(current_entry, entry_start_idx, entry_end_idx)
                    _finalize_entry(current_entry, entries)
                    current_entry = None
                    collecting = False
                    entry_start_idx = None
                    entry_end_idx = None
                    i += 1
                continue
        i += 1

    if current_entry:
        attach_source(current_entry, entry_start_idx, entry_end_idx or (len(lines) - 1))
        _finalize_entry(current_entry, entries)

    return entries


def parse_api_documents(
    api_doc_path: Path | None = None, api_arg_path: Path | None = None
) -> ApiBundle:
    logger = get_logger("rule_parser.parse_api_documents")
    logger.info("Starting API document parsing...")

    config = PipelineConfig()
    doc_path = Path(api_doc_path) if api_doc_path else config.api_doc_path
    arg_path = Path(api_arg_path) if api_arg_path else config.api_arg_path

    logger.info(f"API doc path: {doc_path}")
    logger.info(f"API arg path: {arg_path}")

    logger.info("Reading API document files...")
    api_text = _read_text_file(doc_path)
    arg_text = _read_text_file(arg_path)

    logger.info(f"API doc text length: {len(api_text)} characters")
    logger.info(f"API arg text length: {len(arg_text)} characters")

    logger.info("Parsing type definitions...")
    types = parse_type_definitions(arg_text, path=arg_path)
    logger.info(f"Parsed {len(types)} type definitions")

    logger.info("Parsing API specifications...")
    entries = parse_api_specs(api_text, path=doc_path)
    logger.info(f"Parsed {len(entries)} API entries")

    checklist = ["parsed_api_doc", "parsed_api_arg"]
    logger.info("API document parsing completed successfully")

    return ApiBundle(type_definitions=types, api_entries=entries, checklist=checklist)


def _should_include_field(value, field_name):
    """空でない値のみフィールドを含める"""
    if field_name in ["examples", "one_of"]:
        return value and len(value) > 0
    if field_name == "source_text":
        return value and value.strip()
    return value is not None and value != ""


def dump_bundle(bundle: ApiBundle, path: Path) -> None:
    logger = get_logger("rule_parser.dump_bundle")
    logger.debug(f"Dumping bundle to {path}")
    logger.info(
        f"Bundle contains {len(bundle.api_entries)} API entries "
        f"and {len(bundle.type_definitions)} type definitions"
    )

    path.parent.mkdir(parents=True, exist_ok=True)

    # 空配列を生成しない形式で出力
    output_data = {
        "type_definitions": [
            {
                "name": td.name,
                "canonical_type": td.canonical_type,
                "description": td.description,
                **(
                    {
                        k: v
                        for k, v in {
                            "examples": td.examples,
                            "one_of": td.one_of,
                        }.items()
                        if _should_include_field(v, k)
                    }
                ),
                **(
                    {"source": {"text": td.source.text}}
                    if td.source
                    and _should_include_field(td.source.text, "source_text")
                    else {}
                ),
            }
            for td in bundle.type_definitions
        ],
        "api_entries": [
            {
                "name": entry.name,
                "description": entry.description,
                "category": entry.category,
                "entry_type": entry.entry_type,
                **(
                    {
                        "params": [
                            {
                                "name": param.name,
                                "type": param.type,
                                "description": param.description,
                                **(
                                    {"is_required": param.is_required}
                                    if param.is_required
                                    else {}
                                ),
                                **(
                                    {"position": param.position}
                                    if param.position is not None
                                    else {}
                                ),
                                **(
                                    {"raw_type": param.raw_type}
                                    if param.raw_type
                                    else {}
                                ),
                                **(
                                    {"dimension": param.dimension}
                                    if param.dimension
                                    else {}
                                ),
                            }
                            for param in entry.params
                        ]
                    }
                    if entry.params
                    else {}
                ),
                **(
                    {
                        "properties": [
                            {
                                "name": prop.name,
                                "type": prop.type,
                                "description": prop.description,
                                **(
                                    {"is_required": prop.is_required}
                                    if prop.is_required
                                    else {}
                                ),
                                **(
                                    {"position": prop.position}
                                    if prop.position is not None
                                    else {}
                                ),
                                **(
                                    {"raw_type": prop.raw_type}
                                    if prop.raw_type
                                    else {}
                                ),
                                **(
                                    {"dimension": prop.dimension}
                                    if prop.dimension
                                    else {}
                                ),
                            }
                            for prop in entry.properties
                        ]
                    }
                    if entry.properties
                    else {}
                ),
                **(
                    {
                        "returns": {
                            "type": entry.returns.type if entry.returns else "void",
                            "description": (
                                entry.returns.description if entry.returns else ""
                            ),
                            **(
                                {"is_array": entry.returns.is_array}
                                if entry.returns and entry.returns.is_array
                                else {}
                            ),
                            **(
                                {"raw_type": entry.returns.raw_type}
                                if entry.returns and entry.returns.raw_type
                                else {}
                            ),
                        }
                    }
                    if entry.returns and entry.returns.type != "void"
                    else {}
                ),
                **(
                    {"title_jp": entry.title_jp}
                    if entry.title_jp and entry.title_jp != entry.description
                    else {}
                ),
                **(
                    {"object_name": entry.object_name}
                    if entry.object_name and entry.object_name != entry.category
                    else {}
                ),
                **(
                    {"source": {"text": entry.source.text}}
                    if entry.source
                    and _should_include_field(entry.source.text, "source_text")
                    else {}
                ),
            }
            for entry in bundle.api_entries
        ],
    }

    path.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(f"Successfully saved bundle to {path}")


def _parameter_from_dict(payload: Dict[str, object]) -> Parameter:
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    return Parameter(
        name=payload["name"],
        type=payload.get("type", ""),
        description=payload.get("description", ""),
        is_required=metadata.get("is_required", False),
        default_value=metadata.get("default_value"),
        position=metadata.get("position", 0),
        raw_type=metadata.get("raw_type"),
        dimension=metadata.get("dimension"),
    )


def _parameters_from_list(values: List[Dict[str, object]]) -> List[Parameter]:
    return [_parameter_from_dict(item) for item in values]


def _return_from_dict(data: Optional[Dict[str, object]]) -> Optional[ReturnSpec]:
    if not data:
        return None
    return ReturnSpec(
        type=data.get("type", "void"),
        description=data.get("description", ""),
        is_array=data.get("is_array", False),
        raw_type=data.get("raw_type"),
    )


def _type_definition_from_dict(data: Dict[str, object]) -> TypeDefinition:
    source_payload = data.get("source")
    source = (
        SourceFragment.from_dict(source_payload)
        if isinstance(source_payload, dict)
        else None
    )
    return TypeDefinition(
        name=data.get("name", ""),
        description=data.get("description", ""),
        examples=list(data.get("examples", [])),
        canonical_type=data.get("canonical_type"),
        py_type=data.get("py_type"),
        one_of=data.get("one_of"),
        source=source,
    )


def _api_entry_from_dict(data: Dict[str, object]) -> ApiEntry:
    params = _parameters_from_list(data.get("params", []))
    properties = _parameters_from_list(data.get("properties", []))
    returns = _return_from_dict(data.get("returns"))
    source_payload = data.get("source")
    source = (
        SourceFragment.from_dict(source_payload)
        if isinstance(source_payload, dict)
        else None
    )
    return ApiEntry(
        entry_type=data.get("entry_type", "function"),
        name=data.get("name", ""),
        description=data.get("description", ""),
        category=data.get("category", ""),
        params=params,
        properties=properties,
        returns=returns,
        notes=data.get("notes"),
        implementation_status=data.get("implementation_status", "implemented"),
        object_name=data.get("object_name"),
        title_jp=data.get("title_jp"),
        raw_return=data.get("raw_return"),
        source=source,
    )


def load_bundle(path: Path) -> ApiBundle:
    logger = get_logger("rule_parser.load_bundle")
    logger.info(f"Loading bundle from {path}")

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    type_definitions = [
        _type_definition_from_dict(item) for item in payload.get("type_definitions", [])
    ]
    entries = [_api_entry_from_dict(item) for item in payload.get("api_entries", [])]
    checklist = payload.get("checklist", [])

    logger.info(
        f"Loaded bundle with {len(entries)} API entries and {len(type_definitions)} type definitions"
    )
    return ApiBundle(
        type_definitions=type_definitions, api_entries=entries, checklist=checklist
    )


def generate_vector_chunks(entries: Iterable[ApiEntry]) -> Iterable[dict]:
    logger = get_logger("rule_parser.generate_vector_chunks")
    logger.debug("Generating vector chunks from API entries")

    chunk_count = 0
    for entry in entries:
        limited_params = []
        for idx, param in enumerate(entry.params):
            if idx >= VECTOR_PARAM_LIMIT:
                break
            description = (
                param.description.strip()
                if param.description
                else FALLBACK_PARAM_DESCRIPTION
            )
            limited_params.append(f"- {param.name} ({param.type}): {description}")
        if len(entry.params) > VECTOR_PARAM_LIMIT:
            remaining = len(entry.params) - VECTOR_PARAM_LIMIT
            limited_params.append(f"... ({remaining} more parameters)")
        params_text = "\n".join(limited_params)
        summary_parts = []
        if entry.description:
            summary_parts.append(f"Description: {entry.description}")
        if entry.category:
            summary_parts.append(f"Category: {entry.category}")
        if entry.returns and entry.returns.description:
            summary_parts.append(f"Return: {entry.returns.description}")
        if params_text:
            summary_parts.append(params_text)
        payload = {
            "id": entry.name,
            "object": entry.object_name,
            "title_jp": entry.title_jp,
            "content": "\n".join(summary_parts),
        }
        chunk_count += 1
        yield payload

    logger.info(f"Generated {chunk_count} vector chunks")
