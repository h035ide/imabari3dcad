# structured_api 検証ログ (2025-10-23 13:43:27)

- XML: `doc_preprocessor_hybrid/out/api_template.xml`
- JSON: `doc_preprocessor_hybrid/out/structured_api.json`
- 結果: 差分あり (exit 1)
- XMLエントリ数: 105
- JSONエントリ数: 121
- XMLのみ: 9件 / JSONのみ: 25件 / 差分: 96件

## 正答率メトリクス

### ⑴関数名の正答率
- 総数: 72
- 正解数: 72
- 正答率: 100.00%

### ⑵パラメータオブジェクトの正答率
- 総数: 9
- 正解数: 0
- 正答率: 0.00%

### ⑶型定義の正答率
- 総数: 0
- 正解数: 25
- 正答率: 0.00%

### ⑷引数定義名の正答率
- 総数: 478
- 正解数: 264
- 正答率: 55.23%

### ⑸引数タイプの正答率
- 総数: 478
- 正解数: 216
- 正答率: 45.19%

### ⑹descriptionの正答率（完全一致）
- 総数: 524
- 正解数: 272
- 正答率: 51.91%

## レポート
```
[XMLのみ]BracketParam, FacePlateParam, LinearSweepParam, LoftParam, ProfileParam, RotationalSweepParam, STLParameter, SlotParam, SweepParam
[JSONのみ]bool, オペレーションタイプ （ボディ）, スイープ方向, モールド位置, 厚み付けタイプ, 変数単位, 平面, 形状タイプ, 形状パラメータ, 数値, 整数, 文字列, 方向, 材料, 注記スタイル, 浮動小数点, 点, 点(2D), 点(3D), 範囲, 要素, 要素グループ, 角度, 長さ, 関連設定
[差分]
- function:Activate return_description -> 期待: なし / 実際: (空)
- function:BlankElement return_description -> 期待: なし / 実際: (空)
- function:BlankElement params[bBlank].type -> 期待: bool / 実際: 不明
- function:BlankElement params[bBlank].description -> 期待: Trueの時は非表示にする。Falseの時は表示する。 / 実際: (空)
- function:BodyDivideByCurves params[pDivideCurves].type -> 期待: 要素(配列) / 実際: 要素[]
- function:BodyDivideByElements params[bUpdate].type -> 期待: bool / 実際: 不明
- function:BodyDivideByElements params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:BodyDivideByElements params[pDivideElements].type -> 期待: 要素(配列) / 実際: 要素[]
- function:BodySeparateBySubSolids params[bUpdate].type -> 期待: bool / 実際: 不明
- function:BodySeparateBySubSolids params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:BodySeparateBySubSolids params[pSubSolids].type -> 期待: 要素(配列) / 実際: 要素[]
- function:Close return_description -> 期待: なし / 実際: (空)
- function:CreateBoundedPlate params[BoundObjects].type -> 期待: 要素(配列) / 実際: 要素[]
- function:CreateBoundingBox params[Bodies].type -> 期待: 要素(配列) / 実際: 要素[]
- function:CreateBracket params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateBracket params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateFacePlate params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateFacePlate params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateLinearSweep params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateLinearSweep params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateLinearSweepSheet params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateLinearSweepSheet params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateLoft params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateLoft params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateLoftSheet params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateLoftSheet params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateNURBSCurve params[CtrlPoints].type -> 期待: 点(配列) / 実際: 点[]
- function:CreateNURBSCurve params[Knots].type -> 期待: 浮動小数点(配列) / 実際: 浮動小数点[]
- function:CreateNURBSCurve params[Weights].type -> 期待: 浮動小数点(配列) / 実際: 浮動小数点[]
- function:CreateOffsetDatumPlane return_description -> 期待: 作成されたデータム平面の要素ID / 実際: (空)
- function:CreateOffsetDatumPlane params[ElementGroup].description -> 期待: 作成するデータム平面要素を入れる場合は指定（空文字可） / 実際: 作成するデータム平面要素を要素グループに入れる場合は要素グループを指定（空文字可）
- function:CreateOffsetSheet params[SrcSurfaces].type -> 期待: 要素(配列) / 実際: 要素[]
- function:CreateOtherSolid params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateOtherSolid params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreatePlate params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreatePlate params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateProfile params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateProfile params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateRotatedDatumPlane return_description -> 期待: 作成されたデータム平面の要素ID / 実際: (空)
- function:CreateRotatedDatumPlane params[Plane].description -> 期待: 元になる平面 / 実際: 元になる平面を指定する
- function:CreateRotationalSweep params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateRotationalSweep params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateRotationalSweepSheet params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateRotationalSweepSheet params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchArc params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSketchArc params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchArc3Pts params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSketchArc3Pts params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchCircle params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSketchCircle params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchEllipse params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSketchEllipse params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchLayer params[SketchPlane].type -> 期待: 要素 / 実際: 不明
- function:CreateSketchLayer params[SketchPlane].description -> 期待: レイヤーを作成するスケッチ要素 / 実際: (空)
- function:CreateSketchLine params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSketchLine params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchNURBSCurve params[CtrlPoints].type -> 期待: 点(配列) / 実際: 点[]
- function:CreateSketchNURBSCurve params[Knots].type -> 期待: 浮動小数点(配列) / 実際: 浮動小数点[]
- function:CreateSketchNURBSCurve params[Weights].type -> 期待: 浮動小数点(配列) / 実際: 浮動小数点[]
- function:CreateSketchNURBSCurve params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSketchNURBSCurve params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchPlane params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSketchPlane params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSlot params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSlot params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSweep params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSweep params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSweepSheet params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateSweepSheet params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateThicken params[Sheet].type -> 期待: 要素(配列) / 実際: 要素[]
- function:CreateThicken params[bUpdate].type -> 期待: bool / 実際: 不明
- function:CreateThicken params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateVariable params[VariableElementGroup].type -> 期待: 要素グループ / 実際: 不明
- function:CreateVariable params[VariableElementGroup].description -> 期待: 作成する変数要素を要素グループに入れる場合は要素グループを指定（空文字可） / 実際: (空)
- function:CutBody params[ReferMethod].type -> 期待: (空) / 実際: 不明
- function:ExporAsSTL return_description -> 期待: なし / 実際: (空)
- function:ExporAsSTL params[pOpt].type -> 期待: STLパラメータオブジェクト / 実際: 不明
- function:ExportToBitmap return_description -> 期待: なし / 実際: (空)
- function:FitAllViews return_description -> 期待: なし / 実際: (空)
- function:MirrorCopy params[[in] BSTR plane] -> 期待: {'type': '', 'description': ''} / 実際: (JSONに無し)
- function:MirrorCopy params[ReferMethod].type -> 期待: 関連設定 / 実際: 不明
- function:MirrorCopy params[ReferMethod].description -> 期待: 要素の関連づけ方法の指定 / 実際: (空)
- function:MirrorCopy params[SrcElements].type -> 期待: 要素(配列) / 実際: 要素[]
- function:MirrorCopy params[plane].type -> 期待: 平面 / 実際: 文字列
- function:MirrorCopy params[plane].description -> 期待: ミラーを作成する平面 / 実際: (空)
- function:Quit return_description -> 期待: なし / 実際: (空)
- function:ReverseSheet params[SheetElement] -> 期待: (XMLに無し) / 実際: {'type': '不明', 'description': ''}
- function:Save return_description -> 期待: なし / 実際: (空)
- function:SetDirection return_description -> 期待: なし / 実際: (空)
- function:SheetAlignNormal return_description -> 期待: なし / 実際: (空)
- function:SheetAlignNormal params[dirZ].type -> 期待: 浮動小数点 / 実際: 不明
- function:SheetAlignNormal params[dirZ].description -> 期待: 方向ベクトルのZ成分 / 実際: (空)
- function:ShowMainWindow return_description -> 期待: なし / 実際: (空)
- function:TranslationCopy params[ReferMethod].type -> 期待: 関連設定 / 実際: 不明
- function:TranslationCopy params[ReferMethod].description -> 期待: 要素の関連づけ方法の指定 / 実際: (空)
- function:TranslationCopy params[SrcElements].type -> 期待: 要素(配列) / 実際: 要素[]
```
