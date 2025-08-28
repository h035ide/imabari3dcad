"""
LLM分析のユーティリティ機能

このモジュールは、LLM分析を簡単に使用するためのユーティリティ機能を提供します。
"""

import ast
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from .enhanced_llm_analyzer import EnhancedLLMAnalyzer
    from .analysis_schemas import SyntaxNode, FunctionAnalysis, ClassAnalysis
except ImportError:
    from enhanced_llm_analyzer import EnhancedLLMAnalyzer
    from analysis_schemas import SyntaxNode, FunctionAnalysis, ClassAnalysis

logger = logging.getLogger(__name__)


class LLMAnalysisManager:
    """LLM分析を管理するシンプルなクラス"""
    
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.1):
        """
        分析マネージャーの初期化
        
        Args:
            model_name: 使用するLLMモデル名
            temperature: LLMの温度パラメータ
        """
        self.analyzer = EnhancedLLMAnalyzer(model_name, temperature)
        self.analysis_cache = {}  # 分析結果のキャッシュ
    
    def analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """
        Pythonファイル全体を分析
        
        Args:
            file_path: 分析するPythonファイルのパス
            
        Returns:
            Dict: 分析結果
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"ファイルが見つかりません: {file_path}")
            return {"error": "File not found"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # ASTパースでコード要素を抽出
            tree = ast.parse(code_content)
            
            analysis_result = {
                "file_path": str(file_path),
                "functions": [],
                "classes": [],
                "error_analysis": None
            }
            
            # 関数とクラスを抽出して分析
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_analysis = self._analyze_function_from_ast(node, code_content)
                    if func_analysis:
                        analysis_result["functions"].append(func_analysis)
                
                elif isinstance(node, ast.ClassDef):
                    class_analysis = self._analyze_class_from_ast(node, code_content)
                    if class_analysis:
                        analysis_result["classes"].append(class_analysis)
            
            # ファイル全体のエラーパターン分析
            error_analysis = self.analyzer.analyze_error_patterns(code_content)
            if error_analysis.is_valid():
                analysis_result["error_analysis"] = error_analysis.to_dict()
            
            logger.info(f"ファイル分析完了: {file_path}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"ファイル分析エラー: {e}")
            return {"error": str(e)}
    
    def analyze_code_snippet(self, code: str, element_type: str = "auto") -> Dict[str, Any]:
        """
        コードスニペットを分析
        
        Args:
            code: 分析するコード
            element_type: 要素タイプ（'function', 'class', 'auto'）
            
        Returns:
            Dict: 分析結果
        """
        try:
            # キャッシュチェック
            cache_key = hash(code + element_type)
            if cache_key in self.analysis_cache:
                logger.info("キャッシュから分析結果を取得")
                return self.analysis_cache[cache_key]
            
            if element_type == "auto":
                element_type = self._detect_element_type(code)
            
            result = {}
            
            if element_type == "function":
                # 関数として分析
                syntax_node = self._create_syntax_node_from_code(code, "function")
                analysis = self.analyzer.analyze_function_purpose(syntax_node)
                result = {
                    "type": "function",
                    "analysis": analysis.to_dict()
                }
            
            elif element_type == "class":
                # クラスとして分析
                syntax_node = self._create_syntax_node_from_code(code, "class")
                analysis = self.analyzer.analyze_class_design(syntax_node)
                result = {
                    "type": "class",
                    "analysis": analysis.to_dict()
                }
            
            else:
                # エラーパターン分析のみ
                error_analysis = self.analyzer.analyze_error_patterns(code)
                result = {
                    "type": "code_snippet",
                    "error_analysis": error_analysis.to_dict()
                }
            
            # キャッシュに保存
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"コードスニペット分析エラー: {e}")
            return {"error": str(e)}
    
    def _analyze_function_from_ast(self, node: ast.FunctionDef, full_code: str) -> Optional[Dict[str, Any]]:
        """ASTノードから関数を分析"""
        try:
            # 関数のソースコードを抽出
            lines = full_code.split('\n')
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else start_line + 1
            
            func_code = '\n'.join(lines[start_line:end_line])
            
            # SyntaxNodeを作成
            syntax_node = SyntaxNode(
                name=node.name,
                text=func_code,
                node_type="function",
                line_start=start_line + 1,
                line_end=end_line
            )
            
            # 分析実行
            analysis = self.analyzer.analyze_function_purpose(syntax_node)
            
            return {
                "name": node.name,
                "line_start": start_line + 1,
                "line_end": end_line,
                "analysis": analysis.to_dict()
            }
            
        except Exception as e:
            logger.error(f"関数分析エラー: {e}")
            return None
    
    def _analyze_class_from_ast(self, node: ast.ClassDef, full_code: str) -> Optional[Dict[str, Any]]:
        """ASTノードからクラスを分析"""
        try:
            # クラスのソースコードを抽出
            lines = full_code.split('\n')
            start_line = node.lineno - 1
            end_line = node.end_lineno if node.end_lineno else start_line + 1
            
            class_code = '\n'.join(lines[start_line:end_line])
            
            # SyntaxNodeを作成
            syntax_node = SyntaxNode(
                name=node.name,
                text=class_code,
                node_type="class",
                line_start=start_line + 1,
                line_end=end_line
            )
            
            # 分析実行
            analysis = self.analyzer.analyze_class_design(syntax_node)
            
            return {
                "name": node.name,
                "line_start": start_line + 1,
                "line_end": end_line,
                "analysis": analysis.to_dict()
            }
            
        except Exception as e:
            logger.error(f"クラス分析エラー: {e}")
            return None
    
    def _detect_element_type(self, code: str) -> str:
        """コードの要素タイプを自動検出"""
        try:
            tree = ast.parse(code.strip())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return "function"
                elif isinstance(node, ast.ClassDef):
                    return "class"
            
            return "snippet"
            
        except:
            return "snippet"
    
    def _create_syntax_node_from_code(self, code: str, node_type: str) -> SyntaxNode:
        """コードからSyntaxNodeを作成"""
        try:
            tree = ast.parse(code.strip())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node_type == "function":
                    return SyntaxNode(
                        name=node.name,
                        text=code.strip(),
                        node_type="function"
                    )
                elif isinstance(node, ast.ClassDef) and node_type == "class":
                    return SyntaxNode(
                        name=node.name,
                        text=code.strip(),
                        node_type="class"
                    )
            
            # 名前が特定できない場合
            return SyntaxNode(
                name="unknown",
                text=code.strip(),
                node_type=node_type
            )
            
        except:
            return SyntaxNode(
                name="parse_error",
                text=code.strip(),
                node_type=node_type
            )
    
    def clear_cache(self):
        """分析結果のキャッシュをクリア"""
        self.analysis_cache.clear()
        logger.info("分析キャッシュをクリアしました")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュの統計情報を取得"""
        return {
            "cache_size": len(self.analysis_cache),
            "memory_usage_estimate": len(str(self.analysis_cache)) / 1024  # KB単位の概算
        }