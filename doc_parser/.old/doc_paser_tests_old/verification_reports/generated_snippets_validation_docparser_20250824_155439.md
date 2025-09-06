# 生成されたテストケース検証レポート

**データベース名**: docparser
**検証日時**: 2025-08-24 15:54:39
**生成元**: test_rag_retrieval.py (修正版)

## データベース基本情報

- **データベース名**: docparser
- **関数数**: 30個
- **パラメータ数**: 272個
- **オブジェクト定義数**: 3個

## 検証結果サマリー

- **総検証数**: 90
- **通過数**: 76
- **失敗数**: 14
- **成功率**: 84.4%

**全体結果**: ❌ 一部検証失敗

## 詳細検証結果

### NEGATIVE テスト

**結果**: 30/30 通過

✅ **BlankElement_negative.py (BlankElement)**
   - 詳細: 引数数不一致を正しく検出: 1/2

✅ **BodyDivideByElements_negative.py (BodyDivideByElements)**
   - 詳細: 引数数不一致を正しく検出: 5/7

✅ **BodySeparateBySubSolids_negative.py (BodySeparateBySubSolids)**
   - 詳細: 引数数不一致を正しく検出: 4/6

✅ **CreateBracketParam_negative.py (CreateBracketParam)**
   - 詳細: 引数数不一致を正しく検出: 2/0

✅ **CreateBracket_negative.py (CreateBracket)**
   - 詳細: 引数数不一致を正しく検出: 1/2

✅ **CreateElementsFromFile_negative.py (CreateElementsFromFile)**
   - 詳細: 引数数不一致を正しく検出: 2/1

✅ **CreateLinearSweepParam_negative.py (CreateLinearSweepParam)**
   - 詳細: 引数数不一致を正しく検出: 2/0

✅ **CreateLinearSweepSheet_negative.py (CreateLinearSweepSheet)**
   - 詳細: 引数数不一致を正しく検出: 1/2

✅ **CreateLinearSweep_negative.py (CreateLinearSweep)**
   - 詳細: 引数数不一致を正しく検出: 3/4

✅ **CreateOffsetSheet_negative.py (CreateOffsetSheet)**
   - 詳細: 引数数不一致を正しく検出: 5/7

✅ **CreateOtherSolid_negative.py (CreateOtherSolid)**
   - 詳細: 引数数不一致を正しく検出: 5/6

✅ **CreatePlate_negative.py (CreatePlate)**
   - 詳細: 引数数不一致を正しく検出: 13/14

✅ **CreateProfileParam_negative.py (CreateProfileParam)**
   - 詳細: 引数数不一致を正しく検出: 2/0

✅ **CreateProfile_negative.py (CreateProfile)**
   - 詳細: 引数数不一致を正しく検出: 1/2

✅ **CreateSketchArc3Pts_negative.py (CreateSketchArc3Pts)**
   - 詳細: 引数数不一致を正しく検出: 6/7

✅ **CreateSketchArc_negative.py (CreateSketchArc)**
   - 詳細: 引数数不一致を正しく検出: 7/8

✅ **CreateSketchCircle_negative.py (CreateSketchCircle)**
   - 詳細: 引数数不一致を正しく検出: 7/8

✅ **CreateSketchEllipse_negative.py (CreateSketchEllipse)**
   - 詳細: 引数数不一致を正しく検出: 9/10

✅ **CreateSketchLayer_negative.py (CreateSketchLayer)**
   - 詳細: 引数数不一致を正しく検出: 1/2

✅ **CreateSketchLine_negative.py (CreateSketchLine)**
   - 詳細: 引数数不一致を正しく検出: 5/6

✅ **CreateSketchNURBSCurve_negative.py (CreateSketchNURBSCurve)**
   - 詳細: 引数数不一致を正しく検出: 7/11

✅ **CreateSketchPlane_negative.py (CreateSketchPlane)**
   - 詳細: 引数数不一致を正しく検出: 11/12

✅ **CreateSolid_negative.py (CreateSolid)**
   - 詳細: 引数数不一致を正しく検出: 2/3

✅ **CreateThicken_negative.py (CreateThicken)**
   - 詳細: 引数数不一致を正しく検出: 8/10

✅ **CreateVariable_negative.py (CreateVariable)**
   - 詳細: 引数数不一致を正しく検出: 3/4

✅ **MirrorCopy_negative.py (MirrorCopy)**
   - 詳細: 引数数不一致を正しく検出: 1/3

✅ **ReverseSheet_negative.py (ReverseSheet)**
   - 詳細: 引数数不一致を正しく検出: 2/1

✅ **SetElementColor_negative.py (SetElementColor)**
   - 詳細: 引数数不一致を正しく検出: 4/5

✅ **SheetAlignNormal_negative.py (SheetAlignNormal)**
   - 詳細: 引数数不一致を正しく検出: 3/4

✅ **TranslationCopy_negative.py (TranslationCopy)**
   - 詳細: 引数数不一致を正しく検出: 3/5

