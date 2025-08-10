from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
import os
import sys

load_dotenv()

def read_file_safely(file_path, encoding="utf-8"):
    """
    ファイルを安全に読み込む共通関数
    Args:
        file_path (str): 読み込むファイルのパス
        encoding (str): ファイルのエンコーディング（デフォルト: utf-8）
    Returns:
        str: ファイルの内容
    Raises:
        FileNotFoundError: 指定されたファイルが見つからない場合
        UnicodeDecodeError: ファイルのエンコーディングが不正な場合
        IOError: その他のファイル読み込みエラー
    """
    try:
        with open(file_path, "r", encoding=encoding) as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"ファイルのエンコーディングが不正です: {file_path}")
    except IOError as e:
        raise IOError(f"ファイル読み込みエラー: {file_path} - {str(e)}")

def load_api_document(file_path=None):
    """
    APIドキュメントを読み込む関数
    
    Args:
        file_path (str, optional): ファイルパス。Noneの場合はデフォルトのAPIドキュメントを返す
        
    Returns:
        str: APIドキュメントの内容
        
    Raises:
        FileNotFoundError: 指定されたファイルが見つからない場合
        UnicodeDecodeError: ファイルのエンコーディングが不正な場合
        IOError: その他のファイル読み込みエラー
    """

    if file_path is None:
        # デフォルトのAPIドキュメント（api 1.txtの内容）
        DEFAULT_API_DOC = """■関数の仕様（引数の型、書式はapi_argを参照）

■Partオブジェクトのメソッド

〇変数要素の作成
　返り値:作成された変数要素の要素ID
　CreateVariable
        VariableName, // 文字列：作成する変数名称（空文字不可）
        VariableValue,// 浮動小数点: 変数の値
        VariableUnit  // 変数単位：作成する変数の単位を指定
        VariableElementGroup );// 要素グループ：作成する変数要素を要素グループに入れる場合は要素グループを指定（空文字可）

〇スケッチ平面の作成
  返り値:作成されたスケッチ平面要素の要素ID
  CreateSketchPlane(
        ElementName,  // 文字列：作成するスケッチ平面名称（空文字可）
        ElementGroup, // 要素グループ：作成するスケッチ平面を要素グループに入れる場合は要素グループを指定（空文字可）
        PlaneDef, 　　// 平面：スケッチ平面を作成する平面を指定する
        PlaneOffset,  // 長さ：平面からのオフセット距離を指定
        bRevPlane,    // bool:スケッチ平面を反転するかどうかのフラグ(bool)
        bRevUV,       // bool:スケッチ平面のX,Y軸を交換するかどうかのフラグ(bool)
        謎            // bool：
        StyleName,    // 注記スタイル:　スケッチ平面に適用する注記スタイル名称（空文字可）
        OriginPoint,  // 点：スケッチ平面の原点を指定（空文字可）
        AxisDirection,// 方向：スケッチ平面の軸方向を指定（空文字可）
        bDefAxisIsX,  // bool：スケッチ平面のX実を指定する場合はTrue(bool)
        bUpdate );    // bool：更新フラグ（未実装、使用しない）

〇スケッチレイヤーの作成
  返り値:作成されたスケッチレイヤー要素の要素ID
  CreateSketchLayer(
        SketchLayerName,  // 文字列：作成するスケッチレイヤー名称（空文字可）
        SketchPlane );　　// 要素：レイヤーを作成するスケッチ要素

〇スケッチ直線作成
  返り値:作成されたスケッチ直線要素の要素ID
  CreateSketchLine(
        SketchPlane,   // 要素：直線を作成するスケッチ要素
        SketchLineName,// 文字列：作成するスケッチ直線名称（空文字可）
        SketchLayer,   // 要素：直線を作成するスケッチレイヤー(空文字可）
        StartPoint,    // 点(2D)：始点
        EndPoint,      // 点(2D)：終点
        bUpdate );     // bool：更新フラグ（未実装、使用しない）

〇スケッチ円弧を中心点と始終点を指定して作成
  返り値:作成されたスケッチ円弧要素の要素ID
  CreateSketchArc(
        SketchPlane,   // 要素：円弧を作成するスケッチ要素
        SketchArcName, // 文字列：作成するスケッチ円弧名称（空文字可）
        SketchLayer,   // 要素：円弧を作成するスケッチレイヤー(空文字可）
        CenterPoint,   // 点(2D)：中心点
        StartPoint,    // 点(2D)：始点
        EndPoint,      // 点(2D)：終点
        bCCW,          // bool： 円弧の回転方向Trueの場合は反時計周り
        bUpdate );     // bool：更新フラグ（未実装、使用しない）

〇スケッチ円弧を周上の３点を指定して作成
  返り値:作成されたスケッチ円弧要素の要素ID
  CreateSketchArc3Pts(
        SketchPlane,   // 要素：円弧を作成するスケッチ要素
        SketchArcName, // 文字列：作成するスケッチ円弧名称（空文字可）
        SketchLayer,   // 要素：円弧を作成するスケッチレイヤー(空文字可）
        StartPoint,    // 点(2D)：始点
        MidPoint,      // 点(2D)：通過点
        EndPoint,      // 点(2D)：終点
        bUpdate );     // bool：更新フラグ（未実装、使用しない）
 
〇スケッチ円を中心点を指定して作成
  返り値:作成されたスケッチ円要素の要素ID
  CreateSketchCircle(
        SketchPlane,   // 要素：円を作成するスケッチ要素
        SketchArcName, // 文字列：作成するスケッチ円名称（空文字可）
        SketchLayer,   // 要素：円を作成するスケッチレイヤー(空文字可）
        Centeroint,    // 点(2D)：中心点
        RadiusOrDiameter, // 長さ：半径または直径
        bDiameter,     // bool：直径を指定する場合はTrue
        bCCW,          // bool：円の回転方向Trueの場合は反時計周り
        bUpdate );     // bool：更新フラグ（未実装、使用しない）

〇スケッチ楕円を中心点を指定して作成
  返り値:作成されたスケッチ楕円要素の要素ID
  CreateSketchEllipse(
        SketchPlane,   // 要素：楕円を作成するスケッチ要素
        SketchArcName, // 文字列：作成するスケッチ楕円名称（空文字可）
        SketchLayer,   // 要素：楕円を作成するスケッチレイヤー(空文字可）
        Centeroint,    // 点(2D)：中心点
        bCCW,          // bool：楕円の回転方向Trueの場合は反時計周り
        MajorDir,　　　// 方向(2D)：主軸方向を指定
        MajorRadius,   // 長さ：主軸半径
        MinorRadius,   // 長さ：副軸半径
        Range,         // 範囲: (0-2pi)
        bUpdate );     // bool：更新フラグ（未実装、使用しない）

〇スケッチＮＵＲＢＳ線を中心点を指定して作成
  返り値:作成されたスケッチＮＵＲＢＳ線要素の要素ID
  CreateSketchNURBSCurve(
        SketchPlane,   // 要素：ＮＵＲＢＳ線を作成するスケッチ要素
        SketchArcName, // 文字列：作成するスケッチＮＵＲＢＳ線名称（空文字可）
        SketchLayer,   // 要素：ＮＵＲＢＳ線を作成するスケッチレイヤー(空文字可）
        nDegree,       // 整数：ＮＵＲＢＳ線の次数
        bClose,        // bool：閉じたＮＵＲＢＳ線の場合True
        bPeriodic,     // bool：周期ＮＵＲＢＳ線の場合True
        CtrlPoints,    // 点(配列): 制御点
        Weights,       // 浮動小数点(配列): 重み
        Knots,         // 浮動小数点(配列): ノットベクトル
        Range,         // 範囲: トリム範囲
        bUpdate );     // bool：更新フラグ（未実装、使用しない）

〇ファイルをインポートして要素を作成
  返り値:作成された要素の要素IDの配列
  CreateElementsFromFile(
        FileName,      // 文字列:ファイルパス（現状、Parasolid形式のみ）
       );

〇オフセットシートを作成
  返り値:作成されたオフセットシート要素の要素ID
  CreateOffsetSheet(
        SheetName,    // 文字列：作成するシート要素名称（空文字可）
        ElementGroup, // 要素グループ：作成するシート要素を要素グループに入れる場合は要素グループを指定（空文字可）
        MaterialName, // 材料：作成するシート要素の材質名称（空文字可）
        SrcSurfaces,  // 要素(配列):オフセットする元シート要素、フェイス要素の指定文字列配列
        OffsetLength, // 長さ：オフセット距離
        bOffsetBackwards, // bool： オフセット方向を反転
        bUpdate,　//bool：更新フラグ（未実装、使用しない）
    ); 

〇押し出しパラメータオブジェクトの作成
　返り値:押し出しパラメータオブジェクト
　CreateLinearSweepParam()　

〇押し出しパラメータオブジェクト
   属性
   NAME   // 文字列：要素名（空文字可）
   ElementGroup, // 要素グループ：作成するシート要素を要素グループに入れる場合は要素グループを指定（空文字可）
   Target1  // 要素(配列)：スイープするターゲット要素１　（点、線、シート、ソリッド、あるいはソリッドフェイス）
   Target2  // 要素(配列)：スイープ方向が２方向の場合に使用。スイープするターゲット要素２
   ProfileNormal // 方向：プロファイルの平面法線方向。（プロファイルが３Dの直線の場合にその平面法線として指定。） 
   ProfileOffset // 長さ：プロファイル位置のオフセット距離
   DirectionType  // スイープ方向： 
   DirectionParameter1 // 長さ： スイープする距離１（SweepTarget1を指定している場合は使用しない）
   DirectionParameter2 // 長さ： スイープ方向が２方向の場合に使用。スイープする距離２（SweepTarget２を指定している場合は使用しない）
   SweepDirection // 方向：スイープする方向を設定する場合に使用。指定しない場合はプロファイルの法線方向
   DraftAngle   // 角度: 押し出し方向の勾配角度
   DraftAngle2Type　// 勾配２のタイプ: ２方向に押し出す際の勾配の取り方指定
   DraftAngle2　// 角度: ２方向目の押し出し方向の勾配角度
   ThickenType　// 厚み付けタイプ: 
   Thickeness1  // 長さ： 板厚
   Thickeness2  // 長さ： 板厚２（厚み付けタイプが２方向のときに使用）
   ThickenessOffset // 長さ： 厚みづけのオフセット距離
   bRefByGeometricMethod // bool：Trueの時は幾何位置にもとづいて関連を設定する
   bIntervalSwep // bool：
   ReferMethod // 関連設定: 要素の関連づけ方法の指定

〇プロファイル要素を押し出してシート要素を作成
  返り値:作成されたシート要素の要素ID
  CreateLinearSweepSheet(
        ParamObj, // 押し出しパラメータオブジェクト
        bUpdate);　// bool：更新フラグ（未実装、使用しない）

〇シート要素の向き（表側、法線方向）を指定した方向に揃える
  返り値:なし
  SheetAlignNormal(
        SheetElement,// 要素：方向を揃えるシート要素
        dirX,   // 浮動小数点: 方向ベクトルのX成分
        dirY,   // 浮動小数点: 方向ベクトルのY成分
        dirZ ); // 浮動小数点: 方向ベクトルのZ成分

〇シート要素の向きを反転する
  返り値:シート反転フィーチャーの要素ID
  ReverseSheet(
        SheetElement ); // 要素：反転するシート要素

〇指定要素を表示状態を設定する
  返り値:なし
  BlankElement(
        Element,  // 要素：表示状態を指定する要素
        bBlank ); // bool： Trueの時は非表示にする。Falseの時は表示する。

〇指定要素を移動コピーする
  返り値:コピーされた要素ID配列
  TranslationCopy(
        SrcElements,// 要素(配列)：コピーする要素
        nCopy,    // 整数: コピーする数
        direction,      // 方向：コピーする方向
        distance,       // 長さ：移動距離
        ReferMethod);  // 関連設定: 要素の関連づけ方法の指定

〇指定要素をミラーコピーする
  返り値:コピーされた要素ID配列
  MirrorCopy(
        SrcElements,// 要素(配列)：コピーする要素
        [in] BSTR plane,
        ReferMethod);  // 関連設定: 要素の関連づけ方法の指定

〇空のソリッド要素を作成する
  返り値:作成されたソリッドの要素ID
  CreateSolid(
        SolidName, // 文字列：作成するソリッド要素名称（空文字可）
        ElementGroup, // 要素グループ：作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
        MaterialName ) // 材料：作成するソリッド要素の材質名称（空文字可）

〇指定したソリッド要素に指定要素厚みづけした形状を作成する
  返り値:作成された厚みづけフィーチャーのID
  CreateThicken(
        ThickenFeatureName, // 文字列：作成する厚みづけフィーチャー要素名称（空文字可）
        TargetSolidName,    // 要素：厚みづけフィーチャーを作成する対象のソリッドを指定
        OperationType,      // オペレーションタイプ: ソリッドオペレーションのタイプを指定する
　　　　Sheet,　　　　　　　// 要素(配列)：厚み付けをするシートやフェイス
        ThickenType,　　　　// 厚み付けタイプ: 
        Thickeness1,        // 長さ： 板厚
        Thickeness2,　　　　// 長さ： 板厚２（厚み付けタイプが２方向のときに使用）
        ThickenessOffset,   // 長さ： 厚みづけをするシート、フェイス要素のオフセット距離
        ReferMethod,　　　　// 関連設定: 要素の関連づけ方法の指定
        bUpdate);　// bool：更新フラグ（未実装、使用しない）

〇指定したソリッド要素に別のソリッド要素形状を付加する
  返り値:作成された別ソリッドフィーチャーのID
  CreateOtherSolid(
　　　　OtherSolidFeatureName, // 文字列：作成する別ソリッドフィーチャー要素名称（空文字可）
        TargetSolidName,  // 要素：別ソリッドフィーチャーを作成する対象のソリッドを指定
        OperationType,  // オペレーションタイプ: ソリッドオペレーションのタイプを指定する
        SourceSolid,    // 要素：別ソリッドフィーチャーとするソリッド要素を指定する
        ReferMethod, // 関連設定: 要素の関連づけ方法の指定
        bUpdate　);　// bool：更新フラグ（未実装、使用しない）

〇指定したソリッド要素に押し出し形状を付加する
  返り値:作成された押し出しフィーチャーのID
  CreateLinearSweep(
        TargetSolidName,         // 要素：押し出しフィーチャーを作成する対象のソリッドを指定
        OperationType,   // オペレーションタイプ: ソリッドオペレーションのタイプを指定する
        pParam, // 押し出しパラメータオブジェクト
        bUpdate 　);　// bool：更新フラグ（未実装、使用しない）

〇船殻のブラケット要素のパラメータオブジェクトの作成
　返り値:ブラケット要素のパラメータオブジェクト
　CreateBracketParam()
　　
〇ブラケット要素のパラメータオブジェクト
   属性
        DefinitionType //　整数: ブラケットの作成方法指定　0: 面指定　1:基準要素指定
        BracketName // 文字列：作成するブラケットソリッド要素名称（空文字可）
        ElementGroup // 要素グループ：作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
        MaterialName // 材料：作成するソリッド要素の材質名称（空文字可）
        BasePlane    //面指定の場合の基準平面
        BasePlaneOffset // 長さ：基準平面のオフセット距離
        BaseElement  // 基準要素指定の場合の基準要素
        UseSideSheetForPlane // bool： 三面指定の場合はTrue
        Thickness // 長さ： 板厚
        Mold     // モールド位置: 
        MoldOffset // 長さ： モールド位置のオフセット距離
        BracketType // 形状タイプ: ブラケットの形状タイプ
        BracketParams,　// 形状パラメータ: ブラケットの形状タイプのパラメータ
        Scallop1Type,　// 形状タイプ: ブラケットのスカラップの形状タイプ
        Scallop1Params,　// 形状パラメータ: ブラケットのスカラップの形状タイプのパラメータ
        nScallop2Type,　// 形状タイプ: ３面ブラケットの場合のスカラップ２の形状タイプ
        Scallop2Params,　// 形状パラメータ: ブラケットのスカラップ２の形状タイプのパラメータ
        Surfaces1, // 要素(配列)：ブラケット作成する面１の要素（ソリッド、シート、フェイス）
        RevSf1, // bool： 面１の反対側にブラケットを作成する場合はTrue
        Surfaces2, // 要素(配列)：ブラケット作成する面2の要素（ソリッド、シート、フェイス）
        RevSf2, // bool： 面2の反対側にブラケットを作成する場合はTrue
        Surfaces3, // 要素(配列)：３面ブラケット作成する場合の面３の要素（ソリッド、シート、フェイス）
        RevSf3, // bool： 面3の反対側にブラケットを作成する場合はTrue
        FlangeType, // 形状タイプ: ブラケットのフランジの形状タイプ　(0の場合はフランジをつけない）
        FlangeParams,// 形状パラメータ: ブラケットのフランジの形状タイプのパラメータ
        RevFlange,　// bool： フランジの向きを反転する場合はTrue
        FlangeAngle, // 角度： フランジの角度指定　０°は直角を意味し、そこからの増分を＋－で指定
        Sf1DimensionType,　// 形状タイプ: 面１方向の寸法タイプ
        Sf1DimensonParams,　// 形状パラメータ: 面１方向の寸法タイプのパラメータ
        Sf1EndElements, // 要素(配列)：面１方向の端部要素（必要な形状タイプの場合）
        Sf1BaseElements,　// 要素(配列)：面１方向の基準要素（必要な形状タイプの場合）
        Sf2DimensionType,　// 形状タイプ: 面２方向の寸法タイプ
        Sf2DimensonParams,　// 形状パラメータ: 面２方向の寸法タイプのパラメータ
        Sf2EndElements,　// 要素(配列)：面２方向の端部要素（必要な形状タイプの場合）
        Sf2BaseElements,　// 要素(配列)：面２方向の基準要素（必要な形状タイプの場合）
        ScallopEnd1LowerType,　// 形状タイプ: 面１方向の下側端部のスカラップのタイプ
        ScallopEnd1LowerParams,　// 形状パラメータ: 面１方向の下側端部のスカラップのタイプのパラメータ
        ScallopEnd1UpperType,　// 形状タイプ: 面１方向の上側端部のスカラップのタイプ
        ScallopEnd1UpperParams,　// 形状パラメータ: 面１方向の上側端部のスカラップのタイプのパラメータ
        ScallopEnd2LowerType,　// 形状タイプ: 面２方向の下側端部のスカラップのタイプ
        ScallopEnd2LowerParams,　// 形状パラメータ: 面２方向の下側端部のスカラップのタイプのパラメータ
        ScallopEnd2UpperType,　// 形状タイプ: 面２方向の上側端部のスカラップのタイプ
        ScallopEnd2UpperParams,// 形状パラメータ: 面２方向の上側端部のスカラップのタイプのパラメータ
        WCS, // 要素： ブラケットが使用する座標系を指定。通常は指定しない
        ReferMethod, // 関連設定: 要素の関連づけ方法の指定
        
〇船殻のブラケットソリッド要素を作成する
  返り値:作成したソリッド要素のID
  CreateBracket(
　　    ParamObj, // ブラケットパラメータオブジェクト
        bUpdate ); // bool：更新フラグ（未実装、使用しない）
        

〇船殻のプレートソリッド要素を作成する
  返り値:作成したソリッド要素のID
  CreatePlate(
        PlateName,     // 文字列：作成するプレートソリッド要素名称（空文字可）
        ElementGroup,  // 要素グループ：作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
        MaterialName, // 材料：作成するソリッド要素の材質名称（空文字可）
        Plane,        // 平面： プレートのる平面位置
        PlaneOffset,　// 長さ：　平面のオフセット距離を指定
        Thickness,　　// 長さ： 板厚
        nMold,　　　　// モールド位置: 
        MoldOffset,  // 長さ： モールド位置のオフセット距離
        BoundSolid,　// 要素：　プレートソリッドの境界となるソリッド要素。
        Section1End1,　// 長さ： プレートソリッドの平面上の方向１の境界位置の座標値１
        Section1End2,　// 長さ： プレートソリッドの平面上の方向１の境界位置の座標値２
        Section2End1,　// 長さ： プレートソリッドの平面上の方向２の境界位置の座標値１
        Section2End2,　// 長さ： プレートソリッドの平面上の方向２の境界位置の座標値２
        bUpdate ); // bool：更新フラグ（未実装、使用しない）

〇船殻の条材ソリッド要素のパラメータオブジェクトの作成
  返り値:条材要素のパラメータオブジェクト
  CreateProfileParam()

〇条材要素のパラメータオブジェクト
   属性
        DefinitionType //　整数: の作成方法指定　0:取付線指定 　1:基準面指定  2:取付線＋指定方向線  3: 元要素指定
　　　　　　　　　　　 // 4:ホール指定  5:２点  6:ロンジ間  7:基準線指定  8:基準点と方向  9:基準要素
        ProfileName // 文字列：作成する条材ソリッド要素名称（空文字可）
        ElementGroup // 要素グループ：作成するソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
        MaterialName // 材料：作成するソリッド要素の材質名称（空文字可）
        FlangeName // 文字列：ビルトアップを作成する場合のフランジソリッド要素名称（空文字可）
        FlangeElementGroup// 要素グループ：フランジソリッド要素を要素グループに入れる場合は要素グループを指定（空文字可）
        FlangeMaterialName// 材料：作成するフランジソリッド要素の材質名称（空文字可）
        ProfileType    // 形状タイプ: 条材の形状タイプを指定
        ProfileParam // 形状パラメータ: 条材の形状タイプのパラメータ
        FaceAngle // 角度： ビルトアップを作成する場合のフランジの角度指定　０°は直角を意味し、そこからの増分を＋－で指定
        ConnectionTol // 長さ： 取付線が複数の場合の連続性の判定トレランスを指定（通常は指定しない、空文字）
        Mold      // モールド位置: 
        MoldOffset // 長さ： モールド位置のオフセット距離
        ReverseDir // bool：取付方向を反転する時True
        ReverseAngle // bool：アングル方向を反転する時True
        BaseOnAttachLines // bool： 取付線の境界を基準にする時True
        CalcSnipOnlyAttachLines // bool：端部スニップ量を取付線のみで計算する時True
        NotProfjectAttachLines // bool：取付線を取付面に投影しない時True
        ProjectionDir // 方向：取付線を投影する場合に設定。通常は設定しない（空白文字）
        AttachDirMethod // 整数:　条材取付方向設定　0: デフォルト　1:基準平面内　2:取付角度指定
        AttachAngle // 角度： 取付角度指定
        AttachDirection // 方向：条材取付方向 を指定する場合に設定する
        DefAnglePositionAxisDir　// 方向：ねじれた条材を作成する場合のそのネジレ角度を定義する軸方向を指定。
        DefAngleBaseDir　// 方向：ねじれた条材を作成する場合のそのネジレ角度の基準となる軸方向を指定。
        CCWDefAngle,　// bool：　ねじれた条材を作成する場合のネジレ角度を反統計まわりに指定する場合はTrue
        DefPossitionAngles // 位置と角度配列: ねじれた条材を作成する場合のネジレ角度を位置と角度で指定
        DefPositionNormalAngles // 位置と角度配列:ねじれた条材を作成する場合のネジレ角度を位置と角度を取付面の法線位置からの差分で指定
        End1Elements  // 要素(配列)： 端部１、端部となる要素を指定する
        End1Type       // 形状タイプ: 端部１、条材の端部タイプを指定
        End1TypeParams // 形状パラメータ: 端部１、条材の端部タイプのパラメータ
        End2Elements   // 要素(配列)： 端部２、端部となる要素を指定する
        End2Type       // 形状タイプ: 端部２、条材の端部タイプを指定
        End2TypeParams // 形状パラメータ: 端部２、条材の端部タイプのパラメータ
        End1ScallopType      // 形状タイプ: 端部１、条材の端部スカラップタイプを指定
        End1ScallopTypeParams// 形状パラメータ: 端部１、条材の端部スカラップタイプのパラメータ
        End2ScallopType      // 形状タイプ: 端部２、条材の端部スカラップタイプを指定
        End2ScallopTypeParams// 形状パラメータ: 端部２、条材の端部スカラップタイプのパラメータ
        AttachLines // 要素(配列)：条材の取付線 
        AttachSurface　// 要素(配列)：条材を取り付ける面要素（フェイス、シートボディ）
        BasePlane　// 要素：基準面要素（平面、シート、フェイス）を指定
        BasePlaneOffset // 長さ： 基準面のオフセット距離を指定
        BaseSolid　// 要素：基準要素（ソリッド）を指定
        PathCurves // 要素(配列)：取付線（取付線＋指定方向線で作成する際に使用する)
        DirLines　　// 要素(配列)：基準直線（取付線＋指定方向線で作成する際に使用する)
        OrignalProfile // 要素： 作成元の条材(元要素指定で作成する際に使用する)
        HoleFeature  // 要素： ホールフィーチャー(ホール指定で作成する際に使用する)
        LocationAtHole //整数: 条材の位置　0:上 1:下 2:左 3:右　(ホール指定で作成する際に使用する)
        BasePoint1 // 点: 基準点1 (２点もしくは基準点と方向で作成する際に使用する)
        BasePoint2 // 点: 基準点2 (２点で作成する際に使用する)
        BaseProfile1 // 要素： ロンジ１(ロンジ間で作成する際に使用する)
        BaseProfile2 // 要素： ロンジ２(ロンジ間で作成する際に使用する)
        BaseDirection1 // 方向： (基準点と方向で作成する際に使用する)
        BaseDirection2 // 方向： 取付方向指定　(基準点と方向で作成する際に使用する)
        BaseLocation //整数:  基準位置 0:左下 1:中下 2:右下 3:左中 4:中中 5:右中 6:左上 7:中上 8:右上 (基準点と方向で作成する際に使用する)
        ReferMethod // 関連設定: 要素の関連づけ方法の指定

〇船殻の条材ソリッド要素を取付線指定で作成する
  返り値:作成した条材ソリッド要素のID(配列　配列[0]Web要素 配列[1]フランジ要素
  CreateProfile(
　　    ParamObj, // 条材要素のパラメータオブジェクト
        bUpdate );  // bool：更新フラグ（未実装、使用しない）

〇ボディを指定した要素で分割する
  返り値:分割で作成されたボディ要素のID配列
BodyDivideByElements(
    pDriveFeatureName, // 文字列：作成する分割フィーチャー要素名称（空文字可）
    pTargetBody,// 要素: 分割対象のボディ
    pDivideElements,  // 要素(配列): 分割をする要素（シートボディ、フェイス、平面要素）
    pAlignmentDirection,　// 方向： 分割されたボディ要素の順番を整列させるのに使用する方向
    pWCS, // 要素： 方向を定義する座標系（通常は指定しない）
    ReferMethod, // 関連設定: 要素の関連づけ方法の指定
     bUpdate);　// bool：更新フラグ（未実装、使用しない）

〇ボディを指定したソリッドで削除することで分割する（ボディの区分けコマンド）
  返り値:分割で作成されたボディ要素のID配列
　BodySeparateBySubSolids(
    pSeparateFeatureName, // 文字列：作成する分割フィーチャー要素名称（空文字可）
    pTargetBody, // 要素: 分割対象のボディ
    pSubSolids, // 要素(配列): 分割をするソリッド要素
    pAlignmentDirection,　// 方向： 分割されたボディ要素の順番を整列させるのに使用する方向
    ReferMethod, // 関連設定: 要素の関連づけ方法の指定
    bUpdate);　// bool：更新フラグ（未実装、使用しない）

〇指定要素の色を設定する
  SetElementColor(
     Element  // 要素：色を設定する要素
     RValue,  // 整数: 赤色の値(0-255)
     GValue,  // 整数: 緑色の値(0-255)
     BValue,  // 整数: 青色の値(0-255)
     Transparency ) // 浮動小数点: 透明度の指定(0.0不透明-1.0透明)"""
        return DEFAULT_API_DOC
    
    return read_file_safely(file_path)

