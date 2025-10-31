import os
import json # 取得したデータ表示のためにjsonライブラリをインポート
from typing import List, Dict, Any

# Janome: 日本語の形態素解析に使用
from janome.tokenizer import Tokenizer

# LangChain: LLMとの連携やプロンプト管理に使用
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_neo4j import Neo4jGraph

import config

### ----------------------------------------------------------------------
### Cypherクエリ生成ロジック
### ----------------------------------------------------------------------

# 形態素解析器の初期化
tokenizer = Tokenizer()

# グラフ内で検索対象とするノードのエイリアスとプロパティ名のマッピング
SEARCH_TARGETS: Dict[str, List[str]] = {
    "se": ["name"],              # ScriptExampleノードのnameプロパティ
    "mc": ["code"],              # MethodCallノードのcodeプロパティ
    "m": ["name", "description"], # Methodノードのnameとdescriptionプロパティ
    "o": ["name"]                # Objectノードのnameプロパティ
}

# 類義語や関連語のグループを定義。このリストは必要に応じて拡張できます。
# 例: "直角"というキーワードで検索した場合、"コーナー"も検索対象に含める
SYNONYM_GROUPS: List[set] = [
    {"直角", "コーナー"},
    {"作成", "生成", "作る"},
    {"取得", "得る", "読み込む"},
]

def _extract_keywords(question: str) -> List[str]:
    """
    質問文からキーワード（主に名詞）を抽出する。
    Args:
        question (str): ユーザーからの質問文。
    Returns:
        List[str]: 抽出されたキーワードのリスト。
    """
    # "Python" や "スクリプト" といった、検索ノイズになりやすい一般的な単語を除外
    stop_words = {"python", "スクリプト", "コード", "方法", "関数", "機能", "処理", "について", "サンプル"}
    
    keywords = [
        token.surface for token in tokenizer.tokenize(question)
        if token.part_of_speech.startswith('名詞') and token.surface.lower() not in stop_words
    ]
    # 重複を除去して返す
    return list(dict.fromkeys(keywords))

def _expand_keywords(keywords: List[str]) -> List[List[str]]:
    """
    キーワードリストを、定義された類義語グループに基づいて拡張する。
    例: ["直角", "柱"] -> [["直角", "コーナー"], ["柱"]]
    Args:
        keywords (List[str]): 抽出されたキーワードのリスト。
    Returns:
        List[List[str]]: 類義語でグループ化されたキーワードのリスト。
    """
    expanded_groups = []
    processed_keywords = set()

    for keyword in keywords:
        if keyword in processed_keywords:
            continue

        found_in_group = False
        for group in SYNONYM_GROUPS:
            if keyword in group:
                expanded_groups.append(list(group))
                processed_keywords.update(group)
                found_in_group = True
                break
        
        if not found_in_group:
            expanded_groups.append([keyword])
            processed_keywords.add(keyword)
            
    return expanded_groups

def generate_cypher_from_question(question: str) -> str:
    """
    ユーザーの質問文からキーワードを抽出し、動的にCypherクエリを生成する。
    `0905.md`のクエリ構造をテンプレートとして使用する。
    Args:
        question (str): ユーザーからの質問文。
    Returns:
        str: 生成されたCypherクエリ文字列。キーワードが見つからない場合は空文字を返す。
    """
    keywords = _extract_keywords(question)
    if not keywords:
        print("⚠️ 質問文から検索キーワードを抽出できませんでした。")
        return ""

    keyword_groups = _expand_keywords(keywords)

    # WHERE句の各AND条件を作成
    where_conditions = []
    for group in keyword_groups:
        # 類義語グループ内はORで連結 (例: 直角 OR コーナー)
        group_or_conditions = []
        for keyword in group:
            # 各プロパティに対するCONTAINSチェックもORで連結
            property_or_conditions = []
            for alias, props in SEARCH_TARGETS.items():
                for prop in props:
                    # toLower()で大文字小文字を区別せずに検索
                    condition = f"toLower({alias}.{prop}) CONTAINS toLower('{keyword}')"
                    property_or_conditions.append(condition)
            group_or_conditions.append(f"({' OR '.join(property_or_conditions)})")
        
        where_conditions.append(f"({' OR '.join(group_or_conditions)})")
    
    # 最終的なWHERE句をANDで連結
    where_clause = " AND\n  ".join(where_conditions)

    # 0905.md を基にしたCypherクエリテンプレート
    cypher_template = f"""
    MATCH (se:ScriptExample)-[:CONTAINS]->(mc:MethodCall)-[:CALLS]->(m:Method)
    OPTIONAL MATCH (m)-[:BELONGS_TO]->(o:Object)
    WHERE
    {where_clause}
    WITH se, mc, m, o
    ORDER BY mc.order ASC
    WITH se, collect(distinct m) AS methods, collect({{order: mc.order, code: mc.code, methodId: m.id, methodName: m.name, objectName: o.name}}) AS calls
    UNWIND methods AS m1
    OPTIONAL MATCH (m1)-[:HAS_PARAMETER]->(p:Parameter)
    OPTIONAL MATCH (p)-[:HAS_TYPE]->(pt:DataType)
    WITH se, calls, collect(distinct {{methodId: m1.id, methodName: m1.name, parameterId: p.id, parameterName: p.name, parameterDescription: p.description, parameterOrder: p.order, parameterType: pt.name}}) AS parameters, methods
    UNWIND methods AS m2
    OPTIONAL MATCH (m2)-[:HAS_RETURNS]->(rv:ReturnValue)-[:HAS_TYPE]->(rvt:DataType)
    WITH se, calls, parameters, collect(distinct {{methodId: m2.id, returnValueId: rv.id, returnDescription: rv.description, returnType: rvt.name}}) AS returns
    RETURN se.id AS scriptExampleId, se.name AS scriptExampleName, calls, parameters, returns
    ORDER BY scriptExampleName
    """
    return cypher_template

