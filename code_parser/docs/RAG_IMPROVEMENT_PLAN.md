# Code Parser RAG改善計画書

## 概要

現在の `code_parser` システムを、独自APIを活用したPythonコード生成のための効果的なRAG（Retrieval-Augmented Generation）システムに進化させるための改善計画です。

## 現状分析

### 現在のシステム構成
- Tree-sitterによるPythonコードの構文解析
- Neo4jへのグラフデータ格納
- LLM統合（OpenAI API使用）
- 基本的なクエリエンジン

### 主要な課題
1. **RAG生成に必要な情報の不足**
   - 機能説明、使用例、入力/出力の詳細情報が不十分
   - エラーハンドリング情報の不足
   - パフォーマンス特性や制限事項の情報なし

2. **データモデルの限界**
   - 構文要素中心で意味的な関係が表現できない
   - 機能的な類似性や互換性の関係が不足

3. **検索・取得機能の課題**
   - 意味的な検索、機能的な検索ができない
   - ベクトル検索の未実装

4. **LLM分析の限界**
   - 基本的な説明のみで、コード生成に必要な詳細情報が不足

## 改善方針

### 1. データモデルの拡張

#### 1.1 ノードタイプの拡張
```python
class EnhancedNodeType(Enum):
    # 既存のノードタイプ
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    VARIABLE = "Variable"
    
    # 新規追加
    FUNCTION_DOC = "FunctionDoc"          # 関数の詳細ドキュメント
    USAGE_EXAMPLE = "UsageExample"        # 使用例
    ERROR_HANDLING = "ErrorHandling"      # エラーハンドリング情報
    PERFORMANCE_INFO = "PerformanceInfo"  # パフォーマンス情報
    INPUT_OUTPUT = "InputOutput"          # 入出力仕様
    DEPENDENCY = "Dependency"             # 依存関係
    ALTERNATIVE = "Alternative"           # 代替実装
    TEST_CASE = "TestCase"                # テストケース
    DOCUMENTATION = "Documentation"       # ドキュメント
    CONFIGURATION = "Configuration"       # 設定情報
    SECURITY_INFO = "SecurityInfo"        # セキュリティ情報
    VERSION_INFO = "VersionInfo"          # バージョン情報
```

#### 1.2 リレーションタイプの拡張
```python
class EnhancedRelationType(Enum):
    # 既存のリレーションタイプ
    CONTAINS = "CONTAINS"
    CALLS = "CALLS"
    USES = "USES"
    
    # 新規追加
    SIMILAR_FUNCTION = "SIMILAR_FUNCTION"     # 類似機能
    COMPATIBLE_INPUT = "COMPATIBLE_INPUT"     # 入力互換性
    COMPATIBLE_OUTPUT = "COMPATIBLE_OUTPUT"   # 出力互換性
    USES_PATTERN = "USES_PATTERN"            # 使用パターン
    ERROR_RELATED = "ERROR_RELATED"          # エラー関連
    PERFORMANCE_RELATED = "PERFORMANCE_RELATED"  # パフォーマンス関連
    ALTERNATIVE_TO = "ALTERNATIVE_TO"        # 代替関係
    TESTED_BY = "TESTED_BY"                  # テスト対象
    DOCUMENTS = "DOCUMENTS"                  # ドキュメント対象
    DEPENDS_ON = "DEPENDS_ON"                # 依存関係
    IMPLEMENTS = "IMPLEMENTS"                # 実装関係
    EXTENDS = "EXTENDS"                      # 拡張関係
    MIGRATES_TO = "MIGRATES_TO"              # 移行先
    SECURITY_RELATED = "SECURITY_RELATED"    # セキュリティ関連
```

### 2. ベクトル検索の実装

#### 2.1 ベクトル化対象
- **関数の機能説明**: 関数の目的、処理内容、入力/出力の詳細
- **クラスの目的・役割**: クラスの設計思想、責任範囲、使用場面
- **使用例の説明**: サンプルコード、実装パターン、ベストプラクティス
- **エラーメッセージ・対処法**: 例外の種類、原因、解決方法、予防策
- **パフォーマンス特性**: 計算量、メモリ使用量、最適化ポイント
- **セキュリティ情報**: 脆弱性、認証要件、アクセス制御
- **ドキュメント**: API仕様、使用方法、制限事項
- **テストケース**: 動作確認、境界値、エラーケース

