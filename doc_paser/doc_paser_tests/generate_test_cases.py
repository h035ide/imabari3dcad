#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
検証レポートから自動的にテストケースを生成するスクリプト
包括的検証レポートの情報を基に、code_snippets/とgolden_snippets/のファイルを生成します
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any

class TestCaseGenerator:
    def __init__(self, report_path: str):
        self.report_path = report_path
        self.functions = {}
        self.objects = {}
        self.parse_report()
    
    def parse_report(self):
        """検証レポートを解析して関数とオブジェクトの情報を抽出"""
        with open(self.report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 関数セクションを抽出
        function_sections = re.findall(
            r'### (\w+)\n\n(.*?)(?=\n### |\n## |\n$)', 
            content, 
            re.DOTALL
        )
        
        for func_name, func_content in function_sections:
            if func_name not in ['ブラケット要素のパラメータオブジェクト', '押し出しパラメータオブジェクト', '条材要素のパラメータオブジェクト']:
                self.functions[func_name] = self._parse_function(func_content)
        
        # オブジェクトセクションを抽出
        object_sections = re.findall(
            r'### (ブラケット要素のパラメータオブジェクト|押し出しパラメータオブジェクト|条材要素のパラメータオブジェクト)\n\n(.*?)(?=\n### |\n## |\n$)', 
            content, 
            re.DOTALL
        )
        
        for obj_name, obj_content in object_sections:
            self.objects[obj_name] = self._parse_object(obj_content)
    
    def _parse_function(self, content: str) -> Dict[str, Any]:
        """関数の内容を解析"""
        func_info = {}
        
        # 説明を抽出
        desc_match = re.search(r'\*\*説明\*\*: (.*?)(?=\n\n|\n\*\*|\n$)', content)
        if desc_match:
            func_info['description'] = desc_match.group(1).strip()
        
        # パラメータを抽出
        params = []
        param_matches = re.findall(
            r'- \*\*(\w+)\*\* \(位置: (\d+), 型: ([^)]+)\)\n\s*- 説明: ([^\n]+)',
            content
        )
        
        for param_name, position, param_type, description in param_matches:
            params.append({
                'name': param_name,
                'position': int(position),
                'type': param_type,
                'description': description.strip()
            })
        
        # 位置でソート
        params.sort(key=lambda x: x['position'])
        func_info['parameters'] = params
        
        return func_info
    
    def _parse_object(self, content: str) -> Dict[str, Any]:
        """オブジェクトの内容を解析"""
        obj_info = {}
        
        # 説明を抽出
        desc_match = re.search(r'\*\*説明\*\*: (.*?)(?=\n\n|\n\*\*|\n$)', content)
        if desc_match:
            obj_info['description'] = desc_match.group(1).strip()
        
        # プロパティを抽出
        properties = []
        prop_matches = re.findall(
            r'- \*\*(\w+)\*\* \(型: ([^,]+), 任意\)\n\s*- 説明: ([^\n]+)',
            content
        )
        
        for prop_name, prop_type, description in prop_matches:
            properties.append({
                'name': prop_name,
                'type': prop_type,
                'description': description.strip()
            })
        
        obj_info['properties'] = properties
        
        return obj_info
    
    def generate_positive_test_case(self, func_name: str, func_info: Dict[str, Any]) -> str:
        """正しいテストケースを生成"""
        params = func_info.get('parameters', [])
        
        # パラメータの値を生成
        param_values = []
        for param in params:
            param_name = param['name']
            param_type = param['type']
            
            # 型に基づいて適切な値を生成
            if 'bool' in param_type:
                param_values.append('True')
            elif '文字列' in param_type:
                param_values.append(f'"{param_name}"')
            elif '整数' in param_type:
                param_values.append('1')
            elif '浮動小数点' in param_type:
                param_values.append('1.0')
            elif '長さ' in param_type:
                param_values.append('100.0')
            elif '角度' in param_type:
                param_values.append('45.0')
            elif '点' in param_type:
                param_values.append('(0.0, 0.0)')
            elif '方向' in param_type:
                param_values.append('(1.0, 0.0, 0.0)')
            elif '平面' in param_type:
                param_values.append('XY_PLANE')
            elif '要素' in param_type:
                param_values.append(f'{param_name}_element')
            elif '要素(配列)' in param_type:
                param_values.append(f'[{param_name}_element]')
            elif '材料' in param_type:
                param_values.append('"STEEL"')
            elif '要素グループ' in param_type:
                param_values.append('"MAIN_GROUP"')
            elif '関連設定' in param_type:
                param_values.append('"GEOMETRIC"')
            elif 'オペレーションタイプ' in param_type:
                param_values.append('"UNION"')
            elif 'モールド位置' in param_type:
                param_values.append('"TOP"')
            elif '形状タイプ' in param_type:
                param_values.append('"RECTANGULAR"')
            elif '形状パラメータ' in param_type:
                param_values.append('"DEFAULT_PARAMS"')
            elif '厚み付けタイプ' in param_type:
                param_values.append('"SINGLE"')
            elif '範囲' in param_type:
                param_values.append('(0.0, 2*3.14159)')
            elif '変数単位' in param_type:
                param_values.append('"MM"')
            elif '注記スタイル' in param_type:
                param_values.append('"DEFAULT_STYLE"')
            elif 'スイープ方向' in param_type:
                param_values.append('"FORWARD"')
            elif '押し出しパラメータオブジェクト' in param_type:
                param_values.append('extrude_param')
            elif 'ブラケット要素のパラメータオブジェクト' in param_type:
                param_values.append('bracket_param')
            elif '条材要素のパラメータオブジェクト' in param_type:
                param_values.append('profile_param')
            else:
                param_values.append(f'"{param_name}_value"')
        
        # テストケースを生成
        test_case = f'# test_type: positive\n'
        test_case += f'# This snippet should pass validation as it has the correct number of arguments.\n\n'
        test_case += f'part.{func_name}(\n'
        
        for i, (param, value) in enumerate(zip(params, param_values)):
            if i == len(params) - 1:
                test_case += f'    {value}                # {param["description"]}\n'
            else:
                test_case += f'    {value},               # {param["description"]}\n'
        
        test_case += ')'
        
        return test_case
    
    def generate_negative_test_case(self, func_name: str, func_info: Dict[str, Any]) -> str:
        """間違ったテストケースを生成（引数が不足）"""
        params = func_info.get('parameters', [])
        
        if len(params) <= 1:
            # パラメータが1個以下の場合は、適当な値を追加して引数数を増やす
            test_case = f'# test_type: negative\n'
            test_case += f'# This snippet should FAIL validation because it has the wrong number of arguments.\n'
            test_case += f'# The test itself should PASS if the validator correctly identifies this failure.\n\n'
            test_case += f'part.{func_name}(\n'
            test_case += f'    "extra_value",           # Extra argument that should cause failure\n'
            test_case += f'    "another_extra_value"    # Another extra argument\n'
            test_case += ')'
        else:
            # 最後の引数を削除して引数不足を作る
            test_case = f'# test_type: negative\n'
            test_case += f'# This snippet should FAIL validation because it has the wrong number of arguments.\n'
            test_case += f'# The test itself should PASS if the validator correctly identifies this failure.\n\n'
            test_case += f'part.{func_name}(\n'
            
            for i, param in enumerate(params[:-1]):  # 最後の引数を除く
                param_name = param['name']
                param_type = param['type']
                
                # 型に基づいて適切な値を生成
                if 'bool' in param_type:
                    value = 'True'
                elif '文字列' in param_type:
                    value = f'"{param_name}"'
                elif '整数' in param_type:
                    value = '1'
                elif '浮動小数点' in param_type:
                    value = '1.0'
                elif '長さ' in param_type:
                    value = '100.0'
                elif '角度' in param_type:
                    value = '45.0'
                elif '点' in param_type:
                    value = '(0.0, 0.0)'
                elif '方向' in param_type:
                    value = '(1.0, 0.0, 0.0)'
                elif '平面' in param_type:
                    value = 'XY_PLANE'
                elif '要素' in param_type:
                    value = f'{param_name}_element'
                elif '要素(配列)' in param_type:
                    value = f'[{param_name}_element]'
                elif '材料' in param_type:
                    value = '"STEEL"'
                elif '要素グループ' in param_type:
                    value = '"MAIN_GROUP"'
                elif '関連設定' in param_type:
                    value = '"GEOMETRIC"'
                elif 'オペレーションタイプ' in param_type:
                    value = '"UNION"'
                elif 'モールド位置' in param_type:
                    value = '"TOP"'
                elif '形状タイプ' in param_type:
                    value = '"RECTANGULAR"'
                elif '形状パラメータ' in param_type:
                    value = '"DEFAULT_PARAMS"'
                elif '厚み付けタイプ' in param_type:
                    value = '"SINGLE"'
                elif '範囲' in param_type:
                    value = '(0.0, 2*3.14159)'
                elif '変数単位' in param_type:
                    value = '"MM"'
                elif '注記スタイル' in param_type:
                    value = '"DEFAULT_STYLE"'
                elif 'スイープ方向' in param_type:
                    value = '"FORWARD"'
                elif '押し出しパラメータオブジェクト' in param_type:
                    value = 'extrude_param'
                elif 'ブラケット要素のパラメータオブジェクト' in param_type:
                    value = 'bracket_param'
                elif '条材要素のパラメータオブジェクト' in param_type:
                    value = 'profile_param'
                else:
                    value = f'"{param_name}_value"'
                
                if i == len(params) - 2:  # 最後から2番目
                    test_case += f'    {value}                # {param["description"]}\n'
                else:
                    test_case += f'    {value},               # {param["description"]}\n'
            
            test_case += f'    # Missing the last argument: {params[-1]["name"]}\n'
            test_case += ')'
        
        return test_case
    
    def generate_golden_snippet(self, func_name: str, func_info: Dict[str, Any]) -> str:
        """期待される出力のテンプレートを生成"""
        params = func_info.get('parameters', [])
        
        # パラメータ名のみを使用
        param_names = [param['name'] for param in params]
        
        golden_snippet = f'part.{func_name}(\n'
        
        for i, param_name in enumerate(param_names):
            if i == len(param_names) - 1:
                golden_snippet += f'    {param_name}\n'
            else:
                golden_snippet += f'    {param_name},\n'
        
        golden_snippet += ')'
        
        return golden_snippet
    
    def generate_all_test_cases(self, output_dir: str):
        """すべてのテストケースを生成"""
        # 出力ディレクトリを作成
        code_snippets_dir = os.path.join(output_dir, 'code_snippets')
        golden_snippets_dir = os.path.join(output_dir, 'golden_snippets')
        
        os.makedirs(code_snippets_dir, exist_ok=True)
        os.makedirs(golden_snippets_dir, exist_ok=True)
        
        print(f"🔧 テストケースを生成中...")
        print(f"📁 出力先: {output_dir}")
        
        for func_name, func_info in self.functions.items():
            print(f"📝 {func_name} のテストケースを生成中...")
            
            # Positive test case
            positive_content = self.generate_positive_test_case(func_name, func_info)
            positive_path = os.path.join(code_snippets_dir, f'{func_name}_positive.py')
            with open(positive_path, 'w', encoding='utf-8') as f:
                f.write(positive_content)
            
            # Negative test case
            negative_content = self.generate_negative_test_case(func_name, func_info)
            negative_path = os.path.join(code_snippets_dir, f'{func_name}_negative.py')
            with open(negative_path, 'w', encoding='utf-8') as f:
                f.write(negative_content)
            
            # Golden snippet
            golden_content = self.generate_golden_snippet(func_name, func_info)
            golden_path = os.path.join(golden_snippets_dir, f'{func_name}_golden.py')
            with open(golden_path, 'w', encoding='utf-8') as f:
                f.write(golden_content)
        
        print(f"✅ {len(self.functions)} 個の関数のテストケースを生成完了")
        print(f"📊 生成されたファイル:")
        print(f"   - Positive test cases: {len(self.functions)} 個")
        print(f"   - Negative test cases: {len(self.functions)} 個")
        print(f"   - Golden snippets: {len(self.functions)} 個")

def main():
    # 検証レポートのパス
    report_path = "verification_reports/comprehensive_verification_20250824_054330.md"
    
    if not os.path.exists(report_path):
        print(f"❌ 検証レポートが見つかりません: {report_path}")
        return
    
    # ジェネレーターを作成
    generator = TestCaseGenerator(report_path)
    
    # テストケースを生成
    generator.generate_all_test_cases(".")

if __name__ == "__main__":
    main()
