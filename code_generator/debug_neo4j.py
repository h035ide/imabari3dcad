#!/usr/bin/env python3
"""
Neo4jデバッグユーティリティ

機能:
 - Neo4jへの接続確認
 - 指定ラベルのノード数カウント（デフォルト: ApiFunction）
 - サンプルノード一覧表示（elementId, name, description 等）
 - ラベル一覧と件数表示
 - （オプション）Chroma の metadata にある `neo4j_node_id` と Neo4j の突合せチェック

使用例:
  python debug_neo4j.py --count --sample 5
  python debug_neo4j.py --list-labels
  python debug_neo4j.py --check-chroma --chroma-dir ../chroma_db_store --k 50
"""
import os
import sys
import argparse
import logging
import re
import json
from typing import List, Any, Dict

from dotenv import load_dotenv

# --- [Path Setup] ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# .env をルートから読み込む
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)
# --- [End Path Setup] ---

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None

try:
    # optional, only needed when --check-chroma
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
except Exception:
    Chroma = None
    OpenAIEmbeddings = None

DB_NAME = os.getenv('NEO4J_DATABASE', 'codeparsar')


def get_neo4j_driver():
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER')
    password = os.getenv('NEO4J_PASSWORD')
    if not all([uri, user, password]):
        raise EnvironmentError('NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD が .env に設定されていません')
    if GraphDatabase is None:
        raise ImportError('neo4j パッケージが見つかりません。pip install neo4j を実行してください')
    return GraphDatabase.driver(uri, auth=(user, password))


def count_nodes(driver, label: str = 'ApiFunction') -> int:
    query = f"MATCH (n:{label}) RETURN count(n) AS cnt"
    with driver.session(database=DB_NAME) as session:
        result = session.run(query)
        record = result.single()
        return record['cnt'] if record else 0


def sample_nodes(driver, label: str = 'ApiFunction', limit: int = 5) -> List[dict]:
    query = f"MATCH (n:{label}) RETURN elementId(n) AS id, n.name AS name, n.description AS description LIMIT $limit"
    with driver.session(database=DB_NAME) as session:
        result = session.run(query, limit=limit)
        return [r.data() for r in result]


def list_labels(driver, limit: int = 200) -> List[dict]:
    query = "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC LIMIT $limit"
    with driver.session(database=DB_NAME) as session:
        result = session.run(query, limit=limit)
        return [r.data() for r in result]


def check_chroma_mapping(driver, chroma_dir: str, collection: str, k_limit: int = None) -> dict:
    """
    Chroma の metadata に含まれる neo4j_node_id が実際に Neo4j 内に存在するかを確認する。
    戻り値: { 'total': int, 'missing': [ids], 'checked': int }
    """
    if Chroma is None:
        raise ImportError('langchain_community.chroma モジュールが見つかりません。必要なら pip install してください')
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise EnvironmentError('OPENAI_API_KEY が設定されていません。Chroma 読み込みには OpenAIEmbeddings の初期化が必要です')

    emb = OpenAIEmbeddings(api_key=api_key)
    vs = Chroma(collection_name=collection, embedding_function=emb, persist_directory=chroma_dir)

    # 内部APIを利用してメタデータ一覧を取得
    try:
        coll = vs._collection.get()
        metadatas = coll.get('metadatas', [])
    except Exception as e:
        raise RuntimeError(f'Chroma メタデータの取得に失敗しました: {e}')

    ids = []
    for m in metadatas:
        nid = None
        if isinstance(m, dict):
            nid = m.get('neo4j_node_id') or m.get('node_id')
        if nid:
            ids.append(nid)
        if k_limit and len(ids) >= k_limit:
            break

    missing = []
    checked = 0
    for nid in ids:
        # elementId を文字列として照合
        query = "MATCH (n) WHERE elementId(n) = $id RETURN count(n) AS cnt"
        with driver.session(database=DB_NAME) as session:
            res = session.run(query, id=str(nid))
            rec = res.single()
            cnt = rec['cnt'] if rec else 0
            checked += 1
            if not cnt:
                missing.append(nid)

    return {'total': len(ids), 'checked': checked, 'missing': missing}


