"""
パフォーマンス特性の分析モジュール

このモジュールはPythonコードの時間計算量、空間計算量、
ボトルネック、最適化提案を分析します。
"""

import ast
import re
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    time_complexity: str  # 時間計算量 (例: O(n), O(n^2))
    space_complexity: str  # 空間計算量
    bottlenecks: List[str]  # ボトルネック
    optimizations: List[str]  # 最適化提案
    memory_usage_estimate: str  # メモリ使用量の推定
    performance_score: float  # パフォーマンススコア (0-1)


class PerformanceAnalyzer:
    """コードのパフォーマンス特性を分析するクラス"""
    
    def __init__(self):
        # パフォーマンスパターンの定義
        self.complexity_patterns = {
            # 基本的なループパターン
            'single_loop': {'pattern': r'for\s+\w+\s+in', 'complexity': 'O(n)'},
            'nested_loop': {'pattern': r'for\s+\w+\s+in.*?for\s+\w+\s+in', 'complexity': 'O(n²)'},
            'triple_loop': {'pattern': r'(for\s+\w+\s+in.*?){3,}', 'complexity': 'O(n³)'},
            
            # 一般的なアルゴリズムパターン
            'sort': {'pattern': r'\.sort\(\)|sorted\(', 'complexity': 'O(n log n)'},
            'dict_lookup': {'pattern': r'\[.*?\]|\\.get\(', 'complexity': 'O(1)'},
            'list_append': {'pattern': r'\.append\(', 'complexity': 'O(1)'},
            'list_extend': {'pattern': r'\.extend\(', 'complexity': 'O(k)'},
            
            # 検索パターン
            'linear_search': {'pattern': r'\s+in\s+\w+', 'complexity': 'O(n)'},
            'recursive': {'pattern': r'def\s+\w+.*?:\s*.*?\w+\(', 'complexity': 'O(2^n)'},
        }
        
        # ボトルネックパターン
        self.bottleneck_patterns = {
            'file_io': r'open\(|\.read\(\)|\.write\(',
            'network_io': r'requests\.|urllib\.|socket\.',
            'database_query': r'\.execute\(|\.query\(',
            'large_list_creation': r'\[.*for.*in.*\]',
            'string_concatenation': r'\+.*["\']',
            'global_access': r'global\s+\w+',
            'exception_handling': r'try:.*except',
        }
        
        # 最適化パターン
        self.optimization_suggestions = {
            'list_comprehension': {
                'pattern': r'for\s+\w+\s+in.*?\.append\(',
                'suggestion': 'リスト内包表記を使用してパフォーマンスを改善'
            },
            'generator_expression': {
                'pattern': r'\[.*for.*in.*\]',
                'suggestion': 'ジェネレータ式を使用してメモリ使用量を削減'
            },
            'set_membership': {
                'pattern': r'\s+in\s+\[.*\]',
                'suggestion': 'リストではなくsetを使用して検索を高速化'
            },
            'string_join': {
                'pattern': r'\+.*["\']',
                'suggestion': 'str.join()を使用して文字列結合を最適化'
            },
            'cache_results': {
                'pattern': r'def\s+\w+.*?return',
                'suggestion': '@lru_cacheデコレータを検討'
            }
        }

    def analyze_code(self, code: str, function_name: str = "") -> PerformanceMetrics:
        """
        コードの包括的なパフォーマンス分析
        
        Args:
            code: 分析対象のコード
            function_name: 関数名（オプション）
        
        Returns:
            PerformanceMetrics: 分析結果
        """
        try:
            # 各種分析の実行
            time_complexity = self.analyze_time_complexity(code)
            space_complexity = self.analyze_space_complexity(code)
            bottlenecks = self.identify_bottlenecks(code)
            optimizations = self.suggest_optimizations(code)
            memory_estimate = self.estimate_memory_usage(code)
            score = self.calculate_performance_score(code)
            
            return PerformanceMetrics(
                time_complexity=time_complexity,
                space_complexity=space_complexity,
                bottlenecks=bottlenecks,
                optimizations=optimizations,
                memory_usage_estimate=memory_estimate,
                performance_score=score
            )
            
        except Exception as e:
            # エラー時のフォールバック
            return PerformanceMetrics(
                time_complexity="分析エラー",
                space_complexity="分析エラー",
                bottlenecks=[f"分析中にエラーが発生: {str(e)}"],
                optimizations=[],
                memory_usage_estimate="不明",
                performance_score=0.0
            )

    def analyze_time_complexity(self, code: str) -> str:
        """時間計算量を分析"""
        # 複雑度の初期値
        max_complexity = "O(1)"
        
        # 各パターンをチェック
        for pattern_name, pattern_info in self.complexity_patterns.items():
            if re.search(pattern_info['pattern'], code, re.DOTALL | re.IGNORECASE):
                current_complexity = pattern_info['complexity']
                # より高い複雑度を採用
                if self._is_higher_complexity(current_complexity, max_complexity):
                    max_complexity = current_complexity
        
        # ネストしたループの特別な処理
        nested_loops = self._count_nested_loops(code)
        if nested_loops > 1:
            max_complexity = f"O(n^{nested_loops})"
        
        return max_complexity

    def analyze_space_complexity(self, code: str) -> str:
        """空間計算量を分析"""
        # データ構造の使用をチェック
        space_indicators = {
            r'list\(|append\(|extend\(': 'O(n)',
            r'dict\(|{.*}': 'O(n)',
            r'set\(': 'O(n)',
            r'range\(': 'O(1)',
            r'yield': 'O(1)',  # ジェネレータ
        }
        
        max_space = "O(1)"
        
        for pattern, complexity in space_indicators.items():
            if re.search(pattern, code):
                if self._is_higher_complexity(complexity, max_space):
                    max_space = complexity
        
        # 再帰関数の場合
        if re.search(r'def\s+\w+.*?:\s*.*?\w+\(.*?\)', code, re.DOTALL):
            max_space = "O(n) (再帰スタック)"
        
        return max_space

    def identify_bottlenecks(self, code: str) -> List[str]:
        """ボトルネックを特定"""
        bottlenecks = []
        
        for bottleneck_type, pattern in self.bottleneck_patterns.items():
            if re.search(pattern, code):
                bottleneck_msg = self._get_bottleneck_message(bottleneck_type)
                bottlenecks.append(bottleneck_msg)
        
        # ネストしたループのチェック
        nested_count = self._count_nested_loops(code)
        if nested_count >= 3:
            bottlenecks.append(f"深いネストループ (レベル {nested_count}) - 計算時間が大幅に増加")
        
        # 大きなデータ構造の作成
        if re.search(r'\[.*for.*in.*for.*in.*\]', code):
            bottlenecks.append("ネストしたリスト内包表記 - メモリ使用量が大きい")
        
        return bottlenecks

    def suggest_optimizations(self, code: str) -> List[str]:
        """最適化提案を生成"""
        optimizations = []
        
        for opt_type, opt_info in self.optimization_suggestions.items():
            if re.search(opt_info['pattern'], code):
                optimizations.append(opt_info['suggestion'])
        
        # 特別な最適化提案
        if re.search(r'for.*in.*range\(len\(', code):
            optimizations.append("enumerate()を使用してより読みやすく効率的に")
        
        if re.search(r'if.*and.*or', code):
            optimizations.append("条件式を分割して短絡評価を活用")
        
        if re.search(r'\.sort\(\).*\.reverse\(\)', code):
            optimizations.append("sort(reverse=True)を使用して一度でソート")
        
        return optimizations

    def estimate_memory_usage(self, code: str) -> str:
        """メモリ使用量を推定"""
        # 基本的なメモリ使用量の推定
        memory_factors = []
        
        # リストの作成
        if re.search(r'\[.*for.*in.*\]', code):
            memory_factors.append("リスト内包表記: O(n)メモリ")
        
        # 辞書の作成
        if re.search(r'{.*for.*in.*}', code):
            memory_factors.append("辞書内包表記: O(n)メモリ")
        
        # 大量データの読み込み
        if re.search(r'\.read\(\)|\.readlines\(\)', code):
            memory_factors.append("ファイル全体読み込み: ファイルサイズ相当")
        
        # ジェネレータの使用
        if re.search(r'yield|generator', code):
            memory_factors.append("ジェネレータ使用: O(1)メモリ (効率的)")
        
        if not memory_factors:
            return "最小限 (O(1))"
        
        return " / ".join(memory_factors)

    def calculate_performance_score(self, code: str) -> float:
        """パフォーマンススコアを計算 (0-1の範囲)"""
        score = 1.0
        
        # 時間計算量によるペナルティ
        complexity = self.analyze_time_complexity(code)
        if "n^3" in complexity or "2^n" in complexity:
            score -= 0.4
        elif "n^2" in complexity:
            score -= 0.3
        elif "n log n" in complexity:
            score -= 0.1
        
        # ボトルネック数によるペナルティ
        bottleneck_count = len(self.identify_bottlenecks(code))
        score -= bottleneck_count * 0.1
        
        # 最適化可能数によるペナルティ
        optimization_count = len(self.suggest_optimizations(code))
        score -= optimization_count * 0.05
        
        # 良いパターンのボーナス
        if re.search(r'yield|generator', code):
            score += 0.1  # ジェネレータ使用
        
        if re.search(r'@lru_cache|@cache', code):
            score += 0.1  # キャッシュ使用
        
        return max(0.0, min(1.0, score))

    def _count_nested_loops(self, code: str) -> int:
        """ネストしたループの深さを数える"""
        try:
            tree = ast.parse(code)
            max_depth = 0
            
            def count_loop_depth(node, current_depth=0):
                nonlocal max_depth
                
                if isinstance(node, (ast.For, ast.While)):
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                
                for child in ast.iter_child_nodes(node):
                    count_loop_depth(child, current_depth)
            
            count_loop_depth(tree)
            return max_depth
            
        except:
            # AST解析に失敗した場合は正規表現で推定
            nested_pattern = r'for\s+\w+\s+in.*?for\s+\w+\s+in'
            if re.search(nested_pattern, code, re.DOTALL):
                return 2
            return 1 if re.search(r'for\s+\w+\s+in', code) else 0

    def _is_higher_complexity(self, complexity1: str, complexity2: str) -> bool:
        """計算量の大小を比較"""
        complexity_order = [
            "O(1)", "O(log n)", "O(n)", "O(n log n)", 
            "O(n²)", "O(n^2)", "O(n³)", "O(n^3)", "O(2^n)"
        ]
        
        try:
            index1 = complexity_order.index(complexity1)
            index2 = complexity_order.index(complexity2)
            return index1 > index2
        except ValueError:
            return False

    def _get_bottleneck_message(self, bottleneck_type: str) -> str:
        """ボトルネックタイプに応じたメッセージを取得"""
        messages = {
            'file_io': "ファイルI/O操作 - 処理時間の大部分を占める可能性",
            'network_io': "ネットワークI/O操作 - 通信遅延の影響を受ける",
            'database_query': "データベースクエリ - クエリ最適化を検討",
            'large_list_creation': "大きなリスト作成 - メモリ使用量とGCの負荷",
            'string_concatenation': "文字列結合 - join()の使用を検討",
            'global_access': "グローバル変数アクセス - ローカル変数の使用を検討",
            'exception_handling': "例外処理 - パフォーマンスオーバーヘッド",
        }
        return messages.get(bottleneck_type, f"検出されたボトルネック: {bottleneck_type}")

    def analyze_file(self, file_path: str) -> Dict[str, PerformanceMetrics]:
        """ファイル全体のパフォーマンス分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 関数ごとに分析
            tree = ast.parse(content)
            results = {}
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_code = ast.get_source_segment(content, node)
                    if func_code:
                        results[node.name] = self.analyze_code(func_code, node.name)
            
            # ファイル全体の分析
            results['__file_overall__'] = self.analyze_code(content, "ファイル全体")
            
            return results
            
        except Exception as e:
            return {
                'error': PerformanceMetrics(
                    time_complexity="分析エラー",
                    space_complexity="分析エラー", 
                    bottlenecks=[f"ファイル分析エラー: {str(e)}"],
                    optimizations=[],
                    memory_usage_estimate="不明",
                    performance_score=0.0
                )
            }

    def generate_report(self, metrics: PerformanceMetrics, function_name: str = "") -> str:
        """分析結果のレポート生成"""
        report = []
        
        if function_name:
            report.append(f"## パフォーマンス分析レポート: {function_name}")
        else:
            report.append("## パフォーマンス分析レポート")
        
        report.append("")
        report.append(f"**パフォーマンススコア**: {metrics.performance_score:.2f}/1.0")
        report.append(f"**時間計算量**: {metrics.time_complexity}")
        report.append(f"**空間計算量**: {metrics.space_complexity}")
        report.append(f"**メモリ使用量推定**: {metrics.memory_usage_estimate}")
        report.append("")
        
        if metrics.bottlenecks:
            report.append("### 🚨 検出されたボトルネック")
            for bottleneck in metrics.bottlenecks:
                report.append(f"- {bottleneck}")
            report.append("")
        
        if metrics.optimizations:
            report.append("### 💡 最適化提案")
            for optimization in metrics.optimizations:
                report.append(f"- {optimization}")
            report.append("")
        
        return "\n".join(report)


# 使用例のデモ関数
def demo_analysis():
    """パフォーマンス分析のデモ"""
    analyzer = PerformanceAnalyzer()
    
    # サンプルコード
    sample_codes = {
        "効率的なコード": """
def find_max(numbers):
    if not numbers:
        return None
    return max(numbers)
        """,
        
        "非効率なコード": """
def find_duplicates(data):
    duplicates = []
    for i in range(len(data)):
        for j in range(len(data)):
            if i != j and data[i] == data[j]:
                if data[i] not in duplicates:
                    duplicates.append(data[i])
    return duplicates
        """,
        
        "最適化が必要なコード": """
def process_data(items):
    result = ""
    for item in items:
        result = result + str(item) + ","
    return result[:-1]
        """
    }
    
    print("=== パフォーマンス分析デモ ===")
    for name, code in sample_codes.items():
        print(f"\n{name}:")
        metrics = analyzer.analyze_code(code, name)
        print(analyzer.generate_report(metrics, name))


if __name__ == "__main__":
    demo_analysis()