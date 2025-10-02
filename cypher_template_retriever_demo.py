#!/usr/bin/env python3
"""
CypherTemplateRetriever デモンストレーション
既存のNeo4jデータ構造に適用したテンプレート駆動型クエリの実装例
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from llama_index.core.indices.property_graph import CypherTemplateRetriever
from neo4j_property_graph_store import Neo4jPropertyGraphStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from main_helper_0905 import Config

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FunctionSearchParams(BaseModel):
    """関数検索用のテンプレートパラメータ"""
    function_name: str = Field(
        description="検索する関数名（部分一致可）"
    )
    include_parameters: bool = Field(
        default=True,
        description="パラメータ情報を含めるかどうか"
    )
    limit: int = Field(
        default=5,
        description="返却する結果の最大数"
    )

class ParameterSearchParams(BaseModel):
    """パラメータ検索用のテンプレートパラメータ"""
    parameter_name: str = Field(
        description="検索するパラメータ名（部分一致可）"
    )
    parameter_type: Optional[str] = Field(
        default=None,
        description="パラメータの型（オプション）"
    )
    limit: int = Field(
        default=10,
        description="返却する結果の最大数"
    )

class TypeSearchParams(BaseModel):
    """型検索用のテンプレートパラメータ"""
    type_name: str = Field(
        description="検索する型名（部分一致可）"
    )
    limit: int = Field(
        default=10,
        description="返却する結果の最大数"
    )

def create_cypher_templates():
    """Cypherクエリテンプレートの定義"""
    
    # 関数検索テンプレート（シンプル版）
    function_search_template = """
    MATCH (f:Function)
    WHERE toLower(f.name) CONTAINS toLower($function_name)
    OPTIONAL MATCH (p:Parameter)
    WHERE toLower(p.parent_function) = toLower(f.name)
    WITH f, collect(p) AS params
    RETURN f.name AS name,
           f.description AS description,
           f.category AS category,
           f.implementation_status AS implementation_status,
           [q IN params WHERE q IS NOT NULL AND q.name IS NOT NULL |
            {name:q.name, description:q.description, type:q.type, required:coalesce(q.is_required,false)}] AS parameters,
           null AS return_value
    LIMIT $limit
    """
    
    # パラメータ検索テンプレート（シンプル版）
    parameter_search_template = """
    MATCH (p:Parameter)
    WHERE toLower(p.name) CONTAINS toLower($parameter_name)
    MATCH (f:Function {name: p.parent_function})
    RETURN p.name AS parameter_name,
           p.description AS parameter_description,
           p.type AS parameter_type,
           p.is_required AS is_required,
           f.name AS parent_function,
           f.description AS function_description
    LIMIT $limit
    """
    
    # 型検索テンプレート
    type_search_template = """
    MATCH (t:Type)
    WHERE toLower(t.name) CONTAINS toLower($type_name)
    OPTIONAL MATCH (p:Parameter {type: t.name})
    OPTIONAL MATCH (f:Function)-[:RETURNS]->(t)
    WITH t, collect(DISTINCT p) AS parameters, collect(DISTINCT f) AS functions
    RETURN t.name AS type_name,
           t.description AS type_description,
           [p IN parameters WHERE p IS NOT NULL |
            {name:p.name, parent_function:p.parent_function}] AS used_in_parameters,
           [f IN functions WHERE f IS NOT NULL |
            {name:f.name, description:f.description}] AS returned_by_functions
    LIMIT $limit
    """
    
    return {
        'function_search': function_search_template,
        'parameter_search': parameter_search_template,
        'type_search': type_search_template
    }

def create_property_graph_store(config: Config):
    """Neo4jPropertyGraphStoreの作成"""
    return Neo4jPropertyGraphStore(
        uri=config.neo4j_uri,
        user=config.neo4j_user,
        password=config.neo4j_password,
        database=config.neo4j_database
    )

def create_template_retrievers(config: Config):
    """テンプレートリトリーバーの作成"""
    property_graph_store = create_property_graph_store(config)
    templates = create_cypher_templates()
    
    retrievers = {}
    
    # 関数検索リトリーバー
    retrievers['function'] = CypherTemplateRetriever(
        property_graph_store,
        FunctionSearchParams,
        templates['function_search']
    )
    
    # パラメータ検索リトリーバー
    retrievers['parameter'] = CypherTemplateRetriever(
        property_graph_store,
        ParameterSearchParams,
        templates['parameter_search']
    )
    
    # 型検索リトリーバー
    retrievers['type'] = CypherTemplateRetriever(
        property_graph_store,
        TypeSearchParams,
        templates['type_search']
    )
    
    return retrievers

def test_template_retrievers():
    """テンプレートリトリーバーのテスト"""
    config = Config()
    
    try:
        # リトリーバーの作成
        retrievers = create_template_retrievers(config)
        logger.info("テンプレートリトリーバーの作成が完了しました")
        
        # 関数検索のテスト
        logger.info("=== 関数検索テスト ===")
        function_results = retrievers['function'].retrieve("CreateSketchLine")
        
        for result in function_results:
            logger.info(f"関数: {result.metadata.get('name', 'N/A')}")
            logger.info(f"説明: {result.metadata.get('description', 'N/A')}")
            logger.info(f"パラメータ数: {len(result.metadata.get('parameters', []))}")
            logger.info("---")
        
        # パラメータ検索のテスト
        logger.info("=== パラメータ検索テスト ===")
        parameter_results = retrievers['parameter'].retrieve("point")
        
        for result in parameter_results:
            logger.info(f"パラメータ: {result.metadata.get('parameter_name', 'N/A')}")
            logger.info(f"型: {result.metadata.get('parameter_type', 'N/A')}")
            logger.info(f"親関数: {result.metadata.get('parent_function', 'N/A')}")
            logger.info("---")
        
        # 型検索のテスト
        logger.info("=== 型検索テスト ===")
        type_results = retrievers['type'].retrieve("Point")
        
        for result in type_results:
            logger.info(f"型: {result.metadata.get('type_name', 'N/A')}")
            logger.info(f"説明: {result.metadata.get('type_description', 'N/A')}")
            logger.info("---")
        
        logger.info("すべてのテストが完了しました")
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_template_retrievers()