### ----------------------------------------------------------------------
### Pythonスクリプト生成ロジック
### ----------------------------------------------------------------------

# Pythonスクリプトを生成するためのプロンプトテンプレート
SCRIPT_GENERATION_PROMPT = """
あなたはCADソフトウェアのベテラン開発者です。
以下のコンテキスト情報とユーザーの質問を基に、質問の要件を満たす完全なPythonスクリプトを作成してください。

### コンテキスト
{context}

### ユーザーの質問
{question}

### 要件
- スクリプトはそのまま実行可能な形式にしてください。
- 必要なライブラリのインポート文もすべて含めてください。
- 変数や処理には、処理内容が理解しやすくなるように適切なコメントを追加してください。
- 幾何学的に存在可能なモデルを作成するスクリプトにしてください。

### 生成するPythonスクリプト
```python
"""

### ----------------------------------------------------------------------
### メイン処理
### ----------------------------------------------------------------------

def main():
    """
    メインの実行関数
    """
    # Neo4jグラフへの接続
    try:
        graph = Neo4jGraph(
            url=config.NEO4J_URI,
            username=config.NEO4J_USER,
            password=config.NEO4J_PASSWORD,
            database=getattr(config, "NEO4J_DATABASE", "neo4j"),
        )
        # 接続確認
        graph.query("RETURN 1")
    except Exception as e:
        print(f"❌ Neo4jへの接続に失敗しました: {e}")
        print("   config.py の接続情報が正しいか、Neo4jサーバーが起動しているか確認してください。")
        return

    # ユーザーからの質問（この部分をコマンドライン引数やWeb APIからの入力に置き換えることができます）
    question = "柱とブラケットを使って直角なコーナーを作成するサンプルコードが欲しい"
    print(f"❓ 質問: {question}")

    # 1. 質問文からプログラムでCypherクエリを生成
    print("\n⚙️  質問内容を解析し、Cypherクエリを生成中...")
    cypher_query = generate_cypher_from_question(question)
    
    if not cypher_query:
        print("プログラムの生成を中止します。")
        return

    print("✅ Cypherクエリが生成されました。")
    ### ▼▼▼ 変更点 ▼▼▼
    # 生成されたCypherクエリをコンソールに出力する
    print("\n--- 生成されたCypherクエリ ---")
    print(cypher_query)
    print("------------------------------")
    ### ▲▲▲ 変更ここまで ▲▲▲

    # 2. Neo4jでクエリを実行し、コンテキスト（関連情報）を取得
    print("\n🔍 グラフデータベースから関連情報を検索中...")
    try:
        context = graph.query(cypher_query)
        if not context:
            print("⚠️ 関連情報が見つかりませんでした。キーワードを変えて試してください。")
            return
        print(f"✅ {len(context)}件の関連情報を取得しました。")

        ### ▼▼▼ 変更点 ▼▼▼
        # 取得したコンテキスト情報を整形して表示する
        print("\n📄 取得したコンテキスト情報:")
        print(json.dumps(context, indent=2, ensure_ascii=False))
        ### ▲▲▲ 変更ここまで ▲▲▲

    except Exception as e:
        print(f"❌ Neo4jでのクエリ実行中にエラーが発生しました: {e}")
        return


    # 3. コンテキストと質問を基にLLMでPythonスクリプトを生成
    print("\n🤖 LLMがPythonスクリプトを生成中...")
    try:
        llm = ChatOpenAI(api_key=config.OPENAI_API_KEY, model="gpt-5-mini", temperature=1)
        
        prompt = ChatPromptTemplate.from_template(SCRIPT_GENERATION_PROMPT)
        
        chain = prompt | llm
        
        response = chain.invoke({
            "context": context,
            "question": question
        })
        generated_script = response.content

        # 生成されたスクリプトから ```python と ``` を除去して整形
        if generated_script.startswith("```python"):
            generated_script = generated_script[len("```python"):].lstrip()
        if generated_script.endswith("```"):
            generated_script = generated_script[:-len("```")].rstrip()
            
        print("\n🎉 Pythonスクリプトが生成されました！")
        print("----------------------------------------")
        print(generated_script)
        print("----------------------------------------")

    except Exception as e:
        print(f"❌ LLMによるスクリプト生成中にエラーが発生しました: {e}")
        print("   OpenAIのAPIキーが正しいか確認してください。")


if __name__ == "__main__":
    main()