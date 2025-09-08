query1

MATCH (m:Method)
WHERE
  (
    (m.name IS NOT NULL AND (
      toLower(m.name) CONTAINS 'thicken' OR
      toLower(m.name) CONTAINS 'shell' OR
      toLower(m.name) CONTAINS 'offset'
    )) OR
    (m.description IS NOT NULL AND (
      m.description CONTAINS '厚み' OR
      m.description CONTAINS '厚み付け' OR
      m.description CONTAINS '厚みづけ' OR
      m.description CONTAINS 'オフセット'
    ))
  )
  AND EXISTS {
    MATCH (m)-[:HAS_PARAMETER]->(pT:Parameter)
    WHERE pT.name IS NOT NULL AND (toLower(pT.name) CONTAINS 'thick' OR pT.name CONTAINS '厚み')
  }
  AND EXISTS {
    MATCH (m)-[:HAS_PARAMETER]->(pS:Parameter)
    WHERE pS.name IS NOT NULL AND (toLower(pS.name) CONTAINS 'solid' OR toLower(pS.name) CONTAINS 'body' OR pS.name CONTAINS 'ソリッド')
  }
OPTIONAL MATCH (m)-[:BELONGS_TO]->(o:Object)
OPTIONAL MATCH (m)-[:HAS_PARAMETER]->(p:Parameter)
OPTIONAL MATCH (p)-[:HAS_TYPE]->(pt:DataType)
OPTIONAL MATCH (m)-[:HAS_RETURNS]->(rv:ReturnValue)
OPTIONAL MATCH (rv)-[:HAS_TYPE]->(rt:DataType)
WITH m, o,
     collect(DISTINCT {id:p.id, name:p.name, order:p.order, description:p.description, typeId:pt.id, typeName:pt.name}) AS parameters,
     rv, rt
RETURN
  m.id AS methodId,
  m.name AS methodName,
  m.description AS methodDescription,
  o.id AS objectId,
  o.name AS objectName,
  parameters,
  rv.id AS returnId,
  rv.description AS returnDescription,
  rt.id AS returnTypeId,
  rt.name AS returnTypeName
ORDER BY methodName
Full Context:
[{'methodId': 'CreateThicken', 'methodName': 'CreateThicken', 'methodDescription': '指定したソリッド要素に指定要素厚みづけした形状を作成する', 'objectId': 'part', 'objectName': 'part', 'parameters': [{'typeName': '長さ', 'id': 'CreateThicken_Thickeness1', 'order': 5, 'description': '板厚', 'name': 'Thickeness1', 'typeId': '長さ'}, {'typeName': '要素', 'id': 'CreateThicken_Sheet', 'order': 3, 'description': '厚み付けをするシートやフェイス', 'name': 'Sheet', 'typeId': '要素'}, {'typeName': '長さ', 'id': 'CreateThicken_Thickeness2', 'order': 6, 'description': '板厚２（厚み付けタイプが２方向のときに使用）', 'name': 'Thickeness2', 'typeId': '長さ'}, {'typeName': '厚み付けタイプ', 'id': 'CreateThicken_ThickenType', 'order': 4, 'description': '', 'name': 'ThickenType', 'typeId': '厚み付けタイプ'}, {'typeName': '文字列', 'id': 'CreateThicken_ThickenFeatureName', 'order': 0, 'description': '作成する厚みづけフィーチャー要素名称（空文字可）', 'name': 'ThickenFeatureName', 'typeId': '文字列'}, {'typeName': 'bool', 'id': 'CreateThicken_bUpdate', 'order': 9, 'description': '更新フラグ（未実装、使用しない）', 'name': 'bUpdate', 'typeId': 'bool'}, {'typeName': '長さ', 'id': 'CreateThicken_ThickenessOffset', 'order': 7, 'description': '厚みづけをするシート、フェイス要素のオフセット距離', 'name': 'ThickenessOffset', 'typeId': '長さ'}, {'typeName': '関連設定', 'id': 'CreateThicken_ReferMethod', 'order': 8, 'description': '要素の関連づけ方法の指定', 'name': 'ReferMethod', 'typeId': '関連設定'}, {'typeName': '要素', 'id': 'CreateThicken_TargetSolidName', 'order': 1, 'description': '厚みづけフィーチャーを作成する対象のソリッドを指定', 'name': 'TargetSolidName', 'typeId': '要素'}, {'typeName': 'オペレーションタイプ', 'id': 'CreateThicken_OperationType', 'order': 2, 'description': 'ソリッドオペレーションのタイプを指定する', 'name': 'OperationType', 'typeId': 'オペレーションタイプ'}], 'returnId': 'CreateThicken_ReturnValue', 'returnDescription': '作成された厚みづけフィーチャーのID', 'returnTypeId': '不明', 'returnTypeName': '不明'}]


query2

MATCH (m:Method)-[:BELONGS_TO]->(o:Object)
WHERE toLower(coalesce(m.name,'')) CONTAINS 'thicken'
   OR toLower(coalesce(m.name,'')) CONTAINS 'thickness'
   OR toLower(coalesce(m.name,'')) CONTAINS 'offset'
   OR toLower(coalesce(m.name,'')) CONTAINS 'shell'
   OR coalesce(m.description,'') CONTAINS '厚み'
   OR coalesce(m.description,'') CONTAINS 'オフセット'
   OR toLower(coalesce(o.name,'')) CONTAINS 'solid'
   OR o.name CONTAINS 'ソリッド'
OPTIONAL MATCH (m)-[:HAS_PARAMETER]->(p:Parameter)
OPTIONAL MATCH (p)-[:HAS_TYPE]->(pt:DataType)
OPTIONAL MATCH (m)-[:HAS_RETURNS]->(r:ReturnValue)
OPTIONAL MATCH (r)-[:HAS_TYPE]->(rt:DataType)
WITH m,o,r,rt,p,pt
ORDER BY m.name, p.order
WITH o,m,
     collect({order:p.order, id:p.id, name:p.name, description:p.description, type:pt.name, typeId:pt.id}) AS parameters,
     coalesce(rt.id,'') AS returnTypeId,
     coalesce(rt.name,'') AS returnType
RETURN o.id AS objectId, o.name AS objectName,
       m.id AS methodId, m.name AS methodName, m.description AS methodDescription,
       parameters, returnTypeId, returnType
ORDER BY objectName, methodName
