"""
プロファイル作成モジュール
EvoShip ケーシング構造のプロファイル（構造材）作成を担当
"""

from config import (
    MATERIALS, COLORS, STANDARD_PROFILES, END_ELEMENT_TYPES, 
    SCALLOP_TYPES, BRACKET_TYPES, DIMENSION_TYPES, 
    get_color, get_profile_params
)

def create_profile_parameters(part, profile_type, profile_params, material=None):
    """プロファイルパラメータの作成"""
    if material is None:
        material = MATERIALS['default']
    
    profile_param = part.CreateProfileParam()
    profile_param.DefinitionType = 1
    profile_param.MaterialName = material
    profile_param.ProfileType = profile_type
    profile_param.ProfileParams = profile_params
    profile_param.Mold = "+"
    profile_param.ReverseDir = True
    profile_param.ReverseAngle = False
    profile_param.CalcSnipOnlyAttachLines = False
    profile_param.AttachDirMethod = 0
    profile_param.CCWDefAngle = False
    
    return profile_param

def create_deck_profile(part, extrude_sheet2, extrude_sheet3, extrude_sheet4, var_elm2):
    """デッキDL02プロファイルの作成"""
    # 設定ファイルからフランジプロファイルのパラメータを取得
    flange_params = get_profile_params('FLANGE_200x14x900')
    
    ProfilePram1 = create_profile_parameters(
        part, 
        flange_params['type'], 
        flange_params['params']
    )
    ProfilePram1.BasePlane = "PL,O," + var_elm2 + "," + "Y"
    ProfilePram1.AddAttachSurfaces(extrude_sheet2)
    ProfilePram1.ProfileName = "HK.Casing.Deck.D.DL02P"
    ProfilePram1.FlangeName = "HK.Casing.Deck.D.DL02P"
    ProfilePram1.FlangeMaterialName = MATERIALS['default']
    ProfilePram1.Mold = "-"
    ProfilePram1.ReverseDir = True
    ProfilePram1.ReverseAngle = False
    
    # エンド要素の設定（設定ファイルから取得）
    flange_end = END_ELEMENT_TYPES['FLANGE']
    ProfilePram1.AddEnd1Elements(extrude_sheet3)
    ProfilePram1.End1Type = flange_end['type']
    ProfilePram1.End1TypeParams = flange_end['params']
    ProfilePram1.AddEnd2Elements(extrude_sheet4)
    ProfilePram1.End2Type = flange_end['type']
    ProfilePram1.End2TypeParams = flange_end['params']
    
    # スカルロップ設定（設定ファイルから取得）
    standard_scallop = SCALLOP_TYPES['STANDARD']
    ProfilePram1.End1ScallopType = standard_scallop['type']
    ProfilePram1.End1ScallopTypeParams = standard_scallop['params']
    ProfilePram1.End2ScallopType = standard_scallop['type']
    ProfilePram1.End2ScallopTypeParams = standard_scallop['params']
    
    profile1 = part.CreateProfile(ProfilePram1, False)
    purple_color = get_color('purple')
    part.BlankElement(profile1[0], True)
    part.SetElementColor(profile1[0], *purple_color)
    part.BlankElement(profile1[1], True)
    part.SetElementColor(profile1[1], *purple_color)
    
    return profile1

def create_side_wall_profile(part, extrude_sheet1, extrude_sheet2, extrude_sheet5, var_elm3):
    """サイド壁FR08プロファイルの作成"""
    # 設定ファイルからアングルプロファイルのパラメータを取得
    angle_params = get_profile_params('ANGLE_150x90x9')
    
    ProfilePram3 = create_profile_parameters(
        part, 
        angle_params['type'], 
        angle_params['params']
    )
    ProfilePram3.BasePlane = "PL,O," + var_elm3 + "," + "X"
    ProfilePram3.AddAttachSurfaces(extrude_sheet1)
    ProfilePram3.ProfileName = "HK.Casing.Wall.Side.FR08.CDP"
    ProfilePram3.ReverseDir = False
    ProfilePram3.ReverseAngle = True
    
    # エンド要素の設定（設定ファイルから取得）
    standard_end = END_ELEMENT_TYPES['STANDARD']
    ProfilePram3.AddEnd1Elements(extrude_sheet2)
    ProfilePram3.End1Type = standard_end['type']
    ProfilePram3.End1TypeParams = standard_end['params']
    ProfilePram3.AddEnd2Elements(extrude_sheet5)
    ProfilePram3.End2Type = standard_end['type']
    ProfilePram3.End2TypeParams = standard_end['params']
    
    # スカルロップ設定（設定ファイルから取得）
    angle_scallop = SCALLOP_TYPES['ANGLE']
    ProfilePram3.End1ScallopType = angle_scallop['type']
    ProfilePram3.End1ScallopTypeParams = angle_scallop['params']
    ProfilePram3.End2ScallopType = angle_scallop['type']
    ProfilePram3.End2ScallopTypeParams = angle_scallop['params']
    
    profile3 = part.CreateProfile(ProfilePram3, False)
    red_color = get_color('red')
    part.BlankElement(profile3[0], True)
    part.SetElementColor(profile3[0], *red_color)
    
    return profile3

