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
    
    def _generate_param_value(self, param_name: str, param_type: str) -> str:
        """パラメータの型に基づいて適切な値を生成"""
        # 型判定の順序を修正：より具体的な型を先に判定
        if '要素(配列)' in param_type:
            # 配列型パラメータの適切な処理
            if 'pDivideElements' in param_name:
                return '[divide_element_1, divide_element_2]'
            elif 'pSubSolids' in param_name:
                return '[subsolid_element_1, subsolid_element_2]'
            elif 'SrcSurfaces' in param_name:
                return '[surface_element_1, surface_element_2]'
            elif 'Sheet' in param_name:
                return '[sheet_element_1, sheet_element_2]'
            elif 'CtrlPoints' in param_name:
                return '[(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]'
            elif 'Weights' in param_name:
                return '[1.0, 1.0, 1.0]'
            elif 'Knots' in param_name:
                return '[0.0, 0.0, 0.0, 1.0, 1.0, 1.0]'
            else:
                return f'[{param_name}_element]'
        elif '点(配列)' in param_type:
            return '[(0.0, 0.0), (1.0, 1.0)]'
        elif '浮動小数点(配列)' in param_type:
            return '[1.0, 2.0, 3.0]'
        elif 'bool' in param_type:
            return 'True'
        elif '文字列' in param_type:
            return f'"{param_name}"'
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
        elif '方向' in param_type:
            return '(1.0, 0.0, 0.0)'
        elif '平面' in param_type:
            return 'XY_PLANE'
        elif '要素' in param_type:
            return f'{param_name}_element'
        elif '材料' in param_type:
            return '"STEEL"'
        elif '要素グループ' in param_type:
            return '"MAIN_GROUP"'
        elif '関連設定' in param_type:
            return '"GEOMETRIC"'
        elif 'オペレーションタイプ' in param_type:
            return '"UNION"'
        elif 'モールド位置' in param_type:
            return '"TOP"'
        elif '形状タイプ' in param_type:
            return '"RECTANGULAR"'
        elif '形状パラメータ' in param_type:
            return '["100.0", "50.0", "10.0"]'
        elif '厚み付けタイプ' in param_type:
            return '"SINGLE"'
        elif '範囲' in param_type:
            return '(0.0, 2*3.14159)'
        elif '変数単位' in param_type:
            return '"MM"'
        elif '注記スタイル' in param_type:
            return '"DEFAULT_STYLE"'
        elif 'スイープ方向' in param_type:
            return '"FORWARD"'
        elif '押し出しパラメータオブジェクト' in param_type:
            return 'extrude_param'
        elif 'ブラケット要素のパラメータオブジェクト' in param_type:
            return 'bracket_param'
        elif '条材要素のパラメータオブジェクト' in param_type:
            return 'profile_param'
        else:
            return f'"{param_name}_value"'
    
    def generate_positive_test_case(self, func_name: str, func_info: Dict[str, Any]) -> str:
        """正しいテストケースを生成"""
        params = func_info.get('parameters', [])
        
        # パラメータの値を生成
        param_values = []
        for param in params:
            param_value = self._generate_param_value(param['name'], param['type'])
            param_values.append(param_value)
        
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
                param_value = self._generate_param_value(param['name'], param['type'])
                
                if i == len(params) - 2:  # 最後から2番目
                    test_case += f'    {param_value}                # {param["description"]}\n'
                else:
                    test_case += f'    {param_value},               # {param["description"]}\n'
            
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
    
    def validate_parameter_order(self, func_name: str, params: List[Dict]) -> bool:
        """パラメータの順序が正しいか検証"""
        # 主要な関数の期待されるパラメータ順序を定義
        expected_orders = {
            'BodyDivideByElements': [
                'pDriveFeatureName', 'pTargetBody', 'pDivideElements', 
                'pAlignmentDirection', 'pWCS', 'ReferMethod', 'bUpdate'
            ],
            'BodySeparateBySubSolids': [
                'pSeparateFeatureName', 'pTargetBody', 'pSubSolids',
                'pAlignmentDirection', 'ReferMethod', 'bUpdate'
            ],
            'CreateOffsetSheet': [
                'SheetName', 'ElementGroup', 'MaterialName', 'SrcSurfaces',
                'OffsetLength', 'bOffsetBackwards', 'bUpdate'
            ],
            'CreateSketchNURBSCurve': [
                'SketchPlane', 'SketchArcName', 'SketchLayer', 'nDegree',
                'bClose', 'bPeriodic', 'CtrlPoints', 'Weights', 'Knots',
                'Range', 'bUpdate'
            ],
            'CreateThicken': [
                'ThickenFeatureName', 'TargetSolidName', 'OperationType',
                'Sheet', 'ThickenType', 'Thickeness1', 'Thickeness2',
                'ThickenessOffset', 'ReferMethod', 'bUpdate'
            ],
            'MirrorCopy': [
                'SrcElements', 'plane', 'ReferMethod'
            ],
            'TranslationCopy': [
                'SrcElements', 'nCopy', 'direction', 'distance', 'ReferMethod'
            ]
        }
        
        if func_name in expected_orders:
            expected_order = expected_orders[func_name]
            actual_order = [param['name'] for param in params]
            
            # 順序の検証
            for i, expected in enumerate(expected_order):
                if i < len(actual_order) and actual_order[i] != expected:
                    print(f"⚠️ パラメータ順序エラー: {func_name}")
                    print(f"   期待: {expected} at position {i}")
                    print(f"   実際: {actual_order[i]} at position {i}")
                    return False
        
        return True
    
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
            
            # パラメータ順序の検証
            if not self.validate_parameter_order(func_name, func_info.get('parameters', [])):
                print(f"   ⚠️ パラメータ順序に問題があります")
            
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
    # スクリプトのディレクトリを基準としたパスを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(script_dir, "verification_reports", "comprehensive_verification_20250824_054330.md")
    
    if not os.path.exists(report_path):
        print(f"❌ 検証レポートが見つかりません: {report_path}")
        print(f"📁 現在のディレクトリ: {os.getcwd()}")
        print(f"📁 スクリプトのディレクトリ: {script_dir}")
        print(f"🔍 利用可能な検証レポート:")
        
        # 利用可能な検証レポートを表示
        verification_dir = os.path.join(script_dir, "verification_reports")
        if os.path.exists(verification_dir):
            for file in os.listdir(verification_dir):
                if file.endswith(".md") and "comprehensive_verification" in file:
                    print(f"   - {file}")
        return
    
    print(f"✅ 検証レポートを発見: {report_path}")
    
    # ジェネレーターを作成
    generator = TestCaseGenerator(report_path)
    
    # テストケースを生成
    generator.generate_all_test_cases(script_dir)

if __name__ == "__main__":
    main()