#### 2.2 ベクトル検索エンジン（ChromaDB）
```python
class VectorSearchEngine:
    def __init__(self, persist_directory="./vector_store", 
                 collection_name="code_functions", 
                 embedding_model="sentence-transformers/all-MiniLM-L6-v2"):
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        # 埋め込みモデルの初期化
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # ChromaDBクライアントの初期化
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # コレクションの作成（最適化された設定）
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 128,
                "hnsw:search_ef": 64,
                "hnsw:m": 32,
                "dimension": self.embedding_dimension
            }
        )
        
        # パフォーマンスメトリクスの初期化
        self.performance_metrics = {}
        self.query_cache = {}  # クエリキャッシュ
        self.cache_ttl = 3600  # キャッシュ有効期限（秒）
    
    def add_function_embedding(self, function_id: str, embedding: List[float], 
                              metadata: Dict[str, Any]):
        """関数のベクトルとメタデータを追加"""
        start_time = time.time()
        self.collection.add(
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[function_id]
        )
        self.performance_metrics[f"add_{function_id}"] = time.time() - start_time
    
    def search_similar_functions(self, query_text: str, 
                               filters: Dict[str, Any] = None, 
                               top_k: int = 5, 
                               similarity_threshold: float = 0.7) -> List[Dict]:
        """類似関数を検索（テキストクエリ対応、メタデータフィルタリング対応）"""
        start_time = time.time()
        
        # クエリのベクトル化
        query_embedding = self.embedding_model.encode(query_text).tolist()
        
        # キャッシュチェック
        cache_key = f"{hash(query_text)}_{hash(str(filters))}_{top_k}"
        if cache_key in self.query_cache:
            cache_time, cached_results = self.query_cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                self.performance_metrics[f"cached_search_{top_k}"] = 0.001
                return cached_results
        
        # ChromaDB検索の実行
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # 類似度フィルタリング用に多めに取得
            where=filters
        )
        
        # 類似度フィルタリング
        filtered_results = []
        if results['distances']:
            for i, distance in enumerate(results['distances'][0]):
                similarity = 1 - distance  # コサイン距離を類似度に変換
                if similarity >= similarity_threshold:
                    filtered_results.append({
                        'id': results['ids'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': similarity,
                        'distance': distance
                    })
        
        # top_kに制限
        filtered_results = sorted(filtered_results, key=lambda x: x['similarity'], reverse=True)[:top_k]
        
        # キャッシュに保存
        self.query_cache[cache_key] = (time.time(), filtered_results)
        
        # パフォーマンス記録
        search_time = time.time() - start_time
        self.performance_metrics[f"search_{top_k}"] = search_time
        
        return filtered_results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        if not self.performance_metrics:
            return {}
        
        add_times = [v for k, v in self.performance_metrics.items() if k.startswith("add_")]
        search_times = [v for k, v in self.performance_metrics.items() if k.startswith("search_")]
        cached_times = [v for k, v in self.performance_metrics.items() if k.startswith("cached_search_")]
        
        # キャッシュヒット率の計算
        total_searches = len(search_times) + len(cached_times)
        cache_hit_rate = len(cached_times) / total_searches if total_searches > 0 else 0
        
        return {
            "total_operations": len(self.performance_metrics),
            "add_operations": len(add_times),
            "search_operations": len(search_times),
            "cached_operations": len(cached_times),
            "cache_hit_rate": cache_hit_rate,
            "avg_add_time": sum(add_times) / len(add_times) if add_times else 0,
            "avg_search_time": sum(search_times) / len(search_times) if search_times else 0,
            "avg_cached_search_time": sum(cached_times) / len(cached_times) if cached_times else 0,
            "max_add_time": max(add_times) if add_times else 0,
            "max_search_time": max(search_times) if search_times else 0,
            "collection_size": self.collection.count(),
            "embedding_dimension": self.embedding_dimension,
            "cache_size": len(self.query_cache)
        }
    
    def clear_cache(self):
        """クエリキャッシュをクリア"""
        self.query_cache.clear()
    
    def optimize_collection(self):
        """コレクションの最適化を実行"""
        # コレクションの統計情報を取得
        stats = self.collection.count()
        
        # サイズに応じた最適化設定の適用
        if stats > 10000:
            # 大規模コレクション用の設定
            optimal_metadata = {
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 256,
                "hnsw:search_ef": 128,
                "hnsw:m": 64
            }
        elif stats > 1000:
            # 中規模コレクション用の設定
            optimal_metadata = {
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 128,
                "hnsw:search_ef": 64,
                "hnsw:m": 32
            }
        else:
            # 小規模コレクション用の設定
            optimal_metadata = {
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 64,
                "hnsw:search_ef": 32,
                "hnsw:m": 16
            }
        
        # 新しいコレクションを作成して最適化設定を適用
        optimized_collection_name = f"{self.collection.name}_optimized"
        optimized_collection = self.client.create_collection(
            name=optimized_collection_name,
            metadata=optimal_metadata
        )
        
        return optimized_collection
```

### 3. 高度なLLM分析の実装

