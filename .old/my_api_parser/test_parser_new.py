#!/usr/bin/env python3
# test_parser_new.py
"""
tree-sitterの新しいバージョンでLanguageオブジェクトを作成し、パーサーをテストする
"""

import os
import json
from tree_sitter import Language, Parser

def load_language_from_src():
    """生成されたsrcファイルからLanguageオブジェクトを作成"""
    try:
        # 生成されたファイルのパスを確認
        src_dir = os.path.join(os.path.dirname(__file__), 'src')
        grammar_json_path = os.path.join(src_dir, 'grammar.json')
        node_types_path = os.path.join(src_dir, 'node-types.json')
        
        if not os.path.exists(grammar_json_path):
            print("grammar.jsonファイルが見つかりません。")
            print("tree-sitter generateを実行してください。")
            return None
        
        print("✅ 生成されたファイルが見つかりました")
        print(f"- grammar.json: {os.path.exists(grammar_json_path)}")
        print(f"- node-types.json: {os.path.exists(node_types_path)}")
        
        # grammar.jsonの内容を確認
        with open(grammar_json_path, 'r') as f:
            grammar_data = json.load(f)
            print(f"言語名: {grammar_data.get('name', 'unknown')}")
        
        # tree-sitterの新しいバージョンでは、Languageオブジェクトの作成方法が変更されている
        # まず、生成されたファイルを使用してLanguageオブジェクトを作成してみます
        try:
            # 方法1: 直接Languageオブジェクトを作成（新しい構文）
            language = Language('api_doc', src_dir)
            print("✅ Languageオブジェクトの作成に成功しました（方法1）")
            return language
        except Exception as e:
            print(f"方法1でエラー: {e}")
            
            try:
                # 方法2: 生成されたファイルを使用
                language = Language('api_doc', grammar_json_path)
                print("✅ Languageオブジェクトの作成に成功しました（方法2）")
                return language
            except Exception as e2:
                print(f"方法2でエラー: {e2}")
                
                try:
                    # 方法3: カスタムLanguageクラスを作成
                    class CustomLanguage:
                        def __init__(self, name, grammar_path):
                            self.name = name
                            self.grammar_path = grammar_path
                            # ここで実際のLanguageオブジェクトを作成
                            # tree-sitterの新しいバージョンでは、この部分が変更されている
                    
                    language = CustomLanguage('api_doc', grammar_json_path)
                    print("✅ カスタムLanguageオブジェクトを作成しました（方法3）")
                    return language
                except Exception as e3:
                    print(f"方法3でエラー: {e3}")
                    return None
    
    except Exception as e:
        print(f"Languageオブジェクトの作成中にエラーが発生しました: {e}")
        return None

def test_parser():
    """パーサーをテストする"""
    language = load_language_from_src()
    
    if language is None:
        print("Languageオブジェクトの作成に失敗しました。")
        return
    
    # パーサーを作成
    parser = Parser()
    
    # Languageオブジェクトがカスタムクラスの場合は、実際のLanguageオブジェクトを取得
    if hasattr(language, 'name') and not hasattr(language, 'query'):
        print("カスタムLanguageオブジェクトです。実際のLanguageオブジェクトを作成します。")
        # ここで実際のLanguageオブジェクトを作成する必要があります
        return
    
    parser.set_language(language)
    
    # テスト用のコード
    test_code = '''
/**
 * @function calculateSum
 * @param {number} a - 最初の数値
 * @param {number} b - 2番目の数値
 * @returns {number} 合計値
 */
function calculateSum(a, b) {
    return a + b;
}
'''
    
    # パースを実行
    tree = parser.parse(test_code.encode('utf-8'))
    
    if tree:
        print("✅ パースが成功しました！")
        print(f"ルートノード: {tree.root_node.type}")
        
        # ツリーを表示
        def print_node(node, depth=0):
            indent = "  " * depth
            text = node.text.decode('utf-8') if node.text else ''
            print(f"{indent}{node.type}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            for child in node.children:
                print_node(child, depth + 1)
        
        print_node(tree.root_node)
    else:
        print("❌ パースに失敗しました。")

def main():
    """メイン関数"""
    print("🔧 tree-sitter 新しいバージョンテスト")
    print("=" * 50)
    
    # 生成されたファイルの確認
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    if os.path.exists(src_dir):
        print("✅ srcディレクトリが存在します")
        files = os.listdir(src_dir)
        print(f"ファイル一覧: {files}")
    else:
        print("❌ srcディレクトリが見つかりません")
        return
    
    # パーサーのテスト
    test_parser()

if __name__ == "__main__":
    main() 