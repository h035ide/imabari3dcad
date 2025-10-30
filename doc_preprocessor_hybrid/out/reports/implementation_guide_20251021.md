# API パーサー改善実装ガイド
## 実行日時: 2025-10-21 14:01:46

---

## 概要

本ガイドは、`doc_preprocessor_hybrid` モジュールの改善を実装するための詳細な手順書です。分析結果に基づいて、優先度の高い改善項目の具体的な実装方法を提供します。

---

## 1. 改善実装の全体計画

### 1.1 実装優先順位

| 優先度 | 改善項目 | 実装期間 | 期待効果 |
|--------|----------|----------|----------|
| 1 | オブジェクト名抽出 | 1週間 | オブジェクト名正答率 0% → 90% |
| 2 | パラメータ型解析改善 | 2週間 | パラメータ正答率 40.70% → 80% |
| 3 | 説明文抽出改善 | 2週間 | Description正答率 45.83% → 70% |

### 1.2 実装アプローチ
- **段階的実装**: 各改善項目を独立して実装
- **テスト駆動**: テストを先に作成してから実装
- **後方互換性**: 既存の機能を壊さない実装

---

## 2. 改善実装1: オブジェクト名抽出

### 2.1 問題の詳細

#### 2.1.1 現在の問題
```python
# 現在の実装ではオブジェクト名が抽出されない
@dataclass
class ApiEntry:
    name: str
    entry_type: str
    # object_name フィールドが存在しない
```

#### 2.1.2 期待される動作
```python
# 入力テキスト
"""
■Applicationオブジェクトのメソッド
〇EvoShipを終了する
返り値:なし
Quit()
"""

# 期待される出力
{
    "name": "Quit",
    "entry_type": "function", 
    "object_name": "Applicationオブジェクト"  # これが抽出されていない
}
```

### 2.2 実装手順

#### Step 1: データ構造の拡張

```python
# doc_preprocessor_hybrid/rule_parser.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ApiEntry:
    name: str
    entry_type: str
    category: Optional[str]
    title_jp: Optional[str]
    raw_return: Optional[str]
    return_description: Optional[str]
    params: List[Parameter]
    object_name: Optional[str]  # 追加
    source: Optional[SourceFragment]
```

#### Step 2: パーサークラスの修正

```python
# doc_preprocessor_hybrid/rule_parser.py
class ApiParser:
    def __init__(self):
        self.current_object_name = None
        
    def parse_api_specs(self, text: str, *, path: Path | None = None) -> List[ApiEntry]:
        """API仕様を解析してApiEntryオブジェクトのリストを返す"""
        lines = text.splitlines()
        entries = []
        current_entry = None
        
        for i, line in enumerate(lines):
            # オブジェクトヘッダーの検出
            header_match = self._match_object_header(line)
            if header_match:
                self.current_object_name = header_match.group(1) + "オブジェクト"
                continue
                
            # 既存の解析ロジック...
            entry = self._parse_function_entry(lines, i)
            if entry:
                # オブジェクト名を設定
                entry.object_name = self.current_object_name
                entries.append(entry)
                
        return entries
        
    def _match_object_header(self, line: str) -> Optional[Match[str]]:
        """オブジェクトヘッダーをマッチング"""
        pattern = r"■(.+?)オブジェクトのメソッド"
        return re.match(pattern, line.strip())
```

#### Step 3: テストの作成

```python
# tests/test_object_name_extraction.py
import pytest
from doc_preprocessor_hybrid.rule_parser import parse_api_specs

class TestObjectNameExtraction:
    def test_application_object_extraction(self):
        """Applicationオブジェクトの名前抽出テスト"""
        text = """
■Applicationオブジェクトのメソッド
〇EvoShipを終了する
返り値:なし
Quit()
"""
        entries = parse_api_specs(text)
        
        assert len(entries) == 1
        assert entries[0].name == "Quit"
        assert entries[0].object_name == "Applicationオブジェクト"
        
    def test_document_object_extraction(self):
        """Documentオブジェクトの名前抽出テスト"""
        text = """
■Documentオブジェクトのメソッド
〇ドキュメントを閉じる
返り値:なし
Close()
"""
        entries = parse_api_specs(text)
        
        assert len(entries) == 1
        assert entries[0].name == "Close"
        assert entries[0].object_name == "Documentオブジェクト"
        
    def test_multiple_objects_extraction(self):
        """複数オブジェクトの名前抽出テスト"""
        text = """
■Applicationオブジェクトのメソッド
〇Quit()
Quit()

■Documentオブジェクトのメソッド
〇Close()
Close()
"""
        entries = parse_api_specs(text)
        
        assert len(entries) == 2
        assert entries[0].object_name == "Applicationオブジェクト"
        assert entries[1].object_name == "Documentオブジェクト"
```