def load_prompt(file_path=None):
    """
    プロンプトファイルを読み込む関数
    
    Args:
        file_path (str): プロンプトファイルのパス
        
    Returns:
        str: プロンプトファイルの内容
        
    Raises:
        FileNotFoundError: 指定されたファイルが見つからない場合
        UnicodeDecodeError: ファイルのエンコーディングが不正な場合
        IOError: その他のファイル読み込みエラー
    """
    if file_path is None:
        DEFAULT_PROMPT = """あなたは優秀なAPIドキュメント解析エンジニアです。ユーザーから提供された日本語のAPI仕様書（自然言語）を厳密に解析し、指定のJSON形式のみを出力してください。

厳守事項:
- 出力は有効なJSON配列のみ。Markdownや余分なテキストは禁止。
- 推測や補完は避け、与えられた本文から根拠があるもののみ抽出。
- 型名は以下の日本語表記のいずれかに正規化して使用（厳密一致）:
  ["文字列","浮動小数点","整数","bool","長さ","角度","方向","方向(2D)","要素","要素(配列)","要素ID","要素ID(配列)","要素グループ","材料","平面","点","点(2D)","注記スタイル","オペレーションタイプ","厚み付けタイプ","関連設定","形状タイプ","形状パラメータ","モールド位置","スイープ方向","勾配２のタイプ","位置と角度配列","範囲","座標系","BSTR","変数単位","浮動小数点(配列)"]
- 配列型は「X(配列)」の表記を優先。可能なら配列要素型をarray_info.element_typeに設定。
- 「空文字不可」は必須。説明に（空文字可）があれば任意。
- 不明な型や説明はnotesに「不明」や根拠付きで記載し、型は最も妥当な候補に揃える。

解析の観点:
1. 関数名・説明・カテゴリ（見出しや本文から）
2. パラメータ名・型・説明・必須性・配列/オブジェクト詳細
3. 戻り値（型・説明・配列構造）
4. 実装状況（「未実装」「使用しない」の記述は厳密に反映）
5. 依存関係（前提要素や必要設定が本文にある場合のみ）

出力フォーマット:
{json_format}

解析対象:
---
{document}
---"""
        return DEFAULT_PROMPT
    return read_file_safely(file_path)

