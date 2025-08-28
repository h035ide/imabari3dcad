"""
コード抽出器 - Tree-sitterを使用してPythonコードから情報を抽出

実際のPythonコードファイルから関数やクラスの情報を抽出し、
ベクトル検索用のCodeInfoオブジェクトを生成します。
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from vector_search import CodeInfo

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser
except ImportError as e:
    print(f"Tree-sitterライブラリがインストールされていません: {e}")
    print("以下のコマンドでインストールしてください:")
    print("pip install tree-sitter tree-sitter-python")
    raise


class CodeExtractor:
    """
    Pythonコードから関数・クラス情報を抽出するクラス
    
    Tree-sitterを使用してPythonコードを解析し、
    ベクトル検索用のデータを生成します。
    """
    
    def __init__(self):
        """コード抽出器を初期化"""
        # Tree-sitterパーサーの初期化
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)
        
        print("コード抽出器が初期化されました")
    
    def extract_from_file(self, file_path: str) -> List[CodeInfo]:
        """
        ファイルからコード情報を抽出
        
        Args:
            file_path: Pythonファイルのパス
            
        Returns:
            List[CodeInfo]: 抽出されたコード情報のリスト
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.extract_from_content(content, file_path)
            
        except Exception as e:
            print(f"ファイル読み込みエラー {file_path}: {e}")
            return []
    
    def extract_from_content(self, content: str, file_path: str = "") -> List[CodeInfo]:
        """
        コード内容からコード情報を抽出
        
        Args:
            content: Pythonコードの内容
            file_path: ファイルパス（オプション）
            
        Returns:
            List[CodeInfo]: 抽出されたコード情報のリスト
        """
        code_infos = []
        
        try:
            # コードを解析
            tree = self.parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node
            
            # 関数とクラスを抽出
            self._extract_functions(root_node, content, file_path, code_infos)
            self._extract_classes(root_node, content, file_path, code_infos)
            
            print(f"コード抽出完了: {len(code_infos)}個の要素を抽出 ({file_path})")
            return code_infos
            
        except Exception as e:
            print(f"コード解析エラー {file_path}: {e}")
            return []
    
    def extract_from_directory(self, directory_path: str, 
                             recursive: bool = True,
                             exclude_patterns: List[str] = None) -> List[CodeInfo]:
        """
        ディレクトリからコード情報を抽出
        
        Args:
            directory_path: ディレクトリパス
            recursive: 再帰的に検索するかどうか
            exclude_patterns: 除外するファイルパターン
            
        Returns:
            List[CodeInfo]: 抽出されたコード情報のリスト
        """
        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", ".git", ".venv", "venv", "env"]
        
        code_infos = []
        directory = Path(directory_path)
        
        if not directory.exists():
            print(f"ディレクトリが存在しません: {directory_path}")
            return code_infos
        
        # .pyファイルを検索
        pattern = "**/*.py" if recursive else "*.py"
        py_files = list(directory.glob(pattern))
        
        print(f"Pythonファイルを検索中: {len(py_files)}ファイル見つかりました")
        
        for py_file in py_files:
            # 除外パターンのチェック
            if any(pattern in str(py_file) for pattern in exclude_patterns):
                continue
            
            file_code_infos = self.extract_from_file(str(py_file))
            code_infos.extend(file_code_infos)
        
        print(f"ディレクトリからの抽出完了: {len(code_infos)}個の要素")
        return code_infos
    
    def _extract_functions(self, node, content: str, file_path: str, code_infos: List[CodeInfo]):
        """関数を抽出"""
        if node.type == "function_definition":
            function_info = self._parse_function(node, content, file_path)
            if function_info:
                code_infos.append(function_info)
        
        # 子ノードを再帰的に探索
        for child in node.children:
            self._extract_functions(child, content, file_path, code_infos)
    
    def _extract_classes(self, node, content: str, file_path: str, code_infos: List[CodeInfo]):
        """クラスを抽出"""
        if node.type == "class_definition":
            class_info = self._parse_class(node, content, file_path)
            if class_info:
                code_infos.append(class_info)
            
            # クラス内のメソッドも抽出
            self._extract_methods(node, content, file_path, code_infos)
        
        # 子ノードを再帰的に探索
        for child in node.children:
            self._extract_classes(child, content, file_path, code_infos)
    
    def _extract_methods(self, class_node, content: str, file_path: str, code_infos: List[CodeInfo]):
        """クラス内のメソッドを抽出"""
        for child in class_node.children:
            if child.type == "function_definition":
                method_info = self._parse_function(child, content, file_path, is_method=True)
                if method_info:
                    code_infos.append(method_info)
    
    def _parse_function(self, function_node, content: str, file_path: str, is_method: bool = False) -> Optional[CodeInfo]:
        """関数ノードを解析"""
        try:
            # 関数名を取得
            name_node = None
            for child in function_node.children:
                if child.type == "identifier":
                    name_node = child
                    break
            
            if not name_node:
                return None
            
            function_name = self._get_node_text(name_node, content)
            
            # 関数全体のテキストを取得
            function_text = self._get_node_text(function_node, content)
            
            # パラメータを抽出
            parameters = self._extract_parameters(function_node, content)
            
            # ドキュメント文字列を抽出
            docstring = self._extract_docstring(function_node, content)
            
            # 戻り値の型ヒントを抽出
            return_type = self._extract_return_type(function_node, content)
            
            # IDを生成
            code_id = self._generate_id(function_name, file_path, "method" if is_method else "function")
            
            return CodeInfo(
                id=code_id,
                name=function_name,
                content=function_text,
                type="method" if is_method else "function",
                file_path=file_path,
                description=docstring,
                parameters=parameters,
                returns=return_type
            )
            
        except Exception as e:
            print(f"関数解析エラー: {e}")
            return None
    
    def _parse_class(self, class_node, content: str, file_path: str) -> Optional[CodeInfo]:
        """クラスノードを解析"""
        try:
            # クラス名を取得
            name_node = None
            for child in class_node.children:
                if child.type == "identifier":
                    name_node = child
                    break
            
            if not name_node:
                return None
            
            class_name = self._get_node_text(name_node, content)
            
            # クラス全体のテキストを取得
            class_text = self._get_node_text(class_node, content)
            
            # ドキュメント文字列を抽出
            docstring = self._extract_docstring(class_node, content)
            
            # 継承関係を抽出
            inheritance = self._extract_inheritance(class_node, content)
            
            # IDを生成
            code_id = self._generate_id(class_name, file_path, "class")
            
            return CodeInfo(
                id=code_id,
                name=class_name,
                content=class_text,
                type="class",
                file_path=file_path,
                description=docstring,
                parameters=inheritance,  # 継承クラスをパラメータとして保存
                returns=""
            )
            
        except Exception as e:
            print(f"クラス解析エラー: {e}")
            return None
    
    def _get_node_text(self, node, content: str) -> str:
        """ノードのテキストを取得"""
        start_byte = node.start_byte
        end_byte = node.end_byte
        return content[start_byte:end_byte]
    
    def _extract_parameters(self, function_node, content: str) -> List[str]:
        """関数のパラメータを抽出"""
        parameters = []
        
        for child in function_node.children:
            if child.type == "parameters":
                for param_child in child.children:
                    if param_child.type == "identifier":
                        param_name = self._get_node_text(param_child, content)
                        parameters.append(param_name)
                    elif param_child.type == "default_parameter":
                        # デフォルト値付きパラメータ
                        for sub_child in param_child.children:
                            if sub_child.type == "identifier":
                                param_name = self._get_node_text(sub_child, content)
                                parameters.append(param_name)
                                break
                break
        
        return parameters
    
    def _extract_docstring(self, node, content: str) -> str:
        """ドキュメント文字列を抽出"""
        # 関数/クラスの本体を探す
        for child in node.children:
            if child.type == "block":
                for block_child in child.children:
                    if block_child.type == "expression_statement":
                        for expr_child in block_child.children:
                            if expr_child.type == "string":
                                docstring = self._get_node_text(expr_child, content)
                                # クォートを除去して返す
                                return self._clean_docstring(docstring)
                break
        
        return ""
    
    def _extract_return_type(self, function_node, content: str) -> str:
        """戻り値の型ヒントを抽出"""
        for child in function_node.children:
            if child.type == "type":
                return self._get_node_text(child, content)
        return ""
    
    def _extract_inheritance(self, class_node, content: str) -> List[str]:
        """継承関係を抽出"""
        inheritance = []
        
        for child in class_node.children:
            if child.type == "argument_list":
                for arg_child in child.children:
                    if arg_child.type == "identifier":
                        parent_class = self._get_node_text(arg_child, content)
                        inheritance.append(parent_class)
                break
        
        return inheritance
    
    def _clean_docstring(self, docstring: str) -> str:
        """ドキュメント文字列をクリーンアップ"""
        # 外側のクォートを除去
        if docstring.startswith('"""') and docstring.endswith('"""'):
            docstring = docstring[3:-3]
        elif docstring.startswith("'''") and docstring.endswith("'''"):
            docstring = docstring[3:-3]
        elif docstring.startswith('"') and docstring.endswith('"'):
            docstring = docstring[1:-1]
        elif docstring.startswith("'") and docstring.endswith("'"):
            docstring = docstring[1:-1]
        
        # 先頭と末尾の空白を除去
        return docstring.strip()
    
    def _generate_id(self, name: str, file_path: str, code_type: str) -> str:
        """一意のIDを生成"""
        # ファイルパスから相対パスを作成
        relative_path = file_path.replace("\\", "/").split("/")[-1] if file_path else "unknown"
        return f"{code_type}_{relative_path}_{name}_{hash(f'{file_path}_{name}') % 10000}"


def demo_extraction():
    """抽出機能のデモ"""
    # サンプルコードを作成
    sample_code = '''
def calculate_area(radius: float) -> float:
    """
    円の面積を計算する関数
    
    Args:
        radius: 円の半径
        
    Returns:
        float: 円の面積
    """
    return 3.14159 * radius * radius

class Calculator:
    """計算機クラス"""
    
    def __init__(self):
        """初期化"""
        self.history = []
    
    def add(self, a: int, b: int) -> int:
        """
        足し算を実行
        
        Args:
            a: 第一の数値
            b: 第二の数値
            
        Returns:
            int: 足し算の結果
        """
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    '''
    
    print("=== コード抽出デモ ===")
    
    extractor = CodeExtractor()
    code_infos = extractor.extract_from_content(sample_code, "demo.py")
    
    print(f"\n抽出結果: {len(code_infos)}個の要素")
    
    for info in code_infos:
        print(f"\n--- {info.type}: {info.name} ---")
        print(f"説明: {info.description}")
        print(f"パラメータ: {info.parameters}")
        print(f"戻り値: {info.returns}")
        print(f"コード（最初の100文字）: {info.content[:100]}...")


if __name__ == "__main__":
    demo_extraction()