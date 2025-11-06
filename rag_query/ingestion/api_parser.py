"""
API仕様書解析モジュール

API仕様書ファイルの読み込みとLLMによる解析を統合管理します。
"""

from pathlib import Path
from typing import List, Dict, Any, Tuple

from ..core.logger import get_logger
from ..core.exceptions import DataProcessingError
from ..utils.file_utils import read_api_files, find_file_from_candidates
from .llm_extractor import LLMExtractor

logger = get_logger(__name__)


class APISpecParser:
    """API仕様書解析クラス"""
    
    def __init__(self, llm_extractor: LLMExtractor):
        """
        初期化
        
        Args:
            llm_extractor: LLM抽出処理インスタンス
        """
        self.llm_extractor = llm_extractor
    
    def parse_api_specs(self, api_file_paths: List[Path]) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        API仕様書ファイルを解析してグラフデータを生成する
        
        Args:
            api_file_paths: API仕様書ファイルパスのリスト
            
        Returns:
            (トリプルのリスト, ノードプロパティ辞書)
            
        Raises:
            DataProcessingError: 解析エラー時
        """
        logger.info("API仕様書の解析を開始")
        
        # API仕様書ファイルを読み込み
        api_files = read_api_files(api_file_paths)
        if not api_files:
            logger.warning("API仕様書ファイルが見つかりませんでした")
            return [], {}
        
        all_nodes = []
        all_relationships = []
        
        # 各ファイルをLLMで解析
        for file_name, content in api_files:
            try:
                logger.info(f"LLMでAPI仕様書を解析中: {file_name}")
                graph_data = self.llm_extractor.extract_graph_from_specs(content)
                
                nodes = graph_data.get("nodes", [])
                rels = graph_data.get("relationships", [])
                
                logger.info(f"解析完了: {file_name} - ノード={len(nodes)}件, リレーション={len(rels)}件")
                
                all_nodes.extend(nodes)
                all_relationships.extend(rels)
                
            except Exception as e:
                logger.error(f"API仕様書解析エラー: {file_name} - {e}")
                continue
        
        # データの統合とクリーニング
        merged_nodes, merged_relationships = self._merge_graph_data(all_nodes, all_relationships)
        
        # トリプル形式に変換
        triples, node_props = self._convert_to_triples(merged_nodes, merged_relationships)
        
        logger.info(f"API仕様書解析完了: ノード={len(merged_nodes)}件, リレーション={len(merged_relationships)}件")
        return triples, node_props
    
    def parse_datatype_descriptions(self, api_arg_candidates: List[Path]) -> Dict[str, str]:
        """
        api_arg.txtからデータ型の説明を抽出する
        
        Args:
            api_arg_candidates: api_arg.txtの候補パスリスト
            
        Returns:
            データ型名と説明のマッピング
            
        Raises:
            DataProcessingError: 解析エラー時
        """
        api_arg_file = find_file_from_candidates(api_arg_candidates)
        if not api_arg_file:
            logger.warning("api_arg.txtが見つかりませんでした")
            return {}
        
        try:
            content = api_arg_file.read_text(encoding="utf-8")
            logger.info("LLMでデータ型説明を抽出中")
            type_descriptions = self.llm_extractor.extract_datatype_descriptions(content)
            logger.info(f"データ型説明抽出完了: {len(type_descriptions)}件")
            return type_descriptions
        except Exception as e:
            raise DataProcessingError(f"データ型説明抽出エラー", str(e))
    
    def _merge_graph_data(self, nodes: List[Dict[str, Any]], 
                         relationships: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        重複するノードとリレーションシップをマージする
        
        Args:
            nodes: ノードデータのリスト
            relationships: リレーションシップデータのリスト
            
        Returns:
            (マージされたノード, マージされたリレーションシップ)
        """
        # 重複ノードをIDに基づいてマージ（後勝ち）
        merged_nodes_dict = {}
        for node in nodes:
            node_id = node.get("id")
            if node_id:
                if node_id in merged_nodes_dict:
                    # 既存のノードプロパティを更新
                    existing_props = merged_nodes_dict[node_id].setdefault("properties", {})
                    existing_props.update(node.get("properties", {}))
                else:
                    merged_nodes_dict[node_id] = node
        
        merged_nodes = list(merged_nodes_dict.values())
        
        # 重複リレーションシップを削除
        seen_rels = set()
        merged_relationships = []
        for rel in relationships:
            rel_tuple = (rel.get("source"), rel.get("target"), rel.get("type"))
            if (rel.get("source") and rel.get("target") and rel.get("type") and 
                rel_tuple not in seen_rels):
                merged_relationships.append(rel)
                seen_rels.add(rel_tuple)
        
        return merged_nodes, merged_relationships
    
    def _convert_to_triples(self, nodes: List[Dict[str, Any]], 
                           relationships: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        LLMの出力をトリプル形式に変換する
        
        Args:
            nodes: ノードデータのリスト
            relationships: リレーションシップデータのリスト
            
        Returns:
            (トリプルのリスト, ノードプロパティ辞書)
        """
        triples = []
        node_props = {}
        node_type_map = {}
        
        # ノード情報を格納
        for node in nodes:
            node_id = node["id"]
            node_type = node["type"]
            properties = node.get("properties", {})
            
            node_props[node_id] = {"type": node_type, "properties": properties}
            node_type_map[node_id] = node_type
        
        # リレーション情報からトリプルを生成
        for rel in relationships:
            source_id = rel["source"]
            target_id = rel["target"]
            
            # 存在しないノードIDはスキップ
            if source_id not in node_type_map or target_id not in node_type_map:
                logger.warning(f"存在しないノードIDのリレーションをスキップ: {source_id} -> {target_id}")
                continue
            
            triples.append({
                "source": source_id,
                "source_type": node_type_map[source_id],
                "label": rel["type"],
                "target": target_id,
                "target_type": node_type_map[target_id],
            })
        
        return triples, node_props
