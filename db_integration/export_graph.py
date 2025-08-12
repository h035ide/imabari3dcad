import os
import sys
import json
import logging
import argparse
from neo4j import GraphDatabase
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_project_root():
    """プロジェクトのルートパスをsys.pathに追加します。"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root

class GraphExporter:
    """
    Neo4jからグラフデータをエクスポートし、vis.js用のJSONを生成するクラス。
    """
    def __init__(self, uri, user, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        logging.info(f"GraphExporterがデータベース '{database}' に接続されました。")

    def close(self):
        self.driver.close()

    def export_to_vis_json(self, output_path="graph_data.json"):
        """
        グラフデータをvis.js互換のJSON形式でエクスポートします。
        """
        logging.info("グラフデータのエクスポートを開始します...")
        with self.driver.session(database=self.database) as session:
            nodes_result = session.run("MATCH (n) RETURN n, labels(n) as labels")
            rels_result = session.run("MATCH (n)-[r]->(m) RETURN r, startNode(r) as start, endNode(r) as end")

            nodes = []
            node_ids = set()
            for record in nodes_result:
                node_data = record["n"]
                node_id = node_data.element_id
                if node_id not in node_ids:
                    node_label = record["labels"][0] if record["labels"] else "Node"
                    node_name = node_data.get('name', 'N/A')
                    nodes.append({
                        "id": node_id,
                        "label": f"{node_label}: {node_name}",
                        "group": node_label,
                        "title": json.dumps(dict(node_data), ensure_ascii=False, indent=2) # ツールチップ用
                    })
                    node_ids.add(node_id)

            edges = []
            for record in rels_result:
                rel_data = record["r"]
                start_node_id = record["start"].element_id
                end_node_id = record["end"].element_id

                edges.append({
                    "from": start_node_id,
                    "to": end_node_id,
                    "label": type(rel_data).__name__
                })

        graph_data = {"nodes": nodes, "edges": edges}
        
        output_path = os.path.join(os.path.dirname(__file__), output_path)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

        logging.info(f"グラフデータを {output_path} に正常にエクスポートしました。")
        logging.info(f"  - ノード数: {len(nodes)}")
        logging.info(f"  - エッジ数: {len(edges)}")


def main():
    """メイン関数"""
    setup_project_root()
    load_dotenv()

    parser = argparse.ArgumentParser(description="Neo4jグラフをvis.js用のJSONとしてエクスポートします。")
    parser.add_argument("--db-name", default="unifieddb", help="対象のNeo4jデータベース名。")
    parser.add_argument("--output-file", default="graph_data.json", help="出力するJSONファイル名。")
    args = parser.parse_args()

    try:
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
        neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not all([neo4j_uri, neo4j_user, neo4j_password]):
            raise ValueError("Neo4jの接続情報 (.envファイル) が不足しています。")

        exporter = GraphExporter(neo4j_uri, neo4j_user, neo4j_password, args.db_name)
        exporter.export_to_vis_json(args.output_file)
        exporter.close()

    except Exception as e:
        logging.error(f"エクスポート中にエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
