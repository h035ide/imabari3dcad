#!/usr/bin/env python3
"""
生成されたキューブ作成コードのテスト
"""

from typing import Dict, List

def CreateSolid(side_length_mm: float) -> Dict[str, List[List[float]]]:
    # Create a cube with the given side length in millimeters
    s = float(side_length_mm)

    # 8 vertices of the cube (0 <= x,y,z <= s)
    vertices: List[List[float]] = [
        [0.0, 0.0, 0.0],  # 0
        [s,   0.0, 0.0],  # 1
        [s,   s,   0.0],  # 2
        [0.0, s,   0.0],  # 3
        [0.0, 0.0, s],    # 4
        [s,   0.0, s],    # 5
        [s,   s,   s],    # 6
        [0.0, s,   s],    # 7
    ]

    # 12 triangles to form the cube
    faces: List[List[int]] = [
        [0, 1, 2], [0, 2, 3],  # bottom
        [4, 5, 6], [4, 6, 7],  # top
        [0, 1, 5], [0, 5, 4],  # front
        [3, 2, 6], [3, 6, 7],  # back
        [1, 2, 6], [1, 6, 5],  # right
        [0, 3, 7], [0, 7, 4],  # left
    ]

    return {'vertices': vertices, 'faces': faces}

def create_cube(side_length_mm: float) -> Dict[str, List[List[float]]]:
    # Convenience alias for readability
    return CreateSolid(side_length_mm)

if __name__ == '__main__':
    print("=== キューブ作成テスト ===")
    
    # 50mmのキューブを作成
    mesh = CreateSolid(50.0)
    
    print(f"頂点数: {len(mesh['vertices'])}")
    print(f"面数: {len(mesh['faces'])}")
    
    print("\n頂点座標:")
    for i, vertex in enumerate(mesh['vertices']):
        print(f"  頂点{i}: ({vertex[0]:.1f}, {vertex[1]:.1f}, {vertex[2]:.1f})")
    
    print("\n面の構成:")
    for i, face in enumerate(mesh['faces']):
        print(f"  面{i}: 頂点{face[0]}, {face[1]}, {face[2]}")
    
    # 体積の計算（検証用）
    side_length = 50.0
    volume = side_length ** 3
    print(f"\n体積: {volume:.1f} mm³")
    
    print("\n✅ テスト完了！")