#### Step 4: 実装の実行

```bash
# テストの実行
uv run pytest tests/test_object_name_extraction.py -v

# パーサーの実行
uv run python doc_preprocessor_hybrid/main.py --api-doc data/src/api.txt --api-arg data/src/api_arg.txt

# バリデーションの実行
uv run python doc_preprocessor_hybrid/validate_structured.py --xml doc_preprocessor_hybrid/out/api_template.xml --json doc_preprocessor_hybrid/out/structured_api.json
```

---

## 3. 改善実装2: パラメータ型解析改善

### 3.1 問題の詳細

#### 3.1.1 現在の問題
```python
# 現在の実装では型情報が正確に抽出されない
def _build_parameter(name: str, raw_type: str, description: str, position: int) -> Parameter:
    # raw_type が "不明" になってしまう問題
    return Parameter(
        name=name,
        type_name=raw_type,  # ここが "不明" になる
        description=description,
        position=position
    )
```

#### 3.1.2 期待される動作
```python
# 入力テキスト
"bShow )　// bool: 表示する時はTrue"

# 期待される出力
{
    "name": "bShow",
    "type_name": "bool",  # 現在は "不明" になってしまう
    "description": "表示する時はTrue"
}
```

### 3.2 実装手順

#### Step 1: 型推論ロジックの強化

```python
# doc_preprocessor_hybrid/rule_parser.py
class TypeInference:
    """型推論を行うクラス"""
    
    TYPE_KEYWORDS = {
        'bool': ['bool', '真偽', 'true', 'false', 'True', 'False'],
        'integer': ['整数', 'int', '数値', '数'],
        'float': ['浮動小数点', 'float', '実数', '小数点'],
        'string': ['文字列', 'string', 'ファイル名', '名前', '名称'],
        'array': ['配列', 'array', '[]', '複数', 'リスト']
    }
    
    @classmethod
    def infer_type(cls, param_text: str) -> str:
        """パラメータテキストから型を推論"""
        param_lower = param_text.lower()
        
        # 直接的な型指定の検出
        for type_name, keywords in cls.TYPE_KEYWORDS.items():
            if any(keyword in param_lower for keyword in keywords):
                return type_name
                
        # パターンマッチングによる型推論
        if re.search(r'\d+', param_text):  # 数値が含まれる
            if '.' in param_text:
                return 'float'
            else:
                return 'integer'
                
        return 'unknown'
    
    @classmethod
    def extract_array_type(cls, param_text: str) -> str:
        """配列型の基底型を抽出"""
        # 例: "要素(配列)" -> "要素"
        match = re.search(r'(.+)\(配列\)', param_text)
        if match:
            base_type = match.group(1)
            return f"{base_type}[]"
        return param_text
```

#### Step 2: パラメータ解析関数の改善

```python
# doc_preprocessor_hybrid/rule_parser.py
def _build_parameter(name: str, raw_type: str, description: str, position: int) -> Parameter:
    """パラメータオブジェクトを構築"""
    
    # 型推論の実行
    if raw_type == "不明" or not raw_type:
        inferred_type = TypeInference.infer_type(description)
    else:
        inferred_type = raw_type
        
    # 配列型の処理
    if "配列" in description or "[]" in description:
        inferred_type = TypeInference.extract_array_type(description)
        
    return Parameter(
        name=name,
        type_name=inferred_type,
        description=description,
        position=position
    )
```

#### Step 3: パラメータ解析ロジックの改善

