from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .config import PipelineConfig
from .schemas import ApiBundle, ApiEntry, Parameter, ReturnSpec, TypeDefinition


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
    if name in ENUM_DESCRIPTION_SUFFIX_NAMES:
        first = lines[0].rstrip("。")
        if "のいずれか" not in first:
            first = f"{first}のいずれか"
        if not first.endswith("。"):
            first = f"{first}。"
        lines[0] = first
    return "\n".join(lines)


def _refine_element_definition(type_def: TypeDefinition) -> None:
    type_def.description = (
        "モデル内の要素を参照する識別子を受け取ります。\n"
        "- element_id: 既存要素を一意に識別する ID（例: ID@...）。\n"
        "- element_group: 要素グループ名。複数要素をまとめて参照します。\n"
        "- element_reference: 操作対象の単一要素を指すラベルや名称。\n"
        "- element_array: 面リストや辺リストなど、複数要素を配列で指定するケース。"
    )


def _apply_type_metadata(type_def: TypeDefinition) -> None:
    type_def.description = _normalize_type_definition_description(type_def.name, type_def.description)
    meta = TYPE_CANONICAL_MAP.get(type_def.name)
    if meta:
        type_def.canonical_type, type_def.py_type = meta
    one_of = TYPE_ONE_OF_MAP.get(type_def.name)
    if one_of:
        type_def.one_of = one_of
    if type_def.name == "要素":
        _refine_element_definition(type_def)
    if type_def.name == "点":
        type_def.description = (
            "モデル座標系の点を表す値を指定します。数値リテラルのほか、変数参照や式を利用できます。"
        )


def _build_point_variants(base: TypeDefinition) -> List[TypeDefinition]:
    variants: List[TypeDefinition] = []
    base_summary = base.description.split("\n")[0] if base.description else "座標を表す点"
    base_summary = base_summary.rstrip("。")
    for dim, token in (("2D", "cartesian_2d"), ("3D", "cartesian_3d")):
        desc = f"{base_summary}（{dim} 座標）"
        variants.append(
            TypeDefinition(
                name=f"{base.name}({dim})",
                description=f"{desc}。",
                examples=list(base.examples),
                canonical_type="point",
                py_type="str",
                one_of=[token, "variable_reference", "expression"],
            )
        )
    return variants


def _augment_type_definitions(definitions: List[TypeDefinition]) -> List[TypeDefinition]:
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
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _clean_type_name(raw: str) -> Tuple[str, bool]:
    name = raw.strip()
    # COM/IDL 属性の除去と代表型の正規化
    name = re.sub(r"\[[^\]]*\]", "", name).strip()  # [in], [out] など
    name = name.replace("BSTR", "string").replace("LPWSTR", "string").replace("LPSTR", "string")
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


def _build_parameter(name: str, raw_type: str, description: str, position: int) -> Parameter:
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
        param.type = f"{param.type}[]"
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
    cand = candidate.strip().rstrip(',').replace("\u3000", " ")
    # 括弧内属性はそのまま型側に残す
    tokens = re.split(r"\s+", cand)
    if not tokens:
        return None
    pname = tokens[-1]
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", pname):
        # 末尾が識別子でない場合は放棄
        return None
    ptype = " ".join(tokens[:-1]).strip() or "不明"
    return pname, ptype


def parse_type_definitions(text: str) -> List[TypeDefinition]:
    definitions: List[TypeDefinition] = []
    current_name = None
    current_lines: List[str] = []
    lines = _normalize_text(text).split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("■"):
            if current_name and current_lines:
                definitions.append(
                    TypeDefinition(name=current_name, description="\n".join(current_lines))
                )
            current_name = line.replace("■", "", 1).strip()
            current_lines = []
            i += 1
            continue
        if current_name:
            # bool型の特別処理：次の行が「以下のタイプは全てPythonの型としては文字列...」の場合はスキップ
            if current_name == "bool" and line == "以下のタイプは全てPythonの型としては文字列。文字列の書式の仕様":
                i += 1
                continue
            current_lines.append(line)
        i += 1

    if current_name and current_lines:
        definitions.append(TypeDefinition(name=current_name, description="\n".join(current_lines)))

    refined: List[TypeDefinition] = []
    for type_def in definitions:
        _apply_type_metadata(type_def)
        refined.append(type_def)
    return _augment_type_definitions(refined)


