#!/usr/bin/env python3
# refactored_test3.py
"""
Neo4jへのデータ登録処理（クラスベース版）
"""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
from dotenv import load_dotenv

@dataclass
class Neo4jConfig:
    """Neo4j接続設定"""
    uri: str = "neo4j://localhost:7687"
    user: str = "neo4j"
    password: str = "your_password"
    database: str = "neo4j"
    input_file: str = 'api_functions_data_enriched.json'

class Neo4jDataUploader:
    """Neo4jへのデータ登録クラス"""
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        self.config = config or Neo4jConfig()
        self._load_environment()
        self.driver = None
        self.uploaded_functions = 0
        self.uploaded_arguments = 0
        self.uploaded_types = 0
        self.error_count = 0
    
    def _load_environment(self):
        """環境変数を読み込み"""
        load_dotenv()
        
        # 環境変数から設定を更新
        self.config.uri = os.environ.get("NEO4J_URI", self.config.uri)
        self.config.user = os.environ.get("NEO4J_USER", self.config.user)
        self.config.password = os.environ.get("NEO4J_PASSWORD", self.config.password)
        
        # パスワードのチェック
        if self.config.password == "your_password":
            raise ValueError("NEO4J_PASSWORD環境変数を設定してください")
    
    def connect_to_neo4j(self):
        """Neo4jに接続"""
        try:
            print(f"🔗 Neo4jに接続中...")
            print(f"   URI: {self.config.uri}")
            print(f"   Database: {self.config.database}")
            print(f"   User: {self.config.user}")
            
            self.driver = GraphDatabase.driver(
                self.config.uri, 
                auth=(self.config.user, self.config.password)
            )
            
            # 接続テスト
            with self.driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 as test")
                result.single()
            
            print("✅ Neo4jへの接続が成功しました")
            
        except Exception as e:
            raise ConnectionError(f"Neo4jへの接続に失敗しました: {e}")
    
    def load_functions_data(self) -> List[Dict[str, Any]]:
        """JSONファイルから関数データを読み込み"""
        try:
            with open(self.config.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 関数データを読み込みました: {self.config.input_file}")
            print(f"   関数数: {len(data)}")
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"エラー: {self.config.input_file} が見つかりません")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSONファイルの形式が正しくありません: {e}")
    
    def upload_function_to_neo4j(self, tx, func_data: Dict[str, Any]):
        """一つの関数データをNeo4jに登録するトランザクション処理"""
        try:
            # Functionノードの作成
            tx.run("""
                MERGE (f:Function {name: $func_name})
                SET f.description = $description
                """,
                func_name=func_data["name"],
                description=func_data.get("description", "")
            )
            self.uploaded_functions += 1
            
            # 返り値のTypeノードとリレーションシップを作成
            if func_data.get("returns") and func_data["returns"].get("type_name"):
                tx.run("""
                    MATCH (f:Function {name: $func_name})
                    MERGE (t:Type {name: $type_name})
                    MERGE (f)-[:RETURNS]->(t)
                    """,
                    func_name=func_data["name"],
                    type_name=func_data["returns"]["type_name"]
                )
                self.uploaded_types += 1
            
            # 引数の処理
            for param in func_data.get("params", []):
                self._upload_parameter(tx, func_data["name"], param)
                
        except Exception as e:
            print(f"   ❌ 関数 '{func_data.get('name', 'N/A')}' の登録に失敗: {e}")
            self.error_count += 1
            raise
    
    def _upload_parameter(self, tx, func_name: str, param: Dict[str, Any]):
        """パラメータをNeo4jに登録"""
        try:
            # Argumentノードを作成
            tx.run("""
                MERGE (a:Argument {name: $param_name})
                SET
                    a.description = $desc,
                    a.summary = $summary,
                    a.constraints = $constraints
                """,
                param_name=param["name"],
                desc=param.get("description_raw", ""),
                summary=param.get("summary_llm", ""),
                constraints=param.get("constraints_llm", [])
            )
            self.uploaded_arguments += 1
            
            # Typeノードを作成
            tx.run("MERGE (t:Type {name: $type_name})", 
                   type_name=param["type_name"])
            self.uploaded_types += 1
            
            # Function と Argument のリレーションシップを作成
            tx.run("""
                MATCH (f:Function {name: $func_name})
                MATCH (a:Argument {name: $param_name})
                MERGE (f)-[:HAS_ARGUMENT]->(a)
                """,
                func_name=func_name,
                param_name=param["name"]
            )
            
            # Argument と Type のリレーションシップを作成
            tx.run("""
                MATCH (a:Argument {name: $param_name})
                MATCH (t:Type {name: $type_name})
                MERGE (a)-[:HAS_TYPE]->(t)
                """,
                param_name=param["name"],
                type_name=param["type_name"]
            )
            
        except Exception as e:
            print(f"     ❌ パラメータ '{param.get('name', 'N/A')}' の登録に失敗: {e}")
            self.error_count += 1
            raise
    
    def upload_all_functions(self, functions_data: List[Dict[str, Any]]):
        """全関数データをNeo4jにアップロード"""
        print("🚀 Neo4jへのデータ登録を開始します...")
        print("=" * 60)
        
        total_functions = len(functions_data)
        total_params = sum(len(func.get("params", [])) for func in functions_data)
        
        print(f"対象関数数: {total_functions}")
        print(f"対象パラメータ数: {total_params}")
        print("-" * 60)
        
        try:
            with self.driver.session(database=self.config.database) as session:
                for i, func in enumerate(functions_data, 1):
                    print(f"[{i}/{total_functions}] Registering function: {func['name']}")
                    try:
                        session.execute_write(self.upload_function_to_neo4j, func)
                        print(f"   ✅ 成功")
                    except Exception as e:
                        print(f"   ❌ 失敗: {e}")
                        continue
                        
        except Exception as e:
            raise RuntimeError(f"データベースセッションでエラーが発生しました: {e}")
    
    def display_statistics(self):
        """アップロード統計を表示"""
        print("\n" + "=" * 60)
        print("📊 アップロード統計")
        print("=" * 60)
        print(f"アップロード済み関数数: {self.uploaded_functions}")
        print(f"アップロード済み引数数: {self.uploaded_arguments}")
        print(f"アップロード済み型数: {self.uploaded_types}")
        print(f"エラー数: {self.error_count}")
        
        total_operations = self.uploaded_functions + self.uploaded_arguments + self.uploaded_types
        if total_operations > 0:
            success_rate = (total_operations - self.error_count) / total_operations * 100
            print(f"成功率: {success_rate:.1f}%")
    
    def close_connection(self):
        """データベース接続を閉じる"""
        if self.driver:
            self.driver.close()
            print("🔌 Neo4j接続を閉じました")
    
    def process(self) -> bool:
        """メイン処理を実行"""
        print("🔧 Neo4jデータアップロード開始")
        print("=" * 60)
        
        try:
            # 1. Neo4jに接続
            self.connect_to_neo4j()
            
            # 2. データ読み込み
            functions_data = self.load_functions_data()
            
            # 3. データアップロード
            self.upload_all_functions(functions_data)
            
            # 4. 統計表示
            self.display_statistics()
            
            print("\nStep 3: Neo4jへのデータ登録が完了しました。")
            return True
            
        except Exception as e:
            print(f"\n❌ 処理中にエラーが発生しました: {e}")
            return False
        
        finally:
            # 5. 接続を閉じる
            self.close_connection()

def main():
    """メイン関数"""
    config = Neo4jConfig()
    uploader = Neo4jDataUploader(config)
    success = uploader.process()
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main() 