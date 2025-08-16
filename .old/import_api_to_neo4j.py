import os
import sys
import re
from dotenv import load_dotenv
from db_integration.core.neo4j_uploader import Neo4jUploader

# プロジェクトルートをパスに追加
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# .envファイルを読み込み
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))

def parse_api_markdown(file_path):
    """APIドキュメントのMarkdownファイルを解析して、構造化されたデータに変換します。"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    api_entries = []
    
    # メソッドセクションを分割
    sections = content.split('### ')
    
    for section in sections[1:]:  # 最初のセクションはヘッダーなのでスキップ
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # メソッド名を取得
        method_name = lines[0].strip()
        if not method_name:
            continue
            
        # 説明を取得
        description = ""
        params = []
        returns = None
        
        current_section = None
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('**返り値:**'):
                current_section = 'returns'
                returns_text = line.replace('**返り値:**', '').strip()
                if returns_text:
                    returns = {'type': returns_text}
            elif line.startswith('**パラメータ:**'):
                current_section = 'params'
            elif line.startswith('- `') and current_section == 'params':
                # パラメータ行を解析
                param_match = re.match(r'- `(\w+)` \(([^)]+)\): (.+)', line)
                if param_match:
                    param_name = param_match.group(1)
                    param_type = param_match.group(2)
                    param_desc = param_match.group(3)
                    
                    # 必須かどうかを判定（空文字不可の記述があるか）
                    is_required = '空文字不可' in param_desc
                    
                    params.append({
                        'name': param_name,
                        'type': param_type,
                        'description': param_desc,
                        'is_required': is_required,
                        'position': len(params)
                    })
            elif current_section == 'returns' and line.startswith('**'):
                # 返り値の詳細情報
                if returns:
                    returns['description'] = line.replace('**', '').strip()
            elif current_section == 'params' and line.startswith('**'):
                # パラメータセクションの終了
                current_section = None
            elif current_section == 'returns' and line.startswith('**'):
                # 返り値セクションの終了
                current_section = None
            elif current_section and line and not line.startswith('---'):
                # 説明文を蓄積
                if current_section == 'returns' and returns:
                    returns['description'] = line
                elif current_section == 'params':
                    # パラメータの追加説明
                    pass
        
        # APIエントリーを作成
        api_entry = {
            'entry_type': 'function',
            'name': method_name,
            'description': description,
            'category': 'Partオブジェクトのメソッド',
            'params': params,
            'returns': returns,
            'notes': '',
            'implementation_status': 'documented'
        }
        
        api_entries.append(api_entry)
    
    return {
        'api_entries': api_entries,
        'type_definitions': []
    }

def main():
    """メインの実行関数"""
    print("=== APIドキュメントをNeo4jにインポート開始 ===")
    
    # 環境変数を確認
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_database = os.getenv("NEO4J_DATABASE", "codegenerator")
    
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        print("エラー: 必要な環境変数が設定されていません。")
        print("NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD を設定してください。")
        sys.exit(1)
    
    try:
        # Neo4jUploaderを初期化
        uploader = Neo4jUploader(neo4j_uri, neo4j_user, neo4j_password, neo4j_database)
        
        # APIドキュメントを解析
        api_file_path = os.path.join(project_root, 'data', 'api_doc', 'api 1.md')
        print(f"APIドキュメントを解析中: {api_file_path}")
        
        api_data = parse_api_markdown(api_file_path)
        print(f"{len(api_data['api_entries'])}件のAPIエントリーを解析しました。")
        
        # Neo4jにデータをアップロード
        print("Neo4jにデータをアップロード中...")
        uploader.upload_api_data(api_data)
        
        print("APIドキュメントのNeo4jへのインポートが完了しました。")
        
        # アップロードされたデータを確認
        print("\nアップロードされたデータの確認:")
        with uploader.driver.session(database=neo4j_database) as session:
            # APIFunctionノードの数を確認
            result = session.run("MATCH (n:ApiFunction) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"APIFunctionノード数: {count}")
            
            # サンプルデータを表示
            if count > 0:
                result = session.run("MATCH (n:ApiFunction) RETURN n.name as name, n.description as desc LIMIT 3")
                print("\nサンプルデータ:")
                for record in result:
                    print(f"  - {record['name']}: {record['desc'][:100]}...")
        
        uploader.close()
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