def _finalize_entry(entry: ApiEntry, entries: List[ApiEntry]) -> None:
    if entry.returns is None:
        entry.returns = ReturnSpec()
    entries.append(entry)


def parse_api_specs(text: str) -> List[ApiEntry]:
    entries: List[ApiEntry] = []
    lines = _normalize_text(text).split("\n")
    current_object = ""
    current_title = ""
    current_return = ""
    collecting = False
    current_entry: ApiEntry | None = None
    param_index = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        header_match = HEADER_RE.match(line)
        if header_match:
            current_object = header_match.group(1).strip()
            i += 1
            continue
        title_match = TITLE_RE.match(line)
        if title_match:
            current_title = title_match.group(1).strip()
            current_return = ""
            i += 1
            if i < len(lines):
                ret_match = RETURN_RE.match(lines[i].strip())
                if ret_match:
                    current_return = ret_match.group(1).strip()
                    i += 1
            continue
        # パラメータ無しの同一行メソッド（e.g., Quit(), Create3DDocument()）
        zero_match = ZERO_PARAM_METHOD_RE.match(line)
        if zero_match:
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
            entries.append(entry)
            i += 1
            continue

        method_match = METHOD_RE.match(line)
        if method_match:
            method_name = method_match.group(1)
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
            i += 1
            continue
        if collecting and current_entry:
            # 閉じ括弧を除去してからパラメータ解析（//の前の）を除去
            import re
            processed_line = re.sub(r'\s*\)\s*(?=//)', '', line.strip())
            param_match = PARAM_RE.match(processed_line)
            if param_match:
                pname, ptype, pdesc = param_match.groups()
                parameter = _build_parameter(pname, ptype, pdesc, param_index)
                current_entry.params.append(parameter)
                param_index += 1
                if _is_closing_line(line):
                    _finalize_entry(current_entry, entries)
                    current_entry = None
                    collecting = False
                i += 1
                continue
            # コロンなしコメントに対応（例: pOpt) // STLパラメータオブジェクト）
            loose_match = PARAM_RE_LOOSE.match(line)
            if loose_match:
                pname, comment = loose_match.groups()
                # コメント中にコロンがあれば型:説明として解釈、なければ型のみ
                if ":" in comment or "：" in comment:
                    raw = re.split(r"[:：]", comment, maxsplit=1)
                    ptype = raw[0].strip()
                    pdesc = raw[1].strip() if len(raw) > 1 else ""
                else:
                    ptype = comment.strip()
                    pdesc = ""
                parameter = _build_parameter(pname, ptype, pdesc, param_index)
                current_entry.params.append(parameter)
                param_index += 1
                if _is_closing_line(line):
                    _finalize_entry(current_entry, entries)
                    current_entry = None
                    collecting = False
                i += 1
                continue
            # コメントが無い純粋な型+名前行の救済（例: "[in] BSTR plane,")
            bare = line
            # 閉じ括弧以降を除去
            if ")" in bare:
                bare = bare.split(")", 1)[0]
            # コメント以降を除去
            if "//" in bare:
                bare = bare.split("//", 1)[0]
            # 末尾のパラメータ片を取得
            pname_ptype = _parse_bare_param(bare)
            if pname_ptype:
                pname, ptype = pname_ptype
                parameter = _build_parameter(pname, ptype, "", param_index)
                current_entry.params.append(parameter)
                param_index += 1
                if _is_closing_line(line):
                    _finalize_entry(current_entry, entries)
                    current_entry = None
                    collecting = False
                i += 1
                continue
            if _is_closing_line(line):
                idx_close = line.rfind(")")
                before = line[:idx_close]
                # カンマで分割して最後の要素を取得（従来の方法）
                if "," in before:
                    candidate = before.split(",")[-1].strip()
                else:
                    # カンマがない場合は、括弧の前の部分全体を候補とする
                    candidate = before.strip()

                # 閉じ括弧を除去
                candidate = candidate.rstrip(")")
                comment = ""
                if "//" in line:
                    comment = line.split("//", 1)[1].strip()
                synthetic = candidate
                if comment:
                    synthetic = f"{candidate} // {comment}"
                pm2 = PARAM_RE.match(synthetic)
                if pm2:
                    pname, ptype, pdesc = pm2.groups()
                    parameter = _build_parameter(pname, ptype, pdesc, param_index)
                    current_entry.params.append(parameter)
                else:
                    # 緩和版でも試す（コロン無しパターンの救済）
                    pm2_loose = PARAM_RE_LOOSE.match(synthetic)
                    if pm2_loose:
                        pname, comment2 = pm2_loose.groups()
                        if ":" in comment2 or "：" in comment2:
                            raw2 = re.split(r"[:：]", comment2, maxsplit=1)
                            ptype = raw2[0].strip()
                            pdesc = raw2[1].strip() if len(raw2) > 1 else ""
                        else:
                            ptype = comment2.strip()
                            pdesc = ""
                        parameter = _build_parameter(pname, ptype, pdesc, param_index)
                        current_entry.params.append(parameter)
                    else:
                        # コメント無しの純粋表記も救済
                        bare_parsed = _parse_bare_param(candidate)
                        if bare_parsed:
                            pname, ptype = bare_parsed
                            parameter = _build_parameter(pname, ptype, "", param_index)
                            current_entry.params.append(parameter)
                _finalize_entry(current_entry, entries)
                current_entry = None
                collecting = False
                i += 1
                continue
        i += 1
    return entries


