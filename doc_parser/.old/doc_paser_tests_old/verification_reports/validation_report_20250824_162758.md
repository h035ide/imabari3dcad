# テストケース検証レポート（詳細版）

**日時**: 2025-08-24 16:27:58
**データベース**: docparser
**生成元**: test_rag_retrieval.py (Neo4jデータのみ使用、詳細分析機能付き)
**検証基準**: Neo4jデータベースの関数仕様

## 📊 全体統計

- **総検証数**: 60
- **成功**: 53 (88.3%)
- **失敗**: 7 (11.7%)

## 🔍 テストタイプ別統計

- **TEST**: 53/60 (88.3%)

## ❌ 失敗したテストの詳細分析

以下のテストケースで詳細な差異が検出されました。

### TEST テストの失敗 (7件)

#### BodyDivideByElements_positive.py

**結果**: 引数数一致: 6/7

**詳細分析**:

- **関数名**: BodyDivideByElements
- **関数の説明**: ボディを指定した要素で分割する。返り値は分割で作成されたボディ要素のID配列。
- **生成されたコードの引数数**: 6
- **データベースの期待パラメータ数**: 7

**データベースの詳細仕様**:

 0. pDriveFeatureName    (文字列            ) - 作成する分割フィーチャー要素名称（空文字可）
 1. pTargetBody          (要素             ) - 分割対象のボディ
 2. pDivideElements      (要素(配列)         ) - 分割をする要素（シートボディ、フェイス、平面要素）
 3. pAlignmentDirection  (方向             ) - 分割されたボディ要素の順番を整列させるのに使用する方向
 4. pWCS                 (要素             ) - 方向を定義する座標系（通常は指定しない）
 5. ReferMethod          (関連設定           ) - 要素の関連づけ方法の指定
 6. bUpdate              (bool           ) - 更新フラグ（未実装、使用しない）

**生成されたコード**:

```python
# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.BodyDivideByElements(
    "pDriveFeatureName",               # 作成する分割フィーチャー要素名称（空文字可）
    pTargetBody_element,               # 分割対象のボディ
    (1.0, 0.0, 0.0),               # 分割されたボディ要素の順番を整列させるのに使用する方向
    pWCS_element,               # 方向を定義する座標系（通常は指定しない）
    "GEOMETRIC",               # 要素の関連づけ方法の指定
    True                # 更新フラグ（未実装、使用しない）
)
```

**判断のポイント**:

- 生成されたコードに 1個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### BodySeparateBySubSolids_positive.py

**結果**: 引数数一致: 5/6

**詳細分析**:

- **関数名**: BodySeparateBySubSolids
- **関数の説明**: 指定したソリッドで削除することでボディを分割する（ボディの区分けコマンド）。返り値は分割で作成されたボディ要素のID配列。
- **生成されたコードの引数数**: 5
- **データベースの期待パラメータ数**: 6

**データベースの詳細仕様**:

 0. pSeparateFeatureName (文字列            ) - 作成する分割フィーチャー要素名称（空文字可）
 1. pTargetBody          (要素             ) - 分割対象のボディ
 2. pSubSolids           (要素(配列)         ) - 分割をするソリッド要素（配列）
 3. pAlignmentDirection  (方向             ) - 分割されたボディ要素の順番を整列させるのに使用する方向
 4. ReferMethod          (関連設定           ) - 要素の関連づけ方法の指定
 5. bUpdate              (bool           ) - 更新フラグ（未実装、使用しない）

**生成されたコード**:

```python
# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.BodySeparateBySubSolids(
    "pSeparateFeatureName",               # 作成する分割フィーチャー要素名称（空文字可）
    pTargetBody_element,               # 分割対象のボディ
    (1.0, 0.0, 0.0),               # 分割されたボディ要素の順番を整列させるのに使用する方向
    "GEOMETRIC",               # 要素の関連づけ方法の指定
    True                # 更新フラグ（未実装、使用しない）
)
```

**判断のポイント**:

- 生成されたコードに 1個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### CreateOffsetSheet_positive.py

**結果**: 引数数一致: 6/7

**詳細分析**:

