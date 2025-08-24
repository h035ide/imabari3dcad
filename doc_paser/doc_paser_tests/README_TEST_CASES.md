# テストケース自動生成システム

このディレクトリには、包括的検証レポートから自動生成されたテストケースが含まれています。

## 📁 ディレクトリ構成

```
doc_paser_tests/
├── code_snippets/           # テスト用コードスニペット
│   ├── {関数名}_positive.py # 正しい引数数のテスト
│   └── {関数名}_negative.py # 間違った引数数のテスト
├── golden_snippets/         # 期待される出力テンプレート
│   └── {関数名}_golden.py   # 期待されるコード形式
├── verification_reports/     # 検証レポート
├── generate_test_cases.py   # テストケース自動生成スクリプト
├── batch_test_runner.py     # バッチテスト実行スクリプト
└── validate_code_snippet.py # 個別テスト実行スクリプト
```

## 🚀 使用方法

### 1. テストケースの自動生成

検証レポートからテストケースを生成する場合：

```bash
python generate_test_cases.py
```

これにより、以下のファイルが生成されます：
- **60個のテストファイル** (30個の関数 × 2種類)
- **30個のgolden snippetファイル**

### 2. 個別テストの実行

特定のテストケースを実行する場合：

```bash
python validate_code_snippet.py code_snippets/CreatePlate_positive.py
python validate_code_snippet.py code_snippets/CreatePlate_negative.py
```

### 3. バッチテストの実行

すべてのテストケースを一括で実行する場合：

```bash
python batch_test_runner.py
```

## 📊 テストケースの種類

### Positive Test Cases (`*_positive.py`)
- **目的**: 正しい引数数のコードが検証を通過することを確認
- **内容**: 関数の仕様に従った正しい引数数と型
- **期待結果**: 検証成功（✅ PASSED）

### Negative Test Cases (`*_negative.py`)
- **目的**: 間違った引数数のコードが適切に検証されることを確認
- **内容**: 最後の引数を削除した不完全なコード
- **期待結果**: 検証失敗を正しく検出（❌ FAILED）

### Golden Snippets (`*_golden.py`)
- **目的**: コード生成の結果を検証するためのテンプレート
- **内容**: 期待される出力形式（パラメータ名のみ）
- **用途**: 生成されたコードとの比較

## 🔧 生成された関数一覧

以下の30個の関数のテストケースが生成されています：

### 基本操作関数
- `BlankElement` - 要素の表示状態設定
- `CreateSolid` - 空のソリッド要素作成
- `CreateVariable` - 変数要素作成

### スケッチ作成関数
- `CreateSketchPlane` - スケッチ平面作成
- `CreateSketchLayer` - スケッチレイヤー作成
- `CreateSketchLine` - スケッチ直線作成
- `CreateSketchCircle` - スケッチ円作成
- `CreateSketchArc` - スケッチ円弧作成
- `CreateSketchArc3Pts` - 3点指定円弧作成
- `CreateSketchEllipse` - スケッチ楕円作成
- `CreateSketchNURBSCurve` - NURBS曲線作成

### ソリッド作成関数
- `CreatePlate` - プレートソリッド作成
- `CreateProfile` - 条材ソリッド作成
- `CreateBracket` - ブラケットソリッド作成
- `CreateLinearSweep` - 押し出し形状作成
- `CreateLinearSweepSheet` - シート押し出し作成
- `CreateOffsetSheet` - オフセットシート作成
- `CreateOtherSolid` - 別ソリッド形状付加
- `CreateThicken` - 厚み付け形状作成

### パラメータオブジェクト作成関数
- `CreateLinearSweepParam` - 押し出しパラメータ作成
- `CreateProfileParam` - 条材パラメータ作成
- `CreateBracketParam` - ブラケットパラメータ作成

### ボディ操作関数
- `BodyDivideByElements` - 要素によるボディ分割
- `BodySeparateBySubSolids` - ソリッドによるボディ分割

### ファイル操作関数
- `CreateElementsFromFile` - ファイルからの要素作成

### 変形・コピー関数
- `TranslationCopy` - 移動コピー
- `MirrorCopy` - ミラーコピー
- `ReverseSheet` - シート向き反転

### 属性設定関数
- `SetElementColor` - 要素色設定
- `SheetAlignNormal` - シート法線方向揃え

## 🧪 テスト実行の前提条件

テストを実行するには、以下の環境が必要です：

1. **Neo4jデータベース接続**
   - `.env`ファイルに接続情報を設定
   - データベースに適切なスキーマが存在

2. **必要なPythonパッケージ**
   - `neo4j`
   - `python-dotenv`

3. **検証スクリプト**
   - `validate_code_snippet.py`が利用可能

## 📈 テスト結果の解釈

### 成功パターン
- **Positive Test**: ✅ PASSED - 正しい引数数が検証される
- **Negative Test**: ✅ PASSED - 間違った引数数が正しく検出される

### 失敗パターン
- **Positive Test**: ❌ FAILED - 正しい引数数が検証されない
- **Negative Test**: ❌ FAILED - 間違った引数数が検出されない

## 🔄 カスタマイズ

### 新しい関数の追加
1. 検証レポートに新しい関数の情報を追加
2. `generate_test_cases.py`を再実行
3. 必要に応じてテストケースを手動調整

### テストケースの修正
生成されたテストケースは自動生成のため、実際の使用例に合わせて調整が必要な場合があります。

## 📝 注意事項

1. **自動生成**: テストケースは検証レポートから自動生成されるため、実際の使用例とは異なる場合があります
2. **データベース依存**: テスト実行にはNeo4jデータベースへの接続が必要です
3. **環境設定**: `.env`ファイルの設定が正しく行われていることを確認してください

## 🆘 トラブルシューティング

### よくある問題

1. **Neo4j接続エラー**
   - `.env`ファイルの設定を確認
   - データベースが起動していることを確認

2. **テストケースが見つからない**
   - `generate_test_cases.py`を実行してテストケースを生成

3. **検証スクリプトエラー**
   - `validate_code_snippet.py`の依存関係を確認

### サポート
問題が発生した場合は、以下を確認してください：
- エラーメッセージの詳細
- 環境設定の状態
- データベースの接続状況