#### 3.1 分析対象の拡張
```python
class EnhancedLLMAnalyzer:
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        """LLMアナライザーの初期化"""
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser
        
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.json_parser = JsonOutputParser()
        
        # 分析テンプレートの定義
        self.function_analysis_template = ChatPromptTemplate.from_messages([
            ("system", """あなたはPythonコードの専門家です。以下の関数を詳細に分析し、指定された形式でJSON出力してください。

分析項目：
1. 関数の目的と役割（簡潔で明確な説明）
2. 入力パラメータの詳細（型、制約、説明、デフォルト値）
3. 戻り値の詳細（型、説明、Noneの場合の条件）
4. 使用例とサンプルコード（実際に動作するコード）
5. エラーハンドリングの方法（発生する可能性のある例外と対処法）
6. パフォーマンス特性（時間計算量、空間計算量、最適化ポイント）
7. 制限事項や注意点（使用上の注意、制約条件）
8. 関連する関数やクラス（依存関係、類似機能）
9. セキュリティ上の考慮事項（入力検証、権限チェック）
10. テストケースの提案（境界値、エラーケース）

出力形式は必ず有効なJSONで、日本語で記述してください。"""),
            ("human", "関数名: {function_name}\nコード:\n```python\n{code_text}\n```")
        ])
        
        self.class_analysis_template = ChatPromptTemplate.from_messages([
            ("system", """あなたはPythonクラス設計の専門家です。以下のクラスを詳細に分析し、指定された形式でJSON出力してください。

分析項目：
1. クラスの目的と責任範囲
2. 設計パターン（Singleton、Factory、Observer等）
3. 継承・実装関係
4. 主要メソッドの説明
5. インスタンス変数の役割
6. 使用場面とベストプラクティス
7. パフォーマンス特性
8. スレッドセーフティ
9. セキュリティ上の考慮事項
10. テスト戦略

出力形式は必ず有効なJSONで、日本語で記述してください。"""),
            ("human", "クラス名: {class_name}\nコード:\n```python\n{class_text}\n```")
        ])
    
    def analyze_function_purpose(self, function_node: SyntaxNode) -> Dict[str, Any]:
        """関数の目的と機能を詳細分析"""
        try:
            # プロンプトの実行
            chain = self.function_analysis_template | self.llm | self.json_parser
            
            response = chain.invoke({
                "function_name": function_node.name,
                "code_text": function_node.text
            })
            
            # 分析結果の検証と補完
            validated_response = self._validate_function_analysis(response)
            
            return validated_response
            
        except Exception as e:
            # エラー時のフォールバック処理
            return self._generate_fallback_analysis(function_node, str(e))
    
    def analyze_class_design(self, class_node: SyntaxNode) -> Dict[str, Any]:
        """クラスの設計パターンと使用方法を分析"""
        try:
            chain = self.class_analysis_template | self.llm | self.json_parser
            
            response = chain.invoke({
                "class_name": class_node.name,
                "class_text": class_node.text
            })
            
            validated_response = self._validate_class_analysis(response)
            
            return validated_response
            
        except Exception as e:
            return self._generate_fallback_class_analysis(class_node, str(e))
    
    def _validate_function_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """関数分析結果の検証と補完"""
        required_fields = [
            "purpose", "input_spec", "output_spec", "usage_examples",
            "error_handling", "performance", "limitations", "related_functions"
        ]
        
        validated = {}
        for field in required_fields:
            if field in analysis and analysis[field]:
                validated[field] = analysis[field]
            else:
                validated[field] = self._get_default_value(field)
        
        return validated
    
    def _get_default_value(self, field: str) -> Any:
        """フィールドのデフォルト値を取得"""
        defaults = {
            "purpose": "分析できませんでした",
            "input_spec": {},
            "output_spec": {},
            "usage_examples": [],
            "error_handling": [],
            "performance": {},
            "limitations": [],
            "related_functions": []
        }
        return defaults.get(field, "")
    
    def analyze_error_patterns(self, code_text: str) -> Dict[str, Any]:
        """エラーパターンと対処法を分析"""
        error_analysis_template = ChatPromptTemplate.from_messages([
            ("system", """あなたはPythonエラーハンドリングの専門家です。以下のコードからエラーパターンを分析し、対処法を提案してください。

分析項目：
1. 発生する可能性のある例外の種類
2. 各例外の原因と発生条件
3. 具体的な対処法とコード例
4. 予防策とベストプラクティス
5. ログ出力の推奨事項
6. ユーザーへの適切なエラーメッセージ

出力形式は必ず有効なJSONで、日本語で記述してください。"""),
            ("human", "コード:\n```python\n{code_text}\n```")
        ])
        
        try:
            chain = error_analysis_template | self.llm | self.json_parser
            response = chain.invoke({"code_text": code_text})
            return self._validate_error_analysis(response)
        except Exception as e:
            return {"error": f"エラー分析に失敗しました: {str(e)}"}
    
    def _validate_class_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """クラス分析結果の検証と補完"""
        required_fields = [
            "purpose", "design_pattern", "inheritance", "methods",
            "instance_variables", "usage_scenarios", "performance", "thread_safety"
        ]
        
        validated = {}
        for field in required_fields:
            if field in analysis and analysis[field]:
                validated[field] = analysis[field]
            else:
                validated[field] = self._get_default_class_value(field)
        
        return validated
    
    def _get_default_class_value(self, field: str) -> Any:
        """クラス分析フィールドのデフォルト値を取得"""
        defaults = {
            "purpose": "分析できませんでした",
            "design_pattern": "不明",
            "inheritance": [],
            "methods": [],
            "instance_variables": [],
            "usage_scenarios": [],
            "performance": {},
            "thread_safety": "不明"
        }
        return defaults.get(field, "")
    
    def _validate_error_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """エラー分析結果の検証と補完"""
        required_fields = [
            "exceptions", "causes", "solutions", "prevention",
            "logging", "user_messages"
        ]
        
        validated = {}
        for field in required_fields:
            if field in analysis and analysis[field]:
                validated[field] = analysis[field]
            else:
                validated[field] = []
        
        return validated
    
    def _generate_fallback_analysis(self, function_node: SyntaxNode, error: str) -> Dict[str, Any]:
        """フォールバック分析の生成"""
        return {
            "purpose": f"分析エラー: {error}",
            "input_spec": {},
            "output_spec": {},
            "usage_examples": [],
            "error_handling": [],
            "performance": {},
            "limitations": [],
            "related_functions": []
        }
    
    def _generate_fallback_class_analysis(self, class_node: SyntaxNode, error: str) -> Dict[str, Any]:
        """フォールバッククラス分析の生成"""
        return {
            "purpose": f"分析エラー: {error}",
            "design_pattern": "不明",
            "inheritance": [],
            "methods": [],
            "instance_variables": [],
            "usage_scenarios": [],
            "performance": {},
            "thread_safety": "不明"
        }
```

