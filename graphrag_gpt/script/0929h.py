import win32com.client
evoship = win32com.client.DispatchEx("EvoShip.Application")
evoship.ShowMainWindow(True)
doc = evoship.Create3DDocument()
part = doc.GetPart()
skt_pl1 = part.CreateSketchPlane("スケッチ2","","PL,Z","0",False,False,False,"","","",False,False)
part.BlankElement(skt_pl1,True)
skt_ln1 = part.CreateSketchLine(skt_pl1,"","デフォルト","27.002899867463938,-5.1232415479819116","220.36369998854195,-5.1232415479819116",False)
skt_ln2 = part.CreateSketchLine(skt_pl1,"","デフォルト","220.36369998854195,-5.1232415479819116","220.36369998854195,208.37764962333941",False)
skt_ln3 = part.CreateSketchLine(skt_pl1,"","デフォルト","220.36369998854195,208.37764962333941","27.002899867463931,208.37764962333941",False)
skt_ln4 = part.CreateSketchLine(skt_pl1,"","デフォルト","27.002899867463938,208.37764962333941","27.002899867463938,-5.1232415479819107",False)
skt_arc1 = part.CreateSketchCircle(skt_pl1,"円1","デフォルト","123.683299928,101.627204037","50",True,True,False)

solid1 = part.CreateSolid("ソリッド1","","SS400")
part.SetElementColor(solid1,"225","225","225","0")
extrudePram1 = part.CreateLinearSweepParam()
extrudePram1.Name="押し出し1"
extrudePram1.AddProfile(skt_pl1)
extrudePram1.DirectionType="N"
extrudePram1.DirectionParameter1="10"
extrudePram1.RefByGeometricMethod=False
extrude1 = part.CreateLinearSweep(solid1,"+",extrudePram1,False)

extrudePram2 = part.CreateLinearSweepParam()
extrudePram2.Name="押し出しカット1"
extrudePram2.AddProfile(skt_arc1)
extrudePram2.DirectionType="T"
extrudePram2.RefByGeometricMethod=False
extrude2 = part.CreateLinearSweep(solid1,"-",extrudePram2,False)
pillar_size = 20.0
pillar_height = 50.0 
min_x = 27.002899867463938
max_x = 220.36369998854195
min_y = -5.1232415479819116
max_y = 208.37764962333941
skt_pl_pillar = part.CreateSketchPlane("柱スケッチ","","PL,Z","10",False,False,False,"","","",False,False)
part.BlankElement(skt_pl_pillar,True)

def draw_rect_on_plane(plane, x1, y1, x2, y2):
    part.CreateSketchLine(plane,"","デフォルト",f"{x1},{y1}",f"{x2},{y1}",False)
    part.CreateSketchLine(plane,"","デフォルト",f"{x2},{y1}",f"{x2},{y2}",False)
    part.CreateSketchLine(plane,"","デフォルト",f"{x2},{y2}",f"{x1},{y2}",False)
    part.CreateSketchLine(plane,"","デフォルト",f"{x1},{y2}",f"{x1},{y1}",False)
draw_rect_on_plane(skt_pl_pillar, min_x, min_y, min_x + pillar_size, min_y + pillar_size)

draw_rect_on_plane(skt_pl_pillar, max_x - pillar_size, min_y, max_x, min_y + pillar_size)

draw_rect_on_plane(skt_pl_pillar, max_x - pillar_size, max_y - pillar_size, max_x, max_y)

draw_rect_on_plane(skt_pl_pillar, min_x, max_y - pillar_size, min_x + pillar_size, max_y)

extrudePram3 = part.CreateLinearSweepParam()
extrudePram3.Name = "柱押し出し"
extrudePram3.AddProfile(skt_pl_pillar)
extrudePram3.DirectionType = "N"
extrudePram3.DirectionParameter1 = str(pillar_height)
extrudePram3.RefByGeometricMethod = False
extrude3 = part.CreateLinearSweep(solid1, "+", extrudePram3, False)