### POSITIVE テスト

**結果**: 23/30 通過

✅ **BlankElement_positive.py (BlankElement)**
   - 詳細: 引数数一致: 2/2

❌ **BodyDivideByElements_positive.py (BodyDivideByElements)**
   - 詳細: 引数数一致: 6/7

❌ **BodySeparateBySubSolids_positive.py (BodySeparateBySubSolids)**
   - 詳細: 引数数一致: 5/6

✅ **CreateBracketParam_positive.py (CreateBracketParam)**
   - 詳細: 引数数一致: 0/0

✅ **CreateBracket_positive.py (CreateBracket)**
   - 詳細: 引数数一致: 2/2

✅ **CreateElementsFromFile_positive.py (CreateElementsFromFile)**
   - 詳細: 引数数一致: 1/1

✅ **CreateLinearSweepParam_positive.py (CreateLinearSweepParam)**
   - 詳細: 引数数一致: 0/0

✅ **CreateLinearSweepSheet_positive.py (CreateLinearSweepSheet)**
   - 詳細: 引数数一致: 2/2

✅ **CreateLinearSweep_positive.py (CreateLinearSweep)**
   - 詳細: 引数数一致: 4/4

❌ **CreateOffsetSheet_positive.py (CreateOffsetSheet)**
   - 詳細: 引数数一致: 6/7

✅ **CreateOtherSolid_positive.py (CreateOtherSolid)**
   - 詳細: 引数数一致: 6/6

✅ **CreatePlate_positive.py (CreatePlate)**
   - 詳細: 引数数一致: 14/14

✅ **CreateProfileParam_positive.py (CreateProfileParam)**
   - 詳細: 引数数一致: 0/0

✅ **CreateProfile_positive.py (CreateProfile)**
   - 詳細: 引数数一致: 2/2

✅ **CreateSketchArc3Pts_positive.py (CreateSketchArc3Pts)**
   - 詳細: 引数数一致: 7/7

✅ **CreateSketchArc_positive.py (CreateSketchArc)**
   - 詳細: 引数数一致: 8/8

✅ **CreateSketchCircle_positive.py (CreateSketchCircle)**
   - 詳細: 引数数一致: 8/8

✅ **CreateSketchEllipse_positive.py (CreateSketchEllipse)**
   - 詳細: 引数数一致: 10/10

✅ **CreateSketchLayer_positive.py (CreateSketchLayer)**
   - 詳細: 引数数一致: 2/2

✅ **CreateSketchLine_positive.py (CreateSketchLine)**
   - 詳細: 引数数一致: 6/6

❌ **CreateSketchNURBSCurve_positive.py (CreateSketchNURBSCurve)**
   - 詳細: 引数数一致: 8/11

✅ **CreateSketchPlane_positive.py (CreateSketchPlane)**
   - 詳細: 引数数一致: 12/12

✅ **CreateSolid_positive.py (CreateSolid)**
   - 詳細: 引数数一致: 3/3

❌ **CreateThicken_positive.py (CreateThicken)**
   - 詳細: 引数数一致: 9/10

✅ **CreateVariable_positive.py (CreateVariable)**
   - 詳細: 引数数一致: 4/4

❌ **MirrorCopy_positive.py (MirrorCopy)**
   - 詳細: 引数数一致: 2/3

✅ **ReverseSheet_positive.py (ReverseSheet)**
   - 詳細: 引数数一致: 1/1

✅ **SetElementColor_positive.py (SetElementColor)**
   - 詳細: 引数数一致: 5/5

✅ **SheetAlignNormal_positive.py (SheetAlignNormal)**
   - 詳細: 引数数一致: 4/4

❌ **TranslationCopy_positive.py (TranslationCopy)**
   - 詳細: 引数数一致: 4/5

### TEMPLATE テスト

**結果**: 23/30 通過

✅ **BlankElement_golden.py (BlankElement)**
   - 詳細: テンプレート引数数: 2, 期待値: 2

❌ **BodyDivideByElements_golden.py (BodyDivideByElements)**
   - 詳細: テンプレート引数数: 6, 期待値: 7

❌ **BodySeparateBySubSolids_golden.py (BodySeparateBySubSolids)**
   - 詳細: テンプレート引数数: 5, 期待値: 6

✅ **CreateBracketParam_golden.py (CreateBracketParam)**
   - 詳細: テンプレート引数数: 0, 期待値: 0

✅ **CreateBracket_golden.py (CreateBracket)**
   - 詳細: テンプレート引数数: 2, 期待値: 2

✅ **CreateElementsFromFile_golden.py (CreateElementsFromFile)**
   - 詳細: テンプレート引数数: 1, 期待値: 1

✅ **CreateLinearSweepParam_golden.py (CreateLinearSweepParam)**
   - 詳細: テンプレート引数数: 0, 期待値: 0

✅ **CreateLinearSweepSheet_golden.py (CreateLinearSweepSheet)**
   - 詳細: テンプレート引数数: 2, 期待値: 2