def load_json_format_instructions(file_path=None):
    if file_path is None:
        DEFAULT_JSON_FORMAT_INSTRUCTIONS = """
        [
            {
    "name": "string",
    "type": "function",
    "category": "string",
    "description": "string",
    "params": [
      {
        "name": "string",
        "type_name": "string",
        "description_raw": "string",
        "constraints": ["string"],
        "summary_llm": "string | null",
        "constraints_llm": ["string"],
        "is_required": "boolean",
        "default_value": "string | null",
        "array_info": {
          "is_array": "boolean",
          "element_type": "string",
          "min_length": "number | null",
          "max_length": "number | null"
        } | null,
        "object_info": {
          "is_object": "boolean",
          "object_type": "string",
          "properties": ["string"]
                        } | null,
        "position": "number"
      }
    ],
    "returns": {
      "type_name": "string",
      "description": "string",
      "is_array": "boolean",
      "array_structure": "string | null"
    },
    "notes": "string | null",
    "implementation_status": "string",
    "complexity_level": "string",
    "dependencies": ["string"],
    "signature_raw": "string | null"
            }
        ]
        """
        return DEFAULT_JSON_FORMAT_INSTRUCTIONS
    return read_file_safely(file_path)

def write_file_safely(file_path, content, encoding="utf-8"):
    """
    ファイルを安全に書き込む共通関数
    
    Args:
        file_path (str): 書き込むファイルのパス
        content (str): 書き込む内容
        encoding (str): ファイルのエンコーディング（デフォルト: utf-8）
        
    Raises:
        IOError: ファイル書き込みエラー
        PermissionError: ファイルへの書き込み権限がない場合
    """
    try:
        # ディレクトリが存在しない場合は作成
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w", encoding=encoding) as file:
            file.write(content)
    except PermissionError:
        raise PermissionError(f"ファイルへの書き込み権限がありません: {file_path}")
    except IOError as e:
        raise IOError(f"ファイル書き込みエラー: {file_path} - {str(e)}")

