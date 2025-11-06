"""
データ取り込みオーケストレーター

API仕様書とスクリプト例の解析を統合管理し、グラフデータベースへの投入を制御します。
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

from ..core.logger import get_logger
from ..core.exceptions import DataProcessingError
from ..utils.file_utils import read_script_files
from .api_parser import APISpecParser
from .script_analyzer import ScriptAnalyzer
from .llm_extractor import LLMExtractor

logger = get_logger(__name__)


class IngestionOrchestrator:
    """データ取り込みオーケストレーター"""

    def __init__(
        self, openai_api_key: str, model_name: str = "gpt-4", temperature: float = 0
    ):
        """
        初期化

        Args:
            openai_api_key: OpenAI APIキー
            model_name: 使用するLLMモデル名
            temperature: LLM生成温度
        """
        self.llm_extractor = LLMExtractor(openai_api_key, model_name, temperature)
        self.api_parser = APISpecParser(self.llm_extractor)
        self.script_analyzer = ScriptAnalyzer()

    def run_ingestion(
        self, config: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        データ取り込み処理を実行する

        Args:
            config: 設定辞書

        Returns:
            (統合されたトリプルのリスト, 統合されたノードプロパティ辞書)

        Raises:
            DataProcessingError: 取り込み処理エラー時
        """
        start_time = time.time()
        errors = []

        try:
            logger.info("=== データ取り込み処理開始 ===")

            # API仕様書の解析
            spec_triples, spec_node_props = self._process_api_specs(config, errors)

            # スクリプト例の解析
            script_triples, script_node_props = self._process_scripts(config, errors)

            # データの統合
            all_triples = spec_triples + script_triples
            all_node_props = {**spec_node_props, **script_node_props}

            processing_time = time.time() - start_time

            logger.info("=== データ取り込み処理完了 ===")
            logger.info("処理時間: %.2f秒", processing_time)
            logger.info("総トリプル数: %d", len(all_triples))
            logger.info("総ノード数: %d", len(all_node_props))

            if errors:
                logger.warning("エラー件数: %d", len(errors))
                for error in errors:
                    logger.warning("  - %s", error)

            return all_triples, all_node_props

        except Exception as e:
            raise DataProcessingError("データ取り込み処理に失敗しました", str(e))

    def _process_api_specs(
        self, config: Dict[str, Any], errors: List[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        API仕様書を処理する

        Args:
            config: 設定辞書
            errors: エラーリスト（出力先）

        Returns:
            (API仕様書由来のトリプル, ノードプロパティ)
        """
        logger.info("📄 API仕様書の解析を開始")

        try:
            # API仕様書ファイルパスを取得
            api_files = self._get_api_file_paths(config)
            if not api_files:
                logger.warning("API仕様書ファイルが設定されていません")
                return [], {}

            # API仕様書を解析
            spec_triples, spec_node_props = self.api_parser.parse_api_specs(api_files)

            # データ型の説明を取得して統合
            api_arg_candidates = self._get_api_arg_candidates(config)
            type_descriptions = self.api_parser.parse_datatype_descriptions(
                api_arg_candidates
            )

            # データ型の説明をノードプロパティに追加
            self._add_datatype_descriptions(spec_node_props, type_descriptions)

            logger.info(f"✅ API仕様書解析完了: トリプル={len(spec_triples)}件")
            return spec_triples, spec_node_props

        except Exception as e:
            error_msg = f"API仕様書解析エラー: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return [], {}

    def _process_scripts(
        self, config: Dict[str, Any], errors: List[str]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        スクリプト例を処理する

        Args:
            config: 設定辞書
            errors: エラーリスト（出力先）

        Returns:
            (スクリプト由来のトリプル, ノードプロパティ)
        """
        logger.info("🐍 スクリプト例の解析を開始")

        try:
            # データディレクトリを取得
            data_dir = Path(config.get("paths", {}).get("data_dir", "data"))

            # スクリプトファイルを読み込み
            script_files = read_script_files(data_dir)
            if not script_files:
                logger.warning("スクリプトファイルが見つかりません")
                return [], {}

            # スクリプトを解析
            all_script_triples = []
            all_script_node_props = {}

            for script_path, script_text in script_files:
                try:
                    triples, node_props = self.script_analyzer.analyze_script(
                        script_path, script_text
                    )
                    all_script_triples.extend(triples)
                    all_script_node_props.update(node_props)
                except Exception as e:
                    error_msg = f"スクリプト解析エラー ({script_path}): {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            logger.info(f"✅ スクリプト解析完了: トリプル={len(all_script_triples)}件")
            return all_script_triples, all_script_node_props

        except Exception as e:
            error_msg = f"スクリプト処理エラー: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return [], {}

    def _get_api_file_paths(self, config: Dict[str, Any]) -> List[Path]:
        """設定からAPI仕様書ファイルパスを取得する"""
        paths_config = config.get("paths", {})
        api_txt_paths = paths_config.get("api_txt", [])

        # 設定ファイルに明示されたパスのみを使用
        api_files = []
        for path_str in api_txt_paths:
            api_files.append(Path(path_str))

        return api_files

    def _get_api_arg_candidates(self, config: Dict[str, Any]) -> List[Path]:
        """設定からapi_arg.txtの候補パスを取得する"""
        paths_config = config.get("paths", {})
        api_arg_paths = paths_config.get("api_arg_txt", [])

        candidates = []
        for path_str in api_arg_paths:
            candidates.append(Path(path_str))

        return candidates

    def _add_datatype_descriptions(
        self, node_props: Dict[str, Dict[str, Any]], type_descriptions: Dict[str, str]
    ) -> None:
        """
        データ型ノードに説明を追加する

        Args:
            node_props: ノードプロパティ辞書（更新対象）
            type_descriptions: データ型説明辞書
        """
        for node_id, node_data in node_props.items():
            if (
                node_data.get("type") == "DataType"
                and node_data.get("properties", {}).get("name") in type_descriptions
            ):

                type_name = node_data["properties"]["name"]
                node_data["properties"]["description"] = type_descriptions[type_name]
