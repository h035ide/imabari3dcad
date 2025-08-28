# 高度なLLM分析機能

このモジュールは、独自APIを活用したPythonコード生成のためのRAGシステムの一部として、高度なLLM分析機能を提供します。

## 主な機能

### 1. 関数分析 (Function Analysis)
- 関数の目的と役割の詳細分析
- 入力/出力仕様の抽出
- 使用例とサンプルコードの生成
- エラーハンドリング情報
- パフォーマンス特性の分析

### 2. クラス分析 (Class Analysis)  
- クラスの設計パターンの識別
- 継承・実装関係の分析
- メソッドとインスタンス変数の詳細
- 使用場面とベストプラクティス
- スレッドセーフティの評価

### 3. エラーパターン分析 (Error Pattern Analysis)
- 発生する可能性のある例外の特定
- エラーの原因と解決方法の提案
- 予防策とベストプラクティス
- 適切なログ出力の推奨事項

## 使用方法

### 基本的な使用例

```python
from code_parser import LLMAnalysisManager

# 分析マネージャーの初期化
manager = LLMAnalysisManager()

# 関数コードの分析
function_code = '''
def calculate_fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("nは0以上である必要があります")
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
'''

# 分析実行
result = manager.analyze_code_snippet(function_code, "function")
print(result["analysis"]["purpose"])
```

### ファイル全体の分析

```python
# Pythonファイル全体を分析
result = manager.analyze_python_file("example.py")

print(f"関数数: {len(result['functions'])}")
print(f"クラス数: {len(result['classes'])}")

# 最初の関数の分析結果
if result['functions']:
    func = result['functions'][0]
    print(f"関数名: {func['name']}")
    print(f"目的: {func['analysis']['purpose']}")
```

### エラーパターンの分析

```python
problematic_code = '''
def risky_function(data):
    result = data / 0  # ZeroDivisionError
    return result[1000]  # IndexError
'''

result = manager.analyze_code_snippet(problematic_code, "snippet")
error_analysis = result["error_analysis"]

print("発見された例外:")
for exception in error_analysis["exceptions"]:
    print(f"  - {exception}")
```

## クラス構成

### LLMAnalysisManager
使いやすいインターフェースを提供するメインクラス
- `analyze_python_file(file_path)`: ファイル全体の分析
- `analyze_code_snippet(code, element_type)`: コードスニペットの分析
- キャッシュ機能による高速化

### EnhancedLLMAnalyzer
LLMを使用した詳細分析を行うコアクラス
- `analyze_function_purpose(function_node)`: 関数分析
- `analyze_class_design(class_node)`: クラス分析
- `analyze_error_patterns(code_text)`: エラーパターン分析

### 分析結果スキーマ
- `FunctionAnalysis`: 関数分析結果
- `ClassAnalysis`: クラス分析結果
- `ErrorAnalysis`: エラー分析結果
- `SyntaxNode`: 構文ノード表現

## 必要な依存関係

```bash
# 基本機能
pip install ast

# LLM機能（オプション）
pip install langchain-openai langchain-core

# OpenAI API（環境変数で設定）
export OPENAI_API_KEY="your-api-key"
```

## 特徴

### 1. シンプルで分かりやすい設計
- 最小限の依存関係
- 明確なインターフェース
- 豊富なドキュメントとコメント

### 2. ロバストなエラーハンドリング
- LLMが利用できない場合のフォールバック
- 分析結果の検証と補完
- 例外処理とログ出力

### 3. パフォーマンス最適化
- 分析結果のキャッシュ機能
- 遅延初期化による高速起動
- メモリ効率的な設計

### 4. 拡張性
- プラグイン可能なアーキテクチャ
- カスタムプロンプトテンプレート
- 複数LLMモデルのサポート

## テスト

```bash
# 基本テストの実行
python test_llm_analysis.py

# 使用例の実行
python llm_analysis_example.py
```

## 今後の拡張予定

1. ベクトル検索機能の統合
2. Neo4jとの連携強化
3. パフォーマンス監視機能
4. 分析品質の継続的改善
5. 多言語対応（JavaScript、Java等）

## 注意事項

- LLM機能を使用するにはOpenAI APIキーが必要です
- 大量のコード分析時はAPI使用量にご注意ください
- 分析結果の品質はLLMモデルに依存します

## サポート

問題や質問がある場合は、プロジェクトのIssueまでお知らせください。