def save_parsed_result(parsed_result, output_file_path="doc_paser/parsed_api_result.json"):
    """
    解析結果をJSONファイルとして保存する関数
    
    Args:
        parsed_result (dict or list): 保存する解析結果（辞書またはリスト）
        output_file_path (str): 出力ファイルのパス（デフォルト: parsed_api_result.json）
        
    Raises:
        IOError: ファイル書き込みエラー
        PermissionError: ファイルへの書き込み権限がない場合
    """
    import json
    
    try:
        # 解析結果をJSON形式で整形
        json_content = json.dumps(parsed_result, ensure_ascii=False, indent=2)
        
        # ファイルに保存
        write_file_safely(output_file_path, json_content)
        
        print(f"解析結果を保存しました: {output_file_path}")
        
    except Exception as e:
        print(f"解析結果の保存に失敗しました: {str(e)}")
        raise

def normalize_type_name(type_name: str) -> str:
    if not isinstance(type_name, str):
        return type_name
    name = type_name.strip()
    mapping = {
        "string": "文字列",
        "str": "文字列",
        "float": "浮動小数点",
        "double": "浮動小数点",
        "number": "浮動小数点",
        "int": "整数",
        "integer": "整数",
        "boolean": "bool",
        "bool": "bool",
        "length": "長さ",
        "angle": "角度",
        "direction": "方向",
        "direction2d": "方向(2D)",
        "plane": "平面",
        "point": "点",
        "point2d": "点(2D)",
        "element": "要素",
        "elementid": "要素ID",
        "element group": "要素グループ",
        "material": "材料",
        "style": "注記スタイル",
        "bstr": "BSTR",
        "配列": "配列",
        "浮動小数点(配列)": "浮動小数点(配列)",
    }
    key = name.lower().replace(" ", "")
    return mapping.get(key, name)


