#!/usr/bin/env python3
# refactored_test1.py
"""
正規表現ベースのAPIドキュメントパーサー（クラスベース版）
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from regex_parser import RegexAPIParser

@dataclass
class FunctionData:
    """関数データを表すデータクラス"""
    name: str
    type: str = "function"
    params: List[Dict[str, Any]] = None
    returns: Optional[Dict[str, Any]] = None
    description: str = ""
    
    def __post_init__(self):
        if self.params is None:
            self.params = []

class APIDocumentParser:
    """APIドキュメント解析クラス"""
    
    def __init__(self, input_file: str = 'api_document.txt', output_file: str = 'api_functions_data.json'):
        self.input_file = input_file
        self.output_file = output_file
        self.parser = RegexAPIParser()
        self.functions_data: List[FunctionData] = []
    
    def load_document(self) -> str:
        """APIドキュメントファイルを読み込み"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ APIドキュメントファイルを読み込みました: {self.input_file}")
            return content
        except FileNotFoundError:
            print(f"❌ {self.input_file}ファイルが見つかりません")
            return self._get_sample_data()
    
    def _get_sample_data(self) -> str:
        """テスト用のサンプルデータを返す"""
        print("テスト用のサンプルデータを使用します")
        return '''
/**
 * @function CreateVariable
 * 変数を作成する関数
 * @param {文字列} VariableName - 作成する変数名称です。[空文字不可]
 * @param {数値} InitialValue - 変数の初期値
 * @returns {文字列} 作成された変数の名前
 */
function CreateVariable(VariableName, InitialValue) {
    // 実装
}

/**
 * @function CalculateSum
 * 2つの数値を足し算する関数
 * @param {数値} a - 最初の数値
 * @param {数値} b - 2番目の数値
 * @returns {数値} 合計値
 */
function CalculateSum(a, b) {
    return a + b;
}
'''
    
    def parse_document(self, content: str) -> Any:
        """ドキュメントをパースしてASTを生成"""
        print("📝 パースを開始...")
        ast = self.parser.parse(content)
        print("✅ パースが完了しました")
        return ast
    
    def extract_function_data(self, ast_node: Any) -> List[FunctionData]:
        """ASTから関数データを抽出"""
        functions_data = []
        
        for doc_comment in ast_node.children:
            if doc_comment.type == 'doc_comment':
                function_data = FunctionData(name="")
                
                for node in doc_comment.children:
                    self._process_doc_node(node, function_data)
                
                if function_data.name:
                    functions_data.append(function_data)
        
        return functions_data
    
    def _process_doc_node(self, node: Any, function_data: FunctionData):
        """ドキュメントノードを処理"""
        if node.type == 'function_tag':
            for child in node.children:
                if child.type == 'identifier':
                    function_data.name = child.text
        
        elif node.type == 'param_tag':
            param_info = self._extract_param_info(node)
            if param_info["name"]:
                function_data.params.append(param_info)
        
        elif node.type == 'returns_tag':
            function_data.returns = self._extract_return_info(node)
        
        elif node.type == 'doc_text':
            if function_data.description:
                function_data.description += " " + node.text
            else:
                function_data.description = node.text
    
    def _extract_param_info(self, node: Any) -> Dict[str, Any]:
        """パラメータ情報を抽出"""
        param_info = {
            "name": None,
            "type_name": None,
            "description_raw": None,
            "summary_llm": None,
            "constraints_llm": []
        }
        
        for child in node.children:
            if child.type == 'type':
                param_info["type_name"] = child.text.strip('{}')
            elif child.type == 'identifier':
                param_info["name"] = child.text
            elif child.type == 'description':
                param_info["description_raw"] = child.text
        
        return param_info
    
    def _extract_return_info(self, node: Any) -> Dict[str, Any]:
        """戻り値情報を抽出"""
        return_info = {
            "type_name": None,
            "description": None
        }
        
        for child in node.children:
            if child.type == 'type':
                return_info["type_name"] = child.text.strip('{}')
            elif child.type == 'description':
                return_info["description"] = child.text
        
        return return_info
    
    def save_results(self, functions_data: List[FunctionData]):
        """結果をJSONファイルに保存"""
        # FunctionDataを辞書に変換
        data_dict = []
        for func in functions_data:
            data_dict.append({
                "name": func.name,
                "type": func.type,
                "params": func.params,
                "returns": func.returns,
                "description": func.description
            })
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            print(f"💾 JSONファイルに保存しました: {self.output_file}")
        except Exception as e:
            print(f"❌ JSONファイルの保存に失敗しました: {e}")
    
    def display_results(self, functions_data: List[FunctionData]):
        """結果を表示"""
        print(f"\n📊 抽出された関数データ: {len(functions_data)}個")
        for i, func in enumerate(functions_data, 1):
            print(f"\n{i}. {func.name}")
            print(f"   説明: {func.description or 'N/A'}")
            print(f"   パラメータ数: {len(func.params)}")
            
            for j, param in enumerate(func.params, 1):
                print(f"     {j}. {param['name']} ({param['type_name']}) - {param['description_raw']}")
            
            if func.returns:
                print(f"   戻り値: {func.returns['type_name']} - {func.returns['description']}")
    
    def process(self) -> List[FunctionData]:
        """メイン処理を実行"""
        print("🔧 APIドキュメント解析開始")
        print("=" * 50)
        
        # 1. ドキュメント読み込み
        content = self.load_document()
        
        # 2. パース実行
        ast = self.parse_document(content)
        
        # 3. 関数データ抽出
        print("🔍 関数データを抽出中...")
        self.functions_data = self.extract_function_data(ast)
        print(f"✅ {len(self.functions_data)}個の関数を抽出しました")
        
        # 4. 結果表示
        self.display_results(self.functions_data)
        
        # 5. ファイル保存
        self.save_results(self.functions_data)
        
        print("\nStep 1: 正規表現ベースパーサーによる解析が完了しました。")
        return self.functions_data

def main():
    """メイン関数"""
    parser = APIDocumentParser()
    parser.process()

if __name__ == "__main__":
    main() 