#### 3.2 分析結果の構造化
```python
@dataclass
class FunctionAnalysis:
    purpose: str                    # 関数の目的
    input_spec: Dict[str, Any]     # 入力仕様
    output_spec: Dict[str, Any]    # 出力仕様
    usage_examples: List[str]      # 使用例
    error_handling: List[str]      # エラーハンドリング
    performance: Dict[str, Any]    # パフォーマンス特性
    limitations: List[str]         # 制限事項
    alternatives: List[str]        # 代替案
    related_functions: List[str]   # 関連関数
    security_considerations: List[str]  # セキュリティ上の考慮事項
    test_cases: List[str]          # テストケースの提案

@dataclass
class ClassAnalysis:
    purpose: str                    # クラスの目的
    design_pattern: str             # 設計パターン
    inheritance: List[str]          # 継承関係
    methods: List[Dict[str, Any]]  # メソッド一覧
    instance_variables: List[Dict[str, Any]]  # インスタンス変数
    usage_scenarios: List[str]     # 使用場面
    performance: Dict[str, Any]    # パフォーマンス特性
    thread_safety: str             # スレッドセーフティ
    security_considerations: List[str]  # セキュリティ上の考慮事項
    test_strategy: str             # テスト戦略

@dataclass
class ErrorAnalysis:
    exceptions: List[Dict[str, Any]]  # 例外の種類と詳細
    causes: List[str]              # 発生原因
    solutions: List[Dict[str, Any]]   # 解決方法
    prevention: List[str]          # 予防策
    logging: List[str]             # ログ出力の推奨事項
    user_messages: List[str]       # ユーザーへのエラーメッセージ

### 4. 使用例とサンプルコードの収集

#### 4.1 自動収集機能
```python
class CodeExampleCollector:
    def __init__(self, project_root: str):
        """コード例収集器の初期化"""
        self.project_root = Path(project_root)
        self.test_patterns = ["*test*.py", "*Test*.py", "test_*.py", "*_test.py"]
        self.example_patterns = ["*example*.py", "*Example*.py", "*demo*.py", "*Demo*.py"]
        
    def collect_usage_examples(self, function_name: str) -> List[Dict[str, Any]]:
        """関数の使用例を包括的に収集"""
        examples = []
        
        # 1. 同じファイル内での使用例
        file_examples = self._find_in_file_usage(function_name)
        examples.extend(file_examples)
        
        # 2. テストファイルでの使用例
        test_examples = self._find_test_examples(function_name)
        examples.extend(test_examples)
        
        # 3. ドキュメント文字列からの抽出
        docstring_examples = self._extract_docstring_examples(function_name)
        examples.extend(docstring_examples)
        
        # 4. インポート先での使用例
        import_examples = self._find_import_usage(function_name)
        examples.extend(import_examples)
        
        # 5. サンプル・デモファイルでの使用例
        sample_examples = self._find_sample_usage(function_name)
        examples.extend(sample_examples)
        
        # 品質スコアの計算
        for example in examples:
            example['quality_score'] = self._calculate_quality_score(example)
        
        # 品質スコアでソート
        examples.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return examples
    
    def _find_in_file_usage(self, function_name: str) -> List[Dict[str, Any]]:
        """同じファイル内での使用例を検索"""
        examples = []
        
        # 関数定義を含むファイルを検索
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 関数定義の検索
                if f"def {function_name}(" in content:
                    # 関数呼び出しの検索
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if function_name in line and f"def {function_name}(" not in line:
                            examples.append({
                                'type': 'in_file_usage',
                                'file_path': str(py_file.relative_to(self.project_root)),
                                'line_number': i,
                                'code': line.strip(),
                                'context': self._get_context(lines, i, 3),
                                'source': 'same_file'
                            })
            except Exception as e:
                continue
        
        return examples
    
    def _find_test_examples(self, function_name: str) -> List[Dict[str, Any]]:
        """テストファイルから使用例を検索"""
        examples = []
        
        for pattern in self.test_patterns:
            for test_file in self.project_root.rglob(pattern):
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if function_name in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if function_name in line and f"def {function_name}(" not in line:
                                examples.append({
                                    'type': 'test_example',
                                    'file_path': str(test_file.relative_to(self.project_root)),
                                    'line_number': i,
                                    'code': line.strip(),
                                    'context': self._get_context(lines, i, 5),
                                    'source': 'test_file'
                                })
                except Exception as e:
                    continue
        
        return examples
    
    def _extract_docstring_examples(self, function_name: str) -> List[Dict[str, Any]]:
        """ドキュメント文字列からサンプルコードを抽出"""
        examples = []
        
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 関数定義とドキュメント文字列の検索
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if f"def {function_name}(" in line:
                        # ドキュメント文字列の抽出
                        docstring = self._extract_docstring(lines, i)
                        if docstring:
                            # コードブロックの抽出
                            code_blocks = self._extract_code_blocks(docstring)
                            for j, code_block in enumerate(code_blocks):
                                examples.append({
                                    'type': 'docstring_example',
                                    'file_path': str(py_file.relative_to(self.project_root)),
                                    'line_number': i + 1,
                                    'code': code_block,
                                    'context': f"ドキュメント文字列内のサンプルコード {j+1}",
                                    'source': 'docstring'
                                })
            except Exception as e:
                continue
        
        return examples
    
    def _get_context(self, lines: List[str], line_number: int, context_lines: int) -> str:
        """指定行の前後のコンテキストを取得"""
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context_lines_list = lines[start:end]
        return '\n'.join(context_lines_list)
    
    def _extract_docstring(self, lines: List[str], function_line: int) -> str:
        """関数定義後のドキュメント文字列を抽出"""
        docstring = ""
        i = function_line + 1
        
        # 空行をスキップ
        while i < len(lines) and lines[i].strip() == "":
            i += 1
        
        # ドキュメント文字列の開始を確認
        if i < len(lines) and '"""' in lines[i]:
            start_line = i
            i += 1
            
            # ドキュメント文字列の終了を検索
            while i < len(lines) and '"""' not in lines[i]:
                docstring += lines[i] + '\n'
                i += 1
            
            if i < len(lines) and '"""' in lines[i]:
                docstring += lines[i]
        
        return docstring.strip()
    
    def _extract_code_blocks(self, docstring: str) -> List[str]:
        """ドキュメント文字列からコードブロックを抽出"""
        import re
        
        # ```python または ``` で囲まれたコードブロックを検索
        code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', docstring, re.DOTALL)
        
        # インデントされたコードブロックも検索
        indented_blocks = re.findall(r'^\s+(.*?)$', docstring, re.MULTILINE | re.DOTALL)
        
        return code_blocks + indented_blocks
    
    def _calculate_quality_score(self, example: Dict[str, Any]) -> float:
        """使用例の品質スコアを計算"""
        score = 0.0
        
        # ソースタイプによる基本スコア
        source_scores = {
            'test_file': 0.9,
            'docstring': 0.8,
            'same_file': 0.7,
            'sample_file': 0.6
        }
        score += source_scores.get(example['source'], 0.5)
        
        # コードの長さによる調整
        code_length = len(example['code'])
        if 10 <= code_length <= 100:
            score += 0.2  # 適切な長さ
        elif code_length > 100:
            score += 0.1  # 長すぎる
        
        # コンテキストの充実度
        context_length = len(example['context'])
        if context_length > 100:
            score += 0.1
        
        return min(score, 1.0)