def create_bracket_parameters(part, bracket_name, base_element, material=None):
    """ブラケットパラメータの作成"""
    if material is None:
        material = MATERIALS['default']
    
    # 設定ファイルからブラケットタイプを取得
    bracket_type = BRACKET_TYPES['STANDARD']
    
    bracket_param = part.CreateBracketParam()
    bracket_param.DefinitionType = 1
    bracket_param.BracketName = bracket_name
    bracket_param.MaterialName = material
    bracket_param.BaseElement = base_element
    bracket_param.UseSideSheetForPlane = False
    bracket_param.Mold = "+"
    bracket_param.Thickness = bracket_type['thickness']
    bracket_param.BracketType = bracket_type['type']
    bracket_param.Scallop1Type = 1801
    bracket_param.Scallop1Params = ["0"]
    bracket_param.Scallop2Type = 0
    
    return bracket_param

def create_deck_bracket(part, profile_element, profile_flange, bracket_name):
    """デッキブラケットの作成"""
    bracket_param = create_bracket_parameters(part, bracket_name, profile_element)
    bracket_param.Surfaces1 = [profile_element + ",FL"]
    bracket_param.RevSf1 = False
    bracket_param.Surfaces2 = [profile_flange + ",FL"]
    bracket_param.RevSf2 = False
    bracket_param.RevSf3 = False
    
    # 寸法設定（設定ファイルから取得）
    standard_dim = DIMENSION_TYPES['STANDARD']
    bracket_param.Sf1DimensionType = standard_dim['type']
    bracket_param.Sf1DimensonParams = standard_dim['params']
    bracket_param.Sf2DimensionType = standard_dim['type']
    bracket_param.Sf2DimensonParams = standard_dim['params']
    
    bracket = part.CreateBracket(bracket_param, False)
    cyan_color = get_color('cyan')
    part.BlankElement(bracket, True)
    part.SetElementColor(bracket, *cyan_color)
    
    return bracket

def create_solid_structure(part, solid_name, extrude_sheet, thickness="10"):
    """ソリッド構造の作成"""
    solid = part.CreateSolid(solid_name, "", MATERIALS['default'])
    brown_color = get_color('brown')
    part.BlankElement(solid, True)
    part.SetElementColor(solid, *brown_color)
    
    thicken = part.CreateThicken("厚み付け", solid, "+", [extrude_sheet], "+", thickness, "0", "0", False, False)
    
    return solid, thicken

def create_mirror_copy(part, elements, mirror_plane="PL,Y"):
    """ミラーコピーの作成"""
    mirror_copied = part.MirrorCopy(elements, mirror_plane, "")
    purple_color = get_color('purple')
    part.BlankElement(mirror_copied[0], True)
    part.SetElementColor(mirror_copied[0], *purple_color)
    
    return mirror_copied

def create_body_division(part, body_name, target_body, division_plane):
    """ボディ分割の作成"""
    separated_bodies = part.BodyDivideByCurves(body_name, target_body, [division_plane], False, "0", "", "", False)
    
    # 色設定（設定ファイルから取得）
    cyan_color = get_color('cyan')
    part.SetElementColor(separated_bodies[0], *cyan_color)
    
    return separated_bodies

# プロファイル作成のヘルパー関数
def setup_profile_end_elements(profile_param, end1_elements, end2_elements):
    """プロファイルのエンド要素設定（設定ファイルから取得）"""
    standard_end = END_ELEMENT_TYPES['STANDARD']
    standard_scallop = SCALLOP_TYPES['STANDARD']
    
    if end1_elements:
        profile_param.AddEnd1Elements(end1_elements)
        profile_param.End1Type = standard_end['type']
        profile_param.End1TypeParams = standard_end['params']
        profile_param.End1ScallopType = standard_scallop['type']
        profile_param.End1ScallopTypeParams = standard_scallop['params']
    
    if end2_elements:
        profile_param.AddEnd2Elements(end2_elements)
        profile_param.End2Type = standard_end['type']
        profile_param.End2TypeParams = standard_end['params']
        profile_param.End2ScallopType = standard_scallop['type']
        profile_param.End2ScallopTypeParams = standard_scallop['params']

def create_standard_profile(part, profile_name, base_plane, attach_surfaces, 
                          profile_type, profile_params, end1_elements=None, end2_elements=None):
    """標準プロファイル作成関数"""
    profile_param = create_profile_parameters(part, profile_type, profile_params)
    profile_param.BasePlane = base_plane
    profile_param.AddAttachSurfaces(attach_surfaces)
    profile_param.ProfileName = profile_name
    
    setup_profile_end_elements(profile_param, end1_elements, end2_elements)
    
    profile = part.CreateProfile(profile_param, False)
    red_color = get_color('red')
    part.BlankElement(profile[0], True)
    part.SetElementColor(profile[0], *red_color)
    
    return profile

def create_profile_from_config(part, profile_name, base_plane, attach_surfaces, 
                              profile_config_name, end1_elements=None, end2_elements=None):
    """設定ファイルからプロファイルを作成"""
    profile_config = get_profile_params(profile_config_name)
    if not profile_config:
        raise ValueError(f"プロファイル設定 '{profile_config_name}' が見つかりません")
    
    return create_standard_profile(
        part=part,
        profile_name=profile_name,
        base_plane=base_plane,
        attach_surfaces=attach_surfaces,
        profile_type=profile_config['type'],
        profile_params=profile_config['params'],
        end1_elements=end1_elements,
        end2_elements=end2_elements
    ) 