"""
分析結果の構造化のためのデータクラス

このモジュールは、LLM分析結果を構造化するためのデータクラスを提供します。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FunctionAnalysis:
    """関数分析結果を格納するデータクラス"""
    purpose: str = ""                                # 関数の目的
    input_spec: Dict[str, Any] = field(default_factory=dict)     # 入力仕様
    output_spec: Dict[str, Any] = field(default_factory=dict)    # 出力仕様
    usage_examples: List[str] = field(default_factory=list)      # 使用例
    error_handling: List[str] = field(default_factory=list)      # エラーハンドリング
    performance: Dict[str, Any] = field(default_factory=dict)    # パフォーマンス特性
    limitations: List[str] = field(default_factory=list)         # 制限事項
    alternatives: List[str] = field(default_factory=list)        # 代替案
    related_functions: List[str] = field(default_factory=list)   # 関連関数
    security_considerations: List[str] = field(default_factory=list)  # セキュリティ上の考慮事項
    test_cases: List[str] = field(default_factory=list)          # テストケースの提案

    def is_valid(self) -> bool:
        """分析結果が有効かどうかをチェック"""
        return self.purpose and self.purpose != "分析できませんでした"

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "purpose": self.purpose,
            "input_spec": self.input_spec,
            "output_spec": self.output_spec,
            "usage_examples": self.usage_examples,
            "error_handling": self.error_handling,
            "performance": self.performance,
            "limitations": self.limitations,
            "alternatives": self.alternatives,
            "related_functions": self.related_functions,
            "security_considerations": self.security_considerations,
            "test_cases": self.test_cases
        }


@dataclass
class ClassAnalysis:
    """クラス分析結果を格納するデータクラス"""
    purpose: str = ""                                # クラスの目的
    design_pattern: str = ""                         # 設計パターン
    inheritance: List[str] = field(default_factory=list)          # 継承関係
    methods: List[Dict[str, Any]] = field(default_factory=list)   # メソッド一覧
    instance_variables: List[Dict[str, Any]] = field(default_factory=list)  # インスタンス変数
    usage_scenarios: List[str] = field(default_factory=list)      # 使用場面
    performance: Dict[str, Any] = field(default_factory=dict)     # パフォーマンス特性
    thread_safety: str = ""                          # スレッドセーフティ
    security_considerations: List[str] = field(default_factory=list)  # セキュリティ上の考慮事項
    test_strategy: str = ""                          # テスト戦略

    def is_valid(self) -> bool:
        """分析結果が有効かどうかをチェック"""
        return self.purpose and self.purpose != "分析できませんでした"

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "purpose": self.purpose,
            "design_pattern": self.design_pattern,
            "inheritance": self.inheritance,
            "methods": self.methods,
            "instance_variables": self.instance_variables,
            "usage_scenarios": self.usage_scenarios,
            "performance": self.performance,
            "thread_safety": self.thread_safety,
            "security_considerations": self.security_considerations,
            "test_strategy": self.test_strategy
        }


@dataclass
class ErrorAnalysis:
    """エラー分析結果を格納するデータクラス"""
    exceptions: List[Dict[str, Any]] = field(default_factory=list)  # 例外の種類と詳細
    causes: List[str] = field(default_factory=list)              # 発生原因
    solutions: List[Dict[str, Any]] = field(default_factory=list)   # 解決方法
    prevention: List[str] = field(default_factory=list)          # 予防策
    logging: List[str] = field(default_factory=list)             # ログ出力の推奨事項
    user_messages: List[str] = field(default_factory=list)       # ユーザーへのエラーメッセージ

    def is_valid(self) -> bool:
        """分析結果が有効かどうかをチェック"""
        return bool(self.exceptions or self.causes or self.solutions)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "exceptions": self.exceptions,
            "causes": self.causes,
            "solutions": self.solutions,
            "prevention": self.prevention,
            "logging": self.logging,
            "user_messages": self.user_messages
        }


@dataclass
class SyntaxNode:
    """構文ノードを表すシンプルなデータクラス"""
    name: str                    # ノード名
    text: str                    # ソースコード
    node_type: str = ""          # ノードタイプ
    line_start: int = 0          # 開始行
    line_end: int = 0            # 終了行

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "text": self.text,
            "node_type": self.node_type,
            "line_start": self.line_start,
            "line_end": self.line_end
        }