#### 4.2 サンプルコードの品質向上
```python
class ExampleCodeEnhancer:
    def __init__(self):
        """サンプルコード品質向上器の初期化"""
        self.import_patterns = {
            'pandas': ['import pandas as pd', 'from pandas import DataFrame'],
            'numpy': ['import numpy as np', 'from numpy import array'],
            'matplotlib': ['import matplotlib.pyplot as plt', 'from matplotlib import pyplot'],
            'requests': ['import requests', 'from requests import get, post'],
            'json': ['import json', 'from json import loads, dumps'],
            'os': ['import os', 'from os import path, listdir'],
            'pathlib': ['from pathlib import Path'],
            'datetime': ['from datetime import datetime, timedelta'],
            'typing': ['from typing import List, Dict, Optional, Union']
        }
    
    def validate_example(self, code: str) -> Dict[str, Any]:
        """サンプルコードの妥当性を検証"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'score': 0.0
        }
        
        try:
            # 基本的な構文チェック
            compile(code, '<string>', 'exec')
            validation_result['score'] += 0.3
        except SyntaxError as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"構文エラー: {str(e)}")
        
        # インポート文の検証
        import_issues = self._validate_imports(code)
        validation_result['warnings'].extend(import_issues['warnings'])
        validation_result['suggestions'].extend(import_issues['suggestions'])
        
        # コードの長さチェック
        if len(code) > 500:
            validation_result['warnings'].append("コードが長すぎます。簡潔にしてください。")
            validation_result['score'] -= 0.1
        
        # 変数名の品質チェック
        naming_issues = self._validate_naming(code)
        validation_result['suggestions'].extend(naming_issues)
        
        # エラーハンドリングのチェック
        if 'try:' in code and 'except:' in code:
            validation_result['score'] += 0.2
        else:
            validation_result['suggestions'].append("エラーハンドリングの追加を検討してください。")
        
        # ドキュメント文字列のチェック
        if '"""' in code or "'''" in code:
            validation_result['score'] += 0.1
        
        validation_result['score'] = min(validation_result['score'], 1.0)
        
        return validation_result
    
    def add_context(self, code: str, context: str) -> str:
        """サンプルコードに文脈を追加"""
        enhanced_code = f"""# {context}
# 使用例: このコードは以下の目的で使用されます

{code}

# 注意事項:
# - 実行前に必要なライブラリをインストールしてください
# - 適切なエラーハンドリングを追加してください
# - 本番環境での使用前に十分なテストを行ってください
"""
        return enhanced_code
    
    def generate_minimal_example(self, function_signature: str) -> str:
        """最小限の使用例を生成"""
        # 関数シグネチャから基本的な使用例を生成
        if '(' in function_signature and ')' in function_signature:
            func_name = function_signature.split('(')[0].strip()
            params = function_signature.split('(')[1].split(')')[0].strip()
            
            if params:
                param_list = [p.strip().split('=')[0].strip() for p in params.split(',')]
                example_params = []
                
                for param in param_list:
                    if param:
                        # パラメータ名から適切なサンプル値を推測
                        if 'file' in param.lower() or 'path' in param.lower():
                            example_params.append('"example.txt"')
                        elif 'data' in param.lower() or 'list' in param.lower():
                            example_params.append('[1, 2, 3]')
                        elif 'count' in param.lower() or 'num' in param.lower():
                            example_params.append('5')
                        elif 'name' in param.lower():
                            example_params.append('"example"')
                        else:
                            example_params.append('None')
                
                example_code = f"""# 基本的な使用例
result = {func_name}({', '.join(example_params)})
print(result)"""
            else:
                example_code = f"""# 基本的な使用例
result = {func_name}()
print(result)"""
        else:
            example_code = f"""# 基本的な使用例
result = {function_signature}
print(result)"""
        
        return example_code
    
    def _validate_imports(self, code: str) -> Dict[str, List[str]]:
        """インポート文の妥当性を検証"""
        result = {'warnings': [], 'suggestions': []}
        
        # 使用されている可能性のあるライブラリを検出
        used_libraries = []
        for lib, patterns in self.import_patterns.items():
            for pattern in patterns:
                if pattern.split()[-1] in code or lib in code:
                    used_libraries.append(lib)
                    break
        
        # インポート文の検証
        import_lines = [line for line in code.split('\n') if line.strip().startswith(('import ', 'from '))]
        
        for lib in used_libraries:
            if not any(lib in line for line in import_lines):
                result['warnings'].append(f"'{lib}'ライブラリのインポートが見つかりません")
        
        return result
    
    def _validate_naming(self, code: str) -> List[str]:
        """変数名の品質を検証"""
        suggestions = []
        
        # 短すぎる変数名のチェック
        import re
        short_vars = re.findall(r'\b[a-z]{1,2}\b', code)
        if short_vars:
            suggestions.append("変数名が短すぎます。意味が分かりやすい名前にしてください。")
        
        # アンダースコアで始まる変数名のチェック
        if '_' in code:
            suggestions.append("アンダースコアで始まる変数名は避けてください。")
        
        return suggestions

### 5. エラーハンドリング情報の充実

#### 5.1 エラー情報の抽出
```python
class ErrorHandlingAnalyzer:
    def extract_exceptions(self, code: str) -> List[str]:
        """コードから例外処理を抽出"""
        pass
    
    def analyze_error_patterns(self, code: str) -> Dict[str, Any]:
        """エラーパターンを分析"""
        pass
    
    def generate_error_handling_guide(self, function_name: str) -> str:
        """エラーハンドリングガイドを生成"""
        pass
