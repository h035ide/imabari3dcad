"""
高度なLLM分析機能

このモジュールは、コード分析のための高度なLLM機能を提供します。
関数、クラス、エラーパターンの詳細分析を行います。
"""

import json
import logging
from typing import Dict, Any, Optional
try:
    from .analysis_schemas import FunctionAnalysis, ClassAnalysis, ErrorAnalysis, SyntaxNode
except ImportError:
    from analysis_schemas import FunctionAnalysis, ClassAnalysis, ErrorAnalysis, SyntaxNode

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedLLMAnalyzer:
    """高度なLLM分析機能を提供するクラス"""
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        """
        LLMアナライザーの初期化
        
        Args:
            model_name: 使用するLLMモデル名
            temperature: LLMの温度パラメータ（0に近いほど一貫性が高い）
        """
        self.model_name = model_name
        self.temperature = temperature
        self.llm = None
        self.json_parser = None
        
        # 遅延初期化でLangChainをインポート（オプショナル依存）
        self._initialize_llm()
    
    def _initialize_llm(self):
        """LLMとパーサーの初期化"""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import JsonOutputParser
            
            self.llm = ChatOpenAI(model=self.model_name, temperature=self.temperature)
            self.json_parser = JsonOutputParser()
            logger.info(f"LLM初期化完了: {self.model_name}")
            
        except ImportError as e:
            logger.warning(f"LangChain not available: {e}")
            self.llm = None
            self.json_parser = None
    
    def analyze_function_purpose(self, function_node: SyntaxNode) -> FunctionAnalysis:
        """
        関数の目的と機能を詳細分析
        
        Args:
            function_node: 分析する関数ノード
            
        Returns:
            FunctionAnalysis: 関数分析結果
        """
        if not self.llm:
            return self._generate_fallback_function_analysis(function_node, "LLM not available")
        
        try:
            # プロンプトテンプレートの作成
            template = self._create_function_analysis_template()
            
            # プロンプトの実行
            chain = template | self.llm | self.json_parser
            
            response = chain.invoke({
                "function_name": function_node.name,
                "code_text": function_node.text
            })
            
            # 分析結果の検証と構造化
            validated_response = self._validate_function_analysis(response)
            
            # FunctionAnalysisオブジェクトの作成
            analysis = FunctionAnalysis(
                purpose=validated_response.get("purpose", ""),
                input_spec=validated_response.get("input_spec", {}),
                output_spec=validated_response.get("output_spec", {}),
                usage_examples=validated_response.get("usage_examples", []),
                error_handling=validated_response.get("error_handling", []),
                performance=validated_response.get("performance", {}),
                limitations=validated_response.get("limitations", []),
                alternatives=validated_response.get("alternatives", []),
                related_functions=validated_response.get("related_functions", []),
                security_considerations=validated_response.get("security_considerations", []),
                test_cases=validated_response.get("test_cases", [])
            )
            
            logger.info(f"関数分析完了: {function_node.name}")
            return analysis
            
        except Exception as e:
            logger.error(f"関数分析エラー: {e}")
            return self._generate_fallback_function_analysis(function_node, str(e))
    
    def analyze_class_design(self, class_node: SyntaxNode) -> ClassAnalysis:
        """
        クラスの設計パターンと使用方法を分析
        
        Args:
            class_node: 分析するクラスノード
            
        Returns:
            ClassAnalysis: クラス分析結果
        """
        if not self.llm:
            return self._generate_fallback_class_analysis(class_node, "LLM not available")
        
        try:
            # プロンプトテンプレートの作成
            template = self._create_class_analysis_template()
            
            chain = template | self.llm | self.json_parser
            
            response = chain.invoke({
                "class_name": class_node.name,
                "class_text": class_node.text
            })
            
            # 分析結果の検証と構造化
            validated_response = self._validate_class_analysis(response)
            
            # ClassAnalysisオブジェクトの作成
            analysis = ClassAnalysis(
                purpose=validated_response.get("purpose", ""),
                design_pattern=validated_response.get("design_pattern", ""),
                inheritance=validated_response.get("inheritance", []),
                methods=validated_response.get("methods", []),
                instance_variables=validated_response.get("instance_variables", []),
                usage_scenarios=validated_response.get("usage_scenarios", []),
                performance=validated_response.get("performance", {}),
                thread_safety=validated_response.get("thread_safety", ""),
                security_considerations=validated_response.get("security_considerations", []),
                test_strategy=validated_response.get("test_strategy", "")
            )
            
            logger.info(f"クラス分析完了: {class_node.name}")
            return analysis
            
        except Exception as e:
            logger.error(f"クラス分析エラー: {e}")
            return self._generate_fallback_class_analysis(class_node, str(e))
    
    def analyze_error_patterns(self, code_text: str) -> ErrorAnalysis:
        """
        エラーパターンと対処法を分析
        
        Args:
            code_text: 分析するコードテキスト
            
        Returns:
            ErrorAnalysis: エラー分析結果
        """
        if not self.llm:
            return ErrorAnalysis()
        
        try:
            # プロンプトテンプレートの作成
            template = self._create_error_analysis_template()
            
            chain = template | self.llm | self.json_parser
            response = chain.invoke({"code_text": code_text})
            
            # 分析結果の検証と構造化
            validated_response = self._validate_error_analysis(response)
            
            # ErrorAnalysisオブジェクトの作成
            analysis = ErrorAnalysis(
                exceptions=validated_response.get("exceptions", []),
                causes=validated_response.get("causes", []),
                solutions=validated_response.get("solutions", []),
                prevention=validated_response.get("prevention", []),
                logging=validated_response.get("logging", []),
                user_messages=validated_response.get("user_messages", [])
            )
            
            logger.info("エラーパターン分析完了")
            return analysis
            
        except Exception as e:
            logger.error(f"エラーパターン分析エラー: {e}")
            return ErrorAnalysis()
    
    def _create_function_analysis_template(self):
        """関数分析用のプロンプトテンプレートを作成"""
        from langchain_core.prompts import ChatPromptTemplate
        
        return ChatPromptTemplate.from_messages([
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
    
    def _create_class_analysis_template(self):
        """クラス分析用のプロンプトテンプレートを作成"""
        from langchain_core.prompts import ChatPromptTemplate
        
        return ChatPromptTemplate.from_messages([
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
    
    def _create_error_analysis_template(self):
        """エラー分析用のプロンプトテンプレートを作成"""
        from langchain_core.prompts import ChatPromptTemplate
        
        return ChatPromptTemplate.from_messages([
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
                validated[field] = self._get_default_function_value(field)
        
        return validated
    
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
    
    def _get_default_function_value(self, field: str) -> Any:
        """関数分析フィールドのデフォルト値を取得"""
        defaults = {
            "purpose": "分析できませんでした",
            "input_spec": {},
            "output_spec": {},
            "usage_examples": [],
            "error_handling": [],
            "performance": {},
            "limitations": [],
            "alternatives": [],
            "related_functions": [],
            "security_considerations": [],
            "test_cases": []
        }
        return defaults.get(field, "")
    
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
            "thread_safety": "不明",
            "security_considerations": [],
            "test_strategy": ""
        }
        return defaults.get(field, "")
    
    def _generate_fallback_function_analysis(self, function_node: SyntaxNode, error: str) -> FunctionAnalysis:
        """フォールバック関数分析の生成"""
        return FunctionAnalysis(
            purpose=f"分析エラー: {error}",
            input_spec={},
            output_spec={},
            usage_examples=[],
            error_handling=[],
            performance={},
            limitations=[],
            alternatives=[],
            related_functions=[],
            security_considerations=[],
            test_cases=[]
        )
    
    def _generate_fallback_class_analysis(self, class_node: SyntaxNode, error: str) -> ClassAnalysis:
        """フォールバッククラス分析の生成"""
        return ClassAnalysis(
            purpose=f"分析エラー: {error}",
            design_pattern="不明",
            inheritance=[],
            methods=[],
            instance_variables=[],
            usage_scenarios=[],
            performance={},
            thread_safety="不明",
            security_considerations=[],
            test_strategy=""
        )