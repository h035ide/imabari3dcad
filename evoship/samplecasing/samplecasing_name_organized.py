"""
EvoShip ケーシング構造モデル作成スクリプト
整理版 - 機能別にセクション分けし、コメントを追加
"""

import win32com.client
from config import (
    FRAME_POSITIONS, DECK_LEVELS, MATERIALS, COLORS, 
    EXTRUDE_PARAMS, SKETCH_PLANES, get_frame_position, 
    get_deck_level, get_color, create_base_plane
)
from profile_creation import (
    create_standard_profile, create_deck_bracket, 
    create_solid_structure, create_mirror_copy, 
    create_body_division, create_profile_from_config
)

# =============================================================================
# 初期化とセットアップ
# =============================================================================
def initialize_evoship():
    """EvoShipアプリケーションの初期化"""
    evoship = win32com.client.DispatchEx("EvoShip.Application")
    evoship.ShowMainWindow(True)
    doc = evoship.Create3DDocument()
    part = doc.GetPart()
    return evoship, doc, part

# =============================================================================
# スケッチ平面とレイヤーの作成
# =============================================================================
def create_sketch_planes_and_layers(part):
    """スケッチ平面とレイヤーの作成"""
    
    # メインスケッチ平面の作成（設定ファイルから取得）
    wall_plane = SKETCH_PLANES['WALL']
    skt_pl1 = part.CreateSketchPlane(
        wall_plane['name'], "", wall_plane['type'], wall_plane['position'],
        False, False, False, "", "", "", True, False
    )
    part.BlankElement(skt_pl1, True)
    
    # 基本線の作成
    skt_ln1 = part.CreateSketchLine(skt_pl1, "", "作図", "0,-18500", "0,18500", False)
    skt_ln2 = part.CreateSketchLine(skt_pl1, "", "作図", "-50000,15500", "250000,15500", False)
    skt_ln3 = part.CreateSketchLine(skt_pl1, "", "作図", "-50000,-15500", "250000,-15500", False)
    
    # ケーシング関連レイヤーの作成
    skt_layer1 = part.CreateSketchLayer("Casing.Fore", skt_pl1)
    skt_ln4 = part.CreateSketchLine(skt_pl1, "", "Casing.Fore", "11370.000000000002,-10394.984078409721", "11370.000000000002,9605.0159215902786", False)
    
    skt_layer2 = part.CreateSketchLayer("Casing.Aft", skt_pl1)
    skt_ln5 = part.CreateSketchLine(skt_pl1, "", "Casing.Aft", "4019.9999999999995,-10394.984078409721", "4019.9999999999995,9605.0159215902786", False)
    
    skt_layer3 = part.CreateSketchLayer("Casing.Side.P", skt_pl1)
    skt_ln6 = part.CreateSketchLine(skt_pl1, "", "Casing.Side.P", "-1500,4800", "18500,4800", False)
    
    skt_layer4 = part.CreateSketchLayer("Casing.Side.S", skt_pl1)
    skt_ln7 = part.CreateSketchLine(skt_pl1, "", "Casing.Side.S", "-1500,-4800", "18500,-4800", False)
    
    skt_layer5 = part.CreateSketchLayer("Dim.CenterLine", skt_pl1)
    skt_ln8 = part.CreateSketchLine(skt_pl1, "", "Dim.CenterLine", "-50000,0", "250000,0", False)
    
    return skt_pl1, skt_layer1, skt_layer2, skt_layer3, skt_layer4, skt_layer5

def create_deck_sketch_planes(part):
    """デッキ関連のスケッチ平面作成"""
    
    # デッキ平面の作成（設定ファイルから取得）
    deck_plane = SKETCH_PLANES['DECK']
    skt_pl2 = part.CreateSketchPlane(
        deck_plane['name'], "", deck_plane['type'], deck_plane['position'],
        False, False, False, "", "", "", True, False
    )
    part.BlankElement(skt_pl2, True)
    
    # デッキ基本線
    skt_ln9 = part.CreateSketchLine(skt_pl2, "", "作図", "15500,31800", "15500,-2999.9999999999964", False)
    skt_ln10 = part.CreateSketchLine(skt_pl2, "", "作図", "-15499.999999999996,31800", "-15500,-2999.9999999999964", False)
    skt_ln11 = part.CreateSketchLine(skt_pl2, "", "作図", "0,-3000", "0,31799.999999999996", False)
    
    # デッキレイヤー
    skt_layer6 = part.CreateSketchLayer("General.Deck.UpperDeck", skt_pl2)
    skt_ln12 = part.CreateSketchLine(skt_pl2, "", "General.Deck.UpperDeck", "2000,15300", "18500,14933.333333333334", False)
    skt_ln13 = part.CreateSketchLine(skt_pl2, "", "General.Deck.UpperDeck", "2000,15300", "-2000,15300", False)
    skt_ln14 = part.CreateSketchLine(skt_pl2, "", "General.Deck.UpperDeck", "-2000,15300", "-18500,14933.333333333336", False)
    
    # ケーシングデッキレイヤー
    skt_layer7 = part.CreateSketchLayer("Casing.Deck.A", skt_pl2)
    skt_ln15 = part.CreateSketchLine(skt_pl2, "", "Casing.Deck.A", "18500,18300", "-18500,18300", False)
    
    skt_layer8 = part.CreateSketchLayer("Casing.Deck.B", skt_pl2)
    skt_ln16 = part.CreateSketchLine(skt_pl2, "", "Casing.Deck.B", "18500,21300", "-18500,21300", False)
    
    skt_layer9 = part.CreateSketchLayer("Casing.Deck.C", skt_pl2)
    skt_ln17 = part.CreateSketchLine(skt_pl2, "", "Casing.Deck.C", "18500,24300", "-18500,24300", False)
    
    skt_layer10 = part.CreateSketchLayer("Casing.Deck.D", skt_pl2)
    skt_ln18 = part.CreateSketchLine(skt_pl2, "", "Casing.Deck.D", "18500,27300", "-18500,27300", False)
    
    return skt_pl2, skt_layer7, skt_layer8, skt_layer9, skt_layer10