```

#### 5.2 エラー対処法のデータベース
```python
@dataclass
class ErrorHandlingInfo:
    error_type: str                # エラーの種類
    description: str               # エラーの説明
    common_causes: List[str]       # よくある原因
    solutions: List[str]           # 解決方法
    prevention: List[str]          # 予防方法
    examples: List[str]            # 例
```

### 6. パフォーマンス特性の分析

#### 6.1 パフォーマンスメトリクス
```python
class PerformanceAnalyzer:
    def analyze_time_complexity(self, code: str) -> str:
        """時間計算量を分析"""
        pass
    
    def analyze_space_complexity(self, code: str) -> str:
        """空間計算量を分析"""
        pass
    
    def identify_bottlenecks(self, code: str) -> List[str]:
        """ボトルネックを特定"""
        pass
    
    def suggest_optimizations(self, code: str) -> List[str]:
        """最適化提案を生成"""
        pass
```

### 7. ChromaDBパフォーマンス評価・最適化

#### 7.1 パフォーマンスベンチマーク
```python
class ChromaDBPerformanceBenchmark:
    def __init__(self, vector_engine: VectorSearchEngine):
        self.vector_engine = vector_engine
        self.benchmark_results = {}
    
    def benchmark_bulk_insert(self, embeddings: List[List[float]], 
                            metadata_list: List[Dict[str, Any]], 
                            batch_sizes: List[int] = [1, 10, 100, 1000]):
        """バッチ挿入のパフォーマンスを測定"""
        for batch_size in batch_sizes:
            start_time = time.time()
            for i in range(0, len(embeddings), batch_size):
                batch_embeddings = embeddings[i:i+batch_size]
                batch_metadata = metadata_list[i:i+batch_size]
                batch_ids = [f"test_{i}_{j}" for j in range(len(batch_embeddings))]
                
                self.vector_engine.collection.add(
                    embeddings=batch_embeddings,
                    metadatas=batch_metadata,
                    ids=batch_ids
                )
            
            total_time = time.time() - start_time
            self.benchmark_results[f"bulk_insert_{batch_size}"] = {
                "total_time": total_time,
                "avg_time_per_item": total_time / len(embeddings),
                "items_per_second": len(embeddings) / total_time
            }
    
    def benchmark_search_performance(self, query_embeddings: List[List[float]], 
                                   top_k_values: List[int] = [1, 5, 10, 20, 50]):
        """検索パフォーマンスを測定"""
        for top_k in top_k_values:
            search_times = []
            for query_emb in query_embeddings:
                start_time = time.time()
                self.vector_engine.collection.query(
                    query_embeddings=[query_emb],
                    n_results=top_k
                )
                search_times.append(time.time() - start_time)
            
            self.benchmark_results[f"search_top_{top_k}"] = {
                "avg_time": sum(search_times) / len(search_times),
                "min_time": min(search_times),
                "max_time": max(search_times),
                "std_dev": statistics.stdev(search_times) if len(search_times) > 1 else 0
            }
    
    def benchmark_filtering_performance(self, query_embedding: List[float], 
                                      filter_combinations: List[Dict[str, Any]]):
        """フィルタリングパフォーマンスを測定"""
        for i, filters in enumerate(filter_combinations):
            start_time = time.time()
            self.vector_engine.collection.query(
                query_embeddings=[query_embedding],
                n_results=10,
                where=filters
            )
            filter_time = time.time() - start_time
            
            self.benchmark_results[f"filter_combo_{i}"] = {
                "filters": filters,
                "search_time": filter_time,
                "filter_complexity": len(filters)
            }
    
    def get_benchmark_summary(self) -> Dict[str, Any]:
        """ベンチマーク結果の要約"""
        return {
            "benchmark_results": self.benchmark_results,
            "vector_engine_stats": self.vector_engine.get_performance_stats(),
            "collection_info": {
                "total_count": self.vector_engine.collection.count(),
                "embedding_dimension": self.vector_engine.collection.metadata.get("dimension", "unknown")
            }
        }
