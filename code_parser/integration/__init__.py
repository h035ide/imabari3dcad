"""
Code Parser パッケージ

このパッケージは、Pythonコードの解析とLLMを活用した高度な分析機能を提供します。
"""

# 高度なLLM分析機能
from .enhanced_llm_analyzer import EnhancedLLMAnalyzer
from .llm_analysis_utils import LLMAnalysisManager
from .analysis_schemas import (
    FunctionAnalysis,
    ClassAnalysis, 
    ErrorAnalysis,
    SyntaxNode
)

# バージョン情報
__version__ = "1.0.0"

# パッケージの公開API
__all__ = [
    "EnhancedLLMAnalyzer",
    "LLMAnalysisManager", 
    "FunctionAnalysis",
    "ClassAnalysis",
    "ErrorAnalysis", 
    "SyntaxNode"
]