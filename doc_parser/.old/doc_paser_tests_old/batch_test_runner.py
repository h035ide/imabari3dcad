#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成されたテストケースを一括で実行するスクリプト
すべてのpositive/negativeテストケースを実行し、結果をレポートします
"""

import os
import sys
import glob
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime

class BatchTestRunner:
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_single_test(self, test_file: str) -> Tuple[bool, str]:
        """単一のテストファイルを実行"""
        try:
            # validate_code_snippet.pyを使用してテストを実行
            result = subprocess.run(
                [sys.executable, "validate_code_snippet.py", test_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # 出力から結果を解析
                if "✅ PASSED" in result.stdout:
                    return True, "PASSED"
                elif "❌ FAILED" in result.stdout:
                    return False, "FAILED"
                else:
                    return False, "UNKNOWN"
            else:
                return False, f"ERROR: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT"
        except Exception as e:
            return False, f"EXCEPTION: {str(e)}"
    
    def run_all_tests(self) -> Dict[str, Any]:
        """すべてのテストを実行"""
        print("🚀 バッチテストを開始します...")
        print("=" * 60)
        
        # code_snippetsディレクトリ内のすべてのテストファイルを取得
        test_files = glob.glob("code_snippets/*.py")
        test_files.sort()
        
        self.total_tests = len(test_files)
        print(f"📊 実行対象: {self.total_tests} 個のテストファイル")
        print()
        
        # 各テストファイルを実行
        for test_file in test_files:
            test_name = os.path.basename(test_file)
            print(f"🧪 実行中: {test_name}")
            
            success, result = self.run_single_test(test_file)
            
            if success:
                self.passed_tests += 1
                status = "✅ PASS"
            else:
                self.failed_tests += 1
                status = "❌ FAIL"
            
            self.test_results[test_name] = {
                'status': success,
                'result': result,
                'file': test_file
            }
            
            print(f"   {status}: {result}")
            print()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """テスト結果レポートを生成"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'success_rate': (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
            'results': self.test_results
        }
        
        # レポートを表示
        print("=" * 60)
        print("📋 テスト結果サマリー")
        print("=" * 60)
        print(f"総テスト数: {self.total_tests}")
        print(f"成功: {self.passed_tests}")
        print(f"失敗: {self.failed_tests}")
        print(f"成功率: {report['success_rate']:.1f}%")
        print()
        
        # 失敗したテストの詳細
        if self.failed_tests > 0:
            print("❌ 失敗したテスト:")
            for test_name, result in self.test_results.items():
                if not result['status']:
                    print(f"   - {test_name}: {result['result']}")
            print()
        
        # レポートをファイルに保存
        self.save_report(report)
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """レポートをファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"verification_reports/batch_test_report_{timestamp}.json"
        
        # verification_reportsディレクトリを作成
        os.makedirs("verification_reports", exist_ok=True)
        
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 レポートを保存しました: {report_file}")
    
    def run_validation_tests(self):
        """既存のvalidate_code_snippet.pyが利用可能かテスト"""
        if not os.path.exists("validate_code_snippet.py"):
            print("❌ validate_code_snippet.py が見つかりません")
            print("   このスクリプトを実行する前に、validate_code_snippet.pyが利用可能であることを確認してください")
            return False
        
        # 簡単なテストファイルで動作確認
        test_file = "code_snippets/CreateSolid_positive.py"
        if os.path.exists(test_file):
            print(f"🔍 動作確認: {test_file}")
            success, result = self.run_single_test(test_file)
            print(f"   結果: {'✅ 成功' if success else '❌ 失敗'} - {result}")
            return success
        else:
            print("❌ テストファイルが見つかりません")
            return False

def main():
    runner = BatchTestRunner()
    
    # 動作確認
    if not runner.run_validation_tests():
        print("❌ バッチテストを実行できません")
        sys.exit(1)
    
    print()
    
    # すべてのテストを実行
    report = runner.run_all_tests()
    
    # 終了コードを設定
    if report['failed_tests'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
