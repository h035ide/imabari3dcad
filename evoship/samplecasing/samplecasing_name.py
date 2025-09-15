import win32com.client
evoship = win32com.client.DispatchEx("EvoShip.Application")
evoship.ShowMainWindow(True)
doc = evoship.Create3DDocument()
part = doc.GetPart()
skt_pl1 = part.CreateSketchPlane("HK.Az.Wall","","PL,Z","0",False,False,False,"","","",True,False)
part.BlankElement(skt_pl1,True)
skt_ln1 = part.CreateSketchLine(skt_pl1,"","作図","0,-18500","0,18500",False)
skt_ln2 = part.CreateSketchLine(skt_pl1,"","作図","-50000,15500","250000,15500",False)
skt_ln3 = part.CreateSketchLine(skt_pl1,"","作図","-50000,-15500","250000,-15500",False)
skt_layer1 = part.CreateSketchLayer("Casing.Fore",skt_pl1)
skt_ln4 = part.CreateSketchLine(skt_pl1,"","Casing.Fore","11370.000000000002,-10394.984078409721","11370.000000000002,9605.0159215902786",False)
skt_layer2 = part.CreateSketchLayer("Casing.Aft",skt_pl1)
skt_ln5 = part.CreateSketchLine(skt_pl1,"","Casing.Aft","4019.9999999999995,-10394.984078409721","4019.9999999999995,9605.0159215902786",False)
skt_layer3 = part.CreateSketchLayer("Casing.Side.P",skt_pl1)
skt_ln6 = part.CreateSketchLine(skt_pl1,"","Casing.Side.P","-1500,4800","18500,4800",False)
skt_layer4 = part.CreateSketchLayer("Casing.Side.S",skt_pl1)
skt_ln7 = part.CreateSketchLine(skt_pl1,"","Casing.Side.S","-1500,-4800","18500,-4800",False)
skt_layer5 = part.CreateSketchLayer("Dim.CenterLine",skt_pl1)
skt_ln8 = part.CreateSketchLine(skt_pl1,"","Dim.CenterLine","-50000,0","250000,0",False)
extrudePram1 = part.CreateLinearSweepParam()
extrudePram1.AddProfile(skt_pl1+",Casing.Side.P")
extrudePram1.DirectionType="2"
extrudePram1.DirectionParameter1="50000"
extrudePram1.DirectionParameter2="10000"
extrudePram1.SweepDirection="+Z"
extrudePram1.Name="HK.Casing.Wall.SideP"
extrudePram1.MaterialName="SS400"
extrudePram1.IntervalSweep=False
extrude_sheet1 = part.CreateLinearSweepSheet(extrudePram1,False)
part.SheetAlignNormal(extrude_sheet1,0,-1,0)
part.BlankElement(extrude_sheet1,True)
part.SetElementColor(extrude_sheet1,"225","225","225","1")
skt_pl2 = part.CreateSketchPlane("HK.Ax.Deck","","PL,X","0",False,False,False,"","","",True,False)
part.BlankElement(skt_pl2,True)
skt_ln9 = part.CreateSketchLine(skt_pl2,"","作図","15500,31800","15500,-2999.9999999999964",False)
skt_ln10 = part.CreateSketchLine(skt_pl2,"","作図","-15499.999999999996,31800","-15500,-2999.9999999999964",False)
skt_ln11 = part.CreateSketchLine(skt_pl2,"","作図","0,-3000","0,31799.999999999996",False)
skt_layer6 = part.CreateSketchLayer("General.Deck.UpperDeck",skt_pl2)
skt_ln12 = part.CreateSketchLine(skt_pl2,"","General.Deck.UpperDeck","2000,15300","18500,14933.333333333334",False)
skt_ln13 = part.CreateSketchLine(skt_pl2,"","General.Deck.UpperDeck","2000,15300","-2000,15300",False)
skt_ln14 = part.CreateSketchLine(skt_pl2,"","General.Deck.UpperDeck","-2000,15300","-18500,14933.333333333336",False)
skt_layer7 = part.CreateSketchLayer("Casing.Deck.A",skt_pl2)
skt_ln15 = part.CreateSketchLine(skt_pl2,"","Casing.Deck.A","18500,18300","-18500,18300",False)
skt_layer8 = part.CreateSketchLayer("Casing.Deck.B",skt_pl2)
skt_ln16 = part.CreateSketchLine(skt_pl2,"","Casing.Deck.B","18500,21300","-18500,21300",False)
skt_layer9 = part.CreateSketchLayer("Casing.Deck.C",skt_pl2)
skt_ln17 = part.CreateSketchLine(skt_pl2,"","Casing.Deck.C","18500,24300","-18500,24300",False)
skt_layer10 = part.CreateSketchLayer("Casing.Deck.D",skt_pl2)
skt_ln18 = part.CreateSketchLine(skt_pl2,"","Casing.Deck.D","18500,27300","-18500,27300",False)
extrudePram2 = part.CreateLinearSweepParam()
extrudePram2.AddProfile(skt_pl2+",Casing.Deck.D")
extrudePram2.DirectionType="2"
extrudePram2.DirectionParameter1="50000"
extrudePram2.DirectionParameter2="10000"
extrudePram2.SweepDirection="+X"
extrudePram2.Name="HK.Casing.Deck.D"
extrudePram2.MaterialName="SS400"
extrudePram2.IntervalSweep=False
extrude_sheet2 = part.CreateLinearSweepSheet(extrudePram2,False)
part.SheetAlignNormal(extrude_sheet2,-0,0,1)
part.BlankElement(extrude_sheet2,True)
part.SetElementColor(extrude_sheet2,"225","225","225","1")
var_elm1 = part.CreateVariable("FR9","6030","mm","")
extrudePram3 = part.CreateLinearSweepParam()
extrudePram3.AddProfile(skt_pl1+",Casing.Aft")
extrudePram3.DirectionType="2"
extrudePram3.DirectionParameter1="50000"
extrudePram3.DirectionParameter2="10000"
extrudePram3.SweepDirection="+Z"
extrudePram3.Name="HK.Casing.Wall.Aft"
extrudePram3.MaterialName="SS400"
extrudePram3.IntervalSweep=False
extrude_sheet3 = part.CreateLinearSweepSheet(extrudePram3,False)
part.SheetAlignNormal(extrude_sheet3,1,0,0)
part.BlankElement(extrude_sheet3,True)
part.SetElementColor(extrude_sheet3,"225","225","225","1")
extrudePram4 = part.CreateLinearSweepParam()
extrudePram4.AddProfile(skt_pl1+",Casing.Fore")
extrudePram4.DirectionType="2"
extrudePram4.DirectionParameter1="50000"
extrudePram4.DirectionParameter2="10000"
extrudePram4.SweepDirection="+Z"
extrudePram4.Name="HK.Casing.Wall.Fore"
extrudePram4.MaterialName="SS400"
extrudePram4.IntervalSweep=False
extrude_sheet4 = part.CreateLinearSweepSheet(extrudePram4,False)
part.SheetAlignNormal(extrude_sheet4,1,0,0)
part.BlankElement(extrude_sheet4,True)
part.SetElementColor(extrude_sheet4,"225","225","225","1")
var_elm2 = part.CreateVariable("Casing.DL02","1600","mm","")
ProfilePram1 = part.CreateProfileParam()
ProfilePram1.DefinitionType=1
ProfilePram1.BasePlane="PL,O,"+var_elm2+","+"Y"
ProfilePram1.AddAttachSurfaces(extrude_sheet2)
ProfilePram1.ProfileName="HK.Casing.Deck.D.DL02P"
ProfilePram1.MaterialName="SS400"
ProfilePram1.FlangeName="HK.Casing.Deck.D.DL02P"
ProfilePram1.FlangeMaterialName="SS400"
ProfilePram1.ProfileType=1201
ProfilePram1.ProfileParams=["200","14","900","10"]
ProfilePram1.Mold="-"
ProfilePram1.ReverseDir=True
ProfilePram1.ReverseAngle=False
ProfilePram1.CalcSnipOnlyAttachLines=False
ProfilePram1.AttachDirMethod=0
ProfilePram1.CCWDefAngle=False
ProfilePram1.AddEnd1Elements(extrude_sheet3)
ProfilePram1.End1Type=1102
ProfilePram1.End1TypeParams=["25","14.999999999999998","0","0"]
ProfilePram1.AddEnd2Elements(extrude_sheet4)
ProfilePram1.End2Type=1102
ProfilePram1.End2TypeParams=["25","14.999999999999998","0","0"]
ProfilePram1.End1ScallopType=1120
ProfilePram1.End1ScallopTypeParams=["50"]
ProfilePram1.End2ScallopType=1120
ProfilePram1.End2ScallopTypeParams=["50"]
profile1 = part.CreateProfile(ProfilePram1,False)
part.BlankElement(profile1[0],True)
part.SetElementColor(profile1[0],"148","0","211","0.39999997615814209")
part.BlankElement(profile1[1],True)
part.SetElementColor(profile1[1],"148","0","211","0.39999997615814209")
ProfilePram2 = part.CreateProfileParam()
ProfilePram2.DefinitionType=1
ProfilePram2.BasePlane="PL,O,"+var_elm1+","+"X"
ProfilePram2.AddAttachSurfaces(extrude_sheet2)
ProfilePram2.ProfileName="HK.Casing.Deck.D.FR09P"
ProfilePram2.MaterialName="SS400"
ProfilePram2.ProfileType=1003
ProfilePram2.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram2.Mold="+"
ProfilePram2.ReverseDir=True
ProfilePram2.ReverseAngle=False
ProfilePram2.CalcSnipOnlyAttachLines=False
ProfilePram2.AttachDirMethod=0
ProfilePram2.CCWDefAngle=False
ProfilePram2.AddEnd1Elements(profile1[0])
ProfilePram2.End1Type=1102
ProfilePram2.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram2.AddEnd2Elements(extrude_sheet1)
ProfilePram2.End2Type=1102
ProfilePram2.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram2.End1ScallopType=1120
ProfilePram2.End1ScallopTypeParams=["50"]
ProfilePram2.End2ScallopType=1120
ProfilePram2.End2ScallopTypeParams=["50"]
profile2 = part.CreateProfile(ProfilePram2,False)
part.BlankElement(profile2[0],True)
part.SetElementColor(profile2[0],"148","0","211","0.39999997615814209")
var_elm3 = part.CreateVariable("FR8","5360","mm","")
extrudePram5 = part.CreateLinearSweepParam()
extrudePram5.AddProfile(skt_pl2+",Casing.Deck.C")
extrudePram5.DirectionType="2"
extrudePram5.DirectionParameter1="50000"
extrudePram5.DirectionParameter2="10000"
extrudePram5.SweepDirection="+X"
extrudePram5.Name="HK.Casing.Deck.C"
extrudePram5.MaterialName="SS400"
extrudePram5.IntervalSweep=False
extrude_sheet5 = part.CreateLinearSweepSheet(extrudePram5,False)
part.SheetAlignNormal(extrude_sheet5,-0,0,1)
part.BlankElement(extrude_sheet5,True)
part.SetElementColor(extrude_sheet5,"225","225","225","1")
ProfilePram3 = part.CreateProfileParam()
ProfilePram3.DefinitionType=1
ProfilePram3.BasePlane="PL,O,"+var_elm3+","+"X"
ProfilePram3.AddAttachSurfaces(extrude_sheet1)
ProfilePram3.ProfileName="HK.Casing.Wall.Side.FR08.CDP"
ProfilePram3.MaterialName="SS400"
ProfilePram3.ProfileType=1002
ProfilePram3.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram3.Mold="+"
ProfilePram3.ReverseDir=False
ProfilePram3.ReverseAngle=True
ProfilePram3.CalcSnipOnlyAttachLines=False
ProfilePram3.AttachDirMethod=0
ProfilePram3.CCWDefAngle=False
ProfilePram3.AddEnd1Elements(extrude_sheet2)
ProfilePram3.End1Type=1102
ProfilePram3.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram3.AddEnd2Elements(extrude_sheet5)
ProfilePram3.End2Type=1102
ProfilePram3.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram3.End1ScallopType=1121
ProfilePram3.End1ScallopTypeParams=["35","40"]
ProfilePram3.End2ScallopType=1121
ProfilePram3.End2ScallopTypeParams=["35","40"]
profile3 = part.CreateProfile(ProfilePram3,False)
part.BlankElement(profile3[0],True)
part.SetElementColor(profile3[0],"255","0","0","0.19999998807907104")
skt_pl3 = part.CreateSketchPlane("HK.Az.Deck.D","","PL,Z","0",False,False,False,"","","",True,False)
part.BlankElement(skt_pl3,True)
skt_layer11 = part.CreateSketchLayer("Edge00",skt_pl3)
skt_ln19 = part.CreateSketchLine(skt_pl3,"","Edge00","11405.000000000002,4835","3984.9999999999995,4835",False)
skt_ln20 = part.CreateSketchLine(skt_pl3,"","Edge00","11405.000000000002,-4835","11405.000000000002,4835",False)
skt_ln21 = part.CreateSketchLine(skt_pl3,"","Edge00","3984.9999999999995,-4835","11405.000000000002,-4835",False)
skt_ln22 = part.CreateSketchLine(skt_pl3,"","Edge00","3984.9999999999995,4835","3984.9999999999995,-4835",False)
skt_layer12 = part.CreateSketchLayer("Edge01",skt_pl3)
skt_arc1 = part.CreateSketchArc(skt_pl3,"","Edge01","6345.0000000000009,1195.0000000000002","6345,1495.0000000000002","6045.0000000000009,1195",True,False)
skt_ln23 = part.CreateSketchLine(skt_pl3,"","Edge01","8580,1495","6345,1495",False)
skt_arc2 = part.CreateSketchArc(skt_pl3,"","Edge01","8580,1195","8880,1195.0000000000002","8580,1495",True,False)
skt_ln24 = part.CreateSketchLine(skt_pl3,"","Edge01","8880,-1195","8880,1195.0000000000005",False)
skt_arc3 = part.CreateSketchArc(skt_pl3,"","Edge01","8580,-1195.0000000000002","8580,-1495.0000000000002","8880,-1195",True,False)
skt_ln25 = part.CreateSketchLine(skt_pl3,"","Edge01","6345,-1495","8580,-1495",False)
skt_arc4 = part.CreateSketchArc(skt_pl3,"","Edge01","6345.0000000000009,-1195","6045.0000000000009,-1195.0000000000002","6345,-1495",True,False)
skt_ln26 = part.CreateSketchLine(skt_pl3,"","Edge01","6045,1195","6045,-1195.0000000000005",False)
solid1 = part.CreateSolid("HK.Casing.Deck.D","","SS400")
part.BlankElement(solid1,True)
part.SetElementColor(solid1,"139","69","19","0.78999996185302734")
thicken1 = part.CreateThicken("厚み付け3",solid1,"+",[extrude_sheet2],"+","10","0","0",False,False)
extrudePram6 = part.CreateLinearSweepParam()
extrudePram6.Name="積-押し出し3"
extrudePram6.AddProfile(skt_pl3+",Edge00")
extrudePram6.DirectionType="N"
extrudePram6.DirectionParameter1="50000"
extrudePram6.SweepDirection="+Z"
extrudePram6.RefByGeometricMethod=True
extrude1 = part.CreateLinearSweep(solid1,"*",extrudePram6,False)
extrudePram7 = part.CreateLinearSweepParam()
extrudePram7.Name="削除-押し出し1"
extrudePram7.AddProfile(skt_pl3+",Edge01")
extrudePram7.DirectionType="T"
extrudePram7.RefByGeometricMethod=True
extrude2 = part.CreateLinearSweep(solid1,"-",extrudePram7,False)
var_elm4 = part.CreateVariable("FR7","4690","mm","")
ProfilePram4 = part.CreateProfileParam()
ProfilePram4.DefinitionType=1
ProfilePram4.BasePlane="PL,O,"+var_elm4+","+"X"
ProfilePram4.AddAttachSurfaces(extrude_sheet1)
ProfilePram4.ProfileName="HK.Casing.Wall.Side.FR07.CDP"
ProfilePram4.MaterialName="SS400"
ProfilePram4.ProfileType=1002
ProfilePram4.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram4.Mold="+"
ProfilePram4.ReverseDir=False
ProfilePram4.ReverseAngle=True
ProfilePram4.CalcSnipOnlyAttachLines=False
ProfilePram4.AttachDirMethod=0
ProfilePram4.CCWDefAngle=False
ProfilePram4.AddEnd1Elements(extrude_sheet2)
ProfilePram4.End1Type=1102
ProfilePram4.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram4.AddEnd2Elements(extrude_sheet5)
ProfilePram4.End2Type=1102
ProfilePram4.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram4.End1ScallopType=1121
ProfilePram4.End1ScallopTypeParams=["35","40"]
ProfilePram4.End2ScallopType=1121
ProfilePram4.End2ScallopTypeParams=["35","40"]
profile4 = part.CreateProfile(ProfilePram4,False)
part.BlankElement(profile4[0],True)
part.SetElementColor(profile4[0],"255","0","0","0.19999998807907104")
var_elm5 = part.CreateVariable("Casing.DL05","4000","mm","")
ProfilePram5 = part.CreateProfileParam()
ProfilePram5.DefinitionType=1
ProfilePram5.BasePlane="PL,O,"+var_elm5+","+"Y"
ProfilePram5.AddAttachSurfaces(extrude_sheet2)
ProfilePram5.ProfileName="HK.Casing.Deck.D.DL05P"
ProfilePram5.MaterialName="SS400"
ProfilePram5.ProfileType=1002
ProfilePram5.ProfileParams=["125","75","7","10","5"]
ProfilePram5.Mold="+"
ProfilePram5.ReverseDir=True
ProfilePram5.ReverseAngle=True
ProfilePram5.CalcSnipOnlyAttachLines=False
ProfilePram5.AttachDirMethod=0
ProfilePram5.CCWDefAngle=False
ProfilePram5.AddEnd1Elements(extrude_sheet3)
ProfilePram5.End1Type=1102
ProfilePram5.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram5.AddEnd2Elements(extrude_sheet4)
ProfilePram5.End2Type=1102
ProfilePram5.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram5.End1ScallopType=1120
ProfilePram5.End1ScallopTypeParams=["50"]
ProfilePram5.End2ScallopType=1120
ProfilePram5.End2ScallopTypeParams=["50"]
profile5 = part.CreateProfile(ProfilePram5,False)
part.BlankElement(profile5[0],True)
part.SetElementColor(profile5[0],"255","0","0","0.19999998807907104")
ProfilePram6 = part.CreateProfileParam()
ProfilePram6.DefinitionType=1
ProfilePram6.BasePlane="PL,O,"+var_elm5+","+"Y"
ProfilePram6.AddAttachSurfaces(extrude_sheet4)
ProfilePram6.ProfileName="HK.Casing.Wall.Fore.DL05.CDP"
ProfilePram6.MaterialName="SS400"
ProfilePram6.ProfileType=1002
ProfilePram6.ProfileParams=["125","75","7","10","5"]
ProfilePram6.Mold="+"
ProfilePram6.ReverseDir=True
ProfilePram6.ReverseAngle=True
ProfilePram6.CalcSnipOnlyAttachLines=False
ProfilePram6.AttachDirMethod=0
ProfilePram6.CCWDefAngle=False
ProfilePram6.AddEnd1Elements(profile5[0])
ProfilePram6.End1Type=1102
ProfilePram6.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram6.AddEnd2Elements(extrude_sheet5)
ProfilePram6.End2Type=1102
ProfilePram6.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram6.End1ScallopType=1120
ProfilePram6.End1ScallopTypeParams=["50"]
ProfilePram6.End2ScallopType=1120
ProfilePram6.End2ScallopTypeParams=["50"]
profile6 = part.CreateProfile(ProfilePram6,False)
part.BlankElement(profile6[0],True)
part.SetElementColor(profile6[0],"255","0","0","0.19999998807907104")
var_elm6 = part.CreateVariable("Casing.DL01","800","mm","")
var_elm7 = part.CreateVariable("FR13","8970","mm","")
mirror_copied1 = part.MirrorCopy([profile1[0]],"PL,Y","")
part.BlankElement(mirror_copied1[0],True)
part.SetElementColor(mirror_copied1[0],"148","0","211","0.39999997615814209")
ProfilePram7 = part.CreateProfileParam()
ProfilePram7.DefinitionType=1
ProfilePram7.BasePlane="PL,O,"+var_elm7+","+"X"
ProfilePram7.AddAttachSurfaces(extrude_sheet2)
ProfilePram7.ProfileName="HK.Casing.Deck.D.FR13C"
ProfilePram7.MaterialName="SS400"
ProfilePram7.ProfileType=1003
ProfilePram7.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram7.Mold="+"
ProfilePram7.ReverseDir=True
ProfilePram7.ReverseAngle=False
ProfilePram7.CalcSnipOnlyAttachLines=False
ProfilePram7.AttachDirMethod=0
ProfilePram7.CCWDefAngle=False
ProfilePram7.AddEnd1Elements(mirror_copied1[0])
ProfilePram7.End1Type=1102
ProfilePram7.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram7.AddEnd2Elements(profile1[0])
ProfilePram7.End2Type=1102
ProfilePram7.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram7.End1ScallopType=1120
ProfilePram7.End1ScallopTypeParams=["50"]
ProfilePram7.End2ScallopType=1120
ProfilePram7.End2ScallopTypeParams=["50"]
profile7 = part.CreateProfile(ProfilePram7,False)
part.BlankElement(profile7[0],True)
part.SetElementColor(profile7[0],"148","0","211","0.39999997615814209")
ProfilePram8 = part.CreateProfileParam()
ProfilePram8.DefinitionType=1
ProfilePram8.BasePlane="PL,O,"+var_elm6+","+"Y"
ProfilePram8.AddAttachSurfaces(extrude_sheet2)
ProfilePram8.ProfileName="HK.Casing.Deck.D.DL01.FP"
ProfilePram8.MaterialName="SS400"
ProfilePram8.ProfileType=1002
ProfilePram8.ProfileParams=["125","75","7","10","5"]
ProfilePram8.Mold="+"
ProfilePram8.ReverseDir=True
ProfilePram8.ReverseAngle=True
ProfilePram8.CalcSnipOnlyAttachLines=False
ProfilePram8.AttachDirMethod=0
ProfilePram8.CCWDefAngle=False
ProfilePram8.AddEnd1Elements(profile7[0])
ProfilePram8.End1Type=1102
ProfilePram8.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram8.AddEnd2Elements(extrude_sheet4)
ProfilePram8.End2Type=1102
ProfilePram8.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram8.End1ScallopType=1121
ProfilePram8.End1ScallopTypeParams=["25","40"]
ProfilePram8.End2ScallopType=1121
ProfilePram8.End2ScallopTypeParams=["25","40"]
profile8 = part.CreateProfile(ProfilePram8,False)
part.BlankElement(profile8[0],True)
part.SetElementColor(profile8[0],"255","0","0","0.19999998807907104")
ProfilePram9 = part.CreateProfileParam()
ProfilePram9.DefinitionType=1
ProfilePram9.BasePlane="PL,O,"+var_elm6+","+"Y"
ProfilePram9.AddAttachSurfaces(extrude_sheet4)
ProfilePram9.ProfileName="HK.Casing.Wall.Fore.DL01.CDP"
ProfilePram9.MaterialName="SS400"
ProfilePram9.ProfileType=1002
ProfilePram9.ProfileParams=["125","75","7","10","5"]
ProfilePram9.Mold="+"
ProfilePram9.ReverseDir=True
ProfilePram9.ReverseAngle=True
ProfilePram9.CalcSnipOnlyAttachLines=False
ProfilePram9.AttachDirMethod=0
ProfilePram9.CCWDefAngle=False
ProfilePram9.AddEnd1Elements(profile8[0])
ProfilePram9.End1Type=1102
ProfilePram9.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram9.AddEnd2Elements(extrude_sheet5)
ProfilePram9.End2Type=1102
ProfilePram9.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram9.End1ScallopType=1120
ProfilePram9.End1ScallopTypeParams=["50"]
ProfilePram9.End2ScallopType=1120
ProfilePram9.End2ScallopTypeParams=["50"]
profile9 = part.CreateProfile(ProfilePram9,False)
part.BlankElement(profile9[0],True)
part.SetElementColor(profile9[0],"255","0","0","0.19999998807907104")
bracketPram1 = part.CreateBracketParam()
bracketPram1.DefinitionType=1
bracketPram1.BracketName="HK.Casing.Wall.Fore.DL01.Deck.DP"
bracketPram1.MaterialName="SS400"
bracketPram1.BaseElement=profile9[0]
bracketPram1.UseSideSheetForPlane=False
bracketPram1.Mold="+"
bracketPram1.Thickness="7.9999999999999964"
bracketPram1.BracketType=1501
bracketPram1.Scallop1Type=1801
bracketPram1.Scallop1Params=["0"]
bracketPram1.Scallop2Type=0
bracketPram1.Surfaces1=[profile9[0]+",FL"]
bracketPram1.RevSf1=False
bracketPram1.Surfaces2=[profile8[0]+",FL"]
bracketPram1.RevSf2=False
bracketPram1.RevSf3=False
bracketPram1.Sf1DimensionType=1531
bracketPram1.Sf1DimensonParams=["200","15"]
bracketPram1.Sf2DimensionType=1531
bracketPram1.Sf2DimensonParams=["200","15"]
bracket1 = part.CreateBracket(bracketPram1,False)
part.BlankElement(bracket1,True)
part.SetElementColor(bracket1,"0","255","255","0.19999998807907104")
skt_pl4 = part.CreateSketchPlane("Sketch3","","PL,Z","0",False,False,False,"","","",False,False)
part.BlankElement(skt_pl4,True)
skt_ln27 = part.CreateSketchLine(skt_pl4,"","Default Layer","2926.4779204678048,400","12241.442807836524,400",False)
separated_bodies1 = part.BodyDivideByCurves("Separe body by curves32",bracket1,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies1[0],"0","255","255","0.19999998807907104")
var_elm8 = part.CreateVariable("FR11","7370","mm","")
ProfilePram10 = part.CreateProfileParam()
ProfilePram10.DefinitionType=1
ProfilePram10.BasePlane="PL,O,"+var_elm8+","+"X"
ProfilePram10.AddAttachSurfaces(extrude_sheet1)
ProfilePram10.ProfileName="HK.Casing.Wall.Side.FR11.CDP"
ProfilePram10.MaterialName="SS400"
ProfilePram10.ProfileType=1002
ProfilePram10.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram10.Mold="+"
ProfilePram10.ReverseDir=False
ProfilePram10.ReverseAngle=True
ProfilePram10.CalcSnipOnlyAttachLines=False
ProfilePram10.AttachDirMethod=0
ProfilePram10.CCWDefAngle=False
ProfilePram10.AddEnd1Elements(extrude_sheet2)
ProfilePram10.End1Type=1102
ProfilePram10.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram10.AddEnd2Elements(extrude_sheet5)
ProfilePram10.End2Type=1102
ProfilePram10.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram10.End1ScallopType=1121
ProfilePram10.End1ScallopTypeParams=["35","40"]
ProfilePram10.End2ScallopType=1121
ProfilePram10.End2ScallopTypeParams=["35","40"]
profile10 = part.CreateProfile(ProfilePram10,False)
part.BlankElement(profile10[0],True)
part.SetElementColor(profile10[0],"255","0","0","0.19999998807907104")
ProfilePram11 = part.CreateProfileParam()
ProfilePram11.DefinitionType=1
ProfilePram11.BasePlane="PL,O,"+var_elm2+","+"Y"
ProfilePram11.AddAttachSurfaces(extrude_sheet3)
ProfilePram11.ProfileName="HK.Casing.Wall.Aft.DL02.CDP"
ProfilePram11.MaterialName="SS400"
ProfilePram11.FlangeName="HK.Casing.Wall.Aft.DL02.CDP"
ProfilePram11.FlangeMaterialName="SS400"
ProfilePram11.ProfileType=1201
ProfilePram11.ProfileParams=["150","12","388","10"]
ProfilePram11.Mold="-"
ProfilePram11.ReverseDir=False
ProfilePram11.ReverseAngle=False
ProfilePram11.CalcSnipOnlyAttachLines=False
ProfilePram11.AttachDirMethod=0
ProfilePram11.CCWDefAngle=False
ProfilePram11.AddEnd1Elements(profile1[1])
ProfilePram11.End1Type=1102
ProfilePram11.End1TypeParams=["25","14.999999999999998","0","0"]
ProfilePram11.AddEnd2Elements(extrude_sheet5)
ProfilePram11.End2Type=1103
ProfilePram11.End2TypeParams=["0"]
ProfilePram11.End1ScallopType=1120
ProfilePram11.End1ScallopTypeParams=["50"]
ProfilePram11.End2ScallopType=1120
ProfilePram11.End2ScallopTypeParams=["50"]
profile11 = part.CreateProfile(ProfilePram11,False)
part.BlankElement(profile11[0],True)
part.SetElementColor(profile11[0],"148","0","211","0.38999998569488525")
part.BlankElement(profile11[1],True)
part.SetElementColor(profile11[1],"148","0","211","0.38999998569488525")
ProfilePram12 = part.CreateProfileParam()
ProfilePram12.DefinitionType=1
ProfilePram12.BasePlane="PL,O,"+var_elm7+","+"X"
ProfilePram12.AddAttachSurfaces(extrude_sheet2)
ProfilePram12.ProfileName="HK.Casing.Deck.D.FR13P"
ProfilePram12.MaterialName="SS400"
ProfilePram12.ProfileType=1003
ProfilePram12.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram12.Mold="+"
ProfilePram12.ReverseDir=True
ProfilePram12.ReverseAngle=False
ProfilePram12.CalcSnipOnlyAttachLines=False
ProfilePram12.AttachDirMethod=0
ProfilePram12.CCWDefAngle=False
ProfilePram12.AddEnd1Elements(profile1[0])
ProfilePram12.End1Type=1102
ProfilePram12.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram12.AddEnd2Elements(extrude_sheet1)
ProfilePram12.End2Type=1102
ProfilePram12.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram12.End1ScallopType=1120
ProfilePram12.End1ScallopTypeParams=["50"]
ProfilePram12.End2ScallopType=1120
ProfilePram12.End2ScallopTypeParams=["50"]
profile12 = part.CreateProfile(ProfilePram12,False)
part.BlankElement(profile12[0],True)
part.SetElementColor(profile12[0],"148","0","211","0.39999997615814209")
ProfilePram13 = part.CreateProfileParam()
ProfilePram13.DefinitionType=1
ProfilePram13.BasePlane="PL,O,"+var_elm7+","+"X"
ProfilePram13.AddAttachSurfaces(extrude_sheet1)
ProfilePram13.ProfileName="HK.Casing.Wall.Side.FR13.CDP"
ProfilePram13.MaterialName="SS400"
ProfilePram13.ProfileType=1003
ProfilePram13.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram13.Mold="+"
ProfilePram13.ReverseDir=False
ProfilePram13.ReverseAngle=True
ProfilePram13.CalcSnipOnlyAttachLines=False
ProfilePram13.AttachDirMethod=0
ProfilePram13.CCWDefAngle=False
ProfilePram13.AddEnd1Elements(profile12[0])
ProfilePram13.End1Type=1102
ProfilePram13.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram13.AddEnd2Elements(extrude_sheet5)
ProfilePram13.End2Type=1103
ProfilePram13.End2TypeParams=["0"]
ProfilePram13.End1ScallopType=1120
ProfilePram13.End1ScallopTypeParams=["50"]
ProfilePram13.End2ScallopType=1120
ProfilePram13.End2ScallopTypeParams=["50"]
profile13 = part.CreateProfile(ProfilePram13,False)
part.BlankElement(profile13[0],True)
part.SetElementColor(profile13[0],"148","0","211","0.39999997615814209")
separated_bodies2 = part.BodyDivideByCurves("Separe body by curves5",profile7[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies2[1],"148","0","211","0.39999997615814209")
var_elm9 = part.CreateVariable("FR10","6700","mm","")
ProfilePram14 = part.CreateProfileParam()
ProfilePram14.DefinitionType=1
ProfilePram14.BasePlane="PL,O,"+var_elm9+","+"X"
ProfilePram14.AddAttachSurfaces(extrude_sheet1)
ProfilePram14.ProfileName="HK.Casing.Wall.Side.FR10.CDP"
ProfilePram14.MaterialName="SS400"
ProfilePram14.ProfileType=1002
ProfilePram14.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram14.Mold="+"
ProfilePram14.ReverseDir=False
ProfilePram14.ReverseAngle=True
ProfilePram14.CalcSnipOnlyAttachLines=False
ProfilePram14.AttachDirMethod=0
ProfilePram14.CCWDefAngle=False
ProfilePram14.AddEnd1Elements(extrude_sheet2)
ProfilePram14.End1Type=1102
ProfilePram14.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram14.AddEnd2Elements(extrude_sheet5)
ProfilePram14.End2Type=1102
ProfilePram14.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram14.End1ScallopType=1121
ProfilePram14.End1ScallopTypeParams=["35","40"]
ProfilePram14.End2ScallopType=1121
ProfilePram14.End2ScallopTypeParams=["35","40"]
profile14 = part.CreateProfile(ProfilePram14,False)
part.BlankElement(profile14[0],True)
part.SetElementColor(profile14[0],"255","0","0","0.19999998807907104")
ProfilePram15 = part.CreateProfileParam()
ProfilePram15.DefinitionType=1
ProfilePram15.BasePlane="PL,O,"+var_elm2+","+"Y"
ProfilePram15.AddAttachSurfaces(extrude_sheet4)
ProfilePram15.ProfileName="HK.Casing.Wall.Fore.DL02.CDP"
ProfilePram15.MaterialName="SS400"
ProfilePram15.FlangeName="HK.Casing.Wall.Fore.DL02.CDP"
ProfilePram15.FlangeMaterialName="SS400"
ProfilePram15.ProfileType=1201
ProfilePram15.ProfileParams=["150","12","388","10"]
ProfilePram15.Mold="-"
ProfilePram15.ReverseDir=True
ProfilePram15.ReverseAngle=False
ProfilePram15.CalcSnipOnlyAttachLines=False
ProfilePram15.AttachDirMethod=0
ProfilePram15.CCWDefAngle=False
ProfilePram15.AddEnd1Elements(profile1[1])
ProfilePram15.End1Type=1102
ProfilePram15.End1TypeParams=["25","14.999999999999998","0","0"]
ProfilePram15.AddEnd2Elements(extrude_sheet5)
ProfilePram15.End2Type=1102
ProfilePram15.End2TypeParams=["25","14.999999999999998","0","0"]
ProfilePram15.End1ScallopType=1120
ProfilePram15.End1ScallopTypeParams=["50"]
ProfilePram15.End2ScallopType=1120
ProfilePram15.End2ScallopTypeParams=["50"]
profile15 = part.CreateProfile(ProfilePram15,False)
part.BlankElement(profile15[0],True)
part.SetElementColor(profile15[0],"148","0","211","0.39999997615814209")
part.BlankElement(profile15[1],True)
part.SetElementColor(profile15[1],"148","0","211","0.39999997615814209")
bracketPram2 = part.CreateBracketParam()
bracketPram2.DefinitionType=1
bracketPram2.BracketName="HK.Casing.Wall.Fore.DL02.Deck.DP"
bracketPram2.MaterialName="SS400"
bracketPram2.BaseElement=profile15[0]
bracketPram2.UseSideSheetForPlane=False
bracketPram2.Mold="-"
bracketPram2.Thickness="12"
bracketPram2.BracketType=1501
bracketPram2.Scallop1Type=1801
bracketPram2.Scallop1Params=["50"]
bracketPram2.Scallop2Type=0
bracketPram2.Surfaces1=["PLS","False","False","-1","-0","0",profile15[1]]
bracketPram2.RevSf1=False
bracketPram2.Surfaces2=["PLS","False","False","-0","-0","-1",profile1[1]]
bracketPram2.RevSf2=False
bracketPram2.RevSf3=False
bracketPram2.FlangeType=262
bracketPram2.FlangeParams=["100","30","29.999999999999996","30","30","1"]
bracketPram2.RevFlange=False
bracketPram2.Sf1DimensionType=1531
bracketPram2.Sf1DimensonParams=["800","15"]
bracketPram2.Sf2DimensionType=1531
bracketPram2.Sf2DimensonParams=["800","15"]
bracket2 = part.CreateBracket(bracketPram2,False)
part.BlankElement(bracket2,True)
part.SetElementColor(bracket2,"0","255","255","0.19999998807907104")
bracketPram3 = part.CreateBracketParam()
bracketPram3.DefinitionType=1
bracketPram3.BracketName="HK.Casing.Deck.D.FR13P"
bracketPram3.MaterialName="SS400"
bracketPram3.BaseElement=profile12[0]
bracketPram3.UseSideSheetForPlane=False
bracketPram3.Mold="+"
bracketPram3.Thickness="8.9999999999999982"
bracketPram3.BracketType=1501
bracketPram3.Scallop1Type=1801
bracketPram3.Scallop1Params=["50"]
bracketPram3.Scallop2Type=0
bracketPram3.Surfaces1=[profile1[0]+",WF"]
bracketPram3.RevSf1=False
bracketPram3.Surfaces2=[profile12[0]+",FL"]
bracketPram3.RevSf2=False
bracketPram3.RevSf3=False
bracketPram3.FlangeType=262
bracketPram3.FlangeParams=["75","30","29.999999999999996","30","50","1"]
bracketPram3.RevFlange=False
bracketPram3.Sf1DimensionType=1541
bracketPram3.Sf1DimensonParams=["0","80"]
bracketPram3.Sf1EndElements=[profile1[1]+",FR"]
bracketPram3.Sf2DimensionType=1531
bracketPram3.Sf2DimensonParams=["300","15"]
bracket3 = part.CreateBracket(bracketPram3,False)
part.BlankElement(bracket3,True)
part.SetElementColor(bracket3,"0","255","255","0.19999998807907104")
var_elm10 = part.CreateVariable("FR12","8170","mm","")
ProfilePram16 = part.CreateProfileParam()
ProfilePram16.DefinitionType=1
ProfilePram16.BasePlane="PL,O,"+var_elm10+","+"X"
ProfilePram16.AddAttachSurfaces(extrude_sheet1)
ProfilePram16.ProfileName="HK.Casing.Wall.Side.FR12.CDP"
ProfilePram16.MaterialName="SS400"
ProfilePram16.ProfileType=1002
ProfilePram16.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram16.Mold="+"
ProfilePram16.ReverseDir=False
ProfilePram16.ReverseAngle=True
ProfilePram16.CalcSnipOnlyAttachLines=False
ProfilePram16.AttachDirMethod=0
ProfilePram16.CCWDefAngle=False
ProfilePram16.AddEnd1Elements(extrude_sheet2)
ProfilePram16.End1Type=1102
ProfilePram16.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram16.AddEnd2Elements(extrude_sheet5)
ProfilePram16.End2Type=1102
ProfilePram16.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram16.End1ScallopType=1121
ProfilePram16.End1ScallopTypeParams=["35","40"]
ProfilePram16.End2ScallopType=1121
ProfilePram16.End2ScallopTypeParams=["35","40"]
profile16 = part.CreateProfile(ProfilePram16,False)
part.BlankElement(profile16[0],True)
part.SetElementColor(profile16[0],"255","0","0","0.19999998807907104")
var_elm11 = part.CreateVariable("Casing.DL03","2400","mm","")
ProfilePram17 = part.CreateProfileParam()
ProfilePram17.DefinitionType=1
ProfilePram17.BasePlane="PL,O,"+var_elm11+","+"Y"
ProfilePram17.AddAttachSurfaces(extrude_sheet2)
ProfilePram17.ProfileName="HK.Casing.Deck.D.DL03P"
ProfilePram17.MaterialName="SS400"
ProfilePram17.ProfileType=1002
ProfilePram17.ProfileParams=["125","75","7","10","5"]
ProfilePram17.Mold="+"
ProfilePram17.ReverseDir=True
ProfilePram17.ReverseAngle=True
ProfilePram17.CalcSnipOnlyAttachLines=False
ProfilePram17.AttachDirMethod=0
ProfilePram17.CCWDefAngle=False
ProfilePram17.AddEnd1Elements(extrude_sheet3)
ProfilePram17.End1Type=1102
ProfilePram17.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram17.AddEnd2Elements(extrude_sheet4)
ProfilePram17.End2Type=1102
ProfilePram17.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram17.End1ScallopType=1120
ProfilePram17.End1ScallopTypeParams=["50"]
ProfilePram17.End2ScallopType=1120
ProfilePram17.End2ScallopTypeParams=["50"]
profile17 = part.CreateProfile(ProfilePram17,False)
part.BlankElement(profile17[0],True)
part.SetElementColor(profile17[0],"255","0","0","0.19999998807907104")
ProfilePram18 = part.CreateProfileParam()
ProfilePram18.DefinitionType=1
ProfilePram18.BasePlane="PL,O,"+var_elm11+","+"Y"
ProfilePram18.AddAttachSurfaces(extrude_sheet3)
ProfilePram18.ProfileName="HK.Casing.Wall.Aft.DL03.CDP"
ProfilePram18.MaterialName="SS400"
ProfilePram18.ProfileType=1002
ProfilePram18.ProfileParams=["125","75","7","10","5"]
ProfilePram18.Mold="+"
ProfilePram18.ReverseDir=False
ProfilePram18.ReverseAngle=True
ProfilePram18.CalcSnipOnlyAttachLines=False
ProfilePram18.AttachDirMethod=0
ProfilePram18.CCWDefAngle=False
ProfilePram18.AddEnd1Elements(profile17[0])
ProfilePram18.End1Type=1102
ProfilePram18.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram18.AddEnd2Elements(extrude_sheet5)
ProfilePram18.End2Type=1102
ProfilePram18.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram18.End1ScallopType=1120
ProfilePram18.End1ScallopTypeParams=["50"]
ProfilePram18.End2ScallopType=1120
ProfilePram18.End2ScallopTypeParams=["50"]
profile18 = part.CreateProfile(ProfilePram18,False)
part.BlankElement(profile18[0],True)
part.SetElementColor(profile18[0],"255","0","0","0.19999998807907104")
separated_bodies3 = part.BodyDivideByCurves("Separe body by curves41",profile18[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies3[0],"255","0","0","0.19999998807907104")
solid2 = part.CreateSolid("HK.Casing.Wall.Aft.CD","","SS400")
part.BlankElement(solid2,True)
part.SetElementColor(solid2,"139","69","19","0.79999995231628418")
thicken2 = part.CreateThicken("厚み付け11",solid2,"+",[extrude_sheet3],"-","10","0","0",False,False)
extrudePram8 = part.CreateLinearSweepParam()
extrudePram8.Name="積-押し出し19"
extrudePram8.AddProfile(extrude_sheet1)
extrudePram8.DirectionType="R"
extrudePram8.DirectionParameter1="50000"
extrudePram8.SweepDirection="+Y"
extrudePram8.RefByGeometricMethod=True
extrude3 = part.CreateLinearSweep(solid2,"*",extrudePram8,False)
var_elm12 = part.CreateVariable("FR14","9770","mm","")
ProfilePram19 = part.CreateProfileParam()
ProfilePram19.DefinitionType=1
ProfilePram19.BasePlane="PL,O,"+var_elm12+","+"X"
ProfilePram19.AddAttachSurfaces(extrude_sheet1)
ProfilePram19.ProfileName="HK.Casing.Wall.Side.FR14.CDP"
ProfilePram19.MaterialName="SS400"
ProfilePram19.ProfileType=1002
ProfilePram19.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram19.Mold="+"
ProfilePram19.ReverseDir=False
ProfilePram19.ReverseAngle=True
ProfilePram19.CalcSnipOnlyAttachLines=False
ProfilePram19.AttachDirMethod=0
ProfilePram19.CCWDefAngle=False
ProfilePram19.AddEnd1Elements(extrude_sheet2)
ProfilePram19.End1Type=1102
ProfilePram19.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram19.AddEnd2Elements(extrude_sheet5)
ProfilePram19.End2Type=1102
ProfilePram19.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram19.End1ScallopType=1121
ProfilePram19.End1ScallopTypeParams=["35","40"]
ProfilePram19.End2ScallopType=1121
ProfilePram19.End2ScallopTypeParams=["35","40"]
profile19 = part.CreateProfile(ProfilePram19,False)
part.BlankElement(profile19[0],True)
part.SetElementColor(profile19[0],"255","0","0","0.19999998807907104")
separated_bodies4 = part.BodyDivideByCurves("Separe body by curves59",profile15[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies4[0],"148","0","211","0.39999997615814209")
ProfilePram20 = part.CreateProfileParam()
ProfilePram20.DefinitionType=1
ProfilePram20.BasePlane="PL,O,"+var_elm5+","+"Y"
ProfilePram20.AddAttachSurfaces(extrude_sheet3)
ProfilePram20.ProfileName="HK.Casing.Wall.Aft.DL05.CDP"
ProfilePram20.MaterialName="SS400"
ProfilePram20.ProfileType=1002
ProfilePram20.ProfileParams=["125","75","7","10","5"]
ProfilePram20.Mold="+"
ProfilePram20.ReverseDir=False
ProfilePram20.ReverseAngle=True
ProfilePram20.CalcSnipOnlyAttachLines=False
ProfilePram20.AttachDirMethod=0
ProfilePram20.CCWDefAngle=False
ProfilePram20.AddEnd1Elements(profile5[0])
ProfilePram20.End1Type=1102
ProfilePram20.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram20.AddEnd2Elements(extrude_sheet5)
ProfilePram20.End2Type=1102
ProfilePram20.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram20.End1ScallopType=1120
ProfilePram20.End1ScallopTypeParams=["50"]
ProfilePram20.End2ScallopType=1120
ProfilePram20.End2ScallopTypeParams=["50"]
profile20 = part.CreateProfile(ProfilePram20,False)
part.BlankElement(profile20[0],True)
part.SetElementColor(profile20[0],"255","0","0","0.19999998807907104")
ProfilePram21 = part.CreateProfileParam()
ProfilePram21.DefinitionType=1
ProfilePram21.BasePlane="PL,O,"+var_elm1+","+"X"
ProfilePram21.AddAttachSurfaces(extrude_sheet2)
ProfilePram21.ProfileName="HK.Casing.Deck.D.FR09C"
ProfilePram21.MaterialName="SS400"
ProfilePram21.ProfileType=1003
ProfilePram21.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram21.Mold="+"
ProfilePram21.ReverseDir=True
ProfilePram21.ReverseAngle=False
ProfilePram21.CalcSnipOnlyAttachLines=False
ProfilePram21.AttachDirMethod=0
ProfilePram21.CCWDefAngle=False
ProfilePram21.AddEnd1Elements(mirror_copied1[0])
ProfilePram21.End1Type=1102
ProfilePram21.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram21.AddEnd2Elements(profile1[0])
ProfilePram21.End2Type=1102
ProfilePram21.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram21.End1ScallopType=1120
ProfilePram21.End1ScallopTypeParams=["50"]
ProfilePram21.End2ScallopType=1120
ProfilePram21.End2ScallopTypeParams=["50"]
profile21 = part.CreateProfile(ProfilePram21,False)
part.BlankElement(profile21[0],True)
part.SetElementColor(profile21[0],"148","0","211","0.39999997615814209")
ProfilePram22 = part.CreateProfileParam()
ProfilePram22.DefinitionType=1
ProfilePram22.BasePlane="PL,O,"+var_elm11+","+"Y"
ProfilePram22.AddAttachSurfaces(extrude_sheet4)
ProfilePram22.ProfileName="HK.Casing.Wall.Fore.DL03.CDP"
ProfilePram22.MaterialName="SS400"
ProfilePram22.ProfileType=1002
ProfilePram22.ProfileParams=["125","75","7","10","5"]
ProfilePram22.Mold="+"
ProfilePram22.ReverseDir=True
ProfilePram22.ReverseAngle=True
ProfilePram22.CalcSnipOnlyAttachLines=False
ProfilePram22.AttachDirMethod=0
ProfilePram22.CCWDefAngle=False
ProfilePram22.AddEnd1Elements(profile17[0])
ProfilePram22.End1Type=1102
ProfilePram22.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram22.AddEnd2Elements(extrude_sheet5)
ProfilePram22.End2Type=1102
ProfilePram22.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram22.End1ScallopType=1120
ProfilePram22.End1ScallopTypeParams=["50"]
ProfilePram22.End2ScallopType=1120
ProfilePram22.End2ScallopTypeParams=["50"]
profile22 = part.CreateProfile(ProfilePram22,False)
part.BlankElement(profile22[0],True)
part.SetElementColor(profile22[0],"255","0","0","0.19999998807907104")
separated_bodies5 = part.BodyDivideByCurves("Separe body by curves31",profile22[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies5[0],"255","0","0","0.19999998807907104")
ProfilePram23 = part.CreateProfileParam()
ProfilePram23.DefinitionType=1
ProfilePram23.BasePlane="PL,O,"+var_elm1+","+"X"
ProfilePram23.AddAttachSurfaces(extrude_sheet1)
ProfilePram23.ProfileName="HK.Casing.Wall.Side.FR09.CDP"
ProfilePram23.MaterialName="SS400"
ProfilePram23.ProfileType=1003
ProfilePram23.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram23.Mold="+"
ProfilePram23.ReverseDir=False
ProfilePram23.ReverseAngle=True
ProfilePram23.CalcSnipOnlyAttachLines=False
ProfilePram23.AttachDirMethod=0
ProfilePram23.CCWDefAngle=False
ProfilePram23.AddEnd1Elements(profile2[0])
ProfilePram23.End1Type=1102
ProfilePram23.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram23.AddEnd2Elements(extrude_sheet5)
ProfilePram23.End2Type=1103
ProfilePram23.End2TypeParams=["0"]
ProfilePram23.End1ScallopType=1120
ProfilePram23.End1ScallopTypeParams=["50"]
ProfilePram23.End2ScallopType=1120
ProfilePram23.End2ScallopTypeParams=["50"]
profile23 = part.CreateProfile(ProfilePram23,False)
part.BlankElement(profile23[0],True)
part.SetElementColor(profile23[0],"148","0","211","0.39999997615814209")
var_elm13 = part.CreateVariable("FR15","10570","mm","")
ProfilePram24 = part.CreateProfileParam()
ProfilePram24.DefinitionType=1
ProfilePram24.BasePlane="PL,O,"+var_elm13+","+"X"
ProfilePram24.AddAttachSurfaces(extrude_sheet1)
ProfilePram24.ProfileName="HK.Casing.Wall.Side.FR15.CDP"
ProfilePram24.MaterialName="SS400"
ProfilePram24.ProfileType=1002
ProfilePram24.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram24.Mold="+"
ProfilePram24.ReverseDir=False
ProfilePram24.ReverseAngle=True
ProfilePram24.CalcSnipOnlyAttachLines=False
ProfilePram24.AttachDirMethod=0
ProfilePram24.CCWDefAngle=False
ProfilePram24.AddEnd1Elements(extrude_sheet2)
ProfilePram24.End1Type=1102
ProfilePram24.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram24.AddEnd2Elements(extrude_sheet5)
ProfilePram24.End2Type=1102
ProfilePram24.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram24.End1ScallopType=1121
ProfilePram24.End1ScallopTypeParams=["35","40"]
ProfilePram24.End2ScallopType=1121
ProfilePram24.End2ScallopTypeParams=["35","40"]
profile24 = part.CreateProfile(ProfilePram24,False)
part.BlankElement(profile24[0],True)
part.SetElementColor(profile24[0],"255","0","0","0.19999998807907104")
extrudePram9 = part.CreateLinearSweepParam()
extrudePram9.AddProfile(skt_pl1+",Casing.Side.S")
extrudePram9.DirectionType="2"
extrudePram9.DirectionParameter1="50000"
extrudePram9.DirectionParameter2="10000"
extrudePram9.SweepDirection="+Z"
extrudePram9.Name="HK.Casing.Wall.SideS"
extrudePram9.MaterialName="SS400"
extrudePram9.IntervalSweep=False
extrude_sheet6 = part.CreateLinearSweepSheet(extrudePram9,False)
part.SheetAlignNormal(extrude_sheet6,0,-1,0)
part.BlankElement(extrude_sheet6,True)
part.SetElementColor(extrude_sheet6,"225","225","225","1")
extrudePram10 = part.CreateLinearSweepParam()
extrudePram10.Name="積-押し出し20"
extrudePram10.AddProfile(extrude_sheet6)
extrudePram10.DirectionType="N"
extrudePram10.DirectionParameter1="50000"
extrudePram10.SweepDirection="+Y"
extrudePram10.RefByGeometricMethod=True
extrude4 = part.CreateLinearSweep(solid2,"*",extrudePram10,False)
extrudePram11 = part.CreateLinearSweepParam()
extrudePram11.Name="積-押し出し21"
extrudePram11.AddProfile(extrude_sheet2)
extrudePram11.DirectionType="R"
extrudePram11.DirectionParameter1="50000"
extrudePram11.SweepDirection="+Z"
extrudePram11.RefByGeometricMethod=True
extrude5 = part.CreateLinearSweep(solid2,"*",extrudePram11,False)
bracketPram4 = part.CreateBracketParam()
bracketPram4.DefinitionType=1
bracketPram4.BracketName="HK.Casing.Wall.Side.FR10.Deck.DP"
bracketPram4.MaterialName="SS400"
bracketPram4.BaseElement=profile14[0]
bracketPram4.UseSideSheetForPlane=False
bracketPram4.Mold="+"
bracketPram4.Thickness="9.9999999999999982"
bracketPram4.BracketType=1505
bracketPram4.BracketParams=["200"]
bracketPram4.Scallop1Type=1801
bracketPram4.Scallop1Params=["0"]
bracketPram4.Scallop2Type=0
bracketPram4.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram4.RevSf1=False
bracketPram4.Surfaces2=[profile14[0]+",FL"]
bracketPram4.RevSf2=False
bracketPram4.RevSf3=False
bracketPram4.Sf1DimensionType=1541
bracketPram4.Sf1DimensonParams=["0","100"]
bracketPram4.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram4.Sf2DimensionType=1531
bracketPram4.Sf2DimensonParams=["200","15"]
bracket4 = part.CreateBracket(bracketPram4,False)
part.BlankElement(bracket4,True)
part.SetElementColor(bracket4,"0","255","255","0.19999998807907104")
separated_bodies6 = part.BodyDivideByCurves("Separe body by curves13",bracket4,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies6[0],"0","255","255","0.19999998807907104")
bracketPram5 = part.CreateBracketParam()
bracketPram5.DefinitionType=1
bracketPram5.BracketName="HK.Casing.Wall.Aft.DL02.Deck.DP"
bracketPram5.MaterialName="SS400"
bracketPram5.BaseElement=profile11[0]
bracketPram5.UseSideSheetForPlane=False
bracketPram5.Mold="-"
bracketPram5.Thickness="12"
bracketPram5.BracketType=1501
bracketPram5.Scallop1Type=1801
bracketPram5.Scallop1Params=["50"]
bracketPram5.Scallop2Type=0
bracketPram5.Surfaces1=["PLS","False","False","1","0","-0",profile11[1]]
bracketPram5.RevSf1=False
bracketPram5.Surfaces2=["PLS","False","False","-0","-0","-1",profile1[1]]
bracketPram5.RevSf2=False
bracketPram5.RevSf3=False
bracketPram5.FlangeType=262
bracketPram5.FlangeParams=["100","30","29.999999999999996","30","30","1"]
bracketPram5.RevFlange=False
bracketPram5.Sf1DimensionType=1531
bracketPram5.Sf1DimensonParams=["800","15"]
bracketPram5.Sf2DimensionType=1531
bracketPram5.Sf2DimensonParams=["800","15"]
bracket5 = part.CreateBracket(bracketPram5,False)
part.BlankElement(bracket5,True)
part.SetElementColor(bracket5,"0","255","255","0.19999998807907104")
var_elm14 = part.CreateVariable("Casing.DL04","3200","mm","")
ProfilePram25 = part.CreateProfileParam()
ProfilePram25.DefinitionType=1
ProfilePram25.BasePlane="PL,O,"+var_elm14+","+"Y"
ProfilePram25.AddAttachSurfaces(extrude_sheet2)
ProfilePram25.ProfileName="HK.Casing.Deck.D.DL04P"
ProfilePram25.MaterialName="SS400"
ProfilePram25.ProfileType=1002
ProfilePram25.ProfileParams=["125","75","7","10","5"]
ProfilePram25.Mold="+"
ProfilePram25.ReverseDir=True
ProfilePram25.ReverseAngle=True
ProfilePram25.CalcSnipOnlyAttachLines=False
ProfilePram25.AttachDirMethod=0
ProfilePram25.CCWDefAngle=False
ProfilePram25.AddEnd1Elements(extrude_sheet3)
ProfilePram25.End1Type=1102
ProfilePram25.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram25.AddEnd2Elements(extrude_sheet4)
ProfilePram25.End2Type=1102
ProfilePram25.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram25.End1ScallopType=1120
ProfilePram25.End1ScallopTypeParams=["50"]
ProfilePram25.End2ScallopType=1120
ProfilePram25.End2ScallopTypeParams=["50"]
profile25 = part.CreateProfile(ProfilePram25,False)
part.BlankElement(profile25[0],True)
part.SetElementColor(profile25[0],"255","0","0","0.19999998807907104")
ProfilePram26 = part.CreateProfileParam()
ProfilePram26.DefinitionType=1
ProfilePram26.BasePlane="PL,O,"+var_elm14+","+"Y"
ProfilePram26.AddAttachSurfaces(extrude_sheet3)
ProfilePram26.ProfileName="HK.Casing.Wall.Aft.DL04.CDP"
ProfilePram26.MaterialName="SS400"
ProfilePram26.ProfileType=1002
ProfilePram26.ProfileParams=["125","75","7","10","5"]
ProfilePram26.Mold="+"
ProfilePram26.ReverseDir=False
ProfilePram26.ReverseAngle=True
ProfilePram26.CalcSnipOnlyAttachLines=False
ProfilePram26.AttachDirMethod=0
ProfilePram26.CCWDefAngle=False
ProfilePram26.AddEnd1Elements(profile25[0])
ProfilePram26.End1Type=1102
ProfilePram26.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram26.AddEnd2Elements(extrude_sheet5)
ProfilePram26.End2Type=1102
ProfilePram26.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram26.End1ScallopType=1120
ProfilePram26.End1ScallopTypeParams=["50"]
ProfilePram26.End2ScallopType=1120
ProfilePram26.End2ScallopTypeParams=["50"]
profile26 = part.CreateProfile(ProfilePram26,False)
part.BlankElement(profile26[0],True)
part.SetElementColor(profile26[0],"255","0","0","0.19999998807907104")
bracketPram6 = part.CreateBracketParam()
bracketPram6.DefinitionType=1
bracketPram6.BracketName="HK.Casing.Wall.Aft.DL04.Deck.DP"
bracketPram6.MaterialName="SS400"
bracketPram6.BaseElement=profile26[0]
bracketPram6.UseSideSheetForPlane=False
bracketPram6.Mold="+"
bracketPram6.Thickness="7.9999999999999964"
bracketPram6.BracketType=1501
bracketPram6.Scallop1Type=1801
bracketPram6.Scallop1Params=["0"]
bracketPram6.Scallop2Type=0
bracketPram6.Surfaces1=[profile26[0]+",FL"]
bracketPram6.RevSf1=False
bracketPram6.Surfaces2=[profile25[0]+",FL"]
bracketPram6.RevSf2=False
bracketPram6.RevSf3=False
bracketPram6.Sf1DimensionType=1531
bracketPram6.Sf1DimensonParams=["200","15"]
bracketPram6.Sf2DimensionType=1531
bracketPram6.Sf2DimensonParams=["200","15"]
bracket6 = part.CreateBracket(bracketPram6,False)
part.BlankElement(bracket6,True)
part.SetElementColor(bracket6,"0","255","255","0.19999998807907104")
separated_bodies7 = part.BodyDivideByCurves("Separe body by curves42",bracket6,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies7[0],"0","255","255","0.19999998807907104")
solid3 = part.CreateSolid("HK.Casing.Wall.Fore.CD","","SS400")
part.BlankElement(solid3,True)
part.SetElementColor(solid3,"139","69","19","0.79999995231628418")
thicken3 = part.CreateThicken("厚み付け15",solid3,"+",[extrude_sheet4],"+","10","0","0",False,False)
extrudePram12 = part.CreateLinearSweepParam()
extrudePram12.Name="積-押し出し35"
extrudePram12.AddProfile(extrude_sheet1)
extrudePram12.DirectionType="R"
extrudePram12.DirectionParameter1="50000"
extrudePram12.SweepDirection="+Y"
extrudePram12.RefByGeometricMethod=True
extrude6 = part.CreateLinearSweep(solid3,"*",extrudePram12,False)
extrudePram13 = part.CreateLinearSweepParam()
extrudePram13.Name="積-押し出し36"
extrudePram13.AddProfile(extrude_sheet6)
extrudePram13.DirectionType="N"
extrudePram13.DirectionParameter1="50000"
extrudePram13.SweepDirection="+Y"
extrudePram13.RefByGeometricMethod=True
extrude7 = part.CreateLinearSweep(solid3,"*",extrudePram13,False)
extrudePram14 = part.CreateLinearSweepParam()
extrudePram14.Name="積-押し出し37"
extrudePram14.AddProfile(extrude_sheet2)
extrudePram14.DirectionType="R"
extrudePram14.DirectionParameter1="50000"
extrudePram14.SweepDirection="+Z"
extrudePram14.RefByGeometricMethod=True
extrude8 = part.CreateLinearSweep(solid3,"*",extrudePram14,False)
extrudePram15 = part.CreateLinearSweepParam()
extrudePram15.Name="積-押し出し38"
extrudePram15.AddProfile(extrude_sheet5)
extrudePram15.DirectionType="N"
extrudePram15.DirectionParameter1="50000"
extrudePram15.SweepDirection="+Z"
extrudePram15.RefByGeometricMethod=True
extrude9 = part.CreateLinearSweep(solid3,"*",extrudePram15,False)
separated_bodies8 = part.BodyDivideByCurves("Separe body by curves54",profile11[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies8[0],"148","0","211","0.38999998569488525")
separated_bodies9 = part.BodyDivideByCurves("Separe body by curves11",profile10[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies9[0],"255","0","0","0.19999998807907104")
ProfilePram27 = part.CreateProfileParam()
ProfilePram27.DefinitionType=1
ProfilePram27.BasePlane="PL,O,"+var_elm14+","+"Y"
ProfilePram27.AddAttachSurfaces(extrude_sheet4)
ProfilePram27.ProfileName="HK.Casing.Wall.Fore.DL04.CDP"
ProfilePram27.MaterialName="SS400"
ProfilePram27.ProfileType=1002
ProfilePram27.ProfileParams=["125","75","7","10","5"]
ProfilePram27.Mold="+"
ProfilePram27.ReverseDir=True
ProfilePram27.ReverseAngle=True
ProfilePram27.CalcSnipOnlyAttachLines=False
ProfilePram27.AttachDirMethod=0
ProfilePram27.CCWDefAngle=False
ProfilePram27.AddEnd1Elements(profile25[0])
ProfilePram27.End1Type=1102
ProfilePram27.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram27.AddEnd2Elements(extrude_sheet5)
ProfilePram27.End2Type=1102
ProfilePram27.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram27.End1ScallopType=1120
ProfilePram27.End1ScallopTypeParams=["50"]
ProfilePram27.End2ScallopType=1120
ProfilePram27.End2ScallopTypeParams=["50"]
profile27 = part.CreateProfile(ProfilePram27,False)
part.BlankElement(profile27[0],True)
part.SetElementColor(profile27[0],"255","0","0","0.19999998807907104")
separated_bodies10 = part.BodyDivideByCurves("Separe body by curves44",profile27[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies10[0],"255","0","0","0.19999998807907104")
bracketPram7 = part.CreateBracketParam()
bracketPram7.DefinitionType=1
bracketPram7.BracketName="HK.Casing.Wall.Side.FR12.Deck.DP"
bracketPram7.MaterialName="SS400"
bracketPram7.BaseElement=profile16[0]
bracketPram7.UseSideSheetForPlane=False
bracketPram7.Mold="+"
bracketPram7.Thickness="9.9999999999999982"
bracketPram7.BracketType=1505
bracketPram7.BracketParams=["200"]
bracketPram7.Scallop1Type=1801
bracketPram7.Scallop1Params=["0"]
bracketPram7.Scallop2Type=0
bracketPram7.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram7.RevSf1=False
bracketPram7.Surfaces2=[profile16[0]+",FL"]
bracketPram7.RevSf2=False
bracketPram7.RevSf3=False
bracketPram7.Sf1DimensionType=1541
bracketPram7.Sf1DimensonParams=["0","100"]
bracketPram7.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram7.Sf2DimensionType=1531
bracketPram7.Sf2DimensonParams=["200","15"]
bracket7 = part.CreateBracket(bracketPram7,False)
part.BlankElement(bracket7,True)
part.SetElementColor(bracket7,"0","255","255","0.19999998807907104")
separated_bodies11 = part.BodyDivideByCurves("Separe body by curves16",bracket7,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies11[0],"0","255","255","0.19999998807907104")
solid4 = part.CreateSolid("HK.Casing.Wall.Side.CDP","","SS400")
part.BlankElement(solid4,True)
part.SetElementColor(solid4,"139","69","19","0.79999995231628418")
thicken4 = part.CreateThicken("厚み付け7",solid4,"+",[extrude_sheet1],"-","10","0","0",False,False)
bracketPram8 = part.CreateBracketParam()
bracketPram8.DefinitionType=1
bracketPram8.BracketName="HK.Casing.Wall.Fore.DL03.Deck.DP"
bracketPram8.MaterialName="SS400"
bracketPram8.BaseElement=profile22[0]
bracketPram8.UseSideSheetForPlane=False
bracketPram8.Mold="+"
bracketPram8.Thickness="7.9999999999999964"
bracketPram8.BracketType=1501
bracketPram8.Scallop1Type=1801
bracketPram8.Scallop1Params=["0"]
bracketPram8.Scallop2Type=0
bracketPram8.Surfaces1=[profile22[0]+",FL"]
bracketPram8.RevSf1=False
bracketPram8.Surfaces2=[profile17[0]+",FL"]
bracketPram8.RevSf2=False
bracketPram8.RevSf3=False
bracketPram8.Sf1DimensionType=1531
bracketPram8.Sf1DimensonParams=["200","15"]
bracketPram8.Sf2DimensionType=1531
bracketPram8.Sf2DimensonParams=["200","15"]
bracket8 = part.CreateBracket(bracketPram8,False)
part.BlankElement(bracket8,True)
part.SetElementColor(bracket8,"0","255","255","0.19999998807907104")
separated_bodies12 = part.BodyDivideByCurves("Separe body by curves36",bracket8,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies12[0],"0","255","255","0.19999998807907104")
bracketPram9 = part.CreateBracketParam()
bracketPram9.DefinitionType=1
bracketPram9.BracketName="HK.Casing.Deck.D.FR13P"
bracketPram9.MaterialName="SS400"
bracketPram9.BaseElement=profile7[0]
bracketPram9.UseSideSheetForPlane=False
bracketPram9.Mold="+"
bracketPram9.Thickness="7.9999999999999964"
bracketPram9.BracketType=1501
bracketPram9.Scallop1Type=1801
bracketPram9.Scallop1Params=["0"]
bracketPram9.Scallop2Type=0
bracketPram9.Surfaces1=[profile1[0]+",WB"]
bracketPram9.RevSf1=False
bracketPram9.Surfaces2=[profile7[0]+",FL"]
bracketPram9.RevSf2=False
bracketPram9.RevSf3=False
bracketPram9.Sf1DimensionType=1531
bracketPram9.Sf1DimensonParams=["250","15"]
bracketPram9.Sf2DimensionType=1531
bracketPram9.Sf2DimensonParams=["250","15"]
bracket9 = part.CreateBracket(bracketPram9,False)
part.BlankElement(bracket9,True)
part.SetElementColor(bracket9,"0","255","255","0.19999998807907104")
separated_bodies13 = part.BodyDivideByCurves("Separe body by curves46",bracket9,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies13[0],"0","255","255","0.19999998807907104")
extrudePram16 = part.CreateLinearSweepParam()
extrudePram16.Name="積-押し出し7"
extrudePram16.AddProfile(skt_pl3+",Edge00")
extrudePram16.DirectionType="N"
extrudePram16.DirectionParameter1="50000"
extrudePram16.SweepDirection="+Z"
extrudePram16.RefByGeometricMethod=True
extrude10 = part.CreateLinearSweep(solid4,"*",extrudePram16,False)
extrudePram17 = part.CreateLinearSweepParam()
extrudePram17.Name="積-押し出し8"
extrudePram17.AddProfile(extrude_sheet2)
extrudePram17.DirectionType="R"
extrudePram17.DirectionParameter1="50000"
extrudePram17.SweepDirection="+Z"
extrudePram17.RefByGeometricMethod=True
extrude11 = part.CreateLinearSweep(solid4,"*",extrudePram17,False)
extrudePram18 = part.CreateLinearSweepParam()
extrudePram18.Name="積-押し出し9"
extrudePram18.AddProfile(extrude_sheet5)
extrudePram18.DirectionType="N"
extrudePram18.DirectionParameter1="50000"
extrudePram18.SweepDirection="+Z"
extrudePram18.RefByGeometricMethod=True
extrude12 = part.CreateLinearSweep(solid4,"*",extrudePram18,False)
separated_bodies14 = part.BodyDivideByCurves("Separe body by curves49",profile13[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies14[0],"148","0","211","0.39999997615814209")
separated_bodies15 = part.BodyDivideByCurves("Separe body by curves55",bracket5,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies15[0],"0","255","255","0.19999998807907104")
bracketPram10 = part.CreateBracketParam()
bracketPram10.DefinitionType=1
bracketPram10.BracketName="HK.Casing.Wall.Fore.DL04.Deck.DP"
bracketPram10.MaterialName="SS400"
bracketPram10.BaseElement=profile27[0]
bracketPram10.UseSideSheetForPlane=False
bracketPram10.Mold="+"
bracketPram10.Thickness="7.9999999999999964"
bracketPram10.BracketType=1501
bracketPram10.Scallop1Type=1801
bracketPram10.Scallop1Params=["0"]
bracketPram10.Scallop2Type=0
bracketPram10.Surfaces1=[profile27[0]+",FL"]
bracketPram10.RevSf1=False
bracketPram10.Surfaces2=[profile25[0]+",FL"]
bracketPram10.RevSf2=False
bracketPram10.RevSf3=False
bracketPram10.Sf1DimensionType=1531
bracketPram10.Sf1DimensonParams=["200","15"]
bracketPram10.Sf2DimensionType=1531
bracketPram10.Sf2DimensonParams=["200","15"]
bracket10 = part.CreateBracket(bracketPram10,False)
part.BlankElement(bracket10,True)
part.SetElementColor(bracket10,"0","255","255","0.19999998807907104")
ProfilePram28 = part.CreateProfileParam()
ProfilePram28.DefinitionType=1
ProfilePram28.BasePlane="PL,O,"+var_elm6+","+"Y"
ProfilePram28.AddAttachSurfaces(extrude_sheet2)
ProfilePram28.ProfileName="HK.Casing.Deck.D.DL01.AP"
ProfilePram28.MaterialName="SS400"
ProfilePram28.ProfileType=1002
ProfilePram28.ProfileParams=["125","75","7","10","5"]
ProfilePram28.Mold="+"
ProfilePram28.ReverseDir=True
ProfilePram28.ReverseAngle=True
ProfilePram28.CalcSnipOnlyAttachLines=False
ProfilePram28.AttachDirMethod=0
ProfilePram28.CCWDefAngle=False
ProfilePram28.AddEnd1Elements(extrude_sheet3)
ProfilePram28.End1Type=1102
ProfilePram28.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram28.AddEnd2Elements(profile21[0])
ProfilePram28.End2Type=1102
ProfilePram28.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram28.End1ScallopType=1120
ProfilePram28.End1ScallopTypeParams=["50"]
ProfilePram28.End2ScallopType=1120
ProfilePram28.End2ScallopTypeParams=["50"]
profile28 = part.CreateProfile(ProfilePram28,False)
part.BlankElement(profile28[0],True)
part.SetElementColor(profile28[0],"255","0","0","0.19999998807907104")
ProfilePram29 = part.CreateProfileParam()
ProfilePram29.DefinitionType=1
ProfilePram29.BasePlane="PL,O,"+var_elm6+","+"Y"
ProfilePram29.AddAttachSurfaces(extrude_sheet3)
ProfilePram29.ProfileName="HK.Casing.Wall.Aft.DL01.CDP"
ProfilePram29.MaterialName="SS400"
ProfilePram29.ProfileType=1002
ProfilePram29.ProfileParams=["125","75","7","10","5"]
ProfilePram29.Mold="+"
ProfilePram29.ReverseDir=False
ProfilePram29.ReverseAngle=True
ProfilePram29.CalcSnipOnlyAttachLines=False
ProfilePram29.AttachDirMethod=0
ProfilePram29.CCWDefAngle=False
ProfilePram29.AddEnd1Elements(profile28[0])
ProfilePram29.End1Type=1102
ProfilePram29.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram29.AddEnd2Elements(extrude_sheet5)
ProfilePram29.End2Type=1102
ProfilePram29.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram29.End1ScallopType=1120
ProfilePram29.End1ScallopTypeParams=["50"]
ProfilePram29.End2ScallopType=1120
ProfilePram29.End2ScallopTypeParams=["50"]
profile29 = part.CreateProfile(ProfilePram29,False)
part.BlankElement(profile29[0],True)
part.SetElementColor(profile29[0],"255","0","0","0.19999998807907104")
separated_bodies16 = part.BodyDivideByCurves("Separe body by curves39",profile29[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies16[0],"255","0","0","0.19999998807907104")
bracketPram11 = part.CreateBracketParam()
bracketPram11.DefinitionType=1
bracketPram11.BracketName="HK.Casing.Wall.Aft.DL01.Deck.DP"
bracketPram11.MaterialName="SS400"
bracketPram11.BaseElement=profile29[0]
bracketPram11.UseSideSheetForPlane=False
bracketPram11.Mold="+"
bracketPram11.Thickness="7.9999999999999964"
bracketPram11.BracketType=1501
bracketPram11.Scallop1Type=1801
bracketPram11.Scallop1Params=["0"]
bracketPram11.Scallop2Type=0
bracketPram11.Surfaces1=[profile29[0]+",FL"]
bracketPram11.RevSf1=False
bracketPram11.Surfaces2=[profile28[0]+",FL"]
bracketPram11.RevSf2=False
bracketPram11.RevSf3=False
bracketPram11.Sf1DimensionType=1531
bracketPram11.Sf1DimensonParams=["200","15"]
bracketPram11.Sf2DimensionType=1531
bracketPram11.Sf2DimensonParams=["200","15"]
bracket11 = part.CreateBracket(bracketPram11,False)
part.BlankElement(bracket11,True)
part.SetElementColor(bracket11,"0","255","255","0.19999998807907104")
separated_bodies17 = part.BodyDivideByCurves("Separe body by curves43",bracket11,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies17[0],"0","255","255","0.19999998807907104")
bracketPram12 = part.CreateBracketParam()
bracketPram12.DefinitionType=1
bracketPram12.BracketName="HK.Casing.Deck.D.FR09P"
bracketPram12.MaterialName="SS400"
bracketPram12.BaseElement=profile2[0]
bracketPram12.UseSideSheetForPlane=False
bracketPram12.Mold="+"
bracketPram12.Thickness="8.9999999999999982"
bracketPram12.BracketType=1501
bracketPram12.Scallop1Type=1801
bracketPram12.Scallop1Params=["50"]
bracketPram12.Scallop2Type=0
bracketPram12.Surfaces1=[profile1[0]+",WF"]
bracketPram12.RevSf1=False
bracketPram12.Surfaces2=[profile2[0]+",FL"]
bracketPram12.RevSf2=False
bracketPram12.RevSf3=False
bracketPram12.FlangeType=262
bracketPram12.FlangeParams=["75","30","29.999999999999996","30","50","1"]
bracketPram12.RevFlange=False
bracketPram12.Sf1DimensionType=1541
bracketPram12.Sf1DimensonParams=["0","80"]
bracketPram12.Sf1EndElements=[profile1[1]+",FR"]
bracketPram12.Sf2DimensionType=1531
bracketPram12.Sf2DimensonParams=["300","15"]
bracket12 = part.CreateBracket(bracketPram12,False)
part.BlankElement(bracket12,True)
part.SetElementColor(bracket12,"0","255","255","0.19999998807907104")
bracketPram13 = part.CreateBracketParam()
bracketPram13.DefinitionType=1
bracketPram13.BracketName="HK.Casing.Wall.Fore.DL05.Deck.DP"
bracketPram13.MaterialName="SS400"
bracketPram13.BaseElement=profile6[0]
bracketPram13.UseSideSheetForPlane=False
bracketPram13.Mold="+"
bracketPram13.Thickness="7.9999999999999964"
bracketPram13.BracketType=1501
bracketPram13.Scallop1Type=1801
bracketPram13.Scallop1Params=["0"]
bracketPram13.Scallop2Type=0
bracketPram13.Surfaces1=[profile6[0]+",FL"]
bracketPram13.RevSf1=False
bracketPram13.Surfaces2=[profile5[0]+",FL"]
bracketPram13.RevSf2=False
bracketPram13.RevSf3=False
bracketPram13.Sf1DimensionType=1531
bracketPram13.Sf1DimensonParams=["200","15"]
bracketPram13.Sf2DimensionType=1531
bracketPram13.Sf2DimensonParams=["200","15"]
bracket13 = part.CreateBracket(bracketPram13,False)
part.BlankElement(bracket13,True)
part.SetElementColor(bracket13,"0","255","255","0.19999998807907104")
separated_bodies18 = part.BodyDivideByCurves("Separe body by curves23",profile5[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies18[0],"255","0","0","0.19999998807907104")
bracketPram14 = part.CreateBracketParam()
bracketPram14.DefinitionType=1
bracketPram14.BracketName="HK.Casing.Wall.Side.FR13.Deck.DP"
bracketPram14.MaterialName="SS400"
bracketPram14.BaseElement=profile13[0]
bracketPram14.UseSideSheetForPlane=False
bracketPram14.Mold="+"
bracketPram14.Thickness="7.9999999999999964"
bracketPram14.BracketType=1501
bracketPram14.Scallop1Type=1801
bracketPram14.Scallop1Params=["0"]
bracketPram14.Scallop2Type=0
bracketPram14.Surfaces1=[profile13[0]+",FL"]
bracketPram14.RevSf1=False
bracketPram14.Surfaces2=[profile12[0]+",FL"]
bracketPram14.RevSf2=False
bracketPram14.RevSf3=False
bracketPram14.Sf1DimensionType=1531
bracketPram14.Sf1DimensonParams=["250","15"]
bracketPram14.Sf2DimensionType=1531
bracketPram14.Sf2DimensonParams=["250","15"]
bracket14 = part.CreateBracket(bracketPram14,False)
part.BlankElement(bracket14,True)
part.SetElementColor(bracket14,"0","255","255","0.19999998807907104")
bracketPram15 = part.CreateBracketParam()
bracketPram15.DefinitionType=1
bracketPram15.BracketName="HK.Casing.Wall.Side.FR14.Deck.DP"
bracketPram15.MaterialName="SS400"
bracketPram15.BaseElement=profile19[0]
bracketPram15.UseSideSheetForPlane=False
bracketPram15.Mold="+"
bracketPram15.Thickness="9.9999999999999982"
bracketPram15.BracketType=1505
bracketPram15.BracketParams=["200"]
bracketPram15.Scallop1Type=1801
bracketPram15.Scallop1Params=["0"]
bracketPram15.Scallop2Type=0
bracketPram15.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram15.RevSf1=False
bracketPram15.Surfaces2=[profile19[0]+",FL"]
bracketPram15.RevSf2=False
bracketPram15.RevSf3=False
bracketPram15.Sf1DimensionType=1541
bracketPram15.Sf1DimensonParams=["0","100"]
bracketPram15.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram15.Sf2DimensionType=1531
bracketPram15.Sf2DimensonParams=["200","15"]
bracket15 = part.CreateBracket(bracketPram15,False)
part.BlankElement(bracket15,True)
part.SetElementColor(bracket15,"0","255","255","0.19999998807907104")
extrudePram19 = part.CreateLinearSweepParam()
extrudePram19.Name="積-押し出し22"
extrudePram19.AddProfile(extrude_sheet5)
extrudePram19.DirectionType="N"
extrudePram19.DirectionParameter1="50000"
extrudePram19.SweepDirection="+Z"
extrudePram19.RefByGeometricMethod=True
extrude13 = part.CreateLinearSweep(solid2,"*",extrudePram19,False)
separated_bodies19 = part.BodyDivideByCurves("Separe body by curves1",solid1,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies19[1],"139","69","19","0.78999996185302734")
bracketPram16 = part.CreateBracketParam()
bracketPram16.DefinitionType=1
bracketPram16.BracketName="HK.Casing.Wall.Aft.DL05.Deck.DP"
bracketPram16.MaterialName="SS400"
bracketPram16.BaseElement=profile20[0]
bracketPram16.UseSideSheetForPlane=False
bracketPram16.Mold="+"
bracketPram16.Thickness="7.9999999999999964"
bracketPram16.BracketType=1501
bracketPram16.Scallop1Type=1801
bracketPram16.Scallop1Params=["0"]
bracketPram16.Scallop2Type=0
bracketPram16.Surfaces1=[profile20[0]+",FL"]
bracketPram16.RevSf1=False
bracketPram16.Surfaces2=[profile5[0]+",FL"]
bracketPram16.RevSf2=False
bracketPram16.RevSf3=False
bracketPram16.Sf1DimensionType=1531
bracketPram16.Sf1DimensonParams=["200","15"]
bracketPram16.Sf2DimensionType=1531
bracketPram16.Sf2DimensonParams=["200","15"]
bracket16 = part.CreateBracket(bracketPram16,False)
part.BlankElement(bracket16,True)
part.SetElementColor(bracket16,"0","255","255","0.19999998807907104")
separated_bodies20 = part.BodyDivideByCurves("Separe body by curves3",profile8[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies20[0],"255","0","0","0.19999998807907104")
bracketPram17 = part.CreateBracketParam()
bracketPram17.DefinitionType=1
bracketPram17.BracketName="HK.Casing.Wall.Side.FR08.Deck.DP"
bracketPram17.MaterialName="SS400"
bracketPram17.BaseElement=profile3[0]
bracketPram17.UseSideSheetForPlane=False
bracketPram17.Mold="+"
bracketPram17.Thickness="9.9999999999999982"
bracketPram17.BracketType=1505
bracketPram17.BracketParams=["200"]
bracketPram17.Scallop1Type=1801
bracketPram17.Scallop1Params=["0"]
bracketPram17.Scallop2Type=0
bracketPram17.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram17.RevSf1=False
bracketPram17.Surfaces2=[profile3[0]+",FL"]
bracketPram17.RevSf2=False
bracketPram17.RevSf3=False
bracketPram17.Sf1DimensionType=1541
bracketPram17.Sf1DimensonParams=["0","100"]
bracketPram17.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram17.Sf2DimensionType=1531
bracketPram17.Sf2DimensonParams=["200","15"]
bracket17 = part.CreateBracket(bracketPram17,False)
part.BlankElement(bracket17,True)
part.SetElementColor(bracket17,"0","255","255","0.19999998807907104")
separated_bodies21 = part.BodyDivideByCurves("Separe body by curves6",bracket17,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies21[0],"0","255","255","0.19999998807907104")
bracketPram18 = part.CreateBracketParam()
bracketPram18.DefinitionType=1
bracketPram18.BracketName="HK.Casing.Deck.D.FR09P"
bracketPram18.MaterialName="SS400"
bracketPram18.BaseElement=profile21[0]
bracketPram18.UseSideSheetForPlane=False
bracketPram18.Mold="+"
bracketPram18.Thickness="7.9999999999999964"
bracketPram18.BracketType=1501
bracketPram18.Scallop1Type=1801
bracketPram18.Scallop1Params=["0"]
bracketPram18.Scallop2Type=0
bracketPram18.Surfaces1=[profile1[0]+",WB"]
bracketPram18.RevSf1=False
bracketPram18.Surfaces2=[profile21[0]+",FL"]
bracketPram18.RevSf2=False
bracketPram18.RevSf3=False
bracketPram18.Sf1DimensionType=1531
bracketPram18.Sf1DimensonParams=["250","15"]
bracketPram18.Sf2DimensionType=1531
bracketPram18.Sf2DimensonParams=["250","15"]
bracket18 = part.CreateBracket(bracketPram18,False)
part.BlankElement(bracket18,True)
part.SetElementColor(bracket18,"0","255","255","0.19999998807907104")
separated_bodies22 = part.BodyDivideByCurves("Separe body by curves52",bracket18,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies22[0],"0","255","255","0.19999998807907104")
bracketPram19 = part.CreateBracketParam()
bracketPram19.DefinitionType=1
bracketPram19.BracketName="HK.Casing.Wall.Side.FR07.Deck.DP"
bracketPram19.MaterialName="SS400"
bracketPram19.BaseElement=profile4[0]
bracketPram19.UseSideSheetForPlane=False
bracketPram19.Mold="+"
bracketPram19.Thickness="9.9999999999999982"
bracketPram19.BracketType=1505
bracketPram19.BracketParams=["200"]
bracketPram19.Scallop1Type=1801
bracketPram19.Scallop1Params=["0"]
bracketPram19.Scallop2Type=0
bracketPram19.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram19.RevSf1=False
bracketPram19.Surfaces2=[profile4[0]+",FL"]
bracketPram19.RevSf2=False
bracketPram19.RevSf3=False
bracketPram19.Sf1DimensionType=1541
bracketPram19.Sf1DimensonParams=["0","100"]
bracketPram19.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram19.Sf2DimensionType=1531
bracketPram19.Sf2DimensonParams=["200","15"]
bracket19 = part.CreateBracket(bracketPram19,False)
part.BlankElement(bracket19,True)
part.SetElementColor(bracket19,"0","255","255","0.19999998807907104")
separated_bodies23 = part.BodyDivideByCurves("Separe body by curves56",bracket2,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies23[0],"0","255","255","0.19999998807907104")
bracketPram20 = part.CreateBracketParam()
bracketPram20.DefinitionType=1
bracketPram20.BracketName="HK.Casing.Wall.Aft.DL03.Deck.DP"
bracketPram20.MaterialName="SS400"
bracketPram20.BaseElement=profile18[0]
bracketPram20.UseSideSheetForPlane=False
bracketPram20.Mold="+"
bracketPram20.Thickness="7.9999999999999964"
bracketPram20.BracketType=1501
bracketPram20.Scallop1Type=1801
bracketPram20.Scallop1Params=["0"]
bracketPram20.Scallop2Type=0
bracketPram20.Surfaces1=[profile18[0]+",FL"]
bracketPram20.RevSf1=False
bracketPram20.Surfaces2=[profile17[0]+",FL"]
bracketPram20.RevSf2=False
bracketPram20.RevSf3=False
bracketPram20.Sf1DimensionType=1531
bracketPram20.Sf1DimensonParams=["200","15"]
bracketPram20.Sf2DimensionType=1531
bracketPram20.Sf2DimensonParams=["200","15"]
bracket20 = part.CreateBracket(bracketPram20,False)
part.BlankElement(bracket20,True)
part.SetElementColor(bracket20,"0","255","255","0.19999998807907104")
separated_bodies24 = part.BodyDivideByCurves("Separe body by curves15",profile21[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies24[1],"148","0","211","0.39999997615814209")
separated_bodies25 = part.BodyDivideByCurves("Separe body by curves2",profile16[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies25[0],"255","0","0","0.19999998807907104")
bracketPram21 = part.CreateBracketParam()
bracketPram21.DefinitionType=1
bracketPram21.BracketName="HK.Casing.Wall.Side.FR11.Deck.DP"
bracketPram21.MaterialName="SS400"
bracketPram21.BaseElement=profile10[0]
bracketPram21.UseSideSheetForPlane=False
bracketPram21.Mold="+"
bracketPram21.Thickness="9.9999999999999982"
bracketPram21.BracketType=1505
bracketPram21.BracketParams=["200"]
bracketPram21.Scallop1Type=1801
bracketPram21.Scallop1Params=["0"]
bracketPram21.Scallop2Type=0
bracketPram21.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram21.RevSf1=False
bracketPram21.Surfaces2=[profile10[0]+",FL"]
bracketPram21.RevSf2=False
bracketPram21.RevSf3=False
bracketPram21.Sf1DimensionType=1541
bracketPram21.Sf1DimensonParams=["0","100"]
bracketPram21.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram21.Sf2DimensionType=1531
bracketPram21.Sf2DimensonParams=["200","15"]
bracket21 = part.CreateBracket(bracketPram21,False)
part.BlankElement(bracket21,True)
part.SetElementColor(bracket21,"0","255","255","0.19999998807907104")
separated_bodies26 = part.BodyDivideByCurves("Separe body by curves8",bracket21,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies26[0],"0","255","255","0.19999998807907104")
bracketPram22 = part.CreateBracketParam()
bracketPram22.DefinitionType=1
bracketPram22.BracketName="HK.Casing.Wall.Side.FR15.Deck.DP"
bracketPram22.MaterialName="SS400"
bracketPram22.BaseElement=profile24[0]
bracketPram22.UseSideSheetForPlane=False
bracketPram22.Mold="+"
bracketPram22.Thickness="9.9999999999999982"
bracketPram22.BracketType=1505
bracketPram22.BracketParams=["200"]
bracketPram22.Scallop1Type=1801
bracketPram22.Scallop1Params=["0"]
bracketPram22.Scallop2Type=0
bracketPram22.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram22.RevSf1=False
bracketPram22.Surfaces2=[profile24[0]+",FL"]
bracketPram22.RevSf2=False
bracketPram22.RevSf3=False
bracketPram22.Sf1DimensionType=1541
bracketPram22.Sf1DimensonParams=["0","100"]
bracketPram22.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram22.Sf2DimensionType=1531
bracketPram22.Sf2DimensonParams=["200","15"]
bracket22 = part.CreateBracket(bracketPram22,False)
part.BlankElement(bracket22,True)
part.SetElementColor(bracket22,"0","255","255","0.19999998807907104")
separated_bodies27 = part.BodyDivideByCurves("Separe body by curves20",profile17[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies27[0],"255","0","0","0.19999998807907104")
bracketPram23 = part.CreateBracketParam()
bracketPram23.DefinitionType=1
bracketPram23.BracketName="HK.Casing.Wall.Side.FR09.Deck.DP"
bracketPram23.MaterialName="SS400"
bracketPram23.BaseElement=profile23[0]
bracketPram23.UseSideSheetForPlane=False
bracketPram23.Mold="+"
bracketPram23.Thickness="7.9999999999999964"
bracketPram23.BracketType=1501
bracketPram23.Scallop1Type=1801
bracketPram23.Scallop1Params=["0"]
bracketPram23.Scallop2Type=0
bracketPram23.Surfaces1=[profile23[0]+",FL"]
bracketPram23.RevSf1=False
bracketPram23.Surfaces2=[profile2[0]+",FL"]
bracketPram23.RevSf2=False
bracketPram23.RevSf3=False
bracketPram23.Sf1DimensionType=1531
bracketPram23.Sf1DimensonParams=["250","15"]
bracketPram23.Sf2DimensionType=1531
bracketPram23.Sf2DimensonParams=["250","15"]
bracket23 = part.CreateBracket(bracketPram23,False)
part.BlankElement(bracket23,True)
part.SetElementColor(bracket23,"0","255","255","0.19999998807907104")
separated_bodies28 = part.BodyDivideByCurves("Separe body by curves21",profile12[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies28[0],"148","0","211","0.39999997615814209")
separated_bodies29 = part.BodyDivideByCurves("Separe body by curves40",profile20[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies29[0],"255","0","0","0.19999998807907104")
separated_bodies30 = part.BodyDivideByCurves("Separe body by curves29",bracket13,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies30[0],"0","255","255","0.19999998807907104")
separated_bodies31 = part.BodyDivideByCurves("Separe body by curves18",bracket15,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies31[0],"0","255","255","0.19999998807907104")
separated_bodies32 = part.BodyDivideByCurves("Separe body by curves38",bracket20,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies32[0],"0","255","255","0.19999998807907104")
separated_bodies33 = part.BodyDivideByCurves("Separe body by curves27",solid4,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies33[0],"139","69","19","0.79999995231628418")
separated_bodies34 = part.BodyDivideByCurves("Separe body by curves50",bracket12,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies34[0],"0","255","255","0.19999998807907104")
separated_bodies35 = part.BodyDivideByCurves("Separe body by curves19",profile1[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies35[0],"148","0","211","0.39999997615814209")
separated_bodies36 = part.BodyDivideByCurves("Separe body by curves14",profile14[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies36[0],"255","0","0","0.19999998807907104")
separated_bodies37 = part.BodyDivideByCurves("Separe body by curves37",profile9[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies37[0],"255","0","0","0.19999998807907104")
separated_bodies38 = part.BodyDivideByCurves("Separe body by curves7",profile3[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies38[0],"255","0","0","0.19999998807907104")
separated_bodies39 = part.BodyDivideByCurves("Separe body by curves48",bracket3,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies39[0],"0","255","255","0.19999998807907104")
separated_bodies40 = part.BodyDivideByCurves("Separe body by curves10",bracket22,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies40[0],"0","255","255","0.19999998807907104")
separated_bodies41 = part.BodyDivideByCurves("Separe body by curves28",solid3,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies41[1],"139","69","19","0.79999995231628418")
separated_bodies42 = part.BodyDivideByCurves("Separe body by curves53",profile1[1],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies42[0],"148","0","211","0.39999997615814209")
separated_bodies43 = part.BodyDivideByCurves("Separe body by curves12",profile2[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies43[0],"148","0","211","0.39999997615814209")
separated_bodies44 = part.BodyDivideByCurves("Separe body by curves26",profile28[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies44[0],"255","0","0","0.19999998807907104")
separated_bodies45 = part.BodyDivideByCurves("Separe body by curves25",profile4[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies45[0],"255","0","0","0.19999998807907104")
separated_bodies46 = part.BodyDivideByCurves("Separe body by curves22",profile25[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies46[0],"255","0","0","0.19999998807907104")
separated_bodies47 = part.BodyDivideByCurves("Separe body by curves24",profile19[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies47[0],"255","0","0","0.19999998807907104")
separated_bodies48 = part.BodyDivideByCurves("Separe body by curves57",profile15[1],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies48[0],"148","0","211","0.39999997615814209")
separated_bodies49 = part.BodyDivideByCurves("Separe body by curves58",profile11[1],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies49[0],"148","0","211","0.38999998569488525")
separated_bodies50 = part.BodyDivideByCurves("Separe body by curves45",bracket14,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies50[0],"0","255","255","0.19999998807907104")
separated_bodies51 = part.BodyDivideByCurves("Separe body by curves35",bracket10,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies51[0],"0","255","255","0.19999998807907104")
separated_bodies52 = part.BodyDivideByCurves("Separe body by curves9",profile24[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies52[0],"255","0","0","0.19999998807907104")
separated_bodies53 = part.BodyDivideByCurves("Separe body by curves33",bracket16,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies53[0],"0","255","255","0.19999998807907104")
separated_bodies54 = part.BodyDivideByCurves("Separe body by curves51",profile23[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies54[0],"148","0","211","0.39999997615814209")
separated_bodies55 = part.BodyDivideByCurves("Separe body by curves34",profile26[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies55[0],"255","0","0","0.19999998807907104")
separated_bodies56 = part.BodyDivideByCurves("Separe body by curves30",profile6[0],[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies56[0],"255","0","0","0.19999998807907104")
separated_bodies57 = part.BodyDivideByCurves("Separe body by curves4",solid2,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies57[1],"139","69","19","0.79999995231628418")
separated_bodies58 = part.BodyDivideByCurves("Separe body by curves17",bracket19,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies58[0],"0","255","255","0.19999998807907104")
separated_bodies59 = part.BodyDivideByCurves("Separe body by curves47",bracket23,[skt_pl4],False,"0","","",False)
part.SetElementColor(separated_bodies59[0],"0","255","255","0.19999998807907104")