```python
# doc_preprocessor_hybrid/rule_parser.py
def _parse_parameter_line(self, line: str) -> Optional[Parameter]:
    """パラメータ行を解析"""
    
    # パラメータ名と説明の分離
    if '//' in line:
        name_part, desc_part = line.split('//', 1)
    else:
        name_part, desc_part = line, ""
        
    # パラメータ名の抽出
    name_match = re.search(r'(\w+)', name_part)
    if not name_match:
        return None
        
    name = name_match.group(1)
    
    # 型情報の抽出
    type_match = re.search(r'(\w+):\s*(.+)', desc_part)
    if type_match:
        raw_type = type_match.group(1)
        description = type_match.group(2)
    else:
        raw_type = "不明"
        description = desc_part.strip()
        
    return self._build_parameter(name, raw_type, description, 0)
```

#### Step 4: テストの作成

```python
# tests/test_parameter_type_inference.py
import pytest
from doc_preprocessor_hybrid.rule_parser import TypeInference, _build_parameter

class TestParameterTypeInference:
    def test_bool_type_inference(self):
        """bool型の推論テスト"""
        assert TypeInference.infer_type("bool: 表示する時はTrue") == "bool"
        assert TypeInference.infer_type("真偽値: True/False") == "bool"
        
    def test_integer_type_inference(self):
        """整数型の推論テスト"""
        assert TypeInference.infer_type("整数: 数値") == "integer"
        assert TypeInference.infer_type("int: 数") == "integer"
        
    def test_string_type_inference(self):
        """文字列型の推論テスト"""
        assert TypeInference.infer_type("文字列: ファイル名") == "string"
        assert TypeInference.infer_type("string: 名前") == "string"
        
    def test_array_type_inference(self):
        """配列型の推論テスト"""
        assert TypeInference.extract_array_type("要素(配列)") == "要素[]"
        assert TypeInference.extract_array_type("点(配列)") == "点[]"
        
    def test_parameter_building(self):
        """パラメータ構築のテスト"""
        param = _build_parameter("bShow", "不明", "bool: 表示する時はTrue", 0)
        
        assert param.name == "bShow"
        assert param.type_name == "bool"
        assert param.description == "表示する時はTrue"
```

---

## 4. 改善実装3: 説明文抽出改善

### 4.1 問題の詳細

#### 4.1.1 現在の問題
```python
# 現在の実装では日本語タイトルが抽出されない
def _parse_function_entry(lines: List[str], start_idx: int) -> Optional[ApiEntry]:
    # title_jp が空になってしまう問題
    return ApiEntry(
        name=name,
        title_jp=None,  # ここが空になってしまう
        # ...
    )
```

#### 4.1.2 期待される動作
```python
# 入力テキスト
"""
〇EvoShipを終了する
返り値:なし
Quit()
"""

# 期待される出力
{
    "name": "Quit",
    "title_jp": "EvoShipを終了する",  # これが抽出されていない
    "return_description": "なし"
}
```

### 4.2 実装手順

#### Step 1: 説明文抽出ロジックの改善

```python
# doc_preprocessor_hybrid/rule_parser.py
class FunctionMetadataExtractor:
    """関数のメタデータを抽出するクラス"""
    
    @classmethod
    def extract_metadata(cls, lines: List[str], start_idx: int) -> Dict[str, str]:
        """関数のメタデータを抽出"""
        metadata = {}
        
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            
            # 日本語タイトルの抽出
            if line.startswith('〇'):
                metadata['title_jp'] = line[1:].strip()
                
            # 返り値の抽出
            elif line.startswith('返り値:'):
                metadata['return_description'] = line[3:].strip()
                
            # 関数定義の検出（解析終了）
            elif re.match(r'\w+\(', line):
                break
                
        return metadata
    
    @classmethod
    def extract_return_type(cls, return_description: str) -> str:
        """返り値の説明から型を抽出"""
        if not return_description or return_description == "なし":
            return "void"
        elif "配列" in return_description:
            return "array"
        elif "オブジェクト" in return_description:
            return "object"
        else:
            return "unknown"
```

#### Step 2: 関数解析関数の改善

