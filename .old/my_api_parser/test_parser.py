# test_parser.py
import os
from tree_sitter import Language, Parser

def load_language():
    """tree-sitterの新しいバージョンでLanguageオブジェクトを読み込む"""
    try:
        # 生成されたファイルのパスを確認
        src_dir = os.path.join(os.path.dirname(__file__), 'src')
        parser_c_path = os.path.join(src_dir, 'parser.c')
        
        if not os.path.exists(parser_c_path):
            print("parser.cファイルが見つかりません。")
            print("tree-sitter generateを実行してください。")
            return None
        
        # tree-sitterの新しいバージョンでは、Languageオブジェクトの作成方法が変更されている可能性があります
        # まず、生成されたファイルを使用してLanguageオブジェクトを作成してみます
        try:
            # 方法1: 直接Languageオブジェクトを作成
            language = Language('api_doc', 'src')
            print("Languageオブジェクトの作成に成功しました")
            return language
        except Exception as e:
            print(f"方法1でエラー: {e}")
            
            try:
                # 方法2: 生成されたファイルを使用
                language = Language('api_doc', parser_c_path)
                print("Languageオブジェクトの作成に成功しました")
                return language
            except Exception as e2:
                print(f"方法2でエラー: {e2}")
                
                # 方法3: 古い方法を試す
                try:
                    from tree_sitter.binding import Language as OldLanguage
                    language = OldLanguage.build_library(
                        'build/my-languages.so',
                        ['.']
                    )
                    print("古い方法でLanguageオブジェクトの作成に成功しました")
                    return language
                except Exception as e3:
                    print(f"方法3でエラー: {e3}")
                    return None
    
    except Exception as e:
        print(f"Languageオブジェクトの作成中にエラーが発生しました: {e}")
        return None

def test_parser():
    """パーサーをテストする"""
    language = load_language()
    
    if language is None:
        print("Languageオブジェクトの作成に失敗しました。")
        return
    
    # パーサーを作成
    parser = Parser()
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
        print("パースが成功しました！")
        print(f"ルートノード: {tree.root_node.type}")
        
        # ツリーを表示
        def print_node(node, depth=0):
            indent = "  " * depth
            print(f"{indent}{node.type}: '{node.text.decode('utf-8') if node.text else ''}'")
            for child in node.children:
                print_node(child, depth + 1)
        
        print_node(tree.root_node)
    else:
        print("パースに失敗しました。")

if __name__ == "__main__":
    test_parser() 