def parse_api_documents(api_doc_path: Path | None = None, api_arg_path: Path | None = None) -> ApiBundle:
    config = PipelineConfig()
    doc_path = Path(api_doc_path) if api_doc_path else config.api_doc_path
    arg_path = Path(api_arg_path) if api_arg_path else config.api_arg_path

    api_text = _read_text_file(doc_path)
    arg_text = _read_text_file(arg_path)

    types = parse_type_definitions(arg_text)
    entries = parse_api_specs(api_text)

    checklist = ["parsed_api_doc", "parsed_api_arg"]

    return ApiBundle(type_definitions=types, api_entries=entries, checklist=checklist)


def dump_bundle(bundle: ApiBundle, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


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
    return TypeDefinition(
        name=data.get("name", ""),
        description=data.get("description", ""),
        examples=list(data.get("examples", [])),
        canonical_type=data.get("canonical_type"),
        py_type=data.get("py_type"),
        one_of=data.get("one_of"),
    )


def _api_entry_from_dict(data: Dict[str, object]) -> ApiEntry:
    params = _parameters_from_list(data.get("params", []))
    properties = _parameters_from_list(data.get("properties", []))
    returns = _return_from_dict(data.get("returns"))
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
    )


def load_bundle(path: Path) -> ApiBundle:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    type_definitions = [_type_definition_from_dict(item) for item in payload.get("type_definitions", [])]
    entries = [_api_entry_from_dict(item) for item in payload.get("api_entries", [])]
    checklist = payload.get("checklist", [])
    return ApiBundle(type_definitions=type_definitions, api_entries=entries, checklist=checklist)


def generate_vector_chunks(entries: Iterable[ApiEntry]) -> Iterable[dict]:
    for entry in entries:
        limited_params = []
        for idx, param in enumerate(entry.params):
            if idx >= VECTOR_PARAM_LIMIT:
                break
            description = param.description.strip() if param.description else FALLBACK_PARAM_DESCRIPTION
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
        yield payload