# =============================================================================
# 押し出しシートの作成
# =============================================================================
def create_extrude_sheets(part, skt_pl1, skt_pl2):
    """押し出しシートの作成"""
    
    # 設定ファイルからパラメータを取得
    extrude_params = EXTRUDE_PARAMS
    material = MATERIALS['default']
    gray_color = get_color('gray')
    
    # サイド壁の押し出し
    extrudePram1 = part.CreateLinearSweepParam()
    extrudePram1.AddProfile(skt_pl1 + ",Casing.Side.P")
    extrudePram1.DirectionType = extrude_params['direction_type']
    extrudePram1.DirectionParameter1 = extrude_params['parameter1']
    extrudePram1.DirectionParameter2 = extrude_params['parameter2']
    extrudePram1.SweepDirection = "+Z"
    extrudePram1.Name = "HK.Casing.Wall.SideP"
    extrudePram1.MaterialName = material
    extrudePram1.IntervalSweep = extrude_params['interval_sweep']
    extrude_sheet1 = part.CreateLinearSweepSheet(extrudePram1, False)
    part.SheetAlignNormal(extrude_sheet1, 0, -1, 0)
    part.BlankElement(extrude_sheet1, True)
    part.SetElementColor(extrude_sheet1, *gray_color)
    
    # デッキDの押し出し
    extrudePram2 = part.CreateLinearSweepParam()
    extrudePram2.AddProfile(skt_pl2 + ",Casing.Deck.D")
    extrudePram2.DirectionType = extrude_params['direction_type']
    extrudePram2.DirectionParameter1 = extrude_params['parameter1']
    extrudePram2.DirectionParameter2 = extrude_params['parameter2']
    extrudePram2.SweepDirection = "+X"
    extrudePram2.Name = "HK.Casing.Deck.D"
    extrudePram2.MaterialName = material
    extrudePram2.IntervalSweep = extrude_params['interval_sweep']
    extrude_sheet2 = part.CreateLinearSweepSheet(extrudePram2, False)
    part.SheetAlignNormal(extrude_sheet2, -0, 0, 1)
    part.BlankElement(extrude_sheet2, True)
    part.SetElementColor(extrude_sheet2, *gray_color)
    
    # 後部壁の押し出し
    extrudePram3 = part.CreateLinearSweepParam()
    extrudePram3.AddProfile(skt_pl1 + ",Casing.Aft")
    extrudePram3.DirectionType = extrude_params['direction_type']
    extrudePram3.DirectionParameter1 = extrude_params['parameter1']
    extrudePram3.DirectionParameter2 = extrude_params['parameter2']
    extrudePram3.SweepDirection = "+Z"
    extrudePram3.Name = "HK.Casing.Wall.Aft"
    extrudePram3.MaterialName = material
    extrudePram3.IntervalSweep = extrude_params['interval_sweep']
    extrude_sheet3 = part.CreateLinearSweepSheet(extrudePram3, False)
    part.SheetAlignNormal(extrude_sheet3, 1, 0, 0)
    part.BlankElement(extrude_sheet3, True)
    part.SetElementColor(extrude_sheet3, *gray_color)
    
    # 前部壁の押し出し
    extrudePram4 = part.CreateLinearSweepParam()
    extrudePram4.AddProfile(skt_pl1 + ",Casing.Fore")
    extrudePram4.DirectionType = extrude_params['direction_type']
    extrudePram4.DirectionParameter1 = extrude_params['parameter1']
    extrudePram4.DirectionParameter2 = extrude_params['parameter2']
    extrudePram4.SweepDirection = "+Z"
    extrudePram4.Name = "HK.Casing.Wall.Fore"
    extrudePram4.MaterialName = material
    extrudePram4.IntervalSweep = extrude_params['interval_sweep']
    extrude_sheet4 = part.CreateLinearSweepSheet(extrudePram4, False)
    part.SheetAlignNormal(extrude_sheet4, 1, 0, 0)
    part.BlankElement(extrude_sheet4, True)
    part.SetElementColor(extrude_sheet4, *gray_color)
    
    # デッキCの押し出し（追加）
    extrudePram5 = part.CreateLinearSweepParam()
    extrudePram5.AddProfile(skt_pl2 + ",Casing.Deck.C")
    extrudePram5.DirectionType = extrude_params['direction_type']
    extrudePram5.DirectionParameter1 = extrude_params['parameter1']
    extrudePram5.DirectionParameter2 = extrude_params['parameter2']
    extrudePram5.SweepDirection = "+X"
    extrudePram5.Name = "HK.Casing.Deck.C"
    extrudePram5.MaterialName = material
    extrudePram5.IntervalSweep = extrude_params['interval_sweep']
    extrude_sheet5 = part.CreateLinearSweepSheet(extrudePram5, False)
    part.SheetAlignNormal(extrude_sheet5, -0, 0, 1)
    part.BlankElement(extrude_sheet5, True)
    part.SetElementColor(extrude_sheet5, *gray_color)
    
    return extrude_sheet1, extrude_sheet2, extrude_sheet3, extrude_sheet4, extrude_sheet5

