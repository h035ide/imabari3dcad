"""
EvoShip ケーシング構造モデル作成の使用例
3つのファイル（config.py, profile_creation.py, samplecasing_name_organized.py）の連携例
"""

from samplecasing_name_organized import main
from config import FRAME_POSITIONS, DECK_LEVELS, STANDARD_PROFILES
from profile_creation import create_profile_from_config

def example_basic_usage():
    """基本的な使用方法の例"""
    print("=== 基本的な使用方法 ===")
    
    # メインスクリプトを実行
    evoship, doc, part = main()
    
    print("基本モデルの作成が完了しました。")
    return evoship, doc, part

def example_config_modification():
    """設定変更の例"""
    print("=== 設定変更の例 ===")
    
    # フレーム位置の変更
    original_fr9 = FRAME_POSITIONS['FR9']
    FRAME_POSITIONS['FR9'] = 6500  # 6030から6500に変更
    print(f"FR9の位置を {original_fr9}mm から {FRAME_POSITIONS['FR9']}mm に変更しました")
    
    # デッキレベルの変更
    original_dl02 = DECK_LEVELS['Casing.DL02']
    DECK_LEVELS['Casing.DL02'] = 1800  # 1600から1800に変更
    print(f"Casing.DL02のレベルを {original_dl02}mm から {DECK_LEVELS['Casing.DL02']}mm に変更しました")
    
    # 変更された設定でメインスクリプトを実行
    evoship, doc, part = main()
    
    print("設定変更後のモデル作成が完了しました。")
    return evoship, doc, part

def example_profile_creation():
    """プロファイル作成の例"""
    print("=== プロファイル作成の例 ===")
    
    # まず基本モデルを作成
    evoship, doc, part = main()
    
    # 追加のプロファイルを作成
    # 例：デッキCシートを作成（実際のコードでは適切なシートが必要）
    print("追加のプロファイルを作成中...")
    
    # 設定ファイルからプロファイルを作成する例
    try:
        # アングルプロファイルの作成例
        profile = create_profile_from_config(
            part=part,
            profile_name="HK.Casing.Wall.Side.FR10.CDP",
            base_plane="PL,O,FR10,X",  # FR10の位置
            attach_surfaces="extrude_sheet1",  # 実際のシート要素
            profile_config_name="ANGLE_150x90x9"
        )
        print("✓ アングルプロファイルの作成が完了しました")
        
    except Exception as e:
        print(f"プロファイル作成でエラーが発生しました: {e}")
    
    return evoship, doc, part

def example_advanced_usage():
    """高度な使用方法の例"""
    print("=== 高度な使用方法 ===")
    
    # 設定の一括変更
    modifications = {
        'FRAME_POSITIONS': {
            'FR9': 6500,
            'FR10': 7000,
            'FR11': 7700
        },
        'DECK_LEVELS': {
            'Casing.DL02': 1800,
            'Casing.DL03': 2600
        }
    }
    
    # 設定を適用
    for category, changes in modifications.items():
        if category == 'FRAME_POSITIONS':
            for key, value in changes.items():
                FRAME_POSITIONS[key] = value
                print(f"{key}の位置を {value}mm に変更しました")
        elif category == 'DECK_LEVELS':
            for key, value in changes.items():
                DECK_LEVELS[key] = value
                print(f"{key}のレベルを {value}mm に変更しました")
    
    # 変更された設定でモデルを作成
    evoship, doc, part = main()
    
    print("高度な設定変更後のモデル作成が完了しました。")
    return evoship, doc, part

def example_error_handling():
    """エラーハンドリングの例"""
    print("=== エラーハンドリングの例 ===")
    
    try:
        # 存在しないプロファイル設定を使用しようとする
        profile = create_profile_from_config(
            part=None,  # 無効なpart
            profile_name="Test.Profile",
            base_plane="PL,O,FR1,X",
            attach_surfaces="test_sheet",
            profile_config_name="NON_EXISTENT_PROFILE"
        )
    except ValueError as e:
        print(f"設定エラー: {e}")
    except Exception as e:
        print(f"予期しないエラー: {e}")
    
    print("エラーハンドリングのテストが完了しました。")

def main_example():
    """メイン実行例"""
    print("🚢 EvoShip ケーシング構造モデル作成システム")
    print("=" * 50)
    
    # 使用例の選択
    examples = {
        '1': ("基本的な使用方法", example_basic_usage),
        '2': ("設定変更の例", example_config_modification),
        '3': ("プロファイル作成の例", example_profile_creation),
        '4': ("高度な使用方法", example_advanced_usage),
        '5': ("エラーハンドリングの例", example_error_handling)
    }
    
    print("使用例を選択してください:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print("  q. 終了")
    
    while True:
        choice = input("\n選択してください (1-5, q): ").strip()
        
        if choice.lower() == 'q':
            print("終了します。")
            break
        
        if choice in examples:
            name, func = examples[choice]
            print(f"\n{name}を実行します...")
            try:
                result = func()
                print(f"{name}が正常に完了しました。")
            except Exception as e:
                print(f"{name}でエラーが発生しました: {e}")
        else:
            print("無効な選択です。1-5またはqを入力してください。")

if __name__ == "__main__":
    main_example() 