# テストケース検証レポート（詳細版）

**日時**: 2025-08-24 17:19:27
**データベース**: docparser
**生成元**: test_rag_retrieval.py (Neo4jデータのみ使用、詳細分析機能付き)
**検証基準**: Neo4jデータベースの関数仕様

## 📊 全体統計

- **総検証数**: 60
- **成功**: 55 (91.7%)
- **失敗**: 5 (8.3%)

## 🔍 テストタイプ別統計

- **TEST**: 55/60 (91.7%)

## ❌ 失敗したテストの詳細分析

以下のテストケースで詳細な差異が検出されました。

### TEST テストの失敗 (5件)

#### BlankElement_negative.py

**結果**: 引数数不一致を正しく検出: 2/2

**詳細分析**:

- **関数名**: BlankElement
- **関数の説明**: 指定要素の表示状態を設定する。返り値はなし。
- **生成されたコードの引数数**: 0
- **データベースの期待パラメータ数**: 2

**データベースの詳細仕様**:

 0. Element              (要素             ) - 表示状態を指定する要素
 1. bBlank               (bool           ) - True の時は非表示にする。False の時は表示する。

**生成されたコード**:

```python
# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.BlankElement(
    "extra_value",           # Extra argument that should cause failure
    "another_extra_value"    # Another extra argument
)
```

**判断のポイント**:

- 生成されたコードに 2個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### CreateBracket_negative.py

**結果**: 引数数不一致を正しく検出: 2/2

**詳細分析**:

- **関数名**: CreateBracket
- **関数の説明**: ブラケットソリッド要素を作成する。返り値は作成したソリッド要素のID。
- **生成されたコードの引数数**: 0
- **データベースの期待パラメータ数**: 2

**データベースの詳細仕様**:

 0. ParamObj             (ブラケット要素のパラメータオブジェクト) - ブラケットパラメータオブジェクト
 1. bUpdate              (bool           ) - 更新フラグ（未実装、使用しない）

**生成されたコード**:

```python
# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateBracket(
    "extra_value",           # Extra argument that should cause failure
    "another_extra_value"    # Another extra argument
)
```

**判断のポイント**:

- 生成されたコードに 2個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### CreateLinearSweepSheet_negative.py

**結果**: 引数数不一致を正しく検出: 2/2

**詳細分析**:

- **関数名**: CreateLinearSweepSheet
- **関数の説明**: プロファイル要素を押し出してシート要素を作成する。返り値は作成されたシート要素の要素ID。
- **生成されたコードの引数数**: 0
- **データベースの期待パラメータ数**: 2

**データベースの詳細仕様**:

 0. ParamObj             (押し出しパラメータオブジェクト) - 押し出しパラメータオブジェクト
 1. bUpdate              (bool           ) - 更新フラグ（未実装、使用しない）

**生成されたコード**:

```python
# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateLinearSweepSheet(
    "extra_value",           # Extra argument that should cause failure
    "another_extra_value"    # Another extra argument
)
```

**判断のポイント**:

- 生成されたコードに 2個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### CreateProfile_negative.py

**結果**: 引数数不一致を正しく検出: 2/2

**詳細分析**:

- **関数名**: CreateProfile
- **関数の説明**: 条材ソリッド要素を作成する（取付線指定等）。返り値は作成した条材ソリッド要素のID配列（配列内に Web 要素やフランジ要素を含む）。
- **生成されたコードの引数数**: 0
- **データベースの期待パラメータ数**: 2

**データベースの詳細仕様**:

 0. ParamObj             (条材要素のパラメータオブジェクト) - 条材要素のパラメータオブジェクト
 1. bUpdate              (bool           ) - 更新フラグ（未実装、使用しない）

**生成されたコード**:

```python
# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateProfile(
    "extra_value",           # Extra argument that should cause failure
    "another_extra_value"    # Another extra argument
)
```

**判断のポイント**:

- 生成されたコードに 2個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### CreateSketchLayer_negative.py

**結果**: 引数数不一致を正しく検出: 2/2

**詳細分析**:

- **関数名**: CreateSketchLayer
- **関数の説明**: スケッチレイヤーを作成する。返り値は作成されたスケッチレイヤー要素の要素ID。
- **生成されたコードの引数数**: 0
- **データベースの期待パラメータ数**: 2

**データベースの詳細仕様**:

 0. SketchLayerName      (文字列            ) - 作成するスケッチレイヤー名称（空文字可）
 1. SketchPlane          (要素             ) - レイヤーを作成するスケッチ要素

**生成されたコード**:

```python
# test_type: negative
# This snippet should FAIL validation because it has the wrong number of arguments.
# The test itself should PASS if the validator correctly identifies this failure.

part.CreateSketchLayer(
    "extra_value",           # Extra argument that should cause failure
    "another_extra_value"    # Another extra argument
)
```

**判断のポイント**:

- 生成されたコードに 2個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

## ✅ 成功したテスト一覧