- **関数名**: CreateOffsetSheet
- **関数の説明**: オフセットシートを作成する。返り値は作成されたオフセットシート要素の要素ID。
- **生成されたコードの引数数**: 6
- **データベースの期待パラメータ数**: 7

**データベースの詳細仕様**:

 0. SheetName            (文字列            ) - 作成するシート要素名称（空文字可）
 1. ElementGroup         (要素グループ         ) - 作成するシート要素を要素グループに入れる場合は要素グループを指定（空文字可）
 2. MaterialName         (材料             ) - 作成するシート要素の材質名称（空文字可）
 3. SrcSurfaces          (要素(配列)         ) - オフセットする元シート要素、フェイス要素の指定文字列配列
 4. OffsetLength         (長さ             ) - オフセット距離
 5. bOffsetBackwards     (bool           ) - オフセット方向を反転するフラグ
 6. bUpdate              (bool           ) - 更新フラグ（未実装、使用しない）

**生成されたコード**:

```python
# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateOffsetSheet(
    "SheetName",               # 作成するシート要素名称（空文字可）
    ElementGroup_element,               # 作成するシート要素を要素グループに入れる場合は要素グループを指定（空文字可）
    "STEEL",               # 作成するシート要素の材質名称（空文字可）
    100.0,               # オフセット距離
    True,               # オフセット方向を反転するフラグ
    True                # 更新フラグ（未実装、使用しない）
)
```

**判断のポイント**:

- 生成されたコードに 1個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### CreateSketchNURBSCurve_positive.py

**結果**: 引数数一致: 8/11

**詳細分析**:

- **関数名**: CreateSketchNURBSCurve
- **関数の説明**: NURBS曲線を作成する。返り値は作成された要素の要素ID。
- **生成されたコードの引数数**: 8
- **データベースの期待パラメータ数**: 11

**データベースの詳細仕様**:

 0. SketchPlane          (要素             ) - ＮＵＲＢＳ線を作成するスケッチ要素
 1. SketchArcName        (文字列            ) - 作成するスケッチＮＵＲＢＳ線名称（空文字可）
 2. SketchLayer          (要素             ) - ＮＵＲＢＳ線を作成するスケッチレイヤー（空文字可）
 3. nDegree              (整数             ) - ＮＵＲＢＳ線の次数
 4. bClose               (bool           ) - 閉じたＮＵＲＢＳ線の場合 True
 5. bPeriodic            (bool           ) - 周期ＮＵＲＢＳ線の場合 True
 6. CtrlPoints           (点(配列)          ) - 制御点（点の配列）
 7. Weights              (浮動小数点(配列)      ) - 重み（浮動小数点の配列）
 8. Knots                (浮動小数点(配列)      ) - ノットベクトル（浮動小数点の配列）
 9. Range                (範囲             ) - トリム範囲
10. bUpdate              (bool           ) - 更新フラグ（未実装、使用しない）

**生成されたコード**:

```python
# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateSketchNURBSCurve(
    SketchPlane_element,               # ＮＵＲＢＳ線を作成するスケッチ要素
    "SketchArcName",               # 作成するスケッチＮＵＲＢＳ線名称（空文字可）
    SketchLayer_element,               # ＮＵＲＢＳ線を作成するスケッチレイヤー（空文字可）
    1,               # ＮＵＲＢＳ線の次数
    True,               # 閉じたＮＵＲＢＳ線の場合 True
    True,               # 周期ＮＵＲＢＳ線の場合 True
    (0.0, 2*3.14159),               # トリム範囲
    True                # 更新フラグ（未実装、使用しない）
)
```

**判断のポイント**:

- 生成されたコードに 3個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### CreateThicken_positive.py

**結果**: 引数数一致: 9/10

**詳細分析**:

- **関数名**: CreateThicken
- **関数の説明**: 指定したソリッド要素に指定要素厚みづけした形状を作成する。返り値は作成された厚みづけフィーチャーのID。
- **生成されたコードの引数数**: 9
- **データベースの期待パラメータ数**: 10