```python
# doc_preprocessor_hybrid/rule_parser.py
def _parse_function_entry(self, lines: List[str], start_idx: int) -> Optional[ApiEntry]:
    """関数エントリを解析"""
    
    # メタデータの抽出
    metadata = FunctionMetadataExtractor.extract_metadata(lines, start_idx)
    
    # 関数名の抽出
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        method_match = re.match(r'(\w+)\s*\(', line)
        if method_match:
            function_name = method_match.group(1)
            break
    else:
        return None
        
    # パラメータの抽出
    params = self._extract_parameters(lines, start_idx)
    
    # 返り値の処理
    return_description = metadata.get('return_description', '')
    return_type = FunctionMetadataExtractor.extract_return_type(return_description)
    
    return ApiEntry(
        name=function_name,
        entry_type="function",
        category=None,
        title_jp=metadata.get('title_jp'),
        raw_return=return_type,
        return_description=return_description,
        params=params,
        object_name=self.current_object_name,
        source=None
    )
```

#### Step 3: テストの作成

```python
# tests/test_description_extraction.py
import pytest
from doc_preprocessor_hybrid.rule_parser import FunctionMetadataExtractor, parse_api_specs

class TestDescriptionExtraction:
    def test_japanese_title_extraction(self):
        """日本語タイトルの抽出テスト"""
        text = """
■Applicationオブジェクトのメソッド
〇EvoShipを終了する
返り値:なし
Quit()
"""
        entries = parse_api_specs(text)
        
        assert len(entries) == 1
        assert entries[0].title_jp == "EvoShipを終了する"
        
    def test_return_description_extraction(self):
        """返り値説明の抽出テスト"""
        text = """
■Applicationオブジェクトのメソッド
〇Partオブジェクトを読み込む
返り値:Partオブジェクト
LoadPart(FileName, bForceEvaluation)
"""
        entries = parse_api_specs(text)
        
        assert len(entries) == 1
        assert entries[0].return_description == "Partオブジェクト"
        
    def test_metadata_extractor(self):
        """メタデータ抽出器のテスト"""
        lines = [
            "〇EvoShipを終了する",
            "返り値:なし", 
            "Quit()"
        ]
        
        metadata = FunctionMetadataExtractor.extract_metadata(lines, 0)
        
        assert metadata['title_jp'] == "EvoShipを終了する"
        assert metadata['return_description'] == "なし"
```

---

## 5. 統合テストとバリデーション

### 5.1 統合テストの作成

```python
# tests/test_integration.py
import pytest
from doc_preprocessor_hybrid.rule_parser import parse_api_specs
from doc_preprocessor_hybrid.validate_structured import calculate_accuracy_metrics

class TestIntegration:
    def test_full_pipeline_accuracy(self):
        """完全なパイプラインの精度テスト"""
        # 実際のファイルを使用
        with open('data/src/api.txt', 'r', encoding='utf-8') as f:
            api_text = f.read()
            
        entries = parse_api_specs(api_text)
        
        # 基本的な検証
        assert len(entries) > 0
        
        # オブジェクト名の検証
        object_names = [entry.object_name for entry in entries if entry.object_name]
        assert len(object_names) > 0, "オブジェクト名が抽出されていない"
        
        # パラメータ型の検証
        params_with_types = [p for entry in entries for p in entry.params if p.type_name != "不明"]
        assert len(params_with_types) > 0, "型情報が抽出されていない"
        
    def test_validation_improvement(self):
        """バリデーション精度の改善テスト"""
        # 改善前後の精度比較
        # (実装後に実行)
        pass
```

### 5.2 パフォーマンステスト

```python
# tests/test_performance.py
import time
import pytest
from doc_preprocessor_hybrid.rule_parser import parse_api_specs

class TestPerformance:
    def test_parsing_performance(self):
        """パース性能のテスト"""
        with open('data/src/api.txt', 'r', encoding='utf-8') as f:
            api_text = f.read()
            
        start_time = time.time()
        entries = parse_api_specs(api_text)
        end_time = time.time()
        
        # 性能要件: 1秒以内
        assert (end_time - start_time) < 1.0, f"パース時間が長すぎます: {end_time - start_time:.2f}秒"
        assert len(entries) > 0, "パース結果が空です"
```

---

## 6. デプロイメント手順

### 6.1 実装の段階的デプロイ

#### Phase 1: オブジェクト名抽出のデプロイ

