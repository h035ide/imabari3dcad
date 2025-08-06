import ezdxf

import ezdxf

def create_cube(dwg, center=(0, 0, 0), size=10):
    """
    DXF に 3DFACE を使用して立方体を作成する
    :param dwg: ezdxf の drawing オブジェクト
    :param center: 立方体の中心座標 (x, y, z)
    :param size: 立方体の一辺の長さ
    """
    modelspace = dwg.modelspace()
    half = size / 2

    # 頂点座標 (x, y, z)
    vertices = [
        (center[0] - half, center[1] - half, center[2] - half),  # v0
        (center[0] + half, center[1] - half, center[2] - half),  # v1
        (center[0] + half, center[1] + half, center[2] - half),  # v2
        (center[0] - half, center[1] + half, center[2] - half),  # v3
        (center[0] - half, center[1] - half, center[2] + half),  # v4
        (center[0] + half, center[1] - half, center[2] + half),  # v5
        (center[0] + half, center[1] + half, center[2] + half),  # v6
        (center[0] - half, center[1] + half, center[2] + half),  # v7
    ]

    # 各面を 3DFACE で作成
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # 底面
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # 上面
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # 側面1
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # 側面2
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # 側面3
        [vertices[3], vertices[0], vertices[4], vertices[7]],  # 側面4
    ]

    for face in faces:
        modelspace.add_3dface(face)

# DXFファイル作成
doc = ezdxf.new()
create_cube(doc, center=(0, 0, 0), size=10)
doc.saveas("cube.dxf")