def parse_args():
    p = argparse.ArgumentParser(description='Neo4j デバッグユーティリティ')
    p.add_argument('--count', action='store_true', help='指定ラベルのノード数を表示')
    p.add_argument('--label', default='ApiFunction', help='対象のラベル（デフォルト: ApiFunction）')
    p.add_argument('--sample', type=int, default=0, help='サンプルノードを表示（件数）')
    p.add_argument('--list-labels', action='store_true', help='ラベル一覧と件数を表示')
    p.add_argument('--check-chroma', action='store_true', help='Chroma の neo4j_node_id と Neo4j の突合せを行う')
    p.add_argument('--query', '-q', default=None, help='（オプション）Chromaで与えたクエリに基づく照合を行う')
    p.add_argument('--chroma-dir', default=os.path.join(project_root, 'chroma_db_store'), help='Chroma 永続化ディレクトリ')
    p.add_argument('--collection', default=os.getenv('CHROMA_COLLECTION_NAME', 'api_functions'), help='Chroma のコレクション名')
    p.add_argument('--k', type=int, default=100, help='Chroma と照合する最大件数（--check-chroma / --query 用）')
    # Cypher 実行系
    p.add_argument('--cypher', help='実行するCypher（1文）')
    p.add_argument('--file', dest='cypher_file', help='実行するCypherファイル（; 区切りで複数可）')
    p.add_argument('--param', action='append', default=[], help='クエリパラメータ。形式: key=value （複数指定可）')
    p.add_argument('--write', action='store_true', help='更新系クエリを許可')
    p.add_argument('--commit', action='store_true', help='更新系クエリをコミット（未指定ならロールバック）')
    p.add_argument('--explain', action='store_true', help='クエリを実行せず EXPLAIN 実行')
    # 便利機能
    p.add_argument('--show-id', dest='show_id', help='elementId を指定してノード詳細を表示')
    p.add_argument('--neighbors', dest='neighbors_id', help='elementId を指定して隣接ノードとリレーションを表示')
    p.add_argument('--limit', type=int, default=25, help='neighbors 表示の上限')
    return p.parse_args()



def query_alignment(driver, chroma_dir: str, collection: str, query: str, k: int = 10) -> None:
    """
    Chromaでクエリ検索を行い、上位候補についてChroma側のmetadataと
    Neo4j側のノード情報を並べて表示する。
    """
    if Chroma is None:
        raise ImportError('langchain_community.chroma モジュールが見つかりません。')
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise EnvironmentError('OPENAI_API_KEY が設定されていません。')

    emb = OpenAIEmbeddings(api_key=api_key)
    vs = Chroma(collection_name=collection, embedding_function=emb, persist_directory=chroma_dir)

    try:
        results = vs.similarity_search_with_score(query, k=k)
    except Exception as e:
        raise RuntimeError(f'Chroma 検索に失敗しました: {e}')

    print(f"=== Chroma top-{len(results)} for query: {query} ===")
    for idx, (doc, score) in enumerate(results, start=1):
        meta = getattr(doc, 'metadata', {}) or {}
        api_name = meta.get('api_name') or meta.get('name')
        nid = meta.get('neo4j_node_id')
        print(f"--- candidate:{idx} ---")
        print(f"score= {score}")
        print(f"metadata.api_name= {api_name}")
        print(f"metadata.neo4j_node_id= {nid}")

        if not nid:
            print("  -> この候補は neo4j_node_id を持っていません")
            continue

        # Neo4j 側の情報を取得
        q = "MATCH (n) WHERE elementId(n) = $id RETURN elementId(n) AS id, n.name AS name, n.description AS description LIMIT 1"
        with driver.session(database=DB_NAME) as session:
            res = session.run(q, id=str(nid))
            rec = res.single()
            if not rec:
                print("  -> Neo4j に該当ノードが見つかりませんでした")
            else:
                nname = rec.get('name')
                ndesc = rec.get('description')
                print(f"  neo4j.name= {nname}")
                if ndesc:
                    print("  neo4j.description=", (ndesc or '').strip()[:400])
                # 簡易一致判定
                if api_name and nname and str(api_name).strip() == str(nname).strip():
                    print("  -> api_name と Neo4j.name は一致します")
                else:
                    print("  -> api_name と Neo4j.name は一致しません (要確認)")


def _is_mutating_cypher(cypher: str) -> bool:
    pattern = r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|CREATE\s+CONSTRAINT|CREATE\s+INDEX)\b"
    return re.search(pattern, cypher, flags=re.IGNORECASE) is not None


def _split_statements(text: str) -> List[str]:
    parts = [p.strip() for p in text.split(';')]
    return [p for p in parts if p]


def _parse_params(param_list: List[str]) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    for item in param_list:
        if '=' not in item:
            continue
        key, raw = item.split('=', 1)
        key = key.strip()
        raw = raw.strip()
        # 型推論: int/float/bool/json/str
        val: Any
        if raw.lower() in ('true', 'false'):
            val = raw.lower() == 'true'
        else:
            try:
                if '.' in raw:
                    val = float(raw)
                else:
                    val = int(raw)
            except ValueError:
                try:
                    val = json.loads(raw)
                except Exception:
                    val = raw.strip('"').strip("'")
        params[key] = val
    return params


def show_node_by_id(driver, element_id: str):
    query = "MATCH (n) WHERE elementId(n) = $id RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props"
    with driver.session(database=DB_NAME) as session:
        res = session.run(query, id=str(element_id))
        rec = res.single()
        if not rec:
            print('該当ノードが見つかりませんでした')
        else:
            print(json.dumps(rec.data(), ensure_ascii=False, indent=2))


