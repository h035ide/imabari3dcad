# Neo4j データベース検証レポート

**データベース名**: docparser
**検証日時**: 2025-08-24 04:25:40
**生成元**: verify_neo4j_data.py

## データベース基本情報

- **データベース名**: docparser

### ノード統計
- Parameter: 272個
- Type: 31個
- Function: 30個
- ObjectDefinition: 3個

### 関係性統計
- HAS_TYPE: 272個
- HAS_PARAMETER: 152個
- HAS_PROPERTY: 120個
- RETURNS: 30個

## 検証結果サマリー

- **node_counts**: ❌ 2/3 通過
- **function_integrity**: ✅ 30/30 通過
- **object_definition_integrity**: ✅ 3/3 通過
- **feeds_into**: ❌ 0/4 通過
- **orphan_nodes**: ✅ 1/1 通過

**全体結果**: ❌ 一部検証失敗 (36/41)

## 詳細検証結果

### Node Counts

✅ **Function count**
   - 詳細: Function count: JSON (30) vs DB (30)

✅ **ObjectDefinition count**
   - 詳細: ObjectDefinition count: JSON (3) vs DB (3)

❌ **Type count**
   - 詳細: Type count: JSON (26) vs DB (31)

### Function Integrity

✅ **CreateVariable**
   - 詳細: Function 'CreateVariable' and its parameters are consistent.

✅ **CreateSketchPlane**
   - 詳細: Function 'CreateSketchPlane' and its parameters are consistent.

✅ **CreateSketchLayer**
   - 詳細: Function 'CreateSketchLayer' and its parameters are consistent.

✅ **CreateSketchLine**
   - 詳細: Function 'CreateSketchLine' and its parameters are consistent.

✅ **CreateSketchArc**
   - 詳細: Function 'CreateSketchArc' and its parameters are consistent.

✅ **CreateSketchArc3Pts**
   - 詳細: Function 'CreateSketchArc3Pts' and its parameters are consistent.

✅ **CreateSketchCircle**
   - 詳細: Function 'CreateSketchCircle' and its parameters are consistent.

✅ **CreateSketchEllipse**
   - 詳細: Function 'CreateSketchEllipse' and its parameters are consistent.

✅ **CreateSketchNURBSCurve**
   - 詳細: Function 'CreateSketchNURBSCurve' and its parameters are consistent.

✅ **CreateElementsFromFile**
   - 詳細: Function 'CreateElementsFromFile' and its parameters are consistent.

✅ **CreateOffsetSheet**
   - 詳細: Function 'CreateOffsetSheet' and its parameters are consistent.

✅ **CreateLinearSweepParam**
   - 詳細: Function 'CreateLinearSweepParam' and its parameters are consistent.

✅ **CreateLinearSweepSheet**
   - 詳細: Function 'CreateLinearSweepSheet' and its parameters are consistent.

✅ **SheetAlignNormal**
   - 詳細: Function 'SheetAlignNormal' and its parameters are consistent.

✅ **ReverseSheet**
   - 詳細: Function 'ReverseSheet' and its parameters are consistent.

✅ **BlankElement**
   - 詳細: Function 'BlankElement' and its parameters are consistent.

✅ **TranslationCopy**
   - 詳細: Function 'TranslationCopy' and its parameters are consistent.

✅ **MirrorCopy**
   - 詳細: Function 'MirrorCopy' and its parameters are consistent.

✅ **CreateSolid**
   - 詳細: Function 'CreateSolid' and its parameters are consistent.

✅ **CreateThicken**
   - 詳細: Function 'CreateThicken' and its parameters are consistent.

✅ **CreateOtherSolid**
   - 詳細: Function 'CreateOtherSolid' and its parameters are consistent.

✅ **CreateLinearSweep**
   - 詳細: Function 'CreateLinearSweep' and its parameters are consistent.

✅ **CreateBracketParam**
   - 詳細: Function 'CreateBracketParam' and its parameters are consistent.

✅ **CreateBracket**
   - 詳細: Function 'CreateBracket' and its parameters are consistent.

✅ **CreatePlate**
   - 詳細: Function 'CreatePlate' and its parameters are consistent.

✅ **CreateProfileParam**
   - 詳細: Function 'CreateProfileParam' and its parameters are consistent.

✅ **CreateProfile**
   - 詳細: Function 'CreateProfile' and its parameters are consistent.

✅ **BodyDivideByElements**
   - 詳細: Function 'BodyDivideByElements' and its parameters are consistent.

✅ **BodySeparateBySubSolids**
   - 詳細: Function 'BodySeparateBySubSolids' and its parameters are consistent.

✅ **SetElementColor**
   - 詳細: Function 'SetElementColor' and its parameters are consistent.

### Object Definition Integrity

✅ **押し出しパラメータオブジェクト**
   - 詳細: ObjectDefinition '押し出しパラメータオブジェクト' and its properties are consistent.

✅ **ブラケット要素のパラメータオブジェクト**
   - 詳細: ObjectDefinition 'ブラケット要素のパラメータオブジェクト' and its properties are consistent.

✅ **条材要素のパラメータオブジェクト**
   - 詳細: ObjectDefinition '条材要素のパラメータオブジェクト' and its properties are consistent.

### Feeds Into

❌ **General Check**
   - 詳細: Missing FEEDS_INTO: (CreateProfileParam) -> (CreateProfile) via [条材要素のパラメータオブジェクト]

❌ **General Check**
   - 詳細: Missing FEEDS_INTO: (CreateBracketParam) -> (CreateBracket) via [ブラケット要素のパラメータオブジェクト]

❌ **General Check**
   - 詳細: Missing FEEDS_INTO: (CreateLinearSweepParam) -> (CreateLinearSweep) via [押し出しパラメータオブジェクト]

❌ **General Check**
   - 詳細: Missing FEEDS_INTO: (CreateLinearSweepParam) -> (CreateLinearSweepSheet) via [押し出しパラメータオブジェクト]

### Orphan Nodes

✅ **General Check**
   - 詳細: No orphan nodes found.

## 推奨事項

❌ 一部の検証が失敗しました。以下の点を確認してください：

### Node Counts
- Type count: JSON (26) vs DB (31)

### Feeds Into
- Missing FEEDS_INTO: (CreateProfileParam) -> (CreateProfile) via [条材要素のパラメータオブジェクト]
- Missing FEEDS_INTO: (CreateBracketParam) -> (CreateBracket) via [ブラケット要素のパラメータオブジェクト]
- Missing FEEDS_INTO: (CreateLinearSweepParam) -> (CreateLinearSweep) via [押し出しパラメータオブジェクト]
- Missing FEEDS_INTO: (CreateLinearSweepParam) -> (CreateLinearSweepSheet) via [押し出しパラメータオブジェクト]


---
*このレポートは 2025-08-24 04:25:40 に自動生成されました。*