```

#### 7.2 パフォーマンス最適化戦略
```python
class ChromaDBOptimizer:
    def __init__(self, vector_engine: VectorSearchEngine):
        self.vector_engine = vector_engine
    
    def optimize_collection_settings(self, collection_size: int, 
                                   embedding_dimension: int) -> Dict[str, Any]:
        """コレクション設定の最適化"""
        # HNSWパラメータの最適化
        if collection_size < 1000:
            # 小規模コレクション
            optimal_settings = {
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 64,
                "hnsw:search_ef": 32,
                "hnsw:m": 16
            }
        elif collection_size < 10000:
            # 中規模コレクション
            optimal_settings = {
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 128,
                "hnsw:search_ef": 64,
                "hnsw:m": 32
            }
        else:
            # 大規模コレクション
            optimal_settings = {
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 256,
                "hnsw:search_ef": 128,
                "hnsw:m": 64
            }
        
        return optimal_settings
    
    def create_performance_indexes(self):
        """パフォーマンス向上のためのインデックス作成"""
        # メタデータフィールドのインデックス作成
        # 注意: ChromaDBの現在のバージョンでは自動インデックス作成
        # 将来的な拡張性を考慮した設計
    
    def optimize_batch_operations(self, batch_size: int = 1000):
        """バッチ操作の最適化"""
        # バッチサイズの最適化
        # メモリ使用量と処理速度のバランス
        return {
            "optimal_batch_size": batch_size,
            "memory_usage_estimate": batch_size * 0.001,  # MB単位の概算
            "expected_throughput": batch_size / 0.1  # 秒あたりの処理数
        }