✅ **CreateLinearSweep_golden.py (CreateLinearSweep)**
   - 詳細: テンプレート引数数: 4, 期待値: 4

❌ **CreateOffsetSheet_golden.py (CreateOffsetSheet)**
   - 詳細: テンプレート引数数: 6, 期待値: 7

✅ **CreateOtherSolid_golden.py (CreateOtherSolid)**
   - 詳細: テンプレート引数数: 6, 期待値: 6

✅ **CreatePlate_golden.py (CreatePlate)**
   - 詳細: テンプレート引数数: 14, 期待値: 14

✅ **CreateProfileParam_golden.py (CreateProfileParam)**
   - 詳細: テンプレート引数数: 0, 期待値: 0

✅ **CreateProfile_golden.py (CreateProfile)**
   - 詳細: テンプレート引数数: 2, 期待値: 2

✅ **CreateSketchArc3Pts_golden.py (CreateSketchArc3Pts)**
   - 詳細: テンプレート引数数: 7, 期待値: 7

✅ **CreateSketchArc_golden.py (CreateSketchArc)**
   - 詳細: テンプレート引数数: 8, 期待値: 8

✅ **CreateSketchCircle_golden.py (CreateSketchCircle)**
   - 詳細: テンプレート引数数: 8, 期待値: 8

✅ **CreateSketchEllipse_golden.py (CreateSketchEllipse)**
   - 詳細: テンプレート引数数: 10, 期待値: 10

✅ **CreateSketchLayer_golden.py (CreateSketchLayer)**
   - 詳細: テンプレート引数数: 2, 期待値: 2

✅ **CreateSketchLine_golden.py (CreateSketchLine)**
   - 詳細: テンプレート引数数: 6, 期待値: 6

❌ **CreateSketchNURBSCurve_golden.py (CreateSketchNURBSCurve)**
   - 詳細: テンプレート引数数: 8, 期待値: 11

✅ **CreateSketchPlane_golden.py (CreateSketchPlane)**
   - 詳細: テンプレート引数数: 12, 期待値: 12

✅ **CreateSolid_golden.py (CreateSolid)**
   - 詳細: テンプレート引数数: 3, 期待値: 3

❌ **CreateThicken_golden.py (CreateThicken)**
   - 詳細: テンプレート引数数: 9, 期待値: 10

✅ **CreateVariable_golden.py (CreateVariable)**
   - 詳細: テンプレート引数数: 4, 期待値: 4

❌ **MirrorCopy_golden.py (MirrorCopy)**
   - 詳細: テンプレート引数数: 2, 期待値: 3

✅ **ReverseSheet_golden.py (ReverseSheet)**
   - 詳細: テンプレート引数数: 1, 期待値: 1

✅ **SetElementColor_golden.py (SetElementColor)**
   - 詳細: テンプレート引数数: 5, 期待値: 5

✅ **SheetAlignNormal_golden.py (SheetAlignNormal)**
   - 詳細: テンプレート引数数: 4, 期待値: 4

❌ **TranslationCopy_golden.py (TranslationCopy)**
   - 詳細: テンプレート引数数: 4, 期待値: 5

## 推奨事項

❌ 一部の検証が失敗しました。以下の点を確認してください：

- **BodyDivideByElements_positive.py (BodyDivideByElements)**: 引数数一致: 6/7
- **BodySeparateBySubSolids_positive.py (BodySeparateBySubSolids)**: 引数数一致: 5/6
- **CreateOffsetSheet_positive.py (CreateOffsetSheet)**: 引数数一致: 6/7
- **CreateSketchNURBSCurve_positive.py (CreateSketchNURBSCurve)**: 引数数一致: 8/11
- **CreateThicken_positive.py (CreateThicken)**: 引数数一致: 9/10
- **MirrorCopy_positive.py (MirrorCopy)**: 引数数一致: 2/3
- **TranslationCopy_positive.py (TranslationCopy)**: 引数数一致: 4/5
- **BodyDivideByElements_golden.py (BodyDivideByElements)**: テンプレート引数数: 6, 期待値: 7
- **BodySeparateBySubSolids_golden.py (BodySeparateBySubSolids)**: テンプレート引数数: 5, 期待値: 6
- **CreateOffsetSheet_golden.py (CreateOffsetSheet)**: テンプレート引数数: 6, 期待値: 7
- **CreateSketchNURBSCurve_golden.py (CreateSketchNURBSCurve)**: テンプレート引数数: 8, 期待値: 11
- **CreateThicken_golden.py (CreateThicken)**: テンプレート引数数: 9, 期待値: 10
- **MirrorCopy_golden.py (MirrorCopy)**: テンプレート引数数: 2, 期待値: 3
- **TranslationCopy_golden.py (TranslationCopy)**: テンプレート引数数: 4, 期待値: 5

---
*このレポートは 2025-08-24 15:54:41 に自動生成されました。*