- **BlankElement_positive.py**: 引数数一致: 2/2
- **BodyDivideByElements_negative.py**: 引数数不一致を正しく検出: 2/7
- **BodyDivideByElements_positive.py**: 引数数一致: 7/7
- **BodySeparateBySubSolids_negative.py**: 引数数不一致を正しく検出: 2/6
- **BodySeparateBySubSolids_positive.py**: 引数数一致: 6/6
- **CreateBracketParam_negative.py**: 引数数不一致を正しく検出: 2/0
- **CreateBracketParam_positive.py**: 引数数一致: 0/0
- **CreateBracket_positive.py**: 引数数一致: 2/2
- **CreateElementsFromFile_negative.py**: 引数数不一致を正しく検出: 2/1
- **CreateElementsFromFile_positive.py**: 引数数一致: 1/1
- **CreateLinearSweepParam_negative.py**: 引数数不一致を正しく検出: 2/0
- **CreateLinearSweepParam_positive.py**: 引数数一致: 0/0
- **CreateLinearSweepSheet_positive.py**: 引数数一致: 2/2
- **CreateLinearSweep_negative.py**: 引数数不一致を正しく検出: 2/4
- **CreateLinearSweep_positive.py**: 引数数一致: 4/4
- **CreateOffsetSheet_negative.py**: 引数数不一致を正しく検出: 2/7
- **CreateOffsetSheet_positive.py**: 引数数一致: 7/7
- **CreateOtherSolid_negative.py**: 引数数不一致を正しく検出: 2/6
- **CreateOtherSolid_positive.py**: 引数数一致: 6/6
- **CreatePlate_negative.py**: 引数数不一致を正しく検出: 2/14
- **CreatePlate_positive.py**: 引数数一致: 14/14
- **CreateProfileParam_negative.py**: 引数数不一致を正しく検出: 2/0
- **CreateProfileParam_positive.py**: 引数数一致: 0/0
- **CreateProfile_positive.py**: 引数数一致: 2/2
- **CreateSketchArc3Pts_negative.py**: 引数数不一致を正しく検出: 2/7
- **CreateSketchArc3Pts_positive.py**: 引数数一致: 7/7
- **CreateSketchArc_negative.py**: 引数数不一致を正しく検出: 2/8
- **CreateSketchArc_positive.py**: 引数数一致: 8/8
- **CreateSketchCircle_negative.py**: 引数数不一致を正しく検出: 2/8
- **CreateSketchCircle_positive.py**: 引数数一致: 8/8
- **CreateSketchEllipse_negative.py**: 引数数不一致を正しく検出: 2/10
- **CreateSketchEllipse_positive.py**: 引数数一致: 10/10
- **CreateSketchLayer_positive.py**: 引数数一致: 2/2
- **CreateSketchLine_negative.py**: 引数数不一致を正しく検出: 2/6
- **CreateSketchLine_positive.py**: 引数数一致: 6/6
- **CreateSketchNURBSCurve_negative.py**: 引数数不一致を正しく検出: 2/11
- **CreateSketchNURBSCurve_positive.py**: 引数数一致: 11/11
- **CreateSketchPlane_negative.py**: 引数数不一致を正しく検出: 2/12
- **CreateSketchPlane_positive.py**: 引数数一致: 12/12
- **CreateSolid_negative.py**: 引数数不一致を正しく検出: 2/3
- **CreateSolid_positive.py**: 引数数一致: 3/3
- **CreateThicken_negative.py**: 引数数不一致を正しく検出: 2/10
- **CreateThicken_positive.py**: 引数数一致: 10/10
- **CreateVariable_negative.py**: 引数数不一致を正しく検出: 2/4
- **CreateVariable_positive.py**: 引数数一致: 4/4
- **MirrorCopy_negative.py**: 引数数不一致を正しく検出: 2/3
- **MirrorCopy_positive.py**: 引数数一致: 3/3
- **ReverseSheet_negative.py**: 引数数不一致を正しく検出: 2/1
- **ReverseSheet_positive.py**: 引数数一致: 1/1
- **SetElementColor_negative.py**: 引数数不一致を正しく検出: 2/5
- **SetElementColor_positive.py**: 引数数一致: 5/5
- **SheetAlignNormal_negative.py**: 引数数不一致を正しく検出: 2/4
- **SheetAlignNormal_positive.py**: 引数数一致: 4/4
- **TranslationCopy_negative.py**: 引数数不一致を正しく検出: 2/5
- **TranslationCopy_positive.py**: 引数数一致: 5/5

## 💡 改善のための推奨事項

❌ 一部のテストが失敗しました。以下の点を確認してください：

1. **失敗したテストケースの詳細分析を確認**
   - 上記の詳細分析セクションで各テストの失敗原因を確認
   - Neo4jデータベース仕様と生成されたコードの差異を検討

2. **生成スクリプトの改善**
   - 不足しているパラメータの追加
   - 余分なパラメータの削除
   - パラメータ順序の修正

3. **Neo4jデータベース仕様の確認**
   - 実際のAPIドキュメントとの照合
   - 使用例との比較
   - 必要に応じてデータベースの更新

4. **テストケースの品質向上**
   - 正しい引数数のテストケースの生成
   - エッジケースの考慮
   - 実際の使用パターンとの整合性確認

---
*このレポートは 2025-08-24 17:19:28 に自動生成されました。*
*Neo4jデータベースの仕様を基準として検証を行いました。*