**データベースの詳細仕様**:

 0. ThickenFeatureName   (文字列            ) - 作成する厚みづけフィーチャー要素名称（空文字可）
 1. TargetSolidName      (要素             ) - 厚みづけフィーチャーを作成する対象のソリッド
 2. OperationType        (オペレーションタイプ     ) - ソリッドオペレーションのタイプを指定（ボディ演算の記号）
 3. Sheet                (要素(配列)         ) - 厚み付けをするシートやフェイス（配列）
 4. ThickenType          (厚み付けタイプ        ) - 厚み付けタイプ
 5. Thickeness1          (長さ             ) - 板厚（厚み1）
 6. Thickeness2          (長さ             ) - 板厚2（厚み付けタイプが2方向のときに使用）
 7. ThickenessOffset     (長さ             ) - 厚みづけをするシート、フェイス要素のオフセット距離
 8. ReferMethod          (関連設定           ) - 要素の関連づけ方法の指定
 9. bUpdate              (bool           ) - 更新フラグ（未実装、使用しない）

**生成されたコード**:

```python
# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.CreateThicken(
    "ThickenFeatureName",               # 作成する厚みづけフィーチャー要素名称（空文字可）
    TargetSolidName_element,               # 厚みづけフィーチャーを作成する対象のソリッド
    "UNION",               # ソリッドオペレーションのタイプを指定（ボディ演算の記号）
    "SINGLE",               # 厚み付けタイプ
    100.0,               # 板厚（厚み1）
    100.0,               # 板厚2（厚み付けタイプが2方向のときに使用）
    100.0,               # 厚みづけをするシート、フェイス要素のオフセット距離
    "GEOMETRIC",               # 要素の関連づけ方法の指定
    True                # 更新フラグ（未実装、使用しない）
)
```

**判断のポイント**:

- 生成されたコードに 1個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### MirrorCopy_positive.py

**結果**: 引数数一致: 2/3

**詳細分析**:

- **関数名**: MirrorCopy
- **関数の説明**: 指定要素をミラーコピーする。返り値はコピーされた要素ID配列。
- **生成されたコードの引数数**: 2
- **データベースの期待パラメータ数**: 3

**データベースの詳細仕様**:

 0. SrcElements          (要素(配列)         ) - コピーする要素（配列）
 1. plane                (平面             ) - ミラーコピーを行う平面（ドキュメントは "[in] BSTR plane" と記載）
 2. ReferMethod          (関連設定           ) - 要素の関連づけ方法の指定

**生成されたコード**:

```python
# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.MirrorCopy(
    XY_PLANE,               # ミラーコピーを行う平面（ドキュメントは "[in] BSTR plane" と記載）
    "GEOMETRIC"                # 要素の関連づけ方法の指定
)
```

**判断のポイント**:

- 生成されたコードに 1個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

#### TranslationCopy_positive.py

**結果**: 引数数一致: 4/5

**詳細分析**:

- **関数名**: TranslationCopy
- **関数の説明**: 指定要素を移動コピーする。返り値はコピーされた要素ID配列。
- **生成されたコードの引数数**: 4
- **データベースの期待パラメータ数**: 5

**データベースの詳細仕様**:

 0. SrcElements          (要素(配列)         ) - コピーする要素（配列）
 1. nCopy                (整数             ) - コピーする数
 2. direction            (方向             ) - コピーする方向
 3. distance             (長さ             ) - 移動距離
 4. ReferMethod          (関連設定           ) - 要素の関連づけ方法の指定

**生成されたコード**:

```python
# test_type: positive
# This snippet should pass validation as it has the correct number of arguments.

part.TranslationCopy(
    1,               # コピーする数
    (1.0, 0.0, 0.0),               # コピーする方向
    100.0,               # 移動距離
    "GEOMETRIC"                # 要素の関連づけ方法の指定
)
```

**判断のポイント**:

- 生成されたコードに 1個 のパラメータが不足しています
- 不足しているパラメータを確認し、必要に応じて追加してください
- どちらが正しいかは、実際のAPIドキュメントや使用例を参照して判断してください

---

## ✅ 成功したテスト一覧

