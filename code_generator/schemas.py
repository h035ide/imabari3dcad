from pydantic import BaseModel, Field
from typing import List

class FinalAnswer(BaseModel):
    """
    エージェントの最終回答を構造化するためのPydanticモデル。
    """
    explanation: str = Field(description="生成されたコードに関する詳細な説明。")
    imports: List[str] = Field(description="コードの実行に必要なimport文のリスト。")
    code_body: str = Field(description="生成されたPythonコードの本体（関数やクラス定義など）。")

    def to_string(self) -> str:
        """
        整形された文字列として最終回答を出力します。
        """
        import_str = "\n".join(self.imports)
        full_code = f"{import_str}\n\n{self.code_body}"

        return (
            f"【説明】\n{self.explanation}\n\n"
            f"【生成されたコード】\n"
            f"```python\n"
            f"{full_code}\n"
            f"```"
        )