```

#### 7.3 パフォーマンス監視・アラート
```python
class ChromaDBPerformanceMonitor:
    def __init__(self, vector_engine: VectorSearchEngine, 
                 alert_thresholds: Dict[str, float] = None):
        self.vector_engine = vector_engine
        self.alert_thresholds = alert_thresholds or {
            "search_time_threshold": 1.0,  # 秒
            "insert_time_threshold": 0.5,  # 秒
            "memory_usage_threshold": 0.8   # 80%
        }
        self.performance_history = []
    
    def monitor_performance(self) -> Dict[str, Any]:
        """現在のパフォーマンスを監視"""
        current_stats = self.vector_engine.get_performance_stats()
        
        # パフォーマンス履歴に追加
        self.performance_history.append({
            "timestamp": time.time(),
            "stats": current_stats
        })
        
        # 履歴の保持（最新100件）
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # アラートチェック
        alerts = self.check_alerts(current_stats)
        
        return {
            "current_stats": current_stats,
            "alerts": alerts,
            "trends": self.analyze_trends()
        }
    
    def check_alerts(self, stats: Dict[str, Any]) -> List[str]:
        """アラート条件をチェック"""
        alerts = []
        
        if stats.get("avg_search_time", 0) > self.alert_thresholds["search_time_threshold"]:
            alerts.append(f"検索時間が閾値を超過: {stats['avg_search_time']:.3f}秒")
        
        if stats.get("avg_add_time", 0) > self.alert_thresholds["insert_time_threshold"]:
            alerts.append(f"挿入時間が閾値を超過: {stats['avg_add_time']:.3f}秒")
        
        return alerts
    
    def analyze_trends(self) -> Dict[str, Any]:
        """パフォーマンストレンドを分析"""
        if len(self.performance_history) < 2:
            return {}
        
        recent_stats = [h["stats"] for h in self.performance_history[-10:]]
        older_stats = [h["stats"] for h in self.performance_history[-20:-10]]
        
        if not older_stats:
            return {}
        
        # 平均値の変化
        recent_avg_search = sum(s.get("avg_search_time", 0) for s in recent_stats) / len(recent_stats)
        older_avg_search = sum(s.get("avg_search_time", 0) for s in older_stats) / len(older_stats)
        
        search_trend = "改善" if recent_avg_search < older_avg_search else "悪化"
        
        return {
            "search_time_trend": search_trend,
            "search_time_change": recent_avg_search - older_avg_search,
            "collection_growth": recent_stats[-1].get("collection_size", 0) - older_stats[0].get("collection_size", 0)
        }
```

## 実装計画

### Phase 1: 基盤拡張（2-3週間）
1. データモデルの拡張
2. ベクトル検索エンジンの実装（ChromaDB）
3. 基本的なベクトル化機能
4. パフォーマンスベンチマーク基盤の構築

### Phase 2: LLM分析強化（2-3週間）
1. 高度なLLM分析の実装
2. 分析結果の構造化
3. 分析品質の向上

### Phase 3: 情報収集・充実（3-4週間）
1. 使用例収集システム
2. エラーハンドリング情報の充実
3. パフォーマンス分析の実装

### Phase 4: 検索・取得の高度化（2-3週間）
1. 意味的検索の実装
2. 機能的検索の実装
3. ハイブリッド検索（構造化+ベクトル）の実装

### Phase 5: 統合・テスト（2-3週間）
1. 全機能の統合
2. パフォーマンステスト・ベンチマーク
3. ChromaDB最適化の適用
4. 品質保証・ドキュメント整備

## 期待される効果

### 1. RAG生成の品質向上
- より適切なコード片の検索・取得
- 文脈に応じたコード生成
- エラーハンドリングの改善

### 2. コード生成の精度向上
- 入力要件に合致した関数の提案
- 使用例に基づく実装の改善
- パフォーマンスを考慮したコード生成

### 3. 開発効率の向上
- 既存コードの再利用性向上
- 学習コストの削減
- コード品質の向上

## 技術要件

### 必要なライブラリ
```bash
# ベクトル検索
pip install sentence-transformers faiss-cpu chromadb

# パフォーマンス分析
pip install ast-complexity

# 追加のLLM機能
pip install langchain-community langchain-openai

# グラフ分析
pip install networkx matplotlib
```

### システム要件
- Neo4j 4.4以上
- Python 3.8以上
- 十分なメモリ（ベクトル検索用）
- GPU（オプション、ベクトル化高速化用）

## リスクと対策

### 1. パフォーマンスリスク
- **リスク**: ベクトル検索による処理時間の増加
- **対策**: ChromaDBのHNSWパラメータ最適化、バッチ処理の最適化、パフォーマンス監視の実装

### 2. データ品質リスク
- **リスク**: LLM分析結果の品質が不安定
- **対策**: 複数LLMでの検証、人間による品質チェック

### 3. スケーラビリティリスク
- **リスク**: 大規模コードベースでの処理負荷
- **対策**: バッチ処理、分散処理の実装、ChromaDBのコレクション分割戦略

### 4. ChromaDB固有のリスク
- **リスク**: 大規模データでの検索性能低下
- **対策**: 段階的なFAISS移行計画、ハイブリッド検索（ChromaDB + FAISS）の実装

## 次のステップ

1. **詳細設計**: 各機能の詳細仕様の策定
2. **プロトタイプ**: 主要機能のプロトタイプ実装
3. **パフォーマンス評価**: ChromaDBベンチマークの実行と最適化
4. **本格実装**: 段階的な実装とテスト
5. **継続的パフォーマンス監視**: 本番環境でのパフォーマンス追跡

---

*このドキュメントは継続的に更新されます。最新版は常に確認してください。*