- **BlankElement_negative.py**: 引数数不一致を正しく検出: 1/2
- **BlankElement_positive.py**: 引数数一致: 2/2
- **BodyDivideByElements_negative.py**: 引数数不一致を正しく検出: 5/7
- **BodySeparateBySubSolids_negative.py**: 引数数不一致を正しく検出: 4/6
- **CreateBracketParam_negative.py**: 引数数不一致を正しく検出: 2/0
- **CreateBracketParam_positive.py**: 引数数一致: 0/0
- **CreateBracket_negative.py**: 引数数不一致を正しく検出: 1/2
- **CreateBracket_positive.py**: 引数数一致: 2/2
- **CreateElementsFromFile_negative.py**: 引数数不一致を正しく検出: 2/1
- **CreateElementsFromFile_positive.py**: 引数数一致: 1/1
- **CreateLinearSweepParam_negative.py**: 引数数不一致を正しく検出: 2/0
- **CreateLinearSweepParam_positive.py**: 引数数一致: 0/0
- **CreateLinearSweepSheet_negative.py**: 引数数不一致を正しく検出: 1/2
- **CreateLinearSweepSheet_positive.py**: 引数数一致: 2/2
- **CreateLinearSweep_negative.py**: 引数数不一致を正しく検出: 3/4
- **CreateLinearSweep_positive.py**: 引数数一致: 4/4
- **CreateOffsetSheet_negative.py**: 引数数不一致を正しく検出: 5/7
- **CreateOtherSolid_negative.py**: 引数数不一致を正しく検出: 5/6
- **CreateOtherSolid_positive.py**: 引数数一致: 6/6
- **CreatePlate_negative.py**: 引数数不一致を正しく検出: 13/14
- **CreatePlate_positive.py**: 引数数一致: 14/14
- **CreateProfileParam_negative.py**: 引数数不一致を正しく検出: 2/0
- **CreateProfileParam_positive.py**: 引数数一致: 0/0
- **CreateProfile_negative.py**: 引数数不一致を正しく検出: 1/2
- **CreateProfile_positive.py**: 引数数一致: 2/2
- **CreateSketchArc3Pts_negative.py**: 引数数不一致を正しく検出: 6/7
- **CreateSketchArc3Pts_positive.py**: 引数数一致: 7/7
- **CreateSketchArc_negative.py**: 引数数不一致を正しく検出: 7/8
- **CreateSketchArc_positive.py**: 引数数一致: 8/8
- **CreateSketchCircle_negative.py**: 引数数不一致を正しく検出: 7/8
- **CreateSketchCircle_positive.py**: 引数数一致: 8/8
- **CreateSketchEllipse_negative.py**: 引数数不一致を正しく検出: 9/10
- **CreateSketchEllipse_positive.py**: 引数数一致: 10/10
- **CreateSketchLayer_negative.py**: 引数数不一致を正しく検出: 1/2
- **CreateSketchLayer_positive.py**: 引数数一致: 2/2
- **CreateSketchLine_negative.py**: 引数数不一致を正しく検出: 5/6
- **CreateSketchLine_positive.py**: 引数数一致: 6/6
- **CreateSketchNURBSCurve_negative.py**: 引数数不一致を正しく検出: 7/11
- **CreateSketchPlane_negative.py**: 引数数不一致を正しく検出: 11/12
- **CreateSketchPlane_positive.py**: 引数数一致: 12/12
- **CreateSolid_negative.py**: 引数数不一致を正しく検出: 2/3
- **CreateSolid_positive.py**: 引数数一致: 3/3
- **CreateThicken_negative.py**: 引数数不一致を正しく検出: 8/10
- **CreateVariable_negative.py**: 引数数不一致を正しく検出: 3/4
- **CreateVariable_positive.py**: 引数数一致: 4/4
- **MirrorCopy_negative.py**: 引数数不一致を正しく検出: 1/3
- **ReverseSheet_negative.py**: 引数数不一致を正しく検出: 2/1
- **ReverseSheet_positive.py**: 引数数一致: 1/1
- **SetElementColor_negative.py**: 引数数不一致を正しく検出: 4/5
- **SetElementColor_positive.py**: 引数数一致: 5/5
- **SheetAlignNormal_negative.py**: 引数数不一致を正しく検出: 3/4
- **SheetAlignNormal_positive.py**: 引数数一致: 4/4
- **TranslationCopy_negative.py**: 引数数不一致を正しく検出: 3/5

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
*このレポートは 2025-08-24 16:27:59 に自動生成されました。*
*Neo4jデータベースの仕様を基準として検証を行いました。*
