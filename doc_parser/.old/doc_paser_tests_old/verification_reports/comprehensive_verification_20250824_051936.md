# 包括的検証レポート

**生成日時**: 2025-08-24 05:19:36
**対象データベース**: docparser

## データベース概要


## 統計情報

- **総関数数**: 30
- **総オブジェクト数**: 3
- **総パラメータ数**: 152
- **パラメータを持つ関数**: 27
- **パラメータのない関数**: 3
- **プロパティを持つオブジェクト**: 3
- **プロパティのないオブジェクト**: 0

### パラメータ型の分布

- **bool**: 42個
- **要素**: 33個
- **長さ**: 28個
- **文字列**: 21個
- **要素(配列)**: 21個
- **形状パラメータ**: 15個
- **形状タイプ**: 15個
- **方向**: 13個
- **点**: 13個
- **整数**: 10個
- **関連設定**: 9個
- **要素グループ**: 9個
- **材料**: 6個
- **浮動小数点**: 5個
- **角度**: 5個
- **平面**: 4個
- **オペレーションタイプ**: 3個
- **モールド位置**: 3個
- **未指定**: 3個
- **押し出しパラメータオブジェクト**: 2個
- **範囲**: 2個
- **浮動小数点(配列)**: 2個
- **厚み付けタイプ**: 2個
- **ブラケット要素のパラメータオブジェクト**: 1個
- **条材要素のパラメータオブジェクト**: 1個
- **点(配列)**: 1個
- **注記スタイル**: 1個
- **変数単位**: 1個
- **スイープ方向**: 1個

### 戻り値型の分布

- **要素**: 24個
- **void**: 3個
- **ブラケット要素のパラメータオブジェクト**: 1個
- **押し出しパラメータオブジェクト**: 1個
- **条材要素のパラメータオブジェクト**: 1個

## 関数一覧

### BlankElement

**説明**: 指定要素の表示状態を設定する。返り値はなし。
**戻り値の型**: void
**戻り値の説明**: None

**パラメータ**:

- **Element** (位置: 0, 型: 要素)
  - 説明: 表示状態を指定する要素
  - オブジェクト定義: いいえ

- **bBlank** (位置: 1, 型: bool)
  - 説明: True の時は非表示にする。False の時は表示する。
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.BlankElement(
    Element,
    bBlank
)
```

### BodyDivideByElements

**説明**: ボディを指定した要素で分割する。返り値は分割で作成されたボディ要素のID配列。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **pDriveFeatureName** (位置: 0, 型: 文字列)
  - 説明: 作成する分割フィーチャー要素名称（空文字可）
  - オブジェクト定義: いいえ

- **pTargetBody** (位置: 1, 型: 要素)
  - 説明: 分割対象のボディ
  - オブジェクト定義: いいえ

- **pDivideElements** (位置: 2, 型: 要素(配列))
  - 説明: 分割をする要素（シートボディ、フェイス、平面要素）
  - オブジェクト定義: いいえ

- **pAlignmentDirection** (位置: 3, 型: 方向)
  - 説明: 分割されたボディ要素の順番を整列させるのに使用する方向
  - オブジェクト定義: いいえ

- **pWCS** (位置: 4, 型: 要素)
  - 説明: 方向を定義する座標系（通常は指定しない）
  - オブジェクト定義: いいえ

- **ReferMethod** (位置: 5, 型: 関連設定)
  - 説明: 要素の関連づけ方法の指定
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 6, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.BodyDivideByElements(
    pDriveFeatureName,
    pTargetBody,
    pDivideElements,
    pAlignmentDirection,
    pWCS,
    ReferMethod,
    bUpdate
)
```

### BodySeparateBySubSolids

**説明**: 指定したソリッドで削除することでボディを分割する（ボディの区分けコマンド）。返り値は分割で作成されたボディ要素のID配列。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **pSeparateFeatureName** (位置: 0, 型: 文字列)
  - 説明: 作成する分割フィーチャー要素名称（空文字可）
  - オブジェクト定義: いいえ

- **pTargetBody** (位置: 1, 型: 要素)
  - 説明: 分割対象のボディ
  - オブジェクト定義: いいえ

- **pSubSolids** (位置: 2, 型: 要素(配列))
  - 説明: 分割をするソリッド要素（配列）
  - オブジェクト定義: いいえ

- **pAlignmentDirection** (位置: 3, 型: 方向)
  - 説明: 分割されたボディ要素の順番を整列させるのに使用する方向
  - オブジェクト定義: いいえ

- **ReferMethod** (位置: 4, 型: 関連設定)
  - 説明: 要素の関連づけ方法の指定
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 5, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.BodySeparateBySubSolids(
    pSeparateFeatureName,
    pTargetBody,
    pSubSolids,
    pAlignmentDirection,
    ReferMethod,
    bUpdate
)
```

### CreateBracket

**説明**: ブラケットソリッド要素を作成する。返り値は作成したソリッド要素のID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **ParamObj** (位置: 0, 型: ブラケット要素のパラメータオブジェクト)
  - 説明: ブラケットパラメータオブジェクト
  - オブジェクト定義: はい

- **bUpdate** (位置: 1, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateBracket(
    ParamObj,
    bUpdate
)
```

### CreateBracketParam

**説明**: 船殻のブラケット要素のパラメータオブジェクトを作成して返す。
**戻り値の型**: ブラケット要素のパラメータオブジェクト
**戻り値の説明**: None

**パラメータ**: なし

**コード生成サンプル**:

```python
part.CreateBracketParam()
```

### CreateElementsFromFile

**説明**: ファイルをインポートして要素を作成する（現状 Parasolid 形式のみ）。返り値は作成された要素の要素IDの配列。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **FileName** (位置: 0, 型: 文字列)
  - 説明: ファイルパス（現状、Parasolid形式のみ）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateElementsFromFile(
    FileName
)
```

### CreateLinearSweep

**説明**: 指定したソリッド要素に押し出し形状を付加する。返り値は作成された押し出しフィーチャーのID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **TargetSolidName** (位置: 0, 型: 要素)
  - 説明: 押し出しフィーチャーを作成する対象のソリッド
  - オブジェクト定義: いいえ

- **OperationType** (位置: 1, 型: オペレーションタイプ)
  - 説明: ソリッドオペレーションのタイプを指定する
  - オブジェクト定義: いいえ

- **pParam** (位置: 2, 型: 押し出しパラメータオブジェクト)
  - 説明: 押し出しパラメータオブジェクト
  - オブジェクト定義: はい

- **bUpdate** (位置: 3, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateLinearSweep(
    TargetSolidName,
    OperationType,
    pParam,
    bUpdate
)
```

### CreateLinearSweepParam

