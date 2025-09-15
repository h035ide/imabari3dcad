#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parsed_api_result_def.jsonからテストケースを生成するスクリプト
LLMで加工された正確なAPI仕様書を基にテストケースを作成します
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any

class APIDocParser:
    def __init__(self, api_json_path: str):
        self.api_json_path = api_json_path
        self.functions = {}
        self.parse_api_json()
    
    def parse_api_json(self):
        """parsed_api_result_def.jsonを解析して関数の情報を抽出"""
        import json
        
        with open(self.api_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # api_entriesから関数を抽出
        for entry in data.get('api_entries', []):
            if entry.get('entry_type') == 'function':
                func_name = entry.get('name')
                if func_name:
                    # パラメータを解析
                    params = self._parse_json_parameters(entry.get('params', []))
                    self.functions[func_name] = {
                        'description': entry.get('description', ''),
                        'parameters': params,
                        'param_count': len(params)
                    }
                    print(f"✅ 関数を発見: {func_name} (パラメータ数: {len(params)})")
    
    def _parse_json_parameters(self, json_params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """JSONからパラメータ情報を解析"""
        params = []
        
        for param in json_params:
            param_name = param.get('name', '')
            param_type = param.get('type', '')
            description = param.get('description', '')
            
            if param_name:
                params.append({
                    'name': param_name,
                    'type': param_type,
                    'comment': description
                })
        
        return params
    
    def _infer_param_type(self, param_name: str, comment: str) -> str:
        """パラメータの型を推測（JSONベース）"""
        # JSONから取得した型情報をそのまま使用
        return comment
    
    def _generate_param_value(self, param_name: str, param_type: str) -> str:
        """パラメータの値を生成（JSONベース）"""
        if '要素(配列)' in param_type:
            if 'pDivideElements' in param_name:
                return '[divide_element_1, divide_element_2]'
            elif 'pSubSolids' in param_name:
                return '[subsolid_element_1, subsolid_element_2]'
            elif 'SrcSurfaces' in param_name:
                return '[surface_element_1, surface_element_2]'
            else:
                return '[element_1, element_2]'
        elif '要素' in param_type:
            return f'{param_name}_element'
        elif '方向' in param_type:
            return '(1.0, 0.0, 0.0)'
        elif '実数' in param_type:
            return '1.0'
        elif '文字列' in param_type:
            if 'pDriveFeatureName' in param_name:
                return '"drive_feature_name"'
            elif 'pTargetBody' in param_name:
                return '"target_body"'
            else:
                return f'"{param_name}_value"'
        elif 'bool' in param_type:
            return 'True'
        elif '座標系' in param_type:
            return 'wcs_element'
        elif '関連設定' in param_type:
            return '"GEOMETRIC"'
        elif '整数' in param_type:
            return '1'
        elif '浮動小数点' in param_type:
            return '1.0'
        elif '長さ' in param_type:
            return '100.0'
        elif '角度' in param_type:
            return '45.0'
        elif '点' in param_type:
            return '(0.0, 0.0)'
        elif '平面' in param_type:
            return '"PL,Z"'
        elif '材料' in param_type:
            return '"STEEL"'
        elif '要素グループ' in param_type:
            return '"MAIN_GROUP"'
        elif 'オペレーションタイプ' in param_type:
            return '"+"'
        elif '厚み付けタイプ' in param_type:
            return '"+"'
        elif 'モールド位置' in param_type:
            return '"+"'
        elif '形状タイプ' in param_type:
            return '"1007"'
        elif '形状パラメータ' in param_type:
            return '["100.0", "50.0", "10.0"]'
        elif '範囲' in param_type:
            return '(0.0, 2*3.14159)'
        elif '変数単位' in param_type:
            return '"MM"'
        elif '注記スタイル' in param_type:
            return '"DEFAULT_STYLE"'
        elif 'スイープ方向' in param_type:
            return '"N"'
        elif '点(配列)' in param_type:
            return '[(0.0, 0.0), (1.0, 1.0)]'
        elif '浮動小数点(配列)' in param_type:
            return '[1.0, 2.0, 3.0]'
        else:
            return f'"{param_name}_value"'
    
    def generate_test_case(self, func_name: str, test_type: str = "positive") -> str:
        """テストケースを生成（改善版）"""
        if func_name not in self.functions:
            return ""
        
        func_info = self.functions[func_name]
        params = func_info['parameters']
        
        if test_type == "positive":
            # 正しいパラメータ数でテストケースを生成
            param_values = []
            for param in params:
                param_value = self._generate_param_value(param['name'], param['type'])
                param_values.append(param_value)
            
            # テストケースのコードを生成
            code = f"""# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.{func_name}(
"""
            for i, (param, value) in enumerate(zip(params, param_values)):
                if i < len(params) - 1:
                    code += f"    {value},               # {param['comment']}\n"
                else:
                    code += f"    {value}                # {param['comment']}\n"
            
            code += ")"
            return code
        
        else:  # negative
            # 間違ったパラメータ数でテストケースを生成
            if len(params) == 0:
                # パラメータがない場合は、適当な値を追加して引数過多を作る
                code = f"""# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.{func_name}(
    "extra_value"    # 引数が不要なのに追加
)"""
            else:
                # 最後の引数を削除して引数不足を作る
                code = f"""# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.{func_name}(
"""
                # 最後の引数を除いてパラメータを生成
                for i, param in enumerate(params[:-1]):
                    param_value = self._generate_param_value(param['name'], param['type'])
                    code += f"    {param_value},               # {param['comment']}\n"
                
                code += f"    # Missing the last argument: {params[-1]['name']}\n"
                code += ")"
            
            return code
    
    def generate_all_test_cases(self, output_dir: str):
        """すべてのテストケースを生成（改善版）"""
        # 出力ディレクトリを作成
        code_snippets_dir = os.path.join(output_dir, "code_snippets")
        golden_snippets_dir = os.path.join(output_dir, "golden_snippets")
        
        os.makedirs(code_snippets_dir, exist_ok=True)
        os.makedirs(golden_snippets_dir, exist_ok=True)
        
        print(f"📁 出力ディレクトリ: {output_dir}")
        print(f"🔍 検出された関数数: {len(self.functions)}")
        
        for func_name, func_info in self.functions.items():
            print(f"\n 関数: {func_name}")
            print(f"   パラメータ数: {func_info['param_count']}")
            print(f"   説明: {func_info['description']}")
            
            # Positive test case
            positive_code = self.generate_test_case(func_name, "positive")
            positive_file = os.path.join(code_snippets_dir, f"{func_name}_positive.py")
            with open(positive_file, 'w', encoding='utf-8') as f:
                f.write(positive_code)
            
            # Negative test case
            negative_code = self.generate_test_case(func_name, "negative")
            negative_file = os.path.join(code_snippets_dir, f"{func_name}_negative.py")
            with open(negative_file, 'w', encoding='utf-8') as f:
                f.write(negative_code)
            
            # Golden snippet (positiveと同じ)
            golden_file = os.path.join(golden_snippets_dir, f"{func_name}_golden.py")
            with open(golden_file, 'w', encoding='utf-8') as f:
                f.write(positive_code)
        
        print(f"\n✅ テストケース生成完了!")
        print(f"   Positive test cases: {len(self.functions)}")
        print(f"   Negative test cases: {len(self.functions)}")
        print(f"   Golden snippets: {len(self.functions)}")

def main():
    # parsed_api_result_def.jsonのパス
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_json_path = os.path.join(script_dir, "..", "parsed_api_result_def.json")
    
    if not os.path.exists(api_json_path):
        print(f"❌ parsed_api_result_def.jsonが見つかりません: {api_json_path}")
        print(f" 現在のディレクトリ: {os.getcwd()}")
        print(f"📁 スクリプトのディレクトリ: {script_dir}")
        return
    
    print(f"✅ parsed_api_result_def.jsonを発見: {api_json_path}")
    
    # パーサーを作成
    parser = APIDocParser(api_json_path)
    
    # テストケースを生成
    parser.generate_all_test_cases(script_dir)

if __name__ == "__main__":
    main()