```bash
# 1. ブランチの作成
git checkout -b feature/object-name-extraction

# 2. 実装の完了
# (上記の実装手順に従って実装)

# 3. テストの実行
uv run pytest tests/test_object_name_extraction.py -v

# 4. 統合テストの実行
uv run pytest tests/test_integration.py -v

# 5. パフォーマンステストの実行
uv run pytest tests/test_performance.py -v

# 6. コミットとプッシュ
git add .
git commit -m "feat: オブジェクト名抽出機能を実装"
git push origin feature/object-name-extraction

# 7. プルリクエストの作成
# (GitHub上でプルリクエストを作成)
```

#### Phase 2: パラメータ型解析改善のデプロイ

```bash
# 1. ブランチの作成
git checkout -b feature/parameter-type-improvement

# 2. 実装の完了
# (上記の実装手順に従って実装)

# 3. テストの実行
uv run pytest tests/test_parameter_type_inference.py -v

# 4. 既存テストの実行（回帰テスト）
uv run pytest tests/ -v

# 5. バリデーション精度の確認
uv run python doc_preprocessor_hybrid/validate_structured.py \
    --xml doc_preprocessor_hybrid/out/api_template.xml \
    --json doc_preprocessor_hybrid/out/structured_api.json

# 6. コミットとプッシュ
git add .
git commit -m "feat: パラメータ型解析機能を改善"
git push origin feature/parameter-type-improvement
```

#### Phase 3: 説明文抽出改善のデプロイ

```bash
# 1. ブランチの作成
git checkout -b feature/description-extraction-improvement

# 2. 実装の完了
# (上記の実装手順に従って実装)

# 3. テストの実行
uv run pytest tests/test_description_extraction.py -v

# 4. 全テストの実行
uv run pytest tests/ -v

# 5. 最終バリデーション
uv run python doc_preprocessor_hybrid/validate_structured.py \
    --xml doc_preprocessor_hybrid/out/api_template.xml \
    --json doc_preprocessor_hybrid/out/structured_api.json

# 6. コミットとプッシュ
git add .
git commit -m "feat: 説明文抽出機能を改善"
git push origin feature/description-extraction-improvement
```

### 6.2 品質保証チェックリスト

#### 6.2.1 実装前チェック
- [ ] 設計書の確認
- [ ] テストケースの作成
- [ ] 実装計画の確認

#### 6.2.2 実装中チェック
- [ ] 単体テストの実行
- [ ] コードレビューの実施
- [ ] ドキュメントの更新

#### 6.2.3 実装後チェック
- [ ] 統合テストの実行
- [ ] パフォーマンステストの実行
- [ ] バリデーション精度の確認
- [ ] 回帰テストの実行

---

## 7. トラブルシューティング

### 7.1 よくある問題と解決方法

#### 問題1: テストが失敗する
```bash
# 原因: 実装が不完全
# 解決方法: 実装を完了してからテストを実行

# デバッグ方法
uv run pytest tests/test_object_name_extraction.py -v -s
```

#### 問題2: パフォーマンスが低下する
```bash
# 原因: 正規表現の最適化不足
# 解決方法: 正規表現の最適化

# プロファイリング
python -m cProfile -s cumulative doc_preprocessor_hybrid/main.py
```

#### 問題3: バリデーション精度が向上しない
```bash
# 原因: 実装にバグがある
# 解決方法: デバッグログの確認

# デバッグログの確認
uv run python doc_preprocessor_hybrid/main.py --log-level DEBUG
```

### 7.2 ロールバック手順

```bash
# 問題が発生した場合のロールバック
git checkout main
git branch -D feature/problematic-feature
git push origin --delete feature/problematic-feature
```

---

## 8. まとめ

### 8.1 実装のポイント
1. **段階的実装**: 各機能を独立して実装・テスト
2. **テスト駆動**: テストを先に作成してから実装
3. **品質保証**: 各段階で品質を確認

### 8.2 期待される効果
- **オブジェクト名正答率**: 0% → 90%以上
- **パラメータ正答率**: 40.70% → 80%以上  
- **Description正答率**: 45.83% → 70%以上

### 8.3 今後の展開
- 機械学習ベースの型推論
- 多言語対応の強化
- リアルタイム解析機能

---

**実装ガイド作成者**: AI Assistant  
**作成日時**: 2025-10-21 14:01:46  
**バージョン**: 1.0
