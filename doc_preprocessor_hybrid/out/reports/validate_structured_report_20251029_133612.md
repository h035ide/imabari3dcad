# structured_api 検証ログ (2025-10-29 13:36:12)

- XML: `doc_preprocessor_hybrid/out/api_template.xml`
- JSON: `doc_preprocessor_hybrid/out/structured_api.json`
- 結果: 差分あり (exit 1)
- XMLエントリ数: 184
- JSONエントリ数: 191
- XMLのみ: 10件 / JSONのみ: 17件 / 差分: 174件

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
- 総数: 23
- 正解数: 25
- 正答率: 108.70%

### ⑷引数定義名の正答率
- 総数: 478
- 正解数: 264
- 正答率: 55.23%

### ⑸引数タイプの正答率
- 総数: 478
- 正解数: 259
- 正答率: 54.18%

### ⑹descriptionの正答率（完全一致）
- 総数: 547
- 正解数: 191
- 正答率: 34.92%

## レポート
```
[XMLのみ]BracketParam, FacePlateParam, LinearSweepParam, LoftParam, ProfileParam, RotationalSweepParam, STLParameter, SlotParam, SweepParam, オペレーションタイプ （ボディ）
[JSONのみ]STLパラメータオブジェクト, オペレーションタイプ (ボディ), スイープパラメータオブジェクト, スロットパラメータオブジェクト, ドキュメントをSTLとして保存する際のパラメータオブジェクト, フェイスプレートパラメータオブジェクト, ブラケット要素のパラメータオブジェクト, ロフトパラメータオブジェクト, 回転パラメータオブジェクト, 押し出しパラメータオブジェクト, 条材要素のパラメータオブジェクト, 点(2D), 点(3D), 船殻のスロットパラメータオブジェクト, 船殻のフェイスプレートパラメータオブジェクト, 船殻のブラケット要素のパラメータオブジェクト, 船殻の条材ソリッド要素のパラメータオブジェクト
[差分]
- function:Activate return_description -> 期待: なし / 実際: (空)
- function:BlankElement return_description -> 期待: なし / 実際: (空)
- function:BlankElement params[bBlank].description -> 期待: Trueの時は非表示にする。Falseの時は表示する。 / 実際: (空)
- function:BodyDivideByCurves params[CorrectEndPointsTolerance].description -> 期待: 分割線が複数の場合の分割線同士のの判定トレランスを指定（通常は指定しない、空文字） / 実際: 分割線が複数の場合の分割線同士のの判定トレランスを指定(通常は指定しない,空文字)
- function:BodyDivideByCurves params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: 更新フラグ(未実装,使用しない)
- function:BodyDivideByCurves params[pDriveFeatureName].description -> 期待: 作成する分割フィーチャー要素名称（空文字可） / 実際: 作成する分割フィーチャー要素名称(空文字可)
- function:BodyDivideByElements params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:BodyDivideByElements params[pDivideElements].description -> 期待: 分割をする要素（シートボディ、フェイス、平面要素） / 実際: 分割をする要素(シートボディ,フェイス,平面要素)
- function:BodyDivideByElements params[pDriveFeatureName].description -> 期待: 作成する分割フィーチャー要素名称（空文字可） / 実際: 作成する分割フィーチャー要素名称(空文字可)
- function:BodyDivideByElements params[pWCS].description -> 期待: 方向を定義する座標系（通常は指定しない） / 実際: 方向を定義する座標系(通常は指定しない)
- function:BodyDivideByPlanes params[WCS].description -> 期待: 要素分割に使用する座標系を指定。通常は指定しない / 実際: 要素分割に使用する座標系を指定.通常は指定しない
- function:BodyDivideByPlanes params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: 更新フラグ(未実装,使用しない)
- function:BodyDivideByPlanes params[nPlaneCopy].description -> 期待: 分割をする平面を複数コピーして分割をする（通常は1) / 実際: 分割をする平面を複数コピーして分割をする(通常は1)
- function:BodyDivideByPlanes params[pDriveFeatureName].description -> 期待: 作成する分割フィーチャー要素名称（空文字可） / 実際: 作成する分割フィーチャー要素名称(空文字可)
- function:BodySeparateBySubSolids params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:BodySeparateBySubSolids params[pSeparateFeatureName].description -> 期待: 作成する分割フィーチャー要素名称（空文字可） / 実際: 作成する分割フィーチャー要素名称(空文字可)
- function:Close return_description -> 期待: なし / 実際: (空)
- function:CreateArc params[MajorDir].description -> 期待: 主軸方向（パラメータ０の位置方向 / 実際: 主軸方向(パラメータ０の位置方向
- function:CreateBoundedPlate params[BoundObjects].description -> 期待: 境界要素（シート、フェイス、スケッチ、平面、ソリッド） / 実際: 境界要素(シート,フェイス,スケッチ,平面,ソリッド)
- function:CreateBoundedPlate params[FeatureName].description -> 期待: 作成する境界要素指定フィーチャー要素名称（空文字可） / 実際: 作成する境界要素指定フィーチャー要素名称(空文字可)
- function:CreateBoundedPlate params[Thickness2].description -> 期待: 板厚２（厚み付けタイプが２方向のときに使用） / 実際: 板厚２(厚み付けタイプが２方向のときに使用)
- function:CreateBoundedPlate params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: 更新フラグ(未実装,使用しない)
- function:CreateBoundingBox params[Bodies].description -> 期待: 境界ボックスを計算するソリッド、シート要素 / 実際: 境界ボックスを計算するソリッド,シート要素
- function:CreateBoundingBox params[FeatureName].description -> 期待: 作成する境界ボックスフィーチャー要素名称（空文字可） / 実際: 作成する境界ボックスフィーチャー要素名称(空文字可)
- function:CreateBoundingBox params[bOptimalBox].description -> 期待: Trueを指定するとボックスを計算する座標系を最適なものにする。（そうでない場合は絶対座標系で計算する） / 実際: Trueを指定するとボックスを計算する座標系を最適なものにする.(そうでない場合は絶対座標系で計算する)
- function:CreateBoundingBox params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: 更新フラグ(未実装,使用しない)
- function:CreateBracket params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateBracketParam return_description -> 期待: ブラケット要素のパラメータオブジェクト / 実際: 作成された別ソリッドフィーチャーのID
- function:CreateElementsFromFile params[FileName].description -> 期待: ファイルパス（現状、Parasolid形式のみ） / 実際: ファイルパス(現状,Parasolid形式のみ)
- function:CreateEllipse params[MajorDir].description -> 期待: 主軸方向（パラメータ０の位置方向 / 実際: 主軸方向(パラメータ０の位置方向
- function:CreateFacePlate params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateFacePlateParam return_description -> 期待: フェイスプレートパラメータオブジェクト / 実際: 作成されたスロットフィーチャー,カラープレート１，カラープレート２の要素ID配列
- function:CreateLinearSweep params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateLinearSweepParam return_description -> 期待: 押し出しパラメータオブジェクト / 実際: 作成されたオフセットシート要素の要素ID
- function:CreateLinearSweepSheet params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateLoft params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateLoftParam return_description -> 期待: ロフトパラメータオブジェクト / 実際: 線要素の要素ID
- function:CreateLoftSheet params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateOffsetDatumPlane return_description -> 期待: 作成されたデータム平面の要素ID / 実際: (空)
- function:CreateOffsetDatumPlane params[ElementGroup].description -> 期待: 作成するデータム平面要素を入れる場合は指定（空文字可） / 実際: 作成するデータム平面要素を要素グループに入れる場合は要素グループを指定(空文字可)
- function:CreateOffsetDatumPlane params[Name].description -> 期待: 作成するデータム平面要素名称（空文字可） / 実際: 作成するデータム平面要素名称(空文字可)
- function:CreateOffsetDatumPlane params[ReferMethod].description -> 期待: 要素の関連づけ方法の指定（未実装、使用しない） / 実際: 要素の関連づけ方法の指定(未実装,使用しない)
- function:CreateOffsetDatumPlane params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: 更新フラグ(未実装,使用しない)
- function:CreateOffsetSheet params[ElementGroup].description -> 期待: 作成するシート要素を要素グループに入れる場合は要素グループを指定（空文字可） / 実際: 作成するシート要素を要素グループに入れる場合は要素グループを指定(空文字可)
- function:CreateOffsetSheet params[MaterialName].description -> 期待: 作成するシート要素の材質名称（空文字可） / 実際: 作成するシート要素の材質名称(空文字可)
- function:CreateOffsetSheet params[SheetName].description -> 期待: 作成するシート要素名称（空文字可） / 実際: 作成するシート要素名称(空文字可)
- function:CreateOffsetSheet params[SrcSurfaces].description -> 期待: オフセットする元シート要素、フェイス要素の指定文字列配列 / 実際: オフセットする元シート要素,フェイス要素の指定文字列配列
- function:CreateOffsetSheet params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: 更新フラグ(未実装,使用しない)
- function:CreateOtherSolid params[OtherSolidFeatureName].description -> 期待: 作成する別ソリッドフィーチャー要素名称（空文字可） / 実際: 作成する別ソリッドフィーチャー要素名称(空文字可)
- function:CreateOtherSolid params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreatePlate params[BoundSolid].description -> 期待: プレートソリッドの境界となるソリッド要素。 / 実際: プレートソリッドの境界となるソリッド要素.
- function:CreatePlate params[ElementGroup].description -> 期待: 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可） / 実際: 作成するソリッド要素を要素グループに入れる場合は要素グループを指定(空文字可)
- function:CreatePlate params[MaterialName].description -> 期待: 作成するソリッド要素の材質名称（空文字可） / 実際: 作成するソリッド要素の材質名称(空文字可)
- function:CreatePlate params[PlateName].description -> 期待: 作成するプレートソリッド要素名称（空文字可） / 実際: 作成するプレートソリッド要素名称(空文字可)
- function:CreatePlate params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateProfile params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateProfileParam return_description -> 期待: 条材要素のパラメータオブジェクト / 実際: 作成したソリッド要素のID
- function:CreateRotatedDatumPlane return_description -> 期待: 作成されたデータム平面の要素ID / 実際: (空)
- function:CreateRotatedDatumPlane params[ElementGroup].description -> 期待: 作成するデータム平面要素を要素グループに入れる場合は要素グループを指定（空文字可） / 実際: 作成するデータム平面要素を要素グループに入れる場合は要素グループを指定(空文字可)
- function:CreateRotatedDatumPlane params[Name].description -> 期待: 作成するデータム平面要素名称（空文字可） / 実際: 作成するデータム平面要素名称(空文字可)
- function:CreateRotatedDatumPlane params[Plane].description -> 期待: 元になる平面 / 実際: 元になる平面を指定する
- function:CreateRotatedDatumPlane params[ReferMethod].description -> 期待: 要素の関連づけ方法の指定（未実装、使用しない） / 実際: 要素の関連づけ方法の指定(未実装,使用しない)
- function:CreateRotatedDatumPlane params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: 更新フラグ(未実装,使用しない)
- function:CreateRotationalSweep params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateRotationalSweepParam return_description -> 期待: 回転パラメータオブジェクト / 実際: 作成されたシート要素の要素ID
- function:CreateRotationalSweepSheet params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSTLOption return_description -> 期待: STLパラメータオブジェクト / 実際: Viewオブジェクトの配列
- function:CreateSketchArc params[SketchArcName].description -> 期待: 作成するスケッチ円弧名称（空文字可） / 実際: 作成するスケッチ円弧名称(空文字可)
- function:CreateSketchArc params[SketchLayer].description -> 期待: 円弧を作成するスケッチレイヤー(空文字可） / 実際: 円弧を作成するスケッチレイヤー(空文字可)
- function:CreateSketchArc params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchArc3Pts params[SketchArcName].description -> 期待: 作成するスケッチ円弧名称（空文字可） / 実際: 作成するスケッチ円弧名称(空文字可)
- function:CreateSketchArc3Pts params[SketchLayer].description -> 期待: 円弧を作成するスケッチレイヤー(空文字可） / 実際: 円弧を作成するスケッチレイヤー(空文字可)
- function:CreateSketchArc3Pts params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchCircle params[SketchArcName].description -> 期待: 作成するスケッチ円名称（空文字可） / 実際: 作成するスケッチ円名称(空文字可)
- function:CreateSketchCircle params[SketchLayer].description -> 期待: 円を作成するスケッチレイヤー(空文字可） / 実際: 円を作成するスケッチレイヤー(空文字可)
- function:CreateSketchCircle params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchEllipse params[SketchArcName].description -> 期待: 作成するスケッチ楕円名称（空文字可） / 実際: 作成するスケッチ楕円名称(空文字可)
- function:CreateSketchEllipse params[SketchLayer].description -> 期待: 楕円を作成するスケッチレイヤー(空文字可） / 実際: 楕円を作成するスケッチレイヤー(空文字可)
- function:CreateSketchEllipse params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchLayer params[SketchLayerName].description -> 期待: 作成するスケッチレイヤー名称（空文字可） / 実際: 作成するスケッチレイヤー名称(空文字可)
- function:CreateSketchLayer params[SketchPlane].type -> 期待: 要素 / 実際: 不明
- function:CreateSketchLayer params[SketchPlane].description -> 期待: レイヤーを作成するスケッチ要素 / 実際: (空)
- function:CreateSketchLine params[SketchLayer].description -> 期待: 直線を作成するスケッチレイヤー(空文字可） / 実際: 直線を作成するスケッチレイヤー(空文字可)
- function:CreateSketchLine params[SketchLineName].description -> 期待: 作成するスケッチ直線名称（空文字可） / 実際: 作成するスケッチ直線名称(空文字可)
- function:CreateSketchLine params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchNURBSCurve params[SketchArcName].description -> 期待: 作成するスケッチＮＵＲＢＳ線名称（空文字可） / 実際: 作成するスケッチＮＵＲＢＳ線名称(空文字可)
- function:CreateSketchNURBSCurve params[SketchLayer].description -> 期待: ＮＵＲＢＳ線を作成するスケッチレイヤー(空文字可） / 実際: ＮＵＲＢＳ線を作成するスケッチレイヤー(空文字可)
- function:CreateSketchNURBSCurve params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSketchPlane params[AxisDirection].description -> 期待: スケッチ平面の軸方向を指定（空文字可） / 実際: スケッチ平面の軸方向を指定(空文字可)
- function:CreateSketchPlane params[ElementGroup].description -> 期待: 作成するスケッチ平面を要素グループに入れる場合は要素グループを指定（空文字可） / 実際: 作成するスケッチ平面を要素グループに入れる場合は要素グループを指定(空文字可)
- function:CreateSketchPlane params[ElementName].description -> 期待: 作成するスケッチ平面名称（空文字可） / 実際: 作成するスケッチ平面名称(空文字可)
- function:CreateSketchPlane params[OriginPoint].description -> 期待: スケッチ平面の原点を指定（空文字可） / 実際: スケッチ平面の原点を指定(空文字可)
- function:CreateSketchPlane params[StyleName].description -> 期待: スケッチ平面に適用する注記スタイル名称（空文字可） / 実際: スケッチ平面に適用する注記スタイル名称(空文字可)
- function:CreateSketchPlane params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSlot return_description -> 期待: 作成されたスロットフィーチャー、カラープレート１，カラープレート２の要素ID配列 / 実際: 作成されたスロットフィーチャー,カラープレート１，カラープレート２の要素ID配列
- function:CreateSlot params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSlotParam return_description -> 期待: スロットパラメータオブジェクト / 実際: 作成されたシート要素の要素ID
- function:CreateSolid params[ElementGroup].description -> 期待: 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可） / 実際: 作成するソリッド要素を要素グループに入れる場合は要素グループを指定(空文字可)
- function:CreateSolid params[MaterialName].description -> 期待: 作成するソリッド要素の材質名称（空文字可） / 実際: 作成するソリッド要素の材質名称(空文字可)
- function:CreateSolid params[SolidName].description -> 期待: 作成するソリッド要素名称（空文字可） / 実際: 作成するソリッド要素名称(空文字可)
- function:CreateSweep params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateSweepParam return_description -> 期待: スイープパラメータオブジェクト / 実際: (空)
- function:CreateSweepSheet params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateThicken params[ThickenFeatureName].description -> 期待: 作成する厚みづけフィーチャー要素名称（空文字可） / 実際: 作成する厚みづけフィーチャー要素名称(空文字可)
- function:CreateThicken params[Thickeness2].description -> 期待: 板厚２（厚み付けタイプが２方向のときに使用） / 実際: 板厚２(厚み付けタイプが２方向のときに使用)
- function:CreateThicken params[ThickenessOffset].description -> 期待: 厚みづけをするシート、フェイス要素のオフセット距離 / 実際: 厚みづけをするシート,フェイス要素のオフセット距離
- function:CreateThicken params[bUpdate].description -> 期待: 更新フラグ（未実装、使用しない） / 実際: (空)
- function:CreateVariable params[VariableElementGroup].description -> 期待: 作成する変数要素を要素グループに入れる場合は要素グループを指定（空文字可） / 実際: (空)
- function:CreateVariable params[VariableName].description -> 期待: 作成する変数名称（空文字不可） / 実際: 作成する変数名称(空文字不可)
- function:CutBody params[CutElement].description -> 期待: カットする要素(平面、シート） / 実際: カットする要素(平面,シート)
- function:CutBody params[FeatureName].description -> 期待: 作成するカットフィーチャー要素名称（空文字可） / 実際: 作成するカットフィーチャー要素名称(空文字可)
- function:CutBody params[ReferMethod].type -> 期待: (空) / 実際: 関連設定
- function:CutBody params[TargetBody].description -> 期待: カット対象のソリッド、シート / 実際: カット対象のソリッド,シート
- function:ExporAsSTL return_description -> 期待: なし / 実際: (空)
- function:ExporAsSTL params[pOpt].type -> 期待: STLパラメータオブジェクト / 実際: 要素
- function:ExportToBitmap return_description -> 期待: なし / 実際: (空)
- function:ExportToBitmap params[nBitapWidth].description -> 期待: ビットマップファイルの横方向のピクセルサイズ（縦方向はビューの縦横比から取得） / 実際: ビットマップファイルの横方向のピクセルサイズ(縦方向はビューの縦横比から取得)
- function:FitAllViews return_description -> 期待: なし / 実際: (空)
- function:LoadPart params[bForceEvaluation].description -> 期待: 強制的に全要素を再計算して開くときはTrue (通常はFalse） / 実際: 強制的に全要素を再計算して開くときはTrue (通常はFalse)
- function:MirrorCopy params[[in] BSTR plane] -> 期待: {'type': '', 'description': ''} / 実際: (JSONに無し)
- function:MirrorCopy params[ReferMethod].description -> 期待: 要素の関連づけ方法の指定 / 実際: (空)
- function:MirrorCopy params[plane].type -> 期待: 平面 / 実際: 文字列
- function:MirrorCopy params[plane].description -> 期待: ミラーを作成する平面 / 実際: (空)
- function:OpenDocument params[bForceEvaluation].description -> 期待: 強制的に全要素を再計算して開くときはTrue (通常はFalse） / 実際: 強制的に全要素を再計算して開くときはTrue (通常はFalse)
- function:Quit return_description -> 期待: なし / 実際: (空)
- function:ReverseSheet params[SheetElement] -> 期待: (XMLに無し) / 実際: {'type': '不明', 'description': ''}
- function:Save return_description -> 期待: なし / 実際: (空)
- function:Save params[bAsCompactFormat].description -> 期待: 最小サイズになる形式で保存する時はTrue（開くのに計算を必要とします） / 実際: 最小サイズになる形式で保存する時はTrue(開くのに計算を必要とします)
- function:SetDirection return_description -> 期待: なし / 実際: (空)
- function:SheetAlignNormal return_description -> 期待: なし / 実際: (空)
- function:SheetAlignNormal params[dirZ].type -> 期待: 浮動小数点 / 実際: 不明
- function:SheetAlignNormal params[dirZ].description -> 期待: 方向ベクトルのZ成分 / 実際: (空)
- function:ShowMainWindow return_description -> 期待: なし / 実際: (空)
- function:TranslationCopy params[ReferMethod].description -> 期待: 要素の関連づけ方法の指定 / 実際: (空)
- type_definition:bool category -> 期待: 型定義 / 実際: (空)
- type_definition:スイープ方向 category -> 期待: 型定義 / 実際: (空)
- type_definition:スイープ方向 description -> 期待: "N" 順方向、"R" 反対方向、"B" 両方向、"2" ２方向、"T" 貫通 / 実際: "N" 順方向 "R" 反対方向 "B" 両方向 "2" ２方向 "T" 貫通
- type_definition:モールド位置 category -> 期待: 型定義 / 実際: (空)
- type_definition:モールド位置 description -> 期待: "+" ＋側、"-" ー側、"" （空文字）センター / 実際: "+" ＋側 "-" ー側 "" (空文字)センター
- type_definition:厚み付けタイプ category -> 期待: 型定義 / 実際: (空)
- type_definition:厚み付けタイプ description -> 期待: "+" 内側、"-" 外側、"B" 両方向、"2" ２方向、"" （空文字）厚み付けしない / 実際: "+" 内側 "-" 外側 "B" 両方向 "2" ２方向 "" (空文字)厚み付けしない
- type_definition:変数単位 category -> 期待: 型定義 / 実際: (空)
- type_definition:変数単位 description -> 期待: 長さ "mm","cm","m","in","ft","pt"のいずれか、角度 "deg","rad"のいずれか、数値 ""(空白),"num"のいずれか / 実際: 長さ "mm", "cm", "m", "in", "ft", "pt"のいずれか 角度 "deg", "rad"のいずれか 数値 ""(空白), "num"のいずれか
- type_definition:平面 category -> 期待: 型定義 / 実際: (空)
- type_definition:平面 description -> 期待: "," コンマで区切られた文字列で指定。最初のカラムは必ず"PL"。例) "PL,Z" グローバルＸＹ平面、"PL,O,500.0,X" グローバルＹＺ平面をＸ方向に500移動させた平面 / 実際: "、 " コンマで区切られた文字列で指定. 最初のカラムは必ず"PL" 次のカラムが"O"の場合はその次のカラムにオフセット距離(長さ)を指定 以降は 〇 "X" グローバルＹＺ平面, "Y" グローバルＺＸ平面, "Z" グローバルＸＹ平面 〇 "F" の場合はボディのフェイスを指定 (要素の項参照) 例)"PL、 Z" グローバルＸＹ平面 "PL、 O、 500。 0、 X" グローバルＹＺ平面をＸ方向に500移動させた平面
- type_definition:形状タイプ category -> 期待: 型定義 / 実際: (空)
- type_definition:形状タイプ description -> 期待: EVO.SHIPの部材既定寸法設定ファイルで用いる形状番号。例) "1007" 平鋼、"1003" 不等辺不等厚山形鋼、"1101" 条材端部Sタイプ、"1120" 条材端部スカラップA1タイプ、"1503" ブラケット2-Bタイプ / 実際: EVO. SHIPの部材既定寸法設定ファイルで用いる形状番号 (ヘルプのEVO. SHIPの基礎→船殻設計機能→部材既定寸法設定ファイルの項を 参照) 例)"1007" 平鋼, "1003" 不等辺不等厚山形鋼 "1101" 条材端部Sタイプ, "1120" 条材端部スカラップA1タイプ "1503" ブラケット2-Bタイプ
- type_definition:形状パラメータ category -> 期待: 型定義 / 実際: (空)
- type_definition:形状パラメータ description -> 期待: 各形状タイプの寸法値を文字列配列で設定。例) 不当辺山形鋼(1002)の形状タイプの場合 ["150.","90.","9.0000000000000018","12.","6."] / 実際: 各形状タイプの寸法値を文字列配列で設定 例) 不当辺山形鋼(1002)の形状タイプの場合 ["150。 ", "90。 ", "9。 0000000000000018", "12。 ", "6。 "]
- type_definition:数値 category -> 期待: 型定義 / 実際: (空)
- type_definition:数値 description -> 期待: 数値、変数要素名,式文字列、のいずれか。例) "3", "N1", "N1*5" / 実際: 数値, 変数要素名, 式文字列, のいずれか. 例) "3", "N1", "N1*5"
- type_definition:整数 category -> 期待: 型定義 / 実際: (空)
- type_definition:文字列 category -> 期待: 型定義 / 実際: (空)
- type_definition:方向 category -> 期待: 型定義 / 実際: (空)
- type_definition:方向 description -> 期待: 各軸方向は"+X","-X","+Y","-X","+Z","-Z" で指定、または"," コンマで区切って各コンポーネントをＸ，Ｙ，Ｚ（３Ｄの場合）を数値（変数も可）で指定 / 実際: 〇 各軸方向は"+X", "-X", "+Y", "-X", "+Z", "-Z" で指定 〇 "、 " コンマで区切って各コンポーネントをＸ，Ｙ，Ｚ(３Ｄの場合)を数値(変数も可)で指定
- type_definition:材料 category -> 期待: 型定義 / 実際: (空)
- type_definition:材料 description -> 期待: EVO.SHIPに設定している材料の名称 / 実際: EVO. SHIPに設定している材料の名称
- type_definition:注記スタイル category -> 期待: 型定義 / 実際: (空)
- type_definition:注記スタイル description -> 期待: EVO.SHIPに設定している注記スタイルの名称 / 実際: EVO. SHIPに設定している注記スタイルの名称
- type_definition:浮動小数点 category -> 期待: 型定義 / 実際: (空)
- type_definition:点 category -> 期待: 型定義 / 実際: (空)
- type_definition:点 description -> 期待: "," コンマで区切って各コンポーネントをＸ，Ｙ，Ｚ（３Ｄの場合）を長さ（変数も可）で指定。例) "100.0,50,0,0.0" , "FRM1,0.0,1000.0" / 実際: モデル座標系の点を表す値を指定します。数値リテラルのほか、変数参照や式を利用できます。
- type_definition:範囲 category -> 期待: 型定義 / 実際: (空)
- type_definition:範囲 description -> 期待: 上限、下限の数値をコンマで区切って指定。例) "0.0,1.0" , "L1,L2", "-1.0,1.0" / 実際: 上限, 下限の数値をコンマで区切って指定 例) "0。 0、 1。 0", "L1、 L2", "-1。 0、 1。 0"
- type_definition:要素 category -> 期待: 型定義 / 実際: (空)
- type_definition:要素 description -> 期待: EVO.SHIPの各要素を指定する。複数要素の場合は文字列の配列とする。IDで指定する場合は"ID@"をプレフィックスとして指定。要素名で指定する場合は要素グループを"/"で区切って指定。板ソリッド要素の板厚面を指定する場合は配列で指定。ソリッドやシート要素のフェイスを指定する場合は"," コンマで区切られた文字列で指定 / 実際: モデル内の要素を参照する識別子を受け取ります。 - element_id: 既存要素を一意に識別する ID（例: ID@...）。 - element_group: 要素グループ名。複数要素をまとめて参照します。 - element_reference: 操作対象の単一要素を指すラベルや名称。 - element_array: 面リストや辺リストなど、複数要素を配列で指定するケース。
- type_definition:要素グループ category -> 期待: 型定義 / 実際: (空)
- type_definition:要素グループ description -> 期待: EVO.SHIPの要素グループ名。要素グループの階層は"/"で区切る / 実際: EVO. SHIPの要素グループ名 要素グループの階層は"/"で区切る
- type_definition:角度 category -> 期待: 型定義 / 実際: (空)
- type_definition:角度 description -> 期待: 度(°)単位の数値、変数要素名,式文字列、のいずれか。例) "30.0" , "Angle1" , "Angle1 * 0.2" / 実際: 度(°)単位の数値, 変数要素名, 式文字列, のいずれか. 例) "30。 0", "Angle1", "Angle1 * 0。 2"
- type_definition:長さ category -> 期待: 型定義 / 実際: (空)
- type_definition:長さ description -> 期待: mm単位の数値、変数要素名,式文字列、のいずれか。例) "100.0" , "L1", "L1 / 2.0" / 実際: mm単位の数値, 変数要素名, 式文字列, のいずれか. 例) "100。 0", "L1", "L1 / 2。 0"
- type_definition:関連設定 category -> 期待: 型定義 / 実際: (空)
- type_definition:関連設定 description -> 期待: ボディ関連とする場合は"B"、それ以外（空白含む）はフィーチャー関連 / 実際: ボディ関連とする場合は"B" それ以外(空白含む)はフィーチャー関連
```