def enrich_array_object_info(param: dict) -> None:
    t = param.get("type_name")
    if not isinstance(t, str):
        return
    is_array = "(配列)" in t or t.endswith("配列") or t.endswith("(array)")
    if is_array:
        base = t.replace("(配列)", "").replace("配列", "").strip("：: ")
        element_type = base if base and base != "要素" else None
        param["array_info"] = {
            "is_array": True,
            "element_type": element_type,
            "min_length": None,
            "max_length": None,
        }
    else:
        if param.get("array_info") is None:
            param["array_info"] = None


def infer_is_required(param: dict) -> None:
    cons = param.get("constraints") or []
    desc = param.get("description_raw") or ""
    text = " ".join(cons) + " " + desc
    required = ("空文字不可" in text) or ("必須" in text)
    if "空文字可" in text:
        required = False
    param["is_required"] = bool(required)


def postprocess_parsed_result(parsed_result):
    if not isinstance(parsed_result, list):
        return parsed_result
    for fn in parsed_result:
        if isinstance(fn.get("returns"), dict):
            r_t = fn["returns"].get("type_name")
            if r_t is not None:
                fn["returns"]["type_name"] = normalize_type_name(r_t)
        params = fn.get("params") or []
        for idx, p in enumerate(params):
            t = p.get("type_name")
            if t is not None:
                p["type_name"] = normalize_type_name(t)
            enrich_array_object_info(p)
            infer_is_required(p)
            p["position"] = idx
        fn["params"] = params
    return parsed_result