# =============================================================================
# 変数の定義
# =============================================================================
def create_variables(part):
    """設計変数の定義（設定ファイルから取得）"""
    variables = {}
    
    # フレーム位置変数の作成
    for frame_name, position in FRAME_POSITIONS.items():
        variables[frame_name] = part.CreateVariable(frame_name, str(position), "mm", "")
    
    # デッキレベル変数の作成
    for deck_name, level in DECK_LEVELS.items():
        variables[deck_name] = part.CreateVariable(deck_name, str(level), "mm", "")
    
    return variables

# =============================================================================
# プロファイル作成の統合
# =============================================================================
def create_profiles_and_brackets(part, extrude_sheets, variables):
    """プロファイルとブラケットの作成"""
    extrude_sheet1, extrude_sheet2, extrude_sheet3, extrude_sheet4, extrude_sheet5 = extrude_sheets
    
    # デッキDL02プロファイルの作成（設定ファイルのプロファイルを使用）
    profile1 = create_profile_from_config(
        part=part,
        profile_name="HK.Casing.Deck.D.DL02P",
        base_plane=create_base_plane("Casing.DL02", "Y"),  # 変数名を直接使用
        attach_surfaces=extrude_sheet2,
        profile_config_name='FLANGE_200x14x900',  # 設定ファイルから取得
        end1_elements=extrude_sheet3,
        end2_elements=extrude_sheet4
    )
    
    # サイド壁FR08プロファイルの作成（設定ファイルのプロファイルを使用）
    profile3 = create_profile_from_config(
        part=part,
        profile_name="HK.Casing.Wall.Side.FR08.CDP",
        base_plane=create_base_plane("FR8", "X"),  # 変数名を直接使用
        attach_surfaces=extrude_sheet1,
        profile_config_name='ANGLE_150x90x9',  # 設定ファイルから取得
        end1_elements=extrude_sheet2,
        end2_elements=extrude_sheet5  # デッキCシートを使用
    )
    
    print("プロファイルの作成が完了しました。")
    return profile1, profile3

# =============================================================================
# メイン実行関数
# =============================================================================
def main():
    """メイン実行関数"""
    print("EvoShip ケーシング構造モデル作成を開始します...")
    
    try:
        # 初期化
        evoship, doc, part = initialize_evoship()
        print("✓ EvoShipの初期化が完了しました")
        
        # スケッチ平面とレイヤーの作成
        skt_pl1, skt_layer1, skt_layer2, skt_layer3, skt_layer4, skt_layer5 = create_sketch_planes_and_layers(part)
        skt_pl2, skt_layer7, skt_layer8, skt_layer9, skt_layer10 = create_deck_sketch_planes(part)
        print("✓ スケッチ平面とレイヤーの作成が完了しました")
        
        # 押し出しシートの作成
        extrude_sheets = create_extrude_sheets(part, skt_pl1, skt_pl2)
        print("✓ 押し出しシートの作成が完了しました")
        
        # 変数の定義
        variables = create_variables(part)
        print("✓ 設計変数の定義が完了しました")
        
        # プロファイルとブラケットの作成
        profiles = create_profiles_and_brackets(part, extrude_sheets, variables)
        print("✓ プロファイルとブラケットの作成が完了しました")
        
        print("🎉 ケーシング構造モデルの作成が完了しました！")
        
        return evoship, doc, part
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    main() 