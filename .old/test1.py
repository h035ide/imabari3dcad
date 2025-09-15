#!/usr/bin/env python3
# test1.py
"""
正規表現ベースのAPIドキュメントパーサーを使用してAPIドキュメントを解析
"""

import json
from regex_parser import RegexAPIParser

def extract_function_data(ast_node):
    """ASTから関数データを抽出"""
    functions_data = []
    
    # doc_commentノードを検索
    for doc_comment in ast_node.children:
        if doc_comment.type == 'doc_comment':
            function_data = {
                "name": None,
                "type": "function",
                "params": [],
                "returns": None,
                "description": ""
            }
            
            # doc_comment内の各ノードを処理
            for node in doc_comment.children:
                if node.type == 'function_tag':
                    # 関数名を取得
                    for child in node.children:
                        if child.type == 'identifier':
                            function_data["name"] = child.text
                
                elif node.type == 'param_tag':
                    # パラメータ情報を取得
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
                    
                    if param_info["name"]:
                        function_data["params"].append(param_info)
                
                elif node.type == 'returns_tag':
                    # 戻り値情報を取得
                    return_info = {
                        "type_name": None,
                        "description": None
                    }
                    
                    for child in node.children:
                        if child.type == 'type':
                            return_info["type_name"] = child.text.strip('{}')
                        elif child.type == 'description':
                            return_info["description"] = child.text
                    
                    function_data["returns"] = return_info
                
                elif node.type == 'doc_text':
                    # 説明文を追加
                    if function_data["description"]:
                        function_data["description"] += " " + node.text
                    else:
                        function_data["description"] = node.text
            
            # 関数名が取得できた場合のみ追加
            if function_data["name"]:
                functions_data.append(function_data)
    
    return functions_data

def main():
    """メイン関数"""
    print("🔧 APIドキュメント解析開始")
    print("=" * 50)
    
    # 正規表現ベースのパーサーを作成
    parser = RegexAPIParser()
    
    # APIドキュメントファイルを読み込み
    try:
        with open('api_document.txt', 'r', encoding='utf-8') as f:
            api_doc_text = f.read()
        print("✅ APIドキュメントファイルを読み込みました")
    except FileNotFoundError:
        print("❌ api_document.txtファイルが見つかりません")
        print("テスト用のサンプルデータを使用します")
        
        # テスト用のサンプルデータ
        api_doc_text = '''
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
    
    # パースを実行
    print("📝 パースを開始...")
    ast = parser.parse(api_doc_text)
    print("✅ パースが完了しました")
    
    # 関数データを抽出
    print("🔍 関数データを抽出中...")
    functions_data = extract_function_data(ast)
    print(f"✅ {len(functions_data)}個の関数を抽出しました")
    
    # 結果を表示
    print("\n📊 抽出された関数データ:")
    for i, func in enumerate(functions_data, 1):
        print(f"\n{i}. {func['name']}")
        print(f"   説明: {func.get('description', 'N/A')}")
        print(f"   パラメータ数: {len(func['params'])}")
        
        for j, param in enumerate(func['params'], 1):
            print(f"     {j}. {param['name']} ({param['type_name']}) - {param['description_raw']}")
        
        if func.get('returns'):
            print(f"   戻り値: {func['returns']['type_name']} - {func['returns']['description']}")
    
    # JSON形式で出力
    print("\n📄 JSON形式:")
    print(json.dumps(functions_data, indent=2, ensure_ascii=False))
    
    # JSONファイルに保存
    output_filename = "api_functions_data.json"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(functions_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 JSONファイルに保存しました: {output_filename}")
    except Exception as e:
        print(f"\n❌ JSONファイルの保存に失敗しました: {e}")
    
    print("\nStep 1: 正規表現ベースパーサーによる解析が完了しました。")

if __name__ == "__main__":
    main()