def main():
    # 解析対象の自然言語APIドキュメント
    api_document_text = load_api_document("data/src/api 1.txt")
    # LLMへの指示をテンプレート化する
    prompt = ChatPromptTemplate.from_template(load_prompt())
    # LLMに生成してほしいJSONの形式を定義する
    json_format_instructions = load_json_format_instructions()
    # JSON出力を専門に行うパーサーを準備
    parser = JsonOutputParser()

    try:
        # LLMモデルを初期化 (環境変数からAPIキーを自動読み込み)
        llm = ChatOpenAI(model="gpt-5-nano")

        # プロンプト、LLM、出力パーサーを `|` で連結してチェーンを作成 (LCEL構文)
        chain = prompt | llm | parser

        print("🤖 LLMを使ってAPIドキュメントを解析しています...")

        # チェーンを実行し、ドキュメントと出力形式を渡す
        parsed_result = chain.invoke({
            "document": api_document_text,
            "json_format": json_format_instructions
        })

        # 出力の後処理（型名の正規化・補完）
        parsed_result = postprocess_parsed_result(parsed_result)

        # --- 5. 結果の表示 ---
        print("\n✅ 解析が完了し、JSONオブジェクトが生成されました。")
        # Pythonの辞書オブジェクトとして整形して表示
        print(json.dumps(parsed_result, indent=2, ensure_ascii=False))

        print("\n---")
        # Pythonオブジェクトとしてデータにアクセスできることを確認
        # parsed_resultはリストなので、最初の要素を取得
        if isinstance(parsed_result, list) and len(parsed_result) > 0:
            first_api = parsed_result[0]
            print(f"API名: {first_api.get('name')}")
            print(f"パラメータ数: {len(first_api.get('params', []))}")
            print(f"戻り値の型: {first_api.get('returns', {}).get('type_name', 'N/A')}")
        else:
            print("解析結果が空または予期しない形式です")

        # 解析結果を保存
        save_parsed_result(parsed_result)


    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print(f"エラーの種類: {type(e).__name__}")
        
        # デバッグ情報を追加
        if 'parsed_result' in locals():
            print(f"parsed_resultの型: {type(parsed_result)}")
            if isinstance(parsed_result, list):
                print(f"parsed_resultの長さ: {len(parsed_result)}")
                if len(parsed_result) > 0:
                    print(f"最初の要素の型: {type(parsed_result[0])}")
        
        if "api_key" in str(e).lower():
            print("\n💡 ヒント: .envファイルに正しいOPENAI_API_KEYが設定されているか確認してください。")
        elif "list" in str(e).lower() and "get" in str(e).lower():
            print("\n💡 ヒント: 解析結果がリスト形式で返されているため、適切なインデックスアクセスが必要です。")

        pass
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print(f"プロジェクトルートパス: {project_root}")
    print(f"Pythonパスに追加されました: {project_root in sys.path}")
    
    main()
