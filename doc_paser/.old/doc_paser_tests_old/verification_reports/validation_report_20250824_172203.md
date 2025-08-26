# テストケース検証レポート（詳細版）

**日時**: 2025-08-24 17:22:03
**データベース**: docparser
**生成元**: test_rag_retrieval.py (Neo4jデータのみ使用、詳細分析機能付き)
**検証基準**: Neo4jデータベースの関数仕様

## 📊 全体統計

- **総検証数**: 60
- **成功**: 60 (100.0%)
- **失敗**: 0 (0.0%)

## 🔍 テストタイプ別統計

- **TEST**: 60/60 (100.0%)

## ✅ 成功したテスト一覧

- **BlankElement_negative.py**: 引数数不一致を正しく検出: 1/2
- **BlankElement_positive.py**: 引数数一致: 2/2
- **BodyDivideByElements_negative.py**: 引数数不一致を正しく検出: 6/7
- **BodyDivideByElements_positive.py**: 引数数一致: 7/7
- **BodySeparateBySubSolids_negative.py**: 引数数不一致を正しく検出: 5/6
- **BodySeparateBySubSolids_positive.py**: 引数数一致: 6/6
- **CreateBracketParam_negative.py**: 引数数不一致を正しく検出: 1/0
- **CreateBracketParam_positive.py**: 引数数一致: 0/0
- **CreateBracket_negative.py**: 引数数不一致を正しく検出: 1/2
- **CreateBracket_positive.py**: 引数数一致: 2/2
- **CreateElementsFromFile_negative.py**: 引数数不一致を正しく検出: 0/1
- **CreateElementsFromFile_positive.py**: 引数数一致: 1/1
- **CreateLinearSweepParam_negative.py**: 引数数不一致を正しく検出: 1/0
- **CreateLinearSweepParam_positive.py**: 引数数一致: 0/0
- **CreateLinearSweepSheet_negative.py**: 引数数不一致を正しく検出: 1/2
- **CreateLinearSweepSheet_positive.py**: 引数数一致: 2/2
- **CreateLinearSweep_negative.py**: 引数数不一致を正しく検出: 3/4
- **CreateLinearSweep_positive.py**: 引数数一致: 4/4
- **CreateOffsetSheet_negative.py**: 引数数不一致を正しく検出: 6/7
- **CreateOffsetSheet_positive.py**: 引数数一致: 7/7
- **CreateOtherSolid_negative.py**: 引数数不一致を正しく検出: 5/6
- **CreateOtherSolid_positive.py**: 引数数一致: 6/6
- **CreatePlate_negative.py**: 引数数不一致を正しく検出: 13/14
- **CreatePlate_positive.py**: 引数数一致: 14/14
- **CreateProfileParam_negative.py**: 引数数不一致を正しく検出: 1/0
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
- **CreateSketchNURBSCurve_negative.py**: 引数数不一致を正しく検出: 10/11
- **CreateSketchNURBSCurve_positive.py**: 引数数一致: 11/11
- **CreateSketchPlane_negative.py**: 引数数不一致を正しく検出: 11/12
- **CreateSketchPlane_positive.py**: 引数数一致: 12/12
- **CreateSolid_negative.py**: 引数数不一致を正しく検出: 2/3
- **CreateSolid_positive.py**: 引数数一致: 3/3
- **CreateThicken_negative.py**: 引数数不一致を正しく検出: 9/10
- **CreateThicken_positive.py**: 引数数一致: 10/10
- **CreateVariable_negative.py**: 引数数不一致を正しく検出: 3/4
- **CreateVariable_positive.py**: 引数数一致: 4/4
- **MirrorCopy_negative.py**: 引数数不一致を正しく検出: 2/3
- **MirrorCopy_positive.py**: 引数数一致: 3/3
- **ReverseSheet_negative.py**: 引数数不一致を正しく検出: 0/1
- **ReverseSheet_positive.py**: 引数数一致: 1/1
- **SetElementColor_negative.py**: 引数数不一致を正しく検出: 4/5
- **SetElementColor_positive.py**: 引数数一致: 5/5
- **SheetAlignNormal_negative.py**: 引数数不一致を正しく検出: 3/4
- **SheetAlignNormal_positive.py**: 引数数一致: 4/4
- **TranslationCopy_negative.py**: 引数数不一致を正しく検出: 4/5
- **TranslationCopy_positive.py**: 引数数一致: 5/5

## 💡 改善のための推奨事項

✅ すべてのテストが成功しました。生成されたテストケースは高品質です。

---
*このレポートは 2025-08-24 17:22:03 に自動生成されました。*
*Neo4jデータベースの仕様を基準として検証を行いました。*