def show_neighbors(driver, element_id: str, limit: int = 25):
    query = (
        "MATCH (n)-[r]-(m) WHERE elementId(n) = $id "
        "RETURN type(r) AS rel, elementId(m) AS id, labels(m) AS labels, properties(m) AS props "
        "LIMIT $limit"
    )
    with driver.session(database=DB_NAME) as session:
        res = session.run(query, id=str(element_id), limit=limit)
        data = [r.data() for r in res]
        if not data:
            print('隣接ノード/リレーションは見つかりませんでした')
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))


def run_cypher(driver, statements: List[str], params: Dict[str, Any], allow_write: bool, do_commit: bool, explain: bool):
    if not statements:
        print('実行するCypherがありません (--cypher か --file を指定)')
        return
    # 書き込み検出
    has_mutation = any(_is_mutating_cypher(s) for s in statements)
    if has_mutation and not allow_write:
        print('更新系クエリが含まれています。--write を指定してください（デフォルトは安全のため禁止）')
        return

    with driver.session(database=DB_NAME) as session:
        if has_mutation:
            # トランザクション制御
            tx = session.begin_transaction()
            try:
                for s in statements:
                    c = f"EXPLAIN {s}" if explain else s
                    result = tx.run(c, **params)
                    try:
                        data = [r.data() for r in result]
                        if data:
                            print(json.dumps(data, ensure_ascii=False, indent=2))
                    except Exception:
                        pass
                if do_commit and not explain:
                    tx.commit()
                    print('トランザクションをコミットしました。')
                else:
                    tx.rollback()
                    if explain:
                        print('EXPLAIN のため変更はありません。')
                    else:
                        print('ドライランのためロールバックしました。--commit を指定すると反映されます。')
            except Exception:
                tx.rollback()
                raise
        else:
            # 読み取り系はそのまま
            for s in statements:
                c = f"EXPLAIN {s}" if explain else s
                result = session.run(c, **params)
                data = [r.data() for r in result]
                if data:
                    print(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    args = parse_args()

    if GraphDatabase is None:
        print('ERROR: neo4j パッケージがインストールされていません。pip install neo4j を実行してください')
        return

    try:
        driver = get_neo4j_driver()
    except Exception as e:
        logger.exception('Neo4j ドライバ初期化に失敗')
        print(f'ERROR: {e}')
        return

    try:
        if args.count:
            cnt = count_nodes(driver, label=args.label)
            print(f"Label={args.label} のノード数: {cnt}")

        if args.sample and args.sample > 0:
            samples = sample_nodes(driver, label=args.label, limit=args.sample)
            print(f"=== sample ({len(samples)}) ===")
            for i, s in enumerate(samples, 1):
                print(f"[{i}] id={s.get('id')} name={s.get('name')}")
                desc = s.get('description')
                if desc:
                    print('  description:', (desc or '').strip()[:400])

        if args.list_labels:
            labs = list_labels(driver)
            print('=== labels ===')
            for l in labs:
                print(f"{l.get('label')}: {l.get('cnt')}")

        if args.query:
            try:
                query_alignment(driver, args.chroma_dir, args.collection, args.query, k=args.k)
            except Exception as e:
                logger.exception('クエリ照合中にエラー')
                print(f'ERROR (query): {e}')

        if args.check_chroma:
            print('Chroma と Neo4j の突合せを開始します...')
            try:
                res = check_chroma_mapping(driver, args.chroma_dir, args.collection, k_limit=args.k)
                print(f"Chroma metadata 中の neo4j_node_id 合計: {res['total']}")
                print(f"チェック済み: {res['checked']}, 見つからない件数: {len(res['missing'])}")
                if res['missing']:
                    print('=== missing ids (一部) ===')
                    for mid in res['missing'][:50]:
                        print(mid)
            except Exception as e:
                logger.exception('Chroma 突合せ中にエラー')
                print(f'ERROR (chroma check): {e}')

        # Cypher 実行
        if args.cypher or args.cypher_file or args.show_id or args.neighbors_id:
            try:
                if args.show_id:
                    show_node_by_id(driver, args.show_id)
                if args.neighbors_id:
                    show_neighbors(driver, args.neighbors_id, limit=args.limit)
                # クエリ実行
                stmts: List[str] = []
                if args.cypher:
                    stmts.extend(_split_statements(args.cypher))
                if args.cypher_file and os.path.exists(args.cypher_file):
                    with open(args.cypher_file, 'r', encoding='utf-8') as f:
                        stmts.extend(_split_statements(f.read()))
                if stmts:
                    params = _parse_params(args.param)
                    run_cypher(driver, stmts, params, allow_write=args.write, do_commit=args.commit, explain=args.explain)
            except Exception as e:
                logger.exception('Cypher実行中にエラー')
                print(f'ERROR (cypher): {e}')

    finally:
        try:
            driver.close()
        except Exception:
            pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()