**説明**: 押し出し（リニアスイープ）用のパラメータオブジェクトを作成して返す。
**戻り値の型**: 押し出しパラメータオブジェクト
**戻り値の説明**: None

**パラメータ**: なし

**コード生成サンプル**:

```python
part.CreateLinearSweepParam()
```

### CreateLinearSweepSheet

**説明**: プロファイル要素を押し出してシート要素を作成する。返り値は作成されたシート要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **ParamObj** (位置: 0, 型: 押し出しパラメータオブジェクト)
  - 説明: 押し出しパラメータオブジェクト
  - オブジェクト定義: はい

- **bUpdate** (位置: 1, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateLinearSweepSheet(
    ParamObj,
    bUpdate
)
```

### CreateOffsetSheet

**説明**: オフセットシートを作成する。返り値は作成されたオフセットシート要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SheetName** (位置: 0, 型: 文字列)
  - 説明: 作成するシート要素名称（空文字可）
  - オブジェクト定義: いいえ

- **ElementGroup** (位置: 1, 型: 要素グループ)
  - 説明: 作成するシート要素を要素グループに入れる場合は要素グループを指定（空文字可）
  - オブジェクト定義: いいえ

- **MaterialName** (位置: 2, 型: 材料)
  - 説明: 作成するシート要素の材質名称（空文字可）
  - オブジェクト定義: いいえ

- **SrcSurfaces** (位置: 3, 型: 要素(配列))
  - 説明: オフセットする元シート要素、フェイス要素の指定文字列配列
  - オブジェクト定義: いいえ

- **OffsetLength** (位置: 4, 型: 長さ)
  - 説明: オフセット距離
  - オブジェクト定義: いいえ

- **bOffsetBackwards** (位置: 5, 型: bool)
  - 説明: オフセット方向を反転するフラグ
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 6, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateOffsetSheet(
    SheetName,
    ElementGroup,
    MaterialName,
    SrcSurfaces,
    OffsetLength,
    bOffsetBackwards,
    bUpdate
)
```

### CreateOtherSolid

**説明**: 指定したソリッド要素に別のソリッド要素形状を付加する。返り値は作成された別ソリッドフィーチャーのID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **OtherSolidFeatureName** (位置: 0, 型: 文字列)
  - 説明: 作成する別ソリッドフィーチャー要素名称（空文字可）
  - オブジェクト定義: いいえ

- **TargetSolidName** (位置: 1, 型: 要素)
  - 説明: 別ソリッドフィーチャーを作成する対象のソリッド
  - オブジェクト定義: いいえ

- **OperationType** (位置: 2, 型: オペレーションタイプ)
  - 説明: ソリッドオペレーションのタイプを指定する
  - オブジェクト定義: いいえ

- **SourceSolid** (位置: 3, 型: 要素)
  - 説明: 別ソリッドフィーチャーとするソリッド要素
  - オブジェクト定義: いいえ

- **ReferMethod** (位置: 4, 型: 関連設定)
  - 説明: 要素の関連づけ方法の指定
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 5, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateOtherSolid(
    OtherSolidFeatureName,
    TargetSolidName,
    OperationType,
    SourceSolid,
    ReferMethod,
    bUpdate
)
```

### CreatePlate

**説明**: プレートソリッド要素を作成する。返り値は作成したソリッド要素のID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **PlateName** (位置: 0, 型: 文字列)
  - 説明: 作成するプレートソリッド要素名称（空文字可）
  - オブジェクト定義: いいえ

- **ElementGroup** (位置: 1, 型: 要素グループ)
  - 説明: 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
  - オブジェクト定義: いいえ

- **MaterialName** (位置: 2, 型: 材料)
  - 説明: 作成するソリッド要素の材質名称（空文字可）
  - オブジェクト定義: いいえ

- **Plane** (位置: 3, 型: 平面)
  - 説明: プレートの平面位置
  - オブジェクト定義: いいえ

- **PlaneOffset** (位置: 4, 型: 長さ)
  - 説明: 平面のオフセット距離
  - オブジェクト定義: いいえ

- **Thickness** (位置: 5, 型: 長さ)
  - 説明: 板厚
  - オブジェクト定義: いいえ

- **nMold** (位置: 6, 型: モールド位置)
  - 説明: モールド位置
  - オブジェクト定義: いいえ

- **MoldOffset** (位置: 7, 型: 長さ)
  - 説明: モールド位置のオフセット距離
  - オブジェクト定義: いいえ

- **BoundSolid** (位置: 8, 型: 要素)
  - 説明: プレートソリッドの境界となるソリッド要素
  - オブジェクト定義: いいえ

- **Section1End1** (位置: 9, 型: 長さ)
  - 説明: 平面上の方向1の境界位置の座標値1
  - オブジェクト定義: いいえ

- **Section1End2** (位置: 10, 型: 長さ)
  - 説明: 平面上の方向1の境界位置の座標値2
  - オブジェクト定義: いいえ

- **Section2End1** (位置: 11, 型: 長さ)
  - 説明: 平面上の方向2の境界位置の座標値1
  - オブジェクト定義: いいえ

- **Section2End2** (位置: 12, 型: 長さ)
  - 説明: 平面上の方向2の境界位置の座標値2
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 13, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreatePlate(
    PlateName,
    ElementGroup,
    MaterialName,
    Plane,
    PlaneOffset,
    Thickness,
    nMold,
    MoldOffset,
    BoundSolid,
    Section1End1,
    Section1End2,
    Section2End1,
    Section2End2,
    bUpdate
)
```

### CreateProfile

**説明**: 条材ソリッド要素を作成する（取付線指定等）。返り値は作成した条材ソリッド要素のID配列（配列内に Web 要素やフランジ要素を含む）。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **ParamObj** (位置: 0, 型: 条材要素のパラメータオブジェクト)
  - 説明: 条材要素のパラメータオブジェクト
  - オブジェクト定義: はい

- **bUpdate** (位置: 1, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateProfile(
    ParamObj,
    bUpdate
)
```

### CreateProfileParam

**説明**: 船殻の条材ソリッド要素のパラメータオブジェクトを作成して返す。
**戻り値の型**: 条材要素のパラメータオブジェクト
**戻り値の説明**: None

**パラメータ**: なし

**コード生成サンプル**:

```python
part.CreateProfileParam()
```

### CreateSketchArc

**説明**: 中心点と始終点を指定してスケッチ円弧を作成する。返り値は作成されたスケッチ円弧要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SketchPlane** (位置: 0, 型: 要素)
  - 説明: 円弧を作成するスケッチ要素
  - オブジェクト定義: いいえ

- **SketchArcName** (位置: 1, 型: 文字列)
  - 説明: 作成するスケッチ円弧名称（空文字可）
  - オブジェクト定義: いいえ

- **SketchLayer** (位置: 2, 型: 要素)
  - 説明: 円弧を作成するスケッチレイヤー（空文字可）
  - オブジェクト定義: いいえ

- **CenterPoint** (位置: 3, 型: 点)
  - 説明: 中心点（点(2D)）
  - オブジェクト定義: いいえ

- **StartPoint** (位置: 4, 型: 点)
  - 説明: 始点（点(2D)）
  - オブジェクト定義: いいえ

- **EndPoint** (位置: 5, 型: 点)
  - 説明: 終点（点(2D)）
  - オブジェクト定義: いいえ

- **bCCW** (位置: 6, 型: bool)
  - 説明: 円弧の回転方向。True の場合は反時計回り
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 7, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateSketchArc(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    CenterPoint,
    StartPoint,
    EndPoint,
    bCCW,
    bUpdate
)
```

### CreateSketchArc3Pts

**説明**: 周上の3点を指定してスケッチ円弧を作成する。返り値は作成されたスケッチ円弧要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SketchPlane** (位置: 0, 型: 要素)
  - 説明: 円弧を作成するスケッチ要素
  - オブジェクト定義: いいえ

- **SketchArcName** (位置: 1, 型: 文字列)
  - 説明: 作成するスケッチ円弧名称（空文字可）
  - オブジェクト定義: いいえ

- **SketchLayer** (位置: 2, 型: 要素)
  - 説明: 円弧を作成するスケッチレイヤー（空文字可）
  - オブジェクト定義: いいえ

- **StartPoint** (位置: 3, 型: 点)
  - 説明: 始点（点(2D)）
  - オブジェクト定義: いいえ

- **MidPoint** (位置: 4, 型: 点)
  - 説明: 通過点（点(2D)）
  - オブジェクト定義: いいえ

- **EndPoint** (位置: 5, 型: 点)
  - 説明: 終点（点(2D)）
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 6, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateSketchArc3Pts(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    StartPoint,
    MidPoint,
    EndPoint,
    bUpdate
)
```

### CreateSketchCircle

**説明**: 中心点と半径/直径を指定してスケッチ円を作成する。返り値は作成されたスケッチ円要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SketchPlane** (位置: 0, 型: 要素)
  - 説明: 円を作成するスケッチ要素
  - オブジェクト定義: いいえ

- **SketchArcName** (位置: 1, 型: 文字列)
  - 説明: 作成するスケッチ円名称（空文字可）
  - オブジェクト定義: いいえ

- **SketchLayer** (位置: 2, 型: 要素)
  - 説明: 円を作成するスケッチレイヤー（空文字可）
  - オブジェクト定義: いいえ

- **Centeroint** (位置: 3, 型: 点)
  - 説明: 中心点（点(2D)）
  - オブジェクト定義: いいえ

- **RadiusOrDiameter** (位置: 4, 型: 長さ)
  - 説明: 半径または直径（長さ）
  - オブジェクト定義: いいえ

- **bDiameter** (位置: 5, 型: bool)
  - 説明: 直径を指定する場合は True
  - オブジェクト定義: いいえ

- **bCCW** (位置: 6, 型: bool)
  - 説明: 円の回転方向。True の場合は反時計回り
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 7, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateSketchCircle(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    Centeroint,
    RadiusOrDiameter,
    bDiameter,
    bCCW,
    bUpdate
)
```

### CreateSketchEllipse

**説明**: 中心点と主軸等を指定してスケッチ楕円を作成する。返り値は作成されたスケッチ楕円要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SketchPlane** (位置: 0, 型: 要素)
  - 説明: 楕円を作成するスケッチ要素
  - オブジェクト定義: いいえ

- **SketchArcName** (位置: 1, 型: 文字列)
  - 説明: 作成するスケッチ楕円名称（空文字可）
  - オブジェクト定義: いいえ

- **SketchLayer** (位置: 2, 型: 要素)
  - 説明: 楕円を作成するスケッチレイヤー（空文字可）
  - オブジェクト定義: いいえ

- **Centeroint** (位置: 3, 型: 点)
  - 説明: 中心点（点(2D)）
  - オブジェクト定義: いいえ

- **bCCW** (位置: 4, 型: bool)
  - 説明: 楕円の回転方向。True の場合は反時計回り
  - オブジェクト定義: いいえ

- **MajorDir** (位置: 5, 型: 方向)
  - 説明: 主軸方向を指定（方向(2D)）
  - オブジェクト定義: いいえ

- **MajorRadius** (位置: 6, 型: 長さ)
  - 説明: 主軸半径
  - オブジェクト定義: いいえ

- **MinorRadius** (位置: 7, 型: 長さ)
  - 説明: 副軸半径
  - オブジェクト定義: いいえ

- **Range** (位置: 8, 型: 範囲)
  - 説明: 楕円の範囲（0-2pi等）
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 9, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateSketchEllipse(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    Centeroint,
    bCCW,
    MajorDir,
    MajorRadius,
    MinorRadius,
    Range,
    bUpdate
)
```

### CreateSketchLayer

**説明**: スケッチレイヤーを作成する。返り値は作成されたスケッチレイヤー要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SketchLayerName** (位置: 0, 型: 文字列)
  - 説明: 作成するスケッチレイヤー名称（空文字可）
  - オブジェクト定義: いいえ

- **SketchPlane** (位置: 1, 型: 要素)
  - 説明: レイヤーを作成するスケッチ要素
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateSketchLayer(
    SketchLayerName,
    SketchPlane
)
```

### CreateSketchLine

**説明**: スケッチ直線を作成する。返り値は作成されたスケッチ直線要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SketchPlane** (位置: 0, 型: 要素)
  - 説明: 直線を作成するスケッチ要素
  - オブジェクト定義: いいえ

- **SketchLineName** (位置: 1, 型: 文字列)
  - 説明: 作成するスケッチ直線名称（空文字可）
  - オブジェクト定義: いいえ

- **SketchLayer** (位置: 2, 型: 要素)
  - 説明: 直線を作成するスケッチレイヤー（空文字可）
  - オブジェクト定義: いいえ

- **StartPoint** (位置: 3, 型: 点)
  - 説明: 始点（点(2D)）
  - オブジェクト定義: いいえ

- **EndPoint** (位置: 4, 型: 点)
  - 説明: 終点（点(2D)）
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 5, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateSketchLine(
    SketchPlane,
    SketchLineName,
    SketchLayer,
    StartPoint,
    EndPoint,
    bUpdate
)
```

### CreateSketchNURBSCurve

**説明**: NURBS曲線を作成する。返り値は作成された要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SketchPlane** (位置: 0, 型: 要素)
  - 説明: ＮＵＲＢＳ線を作成するスケッチ要素
  - オブジェクト定義: いいえ

- **SketchArcName** (位置: 1, 型: 文字列)
  - 説明: 作成するスケッチＮＵＲＢＳ線名称（空文字可）
  - オブジェクト定義: いいえ

- **SketchLayer** (位置: 2, 型: 要素)
  - 説明: ＮＵＲＢＳ線を作成するスケッチレイヤー（空文字可）
  - オブジェクト定義: いいえ

- **nDegree** (位置: 3, 型: 整数)
  - 説明: ＮＵＲＢＳ線の次数
  - オブジェクト定義: いいえ

- **bClose** (位置: 4, 型: bool)
  - 説明: 閉じたＮＵＲＢＳ線の場合 True
  - オブジェクト定義: いいえ

- **bPeriodic** (位置: 5, 型: bool)
  - 説明: 周期ＮＵＲＢＳ線の場合 True
  - オブジェクト定義: いいえ

- **CtrlPoints** (位置: 6, 型: 点(配列))
  - 説明: 制御点（点の配列）
  - オブジェクト定義: いいえ

- **Weights** (位置: 7, 型: 浮動小数点(配列))
  - 説明: 重み（浮動小数点の配列）
  - オブジェクト定義: いいえ

- **Knots** (位置: 8, 型: 浮動小数点(配列))
  - 説明: ノットベクトル（浮動小数点の配列）
  - オブジェクト定義: いいえ

- **Range** (位置: 9, 型: 範囲)
  - 説明: トリム範囲
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 10, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateSketchNURBSCurve(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    nDegree,
    bClose,
    bPeriodic,
    CtrlPoints,
    Weights,
    Knots,
    Range,
    bUpdate
)
```

### CreateSketchPlane

**説明**: スケッチ平面を作成する。返り値は作成されたスケッチ平面要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **ElementName** (位置: 0, 型: 文字列)
  - 説明: 作成するスケッチ平面名称（空文字可）
  - オブジェクト定義: いいえ

- **ElementGroup** (位置: 1, 型: 要素グループ)
  - 説明: 作成するスケッチ平面を要素グループに入れる場合は要素グループを指定（空文字可）
  - オブジェクト定義: いいえ

- **PlaneDef** (位置: 2, 型: 平面)
  - 説明: スケッチ平面を作成する平面を指定する
  - オブジェクト定義: いいえ

- **PlaneOffset** (位置: 3, 型: 長さ)
  - 説明: 平面からのオフセット距離を指定
  - オブジェクト定義: いいえ

- **bRevPlane** (位置: 4, 型: bool)
  - 説明: スケッチ平面を反転するかどうかのフラグ
  - オブジェクト定義: いいえ

- **bRevUV** (位置: 5, 型: bool)
  - 説明: スケッチ平面のX,Y軸を交換するかどうかのフラグ
  - オブジェクト定義: いいえ

- **謎** (位置: 6, 型: bool)
  - 説明: ドキュメント上の名称が "謎" とされているパラメータ（型は bool と記載）。詳細不明
  - オブジェクト定義: いいえ

- **StyleName** (位置: 7, 型: 注記スタイル)
  - 説明: スケッチ平面に適用する注記スタイル名称（空文字可）
  - オブジェクト定義: いいえ

- **OriginPoint** (位置: 8, 型: 点)
  - 説明: スケッチ平面の原点を指定（空文字可）
  - オブジェクト定義: いいえ

- **AxisDirection** (位置: 9, 型: 方向)
  - 説明: スケッチ平面の軸方向を指定（空文字可）
  - オブジェクト定義: いいえ

- **bDefAxisIsX** (位置: 10, 型: bool)
  - 説明: スケッチ平面のX軸を指定する場合は True
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 11, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateSketchPlane(
    ElementName,
    ElementGroup,
    PlaneDef,
    PlaneOffset,
    bRevPlane,
    bRevUV,
    謎,
    StyleName,
    OriginPoint,
    AxisDirection,
    bDefAxisIsX,
    bUpdate
)
```

### CreateSolid

**説明**: 空のソリッド要素を作成する。返り値は作成されたソリッドの要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SolidName** (位置: 0, 型: 文字列)
  - 説明: 作成するソリッド要素名称（空文字可）
  - オブジェクト定義: いいえ

- **ElementGroup** (位置: 1, 型: 要素グループ)
  - 説明: 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
  - オブジェクト定義: いいえ

- **MaterialName** (位置: 2, 型: 材料)
  - 説明: 作成するソリッド要素の材質名称（空文字可）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateSolid(
    SolidName,
    ElementGroup,
    MaterialName
)
```

### CreateThicken

**説明**: 指定したソリッド要素に指定要素厚みづけした形状を作成する。返り値は作成された厚みづけフィーチャーのID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **ThickenFeatureName** (位置: 0, 型: 文字列)
  - 説明: 作成する厚みづけフィーチャー要素名称（空文字可）
  - オブジェクト定義: いいえ

- **TargetSolidName** (位置: 1, 型: 要素)
  - 説明: 厚みづけフィーチャーを作成する対象のソリッド
  - オブジェクト定義: いいえ

- **OperationType** (位置: 2, 型: オペレーションタイプ)
  - 説明: ソリッドオペレーションのタイプを指定（ボディ演算の記号）
  - オブジェクト定義: いいえ

- **Sheet** (位置: 3, 型: 要素(配列))
  - 説明: 厚み付けをするシートやフェイス（配列）
  - オブジェクト定義: いいえ

- **ThickenType** (位置: 4, 型: 厚み付けタイプ)
  - 説明: 厚み付けタイプ
  - オブジェクト定義: いいえ

- **Thickeness1** (位置: 5, 型: 長さ)
  - 説明: 板厚（厚み1）
  - オブジェクト定義: いいえ

- **Thickeness2** (位置: 6, 型: 長さ)
  - 説明: 板厚2（厚み付けタイプが2方向のときに使用）
  - オブジェクト定義: いいえ

- **ThickenessOffset** (位置: 7, 型: 長さ)
  - 説明: 厚みづけをするシート、フェイス要素のオフセット距離
  - オブジェクト定義: いいえ

- **ReferMethod** (位置: 8, 型: 関連設定)
  - 説明: 要素の関連づけ方法の指定
  - オブジェクト定義: いいえ

- **bUpdate** (位置: 9, 型: bool)
  - 説明: 更新フラグ（未実装、使用しない）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateThicken(
    ThickenFeatureName,
    TargetSolidName,
    OperationType,
    Sheet,
    ThickenType,
    Thickeness1,
    Thickeness2,
    ThickenessOffset,
    ReferMethod,
    bUpdate
)
```

### CreateVariable

**説明**: 変数要素を作成する。返り値は作成された変数要素の要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **VariableName** (位置: 0, 型: 文字列)
  - 説明: 作成する変数名称（空文字不可）
  - オブジェクト定義: いいえ

- **VariableValue** (位置: 1, 型: 浮動小数点)
  - 説明: 変数の値
  - オブジェクト定義: いいえ

- **VariableUnit** (位置: 2, 型: 変数単位)
  - 説明: 作成する変数の単位を指定
  - オブジェクト定義: いいえ

- **VariableElementGroup** (位置: 3, 型: 要素グループ)
  - 説明: 作成する変数要素を要素グループに入れる場合は要素グループを指定（空文字可）
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.CreateVariable(
    VariableName,
    VariableValue,
    VariableUnit,
    VariableElementGroup
)
```

### MirrorCopy

**説明**: 指定要素をミラーコピーする。返り値はコピーされた要素ID配列。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SrcElements** (位置: 0, 型: 要素(配列))
  - 説明: コピーする要素（配列）
  - オブジェクト定義: いいえ

- **plane** (位置: 1, 型: 平面)
  - 説明: ミラーコピーを行う平面（ドキュメントは "[in] BSTR plane" と記載）
  - オブジェクト定義: いいえ

- **ReferMethod** (位置: 2, 型: 関連設定)
  - 説明: 要素の関連づけ方法の指定
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.MirrorCopy(
    SrcElements,
    plane,
    ReferMethod
)
```

### ReverseSheet

**説明**: シート要素の向きを反転する。返り値はシート反転フィーチャーの要素ID。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SheetElement** (位置: 0, 型: 要素)
  - 説明: 反転するシート要素
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.ReverseSheet(
    SheetElement
)
```

### SetElementColor

**説明**: 指定要素の色を設定する。ドキュメントでは返り値の明記がない（属性設定関数であるため戻り値無しと解釈される）。
**戻り値の型**: void
**戻り値の説明**: None

**パラメータ**:

- **Element** (位置: 0, 型: 要素)
  - 説明: 色を設定する要素
  - オブジェクト定義: いいえ

- **RValue** (位置: 1, 型: 整数)
  - 説明: 赤色の値 (0-255)
  - オブジェクト定義: いいえ

- **GValue** (位置: 2, 型: 整数)
  - 説明: 緑色の値 (0-255)
  - オブジェクト定義: いいえ

- **BValue** (位置: 3, 型: 整数)
  - 説明: 青色の値 (0-255)
  - オブジェクト定義: いいえ

- **Transparency** (位置: 4, 型: 浮動小数点)
  - 説明: 透明度の指定 (0.0 = 不透明, 1.0 = 完全透明 として記載されているがドキュメントでは 0.0不透明-1.0透明 と表記)
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.SetElementColor(
    Element,
    RValue,
    GValue,
    BValue,
    Transparency
)
```

### SheetAlignNormal

**説明**: シート要素の向き（表側、法線方向）を指定した方向に揃える。返り値はなし。
**戻り値の型**: void
**戻り値の説明**: None

**パラメータ**:

- **SheetElement** (位置: 0, 型: 要素)
  - 説明: 方向を揃えるシート要素
  - オブジェクト定義: いいえ

- **dirX** (位置: 1, 型: 浮動小数点)
  - 説明: 方向ベクトルのX成分
  - オブジェクト定義: いいえ

- **dirY** (位置: 2, 型: 浮動小数点)
  - 説明: 方向ベクトルのY成分
  - オブジェクト定義: いいえ

- **dirZ** (位置: 3, 型: 浮動小数点)
  - 説明: 方向ベクトルのZ成分
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.SheetAlignNormal(
    SheetElement,
    dirX,
    dirY,
    dirZ
)
```

### TranslationCopy

**説明**: 指定要素を移動コピーする。返り値はコピーされた要素ID配列。
**戻り値の型**: 要素
**戻り値の説明**: EVO.SHIP の要素を指定する文字列。単一要素は文字列、複数要素は文字列配列で指定する。IDで指定する場合は "ID@<GUID>" の形式を用いる（例: "ID@d8baafc30be94411a6ab9d6173c1d1dd"）。要素名称や要素グループパスも指定可能（例: "G1/G2/A"）。板ソリッドの板厚面指定など特殊な配列形式（先頭が "PLS" など）や、ソリッド/シート要素のフェイス指定文字列（"ID@...,F,x1,y1,z1,x2,y2,z2"）など、ドキュメントに記載された複数の表現がある。

**パラメータ**:

- **SrcElements** (位置: 0, 型: 要素(配列))
  - 説明: コピーする要素（配列）
  - オブジェクト定義: いいえ

- **nCopy** (位置: 1, 型: 整数)
  - 説明: コピーする数
  - オブジェクト定義: いいえ

- **direction** (位置: 2, 型: 方向)
  - 説明: コピーする方向
  - オブジェクト定義: いいえ

- **distance** (位置: 3, 型: 長さ)
  - 説明: 移動距離
  - オブジェクト定義: いいえ

- **ReferMethod** (位置: 4, 型: 関連設定)
  - 説明: 要素の関連づけ方法の指定
  - オブジェクト定義: いいえ

**コード生成サンプル**:

```python
part.TranslationCopy(
    SrcElements,
    nCopy,
    direction,
    distance,
    ReferMethod
)
```

## オブジェクト定義一覧

### ブラケット要素のパラメータオブジェクト

**説明**: ブラケット要素を作成する際に用いるパラメータオブジェクト。ブラケット形状、材質、基準面、フランジ／スカラップ等多数の設定を含む。

**プロパティ**:

- **BaseElement** (型: 要素, 任意)
  - 説明: 基準要素指定の場合の基準要素

- **BasePlane** (型: 平面, 任意)
  - 説明: 面指定の場合の基準平面

- **BasePlaneOffset** (型: 長さ, 任意)
  - 説明: 基準平面のオフセット距離

- **BracketName** (型: 文字列, 任意)
  - 説明: 作成するブラケットソリッド要素名称（空文字可）

- **BracketParams** (型: 形状パラメータ, 任意)
  - 説明: ブラケットの形状タイプのパラメータ

- **BracketType** (型: 形状タイプ, 任意)
  - 説明: ブラケットの形状タイプ

- **DefinitionType** (型: 整数, 任意)
  - 説明: ブラケットの作成方法指定。0: 面指定、1: 基準要素指定

- **ElementGroup** (型: 要素グループ, 任意)
  - 説明: 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）

- **FlangeAngle** (型: 角度, 任意)
  - 説明: フランジの角度指定（0°は直角を意味し、そこからの増分を＋/－で指定）

- **FlangeParams** (型: 形状パラメータ, 任意)
  - 説明: ブラケットのフランジの形状タイプのパラメータ

- **FlangeType** (型: 形状タイプ, 任意)
  - 説明: ブラケットのフランジの形状タイプ（0 の場合はフランジを付けない）

- **MaterialName** (型: 材料, 任意)
  - 説明: 作成するソリッド要素の材質名称（空文字可）

- **Mold** (型: モールド位置, 任意)
  - 説明: モールド位置

- **MoldOffset** (型: 長さ, 任意)
  - 説明: モールド位置のオフセット距離

- **ReferMethod** (型: 関連設定, 任意)
  - 説明: 要素の関連づけ方法の指定

- **RevFlange** (型: bool, 任意)
  - 説明: フランジの向きを反転する場合は True

- **RevSf1** (型: bool, 任意)
  - 説明: 面1の反対側にブラケットを作成する場合は True

- **RevSf2** (型: bool, 任意)
  - 説明: 面2の反対側にブラケットを作成する場合は True

- **RevSf3** (型: bool, 任意)
  - 説明: 面3の反対側にブラケットを作成する場合は True

- **Scallop1Params** (型: 形状パラメータ, 任意)
  - 説明: ブラケットのスカラップ1の形状タイプのパラメータ

- **Scallop1Type** (型: 形状タイプ, 任意)
  - 説明: ブラケットのスカラップ1の形状タイプ

- **Scallop2Params** (型: 形状パラメータ, 任意)
  - 説明: ブラケットのスカラップ2の形状タイプのパラメータ

- **ScallopEnd1LowerParams** (型: 形状パラメータ, 任意)
  - 説明: 面1方向の下側端部のスカラップのパラメータ

- **ScallopEnd1LowerType** (型: 形状タイプ, 任意)
  - 説明: 面1方向の下側端部のスカラップのタイプ

- **ScallopEnd1UpperParams** (型: 形状パラメータ, 任意)
  - 説明: 面1方向の上側端部のスカラップのパラメータ

- **ScallopEnd1UpperType** (型: 形状タイプ, 任意)
  - 説明: 面1方向の上側端部のスカラップのタイプ

- **ScallopEnd2LowerParams** (型: 形状パラメータ, 任意)
  - 説明: 面2方向の下側端部のスカラップのパラメータ

- **ScallopEnd2LowerType** (型: 形状タイプ, 任意)
  - 説明: 面2方向の下側端部のスカラップのタイプ

- **ScallopEnd2UpperParams** (型: 形状パラメータ, 任意)
  - 説明: 面2方向の上側端部のスカラップのパラメータ

- **ScallopEnd2UpperType** (型: 形状タイプ, 任意)
  - 説明: 面2方向の上側端部のスカラップのタイプ

- **Sf1BaseElements** (型: 要素(配列), 任意)
  - 説明: 面1方向の基準要素（必要な形状タイプの場合）

- **Sf1DimensionType** (型: 形状タイプ, 任意)
  - 説明: 面1方向の寸法タイプ

- **Sf1DimensonParams** (型: 形状パラメータ, 任意)
  - 説明: 面1方向の寸法タイプのパラメータ

- **Sf1EndElements** (型: 要素(配列), 任意)
  - 説明: 面1方向の端部要素（必要な形状タイプの場合）

- **Sf2BaseElements** (型: 要素(配列), 任意)
  - 説明: 面2方向の基準要素（必要な形状タイプの場合）

- **Sf2DimensionType** (型: 形状タイプ, 任意)
  - 説明: 面2方向の寸法タイプ

- **Sf2DimensonParams** (型: 形状パラメータ, 任意)
  - 説明: 面2方向の寸法タイプのパラメータ

- **Sf2EndElements** (型: 要素(配列), 任意)
  - 説明: 面2方向の端部要素（必要な形状タイプの場合）

- **Surfaces1** (型: 要素(配列), 任意)
  - 説明: ブラケット作成する面1の要素（ソリッド、シート、フェイス）

- **Surfaces2** (型: 要素(配列), 任意)
  - 説明: ブラケット作成する面2の要素（ソリッド、シート、フェイス）

- **Surfaces3** (型: 要素(配列), 任意)
  - 説明: 3面ブラケット作成する場合の面3の要素（ソリッド、シート、フェイス）

- **Thickness** (型: 長さ, 任意)
  - 説明: 板厚

- **UseSideSheetForPlane** (型: bool, 任意)
  - 説明: 三面指定の場合は True

- **WCS** (型: 要素, 任意)
  - 説明: ブラケットが使用する座標系を指定。通常は指定しない

- **nScallop2Type** (型: 形状タイプ, 任意)
  - 説明: 3面ブラケットの場合のスカラップ2の形状タイプ

### 押し出しパラメータオブジェクト

**説明**: CreateLinearSweepParam() が作成する押し出し（スイープ）用のパラメータオブジェクト。押し出しのターゲットや方向・勾配・厚み付け等の設定プロパティを持つ。

**プロパティ**:

- **DirectionParameter1** (型: 長さ, 任意)
  - 説明: スイープする距離1（SweepTarget1を指定している場合は使用しない）

- **DirectionParameter2** (型: 長さ, 任意)
  - 説明: スイープ方向が2方向の場合に使用する距離2（SweepTarget2を指定している場合は使用しない）

- **DirectionType** (型: スイープ方向, 任意)
  - 説明: スイープ方向（ドキュメントのスイープ方向指定を使用）

- **DraftAngle** (型: 角度, 任意)
  - 説明: 押し出し方向の勾配角度

- **DraftAngle2** (型: 角度, 任意)
  - 説明: 2方向目の押し出し方向の勾配角度

- **DraftAngle2Type** (型: 未指定, 任意)
  - 説明: 勾配2のタイプ: 2方向に押し出す際の勾配の取り方指定（ドキュメントで型の明記なし）

- **ElementGroup** (型: 要素グループ, 任意)
  - 説明: 作成するシート要素を要素グループに入れる場合は要素グループを指定（空文字可）

- **NAME** (型: 文字列, 任意)
  - 説明: 要素名（空文字可）

- **ProfileNormal** (型: 方向, 任意)
  - 説明: プロファイルの平面法線方向（プロファイルが3Dの直線の場合の平面法線として指定）

- **ProfileOffset** (型: 長さ, 任意)
  - 説明: プロファイル位置のオフセット距離

- **ReferMethod** (型: 関連設定, 任意)
  - 説明: 要素の関連づけ方法の指定

- **SweepDirection** (型: 方向, 任意)
  - 説明: スイープする方向を設定する場合に使用。指定しない場合はプロファイルの法線方向

- **Target1** (型: 要素(配列), 任意)
  - 説明: スイープするターゲット要素1（点、線、シート、ソリッド、あるいはソリッドフェイス）

- **Target2** (型: 要素(配列), 任意)
  - 説明: スイープするターゲット要素2（スイープが2方向の場合に使用）

- **ThickenType** (型: 厚み付けタイプ, 任意)
  - 説明: 厚み付けタイプ

- **Thickeness1** (型: 長さ, 任意)
  - 説明: 板厚（厚み1）

- **Thickeness2** (型: 長さ, 任意)
  - 説明: 板厚2（厚み付けタイプが2方向のときに使用）

- **ThickenessOffset** (型: 長さ, 任意)
  - 説明: 厚みづけのオフセット距離

- **bIntervalSwep** (型: bool, 任意)
  - 説明: 区間スイープかどうかを示すフラグ（ドキュメントでは bool と記載）

- **bRefByGeometricMethod** (型: bool, 任意)
  - 説明: True の時は幾何位置にもとづいて関連を設定する

### 条材要素のパラメータオブジェクト

**説明**: 条材（プロファイル）ソリッド要素を作成するためのパラメータオブジェクト。作成方法、形状、材質、取付線や端部、スカラップ等の設定を含む。

**プロパティ**:

- **AttachAngle** (型: 角度, 任意)
  - 説明: 取付角度指定

- **AttachDirMethod** (型: 整数, 任意)
  - 説明: 条材取付方向設定。0: デフォルト、1:基準平面内、2:取付角度指定

- **AttachDirection** (型: 方向, 任意)
  - 説明: 条材取付方向を指定する場合に設定する

- **AttachLines** (型: 要素(配列), 任意)
  - 説明: 条材の取付線（配列）

- **AttachSurface** (型: 要素(配列), 任意)
  - 説明: 条材を取り付ける面要素（フェイス、シートボディ等、配列）

- **BaseDirection1** (型: 方向, 任意)
  - 説明: （基準点と方向で作成する際に使用する）

- **BaseDirection2** (型: 方向, 任意)
  - 説明: 取付方向指定（基準点と方向で使用）

- **BaseLocation** (型: 整数, 任意)
  - 説明: 基準位置。0:左下 1:中下 2:右下 3:左中 4:中中 5:右中 6:左上 7:中上 8:右上

- **BaseOnAttachLines** (型: bool, 任意)
  - 説明: 取付線の境界を基準にする時 True

- **BasePlane** (型: 要素, 任意)
  - 説明: 基準面要素（平面、シート、フェイス）を指定

- **BasePlaneOffset** (型: 長さ, 任意)
  - 説明: 基準面のオフセット距離

- **BasePoint1** (型: 点, 任意)
  - 説明: 基準点1（2点または基準点と方向で作成する際に使用）

- **BasePoint2** (型: 点, 任意)
  - 説明: 基準点2（2点で作成する際に使用）

- **BaseProfile1** (型: 要素, 任意)
  - 説明: ロンジ1（ロンジ間で作成する際に使用）

- **BaseProfile2** (型: 要素, 任意)
  - 説明: ロンジ2（ロンジ間で作成する際に使用）

- **BaseSolid** (型: 要素, 任意)
  - 説明: 基準要素（ソリッド）を指定

- **CCWDefAngle** (型: bool, 任意)
  - 説明: ねじれた条材を作成する場合のネジレ角度を反時計回りに指定する場合は True

- **CalcSnipOnlyAttachLines** (型: bool, 任意)
  - 説明: 端部スニップ量を取付線のみで計算する時 True

- **ConnectionTol** (型: 長さ, 任意)
  - 説明: 取付線が複数の場合の連続性の判定トレランス（通常は指定しない、空文字）

- **DefAngleBaseDir** (型: 方向, 任意)
  - 説明: ねじれた条材のネジレ角度の基準となる軸方向

- **DefAnglePositionAxisDir** (型: 方向, 任意)
  - 説明: ねじれた条材のネジレ角度を定義する軸方向

- **DefPositionNormalAngles** (型: 未指定, 任意)
  - 説明: 位置と角度配列: ねじれた条材のネジレ角度を取付面の法線位置からの差分で指定（ドキュメントで専用の型説明は無し）

- **DefPossitionAngles** (型: 未指定, 任意)
  - 説明: 位置と角度配列: ねじれた条材のネジレ角度を位置と角度で指定（ドキュメントで専用の型説明は無し）

- **DefinitionType** (型: 整数, 任意)
  - 説明: 作成方法指定。0:取付線指定、1:基準面指定、2:取付線＋指定方向線、3:元要素指定、4:ホール指定、5:2点、6:ロンジ間、7:基準線指定、8:基準点と方向、9:基準要素

- **DirLines** (型: 要素(配列), 任意)
  - 説明: 基準直線（取付線＋指定方向線で作成する際に使用）

- **ElementGroup** (型: 要素グループ, 任意)
  - 説明: 作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）

- **End1Elements** (型: 要素(配列), 任意)
  - 説明: 端部1となる要素を指定する配列

- **End1ScallopType** (型: 形状タイプ, 任意)
  - 説明: 端部1のスカラップタイプ

- **End1ScallopTypeParams** (型: 形状パラメータ, 任意)
  - 説明: 端部1のスカラップパラメータ

- **End1Type** (型: 形状タイプ, 任意)
  - 説明: 端部1の条材の端部タイプ

- **End1TypeParams** (型: 形状パラメータ, 任意)
  - 説明: 端部1の端部タイプのパラメータ

- **End2Elements** (型: 要素(配列), 任意)
  - 説明: 端部2となる要素を指定する配列

- **End2ScallopType** (型: 形状タイプ, 任意)
  - 説明: 端部2のスカラップタイプ

- **End2ScallopTypeParams** (型: 形状パラメータ, 任意)
  - 説明: 端部2のスカラップパラメータ

- **End2Type** (型: 形状タイプ, 任意)
  - 説明: 端部2の条材の端部タイプ

- **End2TypeParams** (型: 形状パラメータ, 任意)
  - 説明: 端部2の端部タイプのパラメータ

- **FaceAngle** (型: 角度, 任意)
  - 説明: ビルトアップを作成する場合のフランジの角度指定（0°は直角を意味し、そこからの増分を＋/－で指定）

- **FlangeElementGroup** (型: 要素グループ, 任意)
  - 説明: フランジソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）

- **FlangeMaterialName** (型: 材料, 任意)
  - 説明: 作成するフランジソリッド要素の材質名称（空文字可）

- **FlangeName** (型: 文字列, 任意)
  - 説明: ビルトアップを作成する場合のフランジソリッド要素名称（空文字可）

- **HoleFeature** (型: 要素, 任意)
  - 説明: ホールフィーチャー（ホール指定で作成する際に使用）

- **LocationAtHole** (型: 整数, 任意)
  - 説明: 条材の位置（ホール指定で使用）: 0:上 1:下 2:左 3:右

- **MaterialName** (型: 材料, 任意)
  - 説明: 作成する条材ソリッド要素の材質名称（空文字可）

- **Mold** (型: モールド位置, 任意)
  - 説明: モールド位置

- **MoldOffset** (型: 長さ, 任意)
  - 説明: モールド位置のオフセット距離

- **NotProfjectAttachLines** (型: bool, 任意)
  - 説明: 取付線を取付面に投影しない時 True（ドキュメントの綴りは NotProfjectAttachLines）

- **OrignalProfile** (型: 要素, 任意)
  - 説明: 作成元の条材（元要素指定で作成する際に使用）

- **PathCurves** (型: 要素(配列), 任意)
  - 説明: 取付線（取付線＋指定方向線で作成する際に使用）

- **ProfileName** (型: 文字列, 任意)
  - 説明: 作成する条材ソリッド要素名称（空文字可）

- **ProfileParam** (型: 形状パラメータ, 任意)
  - 説明: 条材の形状タイプのパラメータ（文字列配列）

- **ProfileType** (型: 形状タイプ, 任意)
  - 説明: 条材の形状タイプ

- **ProjectionDir** (型: 方向, 任意)
  - 説明: 取付線を投影する場合に設定する方向（通常は設定しない、空白文字）

- **ReferMethod** (型: 関連設定, 任意)
  - 説明: 要素の関連づけ方法の指定

- **ReverseAngle** (型: bool, 任意)
  - 説明: アングル方向を反転する場合は True

- **ReverseDir** (型: bool, 任意)
  - 説明: 取付方向を反転する場合は True

## コード生成サンプル一覧

以下は、各関数の使用例です。

### BlankElement

```python
part.BlankElement(
    Element,
    bBlank
)
```

### BodyDivideByElements

```python
part.BodyDivideByElements(
    pDriveFeatureName,
    pTargetBody,
    pDivideElements,
    pAlignmentDirection,
    pWCS,
    ReferMethod,
    bUpdate
)
```

### BodySeparateBySubSolids

```python
part.BodySeparateBySubSolids(
    pSeparateFeatureName,
    pTargetBody,
    pSubSolids,
    pAlignmentDirection,
    ReferMethod,
    bUpdate
)
```

### CreateBracket

```python
part.CreateBracket(
    ParamObj,
    bUpdate
)
```

### CreateBracketParam

```python
part.CreateBracketParam()
```

### CreateElementsFromFile

```python
part.CreateElementsFromFile(
    FileName
)
```

### CreateLinearSweep

```python
part.CreateLinearSweep(
    TargetSolidName,
    OperationType,
    pParam,
    bUpdate
)
```

### CreateLinearSweepParam

```python
part.CreateLinearSweepParam()
```

### CreateLinearSweepSheet

```python
part.CreateLinearSweepSheet(
    ParamObj,
    bUpdate
)
```

### CreateOffsetSheet

```python
part.CreateOffsetSheet(
    SheetName,
    ElementGroup,
    MaterialName,
    SrcSurfaces,
    OffsetLength,
    bOffsetBackwards,
    bUpdate
)
```

### CreateOtherSolid

```python
part.CreateOtherSolid(
    OtherSolidFeatureName,
    TargetSolidName,
    OperationType,
    SourceSolid,
    ReferMethod,
    bUpdate
)
```

### CreatePlate

```python
part.CreatePlate(
    PlateName,
    ElementGroup,
    MaterialName,
    Plane,
    PlaneOffset,
    Thickness,
    nMold,
    MoldOffset,
    BoundSolid,
    Section1End1,
    Section1End2,
    Section2End1,
    Section2End2,
    bUpdate
)
```

### CreateProfile

```python
part.CreateProfile(
    ParamObj,
    bUpdate
)
```

### CreateProfileParam

```python
part.CreateProfileParam()
```

### CreateSketchArc

```python
part.CreateSketchArc(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    CenterPoint,
    StartPoint,
    EndPoint,
    bCCW,
    bUpdate
)
```

### CreateSketchArc3Pts

```python
part.CreateSketchArc3Pts(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    StartPoint,
    MidPoint,
    EndPoint,
    bUpdate
)
```

### CreateSketchCircle

```python
part.CreateSketchCircle(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    Centeroint,
    RadiusOrDiameter,
    bDiameter,
    bCCW,
    bUpdate
)
```

### CreateSketchEllipse

```python
part.CreateSketchEllipse(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    Centeroint,
    bCCW,
    MajorDir,
    MajorRadius,
    MinorRadius,
    Range,
    bUpdate
)
```

### CreateSketchLayer

```python
part.CreateSketchLayer(
    SketchLayerName,
    SketchPlane
)
```

### CreateSketchLine

```python
part.CreateSketchLine(
    SketchPlane,
    SketchLineName,
    SketchLayer,
    StartPoint,
    EndPoint,
    bUpdate
)
```

### CreateSketchNURBSCurve

```python
part.CreateSketchNURBSCurve(
    SketchPlane,
    SketchArcName,
    SketchLayer,
    nDegree,
    bClose,
    bPeriodic,
    CtrlPoints,
    Weights,
    Knots,
    Range,
    bUpdate
)
```

### CreateSketchPlane

```python
part.CreateSketchPlane(
    ElementName,
    ElementGroup,
    PlaneDef,
    PlaneOffset,
    bRevPlane,
    bRevUV,
    謎,
    StyleName,
    OriginPoint,
    AxisDirection,
    bDefAxisIsX,
    bUpdate
)
```

### CreateSolid

```python
part.CreateSolid(
    SolidName,
    ElementGroup,
    MaterialName
)
```

### CreateThicken

```python
part.CreateThicken(
    ThickenFeatureName,
    TargetSolidName,
    OperationType,
    Sheet,
    ThickenType,
    Thickeness1,
    Thickeness2,
    ThickenessOffset,
    ReferMethod,
    bUpdate
)
```

### CreateVariable

```python
part.CreateVariable(
    VariableName,
    VariableValue,
    VariableUnit,
    VariableElementGroup
)
```

### MirrorCopy

```python
part.MirrorCopy(
    SrcElements,
    plane,
    ReferMethod
)
```

### ReverseSheet

```python
part.ReverseSheet(
    SheetElement
)
```

### SetElementColor

```python
part.SetElementColor(
    Element,
    RValue,
    GValue,
    BValue,
    Transparency
)
```

### SheetAlignNormal

```python
part.SheetAlignNormal(
    SheetElement,
    dirX,
    dirY,
    dirZ
)
```

### TranslationCopy

```python
part.TranslationCopy(
    SrcElements,
    nCopy,
    direction,
    distance,
    ReferMethod
)
```
