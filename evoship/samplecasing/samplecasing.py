import win32com.client
evoship = win32com.client.DispatchEx("EvoShip.Application")
evoship.ShowMainWindow(True)
doc = evoship.Create3DDocument()
part = doc.GetPart()
skt_pl1 = part.CreateSketchPlane("HK.Ax.Deck","","PL,X","0",False,False,"","","",True,False)
part.BlankElement(skt_pl1,True)
skt_ln1 = part.CreateSketchLine(skt_pl1,"","作図","15500,31800","15500,-2999.9999999999964",False)
skt_ln2 = part.CreateSketchLine(skt_pl1,"","作図","-15499.999999999996,31800","-15500,-2999.9999999999964",False)
skt_ln3 = part.CreateSketchLine(skt_pl1,"","作図","0,-3000","0,31799.999999999996",False)
skt_layer1 = part.CreateSketchLayer("General.Deck.UpperDeck",skt_pl1)
skt_ln4 = part.CreateSketchLine(skt_pl1,"","General.Deck.UpperDeck","2000,15300","18500,14933.333333333334",False)
skt_ln5 = part.CreateSketchLine(skt_pl1,"","General.Deck.UpperDeck","2000,15300","-2000,15300",False)
skt_ln6 = part.CreateSketchLine(skt_pl1,"","General.Deck.UpperDeck","-2000,15300","-18500,14933.333333333336",False)
skt_layer2 = part.CreateSketchLayer("Casing.Deck.A",skt_pl1)
skt_ln7 = part.CreateSketchLine(skt_pl1,"","Casing.Deck.A","18500,18300","-18500,18300",False)
skt_layer3 = part.CreateSketchLayer("Casing.Deck.B",skt_pl1)
skt_ln8 = part.CreateSketchLine(skt_pl1,"","Casing.Deck.B","18500,21300","-18500,21300",False)
skt_layer4 = part.CreateSketchLayer("Casing.Deck.C",skt_pl1)
skt_ln9 = part.CreateSketchLine(skt_pl1,"","Casing.Deck.C","18500,24300","-18500,24300",False)
skt_layer5 = part.CreateSketchLayer("Casing.Deck.D",skt_pl1)
skt_ln10 = part.CreateSketchLine(skt_pl1,"","Casing.Deck.D","18500,27300","-18500,27300",False)
extrudePram1 = part.CreateLinearSweepParam()
extrudePram1.AddProfile(skt_pl1+",Casing.Deck.B")
extrudePram1.DirectionType=2
extrudePram1.DirectionParameter1="50000"
extrudePram1.DirectionParameter2="10000"
extrudePram1.SweepDirection="+X"
extrudePram1.Name="HK.Casing.Deck.B"
extrudePram1.MaterialName="SS400"
extrudePram1.IntervalSweep=False
extrude_sheet1 = part.CreateLinearSweepSheet(extrudePram1,False)
part.SheetAlignNormal(extrude_sheet1,-0,0,1)
part.BlankElement(extrude_sheet1,True)
part.SetElementColor(extrude_sheet1,"225","225","225","1")
extrudePram2 = part.CreateLinearSweepParam()
extrudePram2.AddProfile(skt_pl1+",Casing.Deck.A")
extrudePram2.DirectionType=2
extrudePram2.DirectionParameter1="50000"
extrudePram2.DirectionParameter2="10000"
extrudePram2.SweepDirection="+X"
extrudePram2.Name="HK.Casing.Deck.A"
extrudePram2.MaterialName="SS400"
extrudePram2.IntervalSweep=False
extrude_sheet2 = part.CreateLinearSweepSheet(extrudePram2,False)
part.SheetAlignNormal(extrude_sheet2,-0,0,1)
part.BlankElement(extrude_sheet2,True)
part.SetElementColor(extrude_sheet2,"225","225","225","1")
skt_pl2 = part.CreateSketchPlane("HK.Az.Wall","","PL,Z","0",False,False,"","","",True,False)
part.BlankElement(skt_pl2,True)
skt_ln11 = part.CreateSketchLine(skt_pl2,"","作図","0,-18500","0,18500",False)
skt_ln12 = part.CreateSketchLine(skt_pl2,"","作図","-50000,15500","250000,15500",False)
skt_ln13 = part.CreateSketchLine(skt_pl2,"","作図","-50000,-15500","250000,-15500",False)
skt_layer6 = part.CreateSketchLayer("Casing.Fore",skt_pl2)
skt_ln14 = part.CreateSketchLine(skt_pl2,"","Casing.Fore","11370.000000000002,-10394.984078409721","11370.000000000002,9605.0159215902786",False)
skt_layer7 = part.CreateSketchLayer("Casing.Aft",skt_pl2)
skt_ln15 = part.CreateSketchLine(skt_pl2,"","Casing.Aft","4019.9999999999995,-10394.984078409721","4019.9999999999995,9605.0159215902786",False)
skt_layer8 = part.CreateSketchLayer("Casing.Side.P",skt_pl2)
skt_ln16 = part.CreateSketchLine(skt_pl2,"","Casing.Side.P","-1500,4800","18500,4800",False)
skt_layer9 = part.CreateSketchLayer("Casing.Side.S",skt_pl2)
skt_ln17 = part.CreateSketchLine(skt_pl2,"","Casing.Side.S","-1500,-4800","18500,-4800",False)
skt_layer10 = part.CreateSketchLayer("Dim.CenterLine",skt_pl2)
skt_ln18 = part.CreateSketchLine(skt_pl2,"","Dim.CenterLine","-50000,0","250000,0",False)
extrudePram3 = part.CreateLinearSweepParam()
extrudePram3.AddProfile(skt_pl2+",Casing.Aft")
extrudePram3.DirectionType=2
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
var_elm1 = part.CreateVariable("Casing.DL04","3200","mm","")
ProfilePram1 = part.CreateProfileParam()
ProfilePram1.DefinitionType=1
ProfilePram1.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram1.AddAttachSurfaces(extrude_sheet3)
ProfilePram1.ProfileName="HK.Casing.Wall.Aft.DL04.ABP"
ProfilePram1.MaterialName="SS400"
ProfilePram1.ProfileType=1003
ProfilePram1.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram1.Mold="+"
ProfilePram1.ReverseDir=False
ProfilePram1.ReverseAngle=True
ProfilePram1.CalcSnipOnlyAttachLines=False
ProfilePram1.AttachDirMethod=0
ProfilePram1.CCWDefAngle=False
ProfilePram1.AddEnd1Elements(extrude_sheet1)
ProfilePram1.End1Type=1102
ProfilePram1.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram1.AddEnd2Elements(extrude_sheet2)
ProfilePram1.End2Type=1102
ProfilePram1.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram1.End1ScallopType=1120
ProfilePram1.End1ScallopTypeParams=["50"]
ProfilePram1.End2ScallopType=1120
ProfilePram1.End2ScallopTypeParams=["50"]
profile1 = part.CreateProfile(ProfilePram1,False)
part.SetElementColor(profile1[0],"148","0","211","0.39999997615814209")
var_elm2 = part.CreateVariable("FR14","9770","mm","")
extrudePram4 = part.CreateLinearSweepParam()
extrudePram4.AddProfile(skt_pl2+",Casing.Side.P")
extrudePram4.DirectionType=2
extrudePram4.DirectionParameter1="50000"
extrudePram4.DirectionParameter2="10000"
extrudePram4.SweepDirection="+Z"
extrudePram4.Name="HK.Casing.Wall.SideP"
extrudePram4.MaterialName="SS400"
extrudePram4.IntervalSweep=False
extrude_sheet4 = part.CreateLinearSweepSheet(extrudePram4,False)
part.SheetAlignNormal(extrude_sheet4,0,-1,0)
part.BlankElement(extrude_sheet4,True)
part.SetElementColor(extrude_sheet4,"225","225","225","1")
ProfilePram2 = part.CreateProfileParam()
ProfilePram2.DefinitionType=1
ProfilePram2.BasePlane="PL,O,"+var_elm2+","+"PL,X"
ProfilePram2.AddAttachSurfaces(extrude_sheet4)
ProfilePram2.ProfileName="HK.Casing.Wall.Side.FR14.ABP"
ProfilePram2.MaterialName="SS400"
ProfilePram2.ProfileType=1002
ProfilePram2.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram2.Mold="+"
ProfilePram2.ReverseDir=False
ProfilePram2.ReverseAngle=True
ProfilePram2.CalcSnipOnlyAttachLines=False
ProfilePram2.AttachDirMethod=0
ProfilePram2.CCWDefAngle=False
ProfilePram2.AddEnd1Elements(extrude_sheet1)
ProfilePram2.End1Type=1102
ProfilePram2.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram2.AddEnd2Elements(extrude_sheet2)
ProfilePram2.End2Type=1102
ProfilePram2.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram2.End1ScallopType=1121
ProfilePram2.End1ScallopTypeParams=["35","40"]
ProfilePram2.End2ScallopType=1121
ProfilePram2.End2ScallopTypeParams=["35","40"]
profile2 = part.CreateProfile(ProfilePram2,False)
part.SetElementColor(profile2[0],"255","0","0","0.19999998807907104")
var_elm3 = part.CreateVariable("Casing.DL05","4000","mm","")
ProfilePram3 = part.CreateProfileParam()
ProfilePram3.DefinitionType=1
ProfilePram3.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram3.AddAttachSurfaces(extrude_sheet3)
ProfilePram3.ProfileName="HK.Casing.Wall.Aft.DL05.ABP"
ProfilePram3.MaterialName="SS400"
ProfilePram3.ProfileType=1002
ProfilePram3.ProfileParams=["125","75","7","10","5"]
ProfilePram3.Mold="+"
ProfilePram3.ReverseDir=False
ProfilePram3.ReverseAngle=True
ProfilePram3.CalcSnipOnlyAttachLines=False
ProfilePram3.AttachDirMethod=0
ProfilePram3.CCWDefAngle=False
ProfilePram3.AddEnd1Elements(extrude_sheet1)
ProfilePram3.End1Type=1102
ProfilePram3.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram3.AddEnd2Elements(extrude_sheet2)
ProfilePram3.End2Type=1102
ProfilePram3.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram3.End1ScallopType=1121
ProfilePram3.End1ScallopTypeParams=["25","40"]
ProfilePram3.End2ScallopType=1121
ProfilePram3.End2ScallopTypeParams=["25","40"]
profile3 = part.CreateProfile(ProfilePram3,False)
part.SetElementColor(profile3[0],"255","0","0","0.19999998807907104")
extrudePram5 = part.CreateLinearSweepParam()
extrudePram5.AddProfile(skt_pl2+",Casing.Fore")
extrudePram5.DirectionType=2
extrudePram5.DirectionParameter1="50000"
extrudePram5.DirectionParameter2="10000"
extrudePram5.SweepDirection="+Z"
extrudePram5.Name="HK.Casing.Wall.Fore"
extrudePram5.MaterialName="SS400"
extrudePram5.IntervalSweep=False
extrude_sheet5 = part.CreateLinearSweepSheet(extrudePram5,False)
part.SheetAlignNormal(extrude_sheet5,1,0,0)
part.BlankElement(extrude_sheet5,True)
part.SetElementColor(extrude_sheet5,"225","225","225","1")
ProfilePram4 = part.CreateProfileParam()
ProfilePram4.DefinitionType=1
ProfilePram4.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram4.AddAttachSurfaces(extrude_sheet5)
ProfilePram4.ProfileName="HK.Casing.Wall.Fore.DL05.ABP"
ProfilePram4.MaterialName="SS400"
ProfilePram4.ProfileType=1002
ProfilePram4.ProfileParams=["125","75","7","10","5"]
ProfilePram4.Mold="+"
ProfilePram4.ReverseDir=True
ProfilePram4.ReverseAngle=True
ProfilePram4.CalcSnipOnlyAttachLines=False
ProfilePram4.AttachDirMethod=0
ProfilePram4.CCWDefAngle=False
ProfilePram4.AddEnd1Elements(extrude_sheet1)
ProfilePram4.End1Type=1102
ProfilePram4.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram4.AddEnd2Elements(extrude_sheet2)
ProfilePram4.End2Type=1102
ProfilePram4.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram4.End1ScallopType=1121
ProfilePram4.End1ScallopTypeParams=["25","40"]
ProfilePram4.End2ScallopType=1121
ProfilePram4.End2ScallopTypeParams=["25","40"]
profile4 = part.CreateProfile(ProfilePram4,False)
part.SetElementColor(profile4[0],"255","0","0","0.19999998807907104")
ProfilePram5 = part.CreateProfileParam()
ProfilePram5.DefinitionType=1
ProfilePram5.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram5.AddAttachSurfaces(extrude_sheet1)
ProfilePram5.ProfileName="HK.Casing.Deck.B.DL05P"
ProfilePram5.MaterialName="SS400"
ProfilePram5.ProfileType=1002
ProfilePram5.ProfileParams=["125","75","7","10","5"]
ProfilePram5.Mold="+"
ProfilePram5.ReverseDir=True
ProfilePram5.ReverseAngle=True
ProfilePram5.CalcSnipOnlyAttachLines=False
ProfilePram5.AttachDirMethod=0
ProfilePram5.CCWDefAngle=False
ProfilePram5.AddEnd1Elements(profile3[0])
ProfilePram5.End1Type=1102
ProfilePram5.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram5.AddEnd2Elements(profile4[0])
ProfilePram5.End2Type=1102
ProfilePram5.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram5.End1ScallopType=1120
ProfilePram5.End1ScallopTypeParams=["50"]
ProfilePram5.End2ScallopType=1120
ProfilePram5.End2ScallopTypeParams=["50"]
profile5 = part.CreateProfile(ProfilePram5,False)
part.SetElementColor(profile5[0],"255","0","0","0.19999998807907104")
skt_pl3 = part.CreateSketchPlane("HK.Az.Deck.B","","PL,Z","0",False,False,"","","",True,False)
part.BlankElement(skt_pl3,True)
skt_layer11 = part.CreateSketchLayer("Edge00",skt_pl3)
skt_ln19 = part.CreateSketchLine(skt_pl3,"","Edge00","11405.000000000002,4835","3984.9999999999995,4835",False)
skt_ln20 = part.CreateSketchLine(skt_pl3,"","Edge00","11405.000000000002,-4835","11405.000000000002,4835",False)
skt_ln21 = part.CreateSketchLine(skt_pl3,"","Edge00","3984.9999999999995,-4835","11405.000000000002,-4835",False)
skt_ln22 = part.CreateSketchLine(skt_pl3,"","Edge00","3984.9999999999995,4835","3984.9999999999995,-4835",False)
skt_layer12 = part.CreateSketchLayer("Edge01",skt_pl3)
skt_ln23 = part.CreateSketchLine(skt_pl3,"","Edge01","9770,3125","4835.0000000000009,3125",False)
skt_ln24 = part.CreateSketchLine(skt_pl3,"","Edge01","10170,-2725","10170,2725",False)
skt_ln25 = part.CreateSketchLine(skt_pl3,"","Edge01","4835.0000000000009,-3125","9770,-3125",False)
skt_ln26 = part.CreateSketchLine(skt_pl3,"","Edge01","4435.0000000000009,2725","4435.0000000000009,-2724.9999999999991",False)
skt_arc1 = part.CreateSketchArc(skt_pl3,"","Edge01","4835.0000000000009,2724.9999999999995","4835.0000000000009,3124.9999999999995","4435.0000000000009,2725",True,False)
skt_arc2 = part.CreateSketchArc(skt_pl3,"","Edge01","9770,2724.9999999999995","10170,2725","9770,3124.9999999999995",True,False)
skt_arc3 = part.CreateSketchArc(skt_pl3,"","Edge01","9770,-2724.9999999999995","9770,-3124.9999999999995","10170,-2725",True,False)
skt_arc4 = part.CreateSketchArc(skt_pl3,"","Edge01","4835.0000000000009,-2725","4435.0000000000009,-2724.9999999999995","4835.0000000000009,-3125",True,False)
solid1 = part.CreateSolid("HK.Casing.Deck.B","","SS400")
part.SetElementColor(solid1,"139","69","19","0.78999996185302734")
thicken1 = part.CreateThicken("厚み付け5",solid1,"+",[extrude_sheet1],"+","10","0","0",False,False)
extrudePram6 = part.CreateLinearSweepParam()
extrudePram6.Name="積-押し出し5"
extrudePram6.AddProfile(skt_pl3+",Edge00")
extrudePram6.DirectionType="N"
extrudePram6.DirectionParameter1="50000"
extrudePram6.SweepDirection="+Z"
extrudePram6.RefByGeometricMethod=True
extrude1 = part.CreateLinearSweep(solid1,"*",extrudePram6,False)
extrudePram7 = part.CreateLinearSweepParam()
extrudePram7.Name="削除-押し出し3"
extrudePram7.AddProfile(skt_pl3+",Edge01")
extrudePram7.DirectionType="T"
extrudePram7.RefByGeometricMethod=True
extrude2 = part.CreateLinearSweep(solid1,"-",extrudePram7,False)
bracketPram1 = part.CreateBracketParam()
bracketPram1.DefinitionType=1
bracketPram1.BracketName="HK.Casing.Wall.Side.FR14.Deck.BP"
bracketPram1.MaterialName="SS400"
bracketPram1.BaseElement=profile2[0]
bracketPram1.UseSideSheetForPlane=False
bracketPram1.Mold="+"
bracketPram1.Thickness="9.9999999999999982"
bracketPram1.BracketType=1505
bracketPram1.BracketParams=["200"]
bracketPram1.Scallop1Type=1801
bracketPram1.Scallop1Params=["0"]
bracketPram1.Scallop2Type=0
bracketPram1.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram1.RevSf1=False
bracketPram1.Surfaces2=[profile2[0]+",FL"]
bracketPram1.RevSf2=False
bracketPram1.RevSf3=False
bracketPram1.Sf1DimensionType=1541
bracketPram1.Sf1DimensonParams=["0","100"]
bracketPram1.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram1.Sf2DimensionType=1531
bracketPram1.Sf2DimensonParams=["200","15"]
bracket1 = part.CreateBracket(bracketPram1,False)
part.SetElementColor(bracket1,"0","255","255","0.19999998807907104")
var_elm4 = part.CreateVariable("Casing.DL01","800","mm","")
extrudePram8 = part.CreateLinearSweepParam()
extrudePram8.AddProfile(skt_pl1+",Casing.Deck.C")
extrudePram8.DirectionType=2
extrudePram8.DirectionParameter1="50000"
extrudePram8.DirectionParameter2="10000"
extrudePram8.SweepDirection="+X"
extrudePram8.Name="HK.Casing.Deck.C"
extrudePram8.MaterialName="SS400"
extrudePram8.IntervalSweep=False
extrude_sheet6 = part.CreateLinearSweepSheet(extrudePram8,False)
part.SheetAlignNormal(extrude_sheet6,-0,0,1)
part.BlankElement(extrude_sheet6,True)
part.SetElementColor(extrude_sheet6,"225","225","225","1")
ProfilePram6 = part.CreateProfileParam()
ProfilePram6.DefinitionType=1
ProfilePram6.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram6.AddAttachSurfaces(extrude_sheet5)
ProfilePram6.ProfileName="HK.Casing.Wall.Fore.DL01.BCP"
ProfilePram6.MaterialName="SS400"
ProfilePram6.ProfileType=1002
ProfilePram6.ProfileParams=["125","75","7","10","5"]
ProfilePram6.Mold="+"
ProfilePram6.ReverseDir=True
ProfilePram6.ReverseAngle=True
ProfilePram6.CalcSnipOnlyAttachLines=False
ProfilePram6.AttachDirMethod=0
ProfilePram6.CCWDefAngle=False
ProfilePram6.AddEnd1Elements(extrude_sheet6)
ProfilePram6.End1Type=1102
ProfilePram6.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram6.AddEnd2Elements(extrude_sheet1)
ProfilePram6.End2Type=1102
ProfilePram6.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram6.End1ScallopType=1121
ProfilePram6.End1ScallopTypeParams=["25","40"]
ProfilePram6.End2ScallopType=1121
ProfilePram6.End2ScallopTypeParams=["25","40"]
profile6 = part.CreateProfile(ProfilePram6,False)
part.SetElementColor(profile6[0],"255","0","0","0.19999998807907104")
ProfilePram7 = part.CreateProfileParam()
ProfilePram7.DefinitionType=1
ProfilePram7.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram7.AddAttachSurfaces(extrude_sheet3)
ProfilePram7.ProfileName="HK.Casing.Wall.Aft.DL04.BCP"
ProfilePram7.MaterialName="SS400"
ProfilePram7.ProfileType=1003
ProfilePram7.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram7.Mold="+"
ProfilePram7.ReverseDir=False
ProfilePram7.ReverseAngle=True
ProfilePram7.CalcSnipOnlyAttachLines=False
ProfilePram7.AttachDirMethod=0
ProfilePram7.CCWDefAngle=False
ProfilePram7.AddEnd1Elements(extrude_sheet6)
ProfilePram7.End1Type=1102
ProfilePram7.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram7.AddEnd2Elements(extrude_sheet1)
ProfilePram7.End2Type=1102
ProfilePram7.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram7.End1ScallopType=1120
ProfilePram7.End1ScallopTypeParams=["50"]
ProfilePram7.End2ScallopType=1120
ProfilePram7.End2ScallopTypeParams=["50"]
profile7 = part.CreateProfile(ProfilePram7,False)
part.SetElementColor(profile7[0],"148","0","211","0.39999997615814209")
ProfilePram8 = part.CreateProfileParam()
ProfilePram8.DefinitionType=1
ProfilePram8.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram8.AddAttachSurfaces(extrude_sheet5)
ProfilePram8.ProfileName="HK.Casing.Wall.Fore.DL04.BCP"
ProfilePram8.MaterialName="SS400"
ProfilePram8.ProfileType=1003
ProfilePram8.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram8.Mold="+"
ProfilePram8.ReverseDir=True
ProfilePram8.ReverseAngle=True
ProfilePram8.CalcSnipOnlyAttachLines=False
ProfilePram8.AttachDirMethod=0
ProfilePram8.CCWDefAngle=False
ProfilePram8.AddEnd1Elements(extrude_sheet6)
ProfilePram8.End1Type=1102
ProfilePram8.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram8.AddEnd2Elements(extrude_sheet1)
ProfilePram8.End2Type=1102
ProfilePram8.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram8.End1ScallopType=1120
ProfilePram8.End1ScallopTypeParams=["50"]
ProfilePram8.End2ScallopType=1120
ProfilePram8.End2ScallopTypeParams=["50"]
profile8 = part.CreateProfile(ProfilePram8,False)
part.SetElementColor(profile8[0],"148","0","211","0.39999997615814209")
ProfilePram9 = part.CreateProfileParam()
ProfilePram9.DefinitionType=1
ProfilePram9.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram9.AddAttachSurfaces(extrude_sheet6)
ProfilePram9.ProfileName="HK.Casing.Deck.C.DL04P"
ProfilePram9.MaterialName="SS400"
ProfilePram9.ProfileType=1003
ProfilePram9.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram9.Mold="-"
ProfilePram9.ReverseDir=True
ProfilePram9.ReverseAngle=False
ProfilePram9.CalcSnipOnlyAttachLines=False
ProfilePram9.AttachDirMethod=0
ProfilePram9.CCWDefAngle=False
ProfilePram9.AddEnd1Elements(profile7[0])
ProfilePram9.End1Type=1102
ProfilePram9.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram9.AddEnd2Elements(profile8[0])
ProfilePram9.End2Type=1102
ProfilePram9.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram9.End1ScallopType=0
ProfilePram9.End2ScallopType=0
profile9 = part.CreateProfile(ProfilePram9,False)
part.SetElementColor(profile9[0],"148","0","211","0.39999997615814209")
mirror_copied1 = part.MirrorCopy([profile9[0]],"PL,Y","")
part.SetElementColor(mirror_copied1[0],"148","0","211","0.39999997615814209")
ProfilePram10 = part.CreateProfileParam()
ProfilePram10.DefinitionType=1
ProfilePram10.BasePlane="PL,O,"+"FR14 + 415 mm"+","+"PL,X"
ProfilePram10.AddAttachSurfaces(extrude_sheet6)
ProfilePram10.ProfileName="HK.Casing.Deck.C.FR14F415"
ProfilePram10.MaterialName="SS400"
ProfilePram10.ProfileType=1003
ProfilePram10.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram10.Mold="+"
ProfilePram10.ReverseDir=True
ProfilePram10.ReverseAngle=True
ProfilePram10.CalcSnipOnlyAttachLines=False
ProfilePram10.AttachDirMethod=0
ProfilePram10.CCWDefAngle=False
ProfilePram10.AddEnd1Elements(mirror_copied1[0])
ProfilePram10.End1Type=1111
ProfilePram10.End1TypeParams=["0","35","50","50","25","29.999999999999996","0"]
ProfilePram10.AddEnd2Elements(profile9[0])
ProfilePram10.End2Type=1111
ProfilePram10.End2TypeParams=["0","35","50","50","25","29.999999999999996","0"]
ProfilePram10.End1ScallopType=1120
ProfilePram10.End1ScallopTypeParams=["50"]
ProfilePram10.End2ScallopType=1120
ProfilePram10.End2ScallopTypeParams=["50"]
profile10 = part.CreateProfile(ProfilePram10,False)
part.SetElementColor(profile10[0],"255","0","0","0.19999998807907104")
ProfilePram11 = part.CreateProfileParam()
ProfilePram11.DefinitionType=1
ProfilePram11.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram11.AddAttachSurfaces(extrude_sheet6)
ProfilePram11.ProfileName="HK.Casing.Deck.C.DL01.FP"
ProfilePram11.MaterialName="SS400"
ProfilePram11.ProfileType=1002
ProfilePram11.ProfileParams=["125","75","7","10","5"]
ProfilePram11.Mold="+"
ProfilePram11.ReverseDir=True
ProfilePram11.ReverseAngle=True
ProfilePram11.CalcSnipOnlyAttachLines=False
ProfilePram11.AttachDirMethod=0
ProfilePram11.CCWDefAngle=False
ProfilePram11.AddEnd1Elements(profile10[0])
ProfilePram11.End1Type=1102
ProfilePram11.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram11.AddEnd2Elements(profile6[0])
ProfilePram11.End2Type=1102
ProfilePram11.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram11.End1ScallopType=1121
ProfilePram11.End1ScallopTypeParams=["25","40"]
ProfilePram11.End2ScallopType=1121
ProfilePram11.End2ScallopTypeParams=["25","40"]
profile11 = part.CreateProfile(ProfilePram11,False)
part.SetElementColor(profile11[0],"255","0","0","0.19999998807907104")
bracketPram2 = part.CreateBracketParam()
bracketPram2.DefinitionType=1
bracketPram2.BracketName="HK.Casing.Wall.Fore.DL02.Deck.CP"
bracketPram2.MaterialName="SS400"
bracketPram2.BaseElement=profile6[0]
bracketPram2.UseSideSheetForPlane=False
bracketPram2.Mold="+"
bracketPram2.Thickness="7.9999999999999964"
bracketPram2.BracketType=1501
bracketPram2.Scallop1Type=1801
bracketPram2.Scallop1Params=["0"]
bracketPram2.Scallop2Type=0
bracketPram2.Surfaces1=[profile6[0]+",FL"]
bracketPram2.RevSf1=False
bracketPram2.Surfaces2=[profile11[0]+",FL"]
bracketPram2.RevSf2=False
bracketPram2.RevSf3=False
bracketPram2.Sf1DimensionType=1531
bracketPram2.Sf1DimensonParams=["200","15"]
bracketPram2.Sf2DimensionType=1531
bracketPram2.Sf2DimensonParams=["200","15"]
bracket2 = part.CreateBracket(bracketPram2,False)
part.SetElementColor(bracket2,"0","255","255","0.19999998807907104")
var_elm5 = part.CreateVariable("FR6","4019.9999999999995","mm","")
ProfilePram12 = part.CreateProfileParam()
ProfilePram12.DefinitionType=1
ProfilePram12.BasePlane="PL,O,"+"FR6 + 400 mm"+","+"PL,X"
ProfilePram12.AddAttachSurfaces(extrude_sheet6)
ProfilePram12.ProfileName="HK.Casing.Deck.C.FR06F400"
ProfilePram12.MaterialName="SS400"
ProfilePram12.ProfileType=1007
ProfilePram12.ProfileParams=["150","12"]
ProfilePram12.Mold="+"
ProfilePram12.ReverseDir=True
ProfilePram12.ReverseAngle=False
ProfilePram12.CalcSnipOnlyAttachLines=False
ProfilePram12.AttachDirMethod=0
ProfilePram12.CCWDefAngle=False
ProfilePram12.AddEnd1Elements(mirror_copied1[0])
ProfilePram12.End1Type=1102
ProfilePram12.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram12.AddEnd2Elements(profile9[0])
ProfilePram12.End2Type=1102
ProfilePram12.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram12.End1ScallopType=-1
ProfilePram12.End2ScallopType=-1
profile12 = part.CreateProfile(ProfilePram12,False)
part.SetElementColor(profile12[0],"255","0","0","0.19999998807907104")
var_elm6 = part.CreateVariable("Casing.DL00","0","mm","")
ProfilePram13 = part.CreateProfileParam()
ProfilePram13.DefinitionType=1
ProfilePram13.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram13.AddAttachSurfaces(extrude_sheet3)
ProfilePram13.ProfileName="HK.Casing.Wall.Aft.DL00.BC"
ProfilePram13.MaterialName="SS400"
ProfilePram13.ProfileType=1002
ProfilePram13.ProfileParams=["125","75","7","10","5"]
ProfilePram13.ReverseDir=False
ProfilePram13.ReverseAngle=True
ProfilePram13.CalcSnipOnlyAttachLines=False
ProfilePram13.AttachDirMethod=0
ProfilePram13.CCWDefAngle=False
ProfilePram13.AddEnd1Elements(extrude_sheet6)
ProfilePram13.End1Type=1102
ProfilePram13.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram13.AddEnd2Elements(extrude_sheet1)
ProfilePram13.End2Type=1102
ProfilePram13.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram13.End1ScallopType=1121
ProfilePram13.End1ScallopTypeParams=["25","40"]
ProfilePram13.End2ScallopType=1121
ProfilePram13.End2ScallopTypeParams=["25","40"]
profile13 = part.CreateProfile(ProfilePram13,False)
part.SetElementColor(profile13[0],"255","0","0","0.19999998807907104")
extrudePram9 = part.CreateLinearSweepParam()
extrudePram9.AddProfile(skt_pl1+",Casing.Deck.D")
extrudePram9.DirectionType=2
extrudePram9.DirectionParameter1="50000"
extrudePram9.DirectionParameter2="10000"
extrudePram9.SweepDirection="+X"
extrudePram9.Name="HK.Casing.Deck.D"
extrudePram9.MaterialName="SS400"
extrudePram9.IntervalSweep=False
extrude_sheet7 = part.CreateLinearSweepSheet(extrudePram9,False)
part.SheetAlignNormal(extrude_sheet7,-0,0,1)
part.BlankElement(extrude_sheet7,True)
part.SetElementColor(extrude_sheet7,"225","225","225","1")
var_elm7 = part.CreateVariable("FR12","8170","mm","")
ProfilePram14 = part.CreateProfileParam()
ProfilePram14.DefinitionType=1
ProfilePram14.BasePlane="PL,O,"+var_elm7+","+"PL,X"
ProfilePram14.AddAttachSurfaces(extrude_sheet4)
ProfilePram14.ProfileName="HK.Casing.Wall.Side.FR12.CDP"
ProfilePram14.MaterialName="SS400"
ProfilePram14.ProfileType=1002
ProfilePram14.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram14.Mold="+"
ProfilePram14.ReverseDir=False
ProfilePram14.ReverseAngle=True
ProfilePram14.CalcSnipOnlyAttachLines=False
ProfilePram14.AttachDirMethod=0
ProfilePram14.CCWDefAngle=False
ProfilePram14.AddEnd1Elements(extrude_sheet7)
ProfilePram14.End1Type=1102
ProfilePram14.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram14.AddEnd2Elements(extrude_sheet6)
ProfilePram14.End2Type=1102
ProfilePram14.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram14.End1ScallopType=1121
ProfilePram14.End1ScallopTypeParams=["35","40"]
ProfilePram14.End2ScallopType=1121
ProfilePram14.End2ScallopTypeParams=["35","40"]
profile14 = part.CreateProfile(ProfilePram14,False)
part.SetElementColor(profile14[0],"255","0","0","0.19999998807907104")
ProfilePram15 = part.CreateProfileParam()
ProfilePram15.DefinitionType=1
ProfilePram15.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram15.AddAttachSurfaces(extrude_sheet7)
ProfilePram15.ProfileName="HK.Casing.Deck.D.DL05P"
ProfilePram15.MaterialName="SS400"
ProfilePram15.ProfileType=1002
ProfilePram15.ProfileParams=["125","75","7","10","5"]
ProfilePram15.Mold="+"
ProfilePram15.ReverseDir=True
ProfilePram15.ReverseAngle=True
ProfilePram15.CalcSnipOnlyAttachLines=False
ProfilePram15.AttachDirMethod=0
ProfilePram15.CCWDefAngle=False
ProfilePram15.AddEnd1Elements(extrude_sheet3)
ProfilePram15.End1Type=1102
ProfilePram15.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram15.AddEnd2Elements(extrude_sheet5)
ProfilePram15.End2Type=1102
ProfilePram15.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram15.End1ScallopType=1120
ProfilePram15.End1ScallopTypeParams=["50"]
ProfilePram15.End2ScallopType=1120
ProfilePram15.End2ScallopTypeParams=["50"]
profile15 = part.CreateProfile(ProfilePram15,False)
part.SetElementColor(profile15[0],"255","0","0","0.19999998807907104")
skt_pl4 = part.CreateSketchPlane("HK.Az.Deck.D","","PL,Z","0",False,False,"","","",True,False)
part.BlankElement(skt_pl4,True)
skt_layer13 = part.CreateSketchLayer("Edge00",skt_pl4)
skt_ln27 = part.CreateSketchLine(skt_pl4,"","Edge00","11405.000000000002,4835","3984.9999999999995,4835",False)
skt_ln28 = part.CreateSketchLine(skt_pl4,"","Edge00","11405.000000000002,-4835","11405.000000000002,4835",False)
skt_ln29 = part.CreateSketchLine(skt_pl4,"","Edge00","3984.9999999999995,-4835","11405.000000000002,-4835",False)
skt_ln30 = part.CreateSketchLine(skt_pl4,"","Edge00","3984.9999999999995,4835","3984.9999999999995,-4835",False)
skt_layer14 = part.CreateSketchLayer("Edge01",skt_pl4)
skt_arc5 = part.CreateSketchArc(skt_pl4,"","Edge01","6345.0000000000009,1195.0000000000002","6345,1495.0000000000002","6045.0000000000009,1195",True,False)
skt_ln31 = part.CreateSketchLine(skt_pl4,"","Edge01","8580,1495","6345,1495",False)
skt_arc6 = part.CreateSketchArc(skt_pl4,"","Edge01","8580,1195","8880,1195.0000000000002","8580,1495",True,False)
skt_ln32 = part.CreateSketchLine(skt_pl4,"","Edge01","8880,-1195","8880,1195.0000000000005",False)
skt_arc7 = part.CreateSketchArc(skt_pl4,"","Edge01","8580,-1195.0000000000002","8580,-1495.0000000000002","8880,-1195",True,False)
skt_ln33 = part.CreateSketchLine(skt_pl4,"","Edge01","6345,-1495","8580,-1495",False)
skt_arc8 = part.CreateSketchArc(skt_pl4,"","Edge01","6345.0000000000009,-1195","6045.0000000000009,-1195.0000000000002","6345,-1495",True,False)
skt_ln34 = part.CreateSketchLine(skt_pl4,"","Edge01","6045,1195","6045,-1195.0000000000005",False)
solid2 = part.CreateSolid("HK.Casing.Deck.D","","SS400")
part.SetElementColor(solid2,"139","69","19","0.78999996185302734")
thicken2 = part.CreateThicken("厚み付け3",solid2,"+",[extrude_sheet7],"+","10","0","0",False,False)
extrudePram10 = part.CreateLinearSweepParam()
extrudePram10.Name="積-押し出し3"
extrudePram10.AddProfile(skt_pl4+",Edge00")
extrudePram10.DirectionType="N"
extrudePram10.DirectionParameter1="50000"
extrudePram10.SweepDirection="+Z"
extrudePram10.RefByGeometricMethod=True
extrude3 = part.CreateLinearSweep(solid2,"*",extrudePram10,False)
extrudePram11 = part.CreateLinearSweepParam()
extrudePram11.Name="削除-押し出し1"
extrudePram11.AddProfile(skt_pl4+",Edge01")
extrudePram11.DirectionType="T"
extrudePram11.RefByGeometricMethod=True
extrude4 = part.CreateLinearSweep(solid2,"-",extrudePram11,False)
extrudePram12 = part.CreateLinearSweepParam()
extrudePram12.AddProfile(skt_pl1+",General.Deck.UpperDeck")
extrudePram12.DirectionType=2
extrudePram12.DirectionParameter1="190000"
extrudePram12.DirectionParameter2="10000"
extrudePram12.SweepDirection="+X"
extrudePram12.Name="HK.General.Deck.UpperDeck"
extrudePram12.MaterialName="SS400"
extrudePram12.IntervalSweep=False
extrude_sheet8 = part.CreateLinearSweepSheet(extrudePram12,False)
part.SheetAlignNormal(extrude_sheet8,0,0,-1)
part.BlankElement(extrude_sheet8,True)
part.SetElementColor(extrude_sheet8,"225","225","225","1")
var_elm8 = part.CreateVariable("Casing.DL02","1600","mm","")
ProfilePram16 = part.CreateProfileParam()
ProfilePram16.DefinitionType=1
ProfilePram16.BasePlane="PL,O,"+var_elm8+","+"PL,Y"
ProfilePram16.AddAttachSurfaces(extrude_sheet7)
ProfilePram16.ProfileName="HK.Casing.Deck.D.DL02P"
ProfilePram16.MaterialName="SS400"
ProfilePram16.FlangeName="HK.Casing.Deck.D.DL02P"
ProfilePram16.FlangeMaterialName="SS400"
ProfilePram16.ProfileType=1201
ProfilePram16.ProfileParams=["200","14","900","10"]
ProfilePram16.Mold="-"
ProfilePram16.ReverseDir=True
ProfilePram16.ReverseAngle=False
ProfilePram16.CalcSnipOnlyAttachLines=False
ProfilePram16.AttachDirMethod=0
ProfilePram16.CCWDefAngle=False
ProfilePram16.AddEnd1Elements(extrude_sheet3)
ProfilePram16.End1Type=1102
ProfilePram16.End1TypeParams=["25","14.999999999999998","0","0"]
ProfilePram16.AddEnd2Elements(extrude_sheet5)
ProfilePram16.End2Type=1102
ProfilePram16.End2TypeParams=["25","14.999999999999998","0","0"]
ProfilePram16.End1ScallopType=1120
ProfilePram16.End1ScallopTypeParams=["50"]
ProfilePram16.End2ScallopType=1120
ProfilePram16.End2ScallopTypeParams=["50"]
profile16 = part.CreateProfile(ProfilePram16,False)
part.SetElementColor(profile16[0],"148","0","211","0.39999997615814209")
part.SetElementColor(profile16[1],"148","0","211","0.39999997615814209")
mirror_copied2 = part.MirrorCopy([profile16[0]],"PL,Y","")
part.SetElementColor(mirror_copied2[0],"148","0","211","0.39999997615814209")
var_elm9 = part.CreateVariable("FR9","6030","mm","")
ProfilePram17 = part.CreateProfileParam()
ProfilePram17.DefinitionType=1
ProfilePram17.BasePlane="PL,O,"+var_elm9+","+"PL,X"
ProfilePram17.AddAttachSurfaces(extrude_sheet7)
ProfilePram17.ProfileName="HK.Casing.Deck.D.FR09C"
ProfilePram17.MaterialName="SS400"
ProfilePram17.ProfileType=1003
ProfilePram17.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram17.Mold="+"
ProfilePram17.ReverseDir=True
ProfilePram17.ReverseAngle=False
ProfilePram17.CalcSnipOnlyAttachLines=False
ProfilePram17.AttachDirMethod=0
ProfilePram17.CCWDefAngle=False
ProfilePram17.AddEnd1Elements(mirror_copied2[0])
ProfilePram17.End1Type=1102
ProfilePram17.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram17.AddEnd2Elements(profile16[0])
ProfilePram17.End2Type=1102
ProfilePram17.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram17.End1ScallopType=1120
ProfilePram17.End1ScallopTypeParams=["50"]
ProfilePram17.End2ScallopType=1120
ProfilePram17.End2ScallopTypeParams=["50"]
profile17 = part.CreateProfile(ProfilePram17,False)
part.SetElementColor(profile17[0],"148","0","211","0.39999997615814209")
var_elm10 = part.CreateVariable("Casing.DL03","2400","mm","")
ProfilePram18 = part.CreateProfileParam()
ProfilePram18.DefinitionType=1
ProfilePram18.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram18.AddAttachSurfaces(extrude_sheet3)
ProfilePram18.ProfileName="HK.Casing.Wall.Aft.DL03.ABP"
ProfilePram18.MaterialName="SS400"
ProfilePram18.ProfileType=1002
ProfilePram18.ProfileParams=["125","75","7","10","5"]
ProfilePram18.Mold="+"
ProfilePram18.ReverseDir=False
ProfilePram18.ReverseAngle=True
ProfilePram18.CalcSnipOnlyAttachLines=False
ProfilePram18.AttachDirMethod=0
ProfilePram18.CCWDefAngle=False
ProfilePram18.AddEnd1Elements(extrude_sheet1)
ProfilePram18.End1Type=1102
ProfilePram18.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram18.AddEnd2Elements(extrude_sheet2)
ProfilePram18.End2Type=1102
ProfilePram18.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram18.End1ScallopType=1121
ProfilePram18.End1ScallopTypeParams=["25","40"]
ProfilePram18.End2ScallopType=1121
ProfilePram18.End2ScallopTypeParams=["25","40"]
profile18 = part.CreateProfile(ProfilePram18,False)
part.SetElementColor(profile18[0],"255","0","0","0.19999998807907104")
var_elm11 = part.CreateVariable("FR11","7370","mm","")
ProfilePram19 = part.CreateProfileParam()
ProfilePram19.DefinitionType=1
ProfilePram19.BasePlane="PL,O,"+var_elm11+","+"PL,X"
ProfilePram19.AddAttachSurfaces(extrude_sheet4)
ProfilePram19.ProfileName="HK.Casing.Wall.Side.FR11.BCP"
ProfilePram19.MaterialName="SS400"
ProfilePram19.ProfileType=1002
ProfilePram19.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram19.Mold="+"
ProfilePram19.ReverseDir=False
ProfilePram19.ReverseAngle=True
ProfilePram19.CalcSnipOnlyAttachLines=False
ProfilePram19.AttachDirMethod=0
ProfilePram19.CCWDefAngle=False
ProfilePram19.AddEnd1Elements(extrude_sheet6)
ProfilePram19.End1Type=1102
ProfilePram19.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram19.AddEnd2Elements(extrude_sheet1)
ProfilePram19.End2Type=1102
ProfilePram19.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram19.End1ScallopType=1121
ProfilePram19.End1ScallopTypeParams=["35","40"]
ProfilePram19.End2ScallopType=1121
ProfilePram19.End2ScallopTypeParams=["35","40"]
profile19 = part.CreateProfile(ProfilePram19,False)
part.SetElementColor(profile19[0],"255","0","0","0.19999998807907104")
solid3 = part.CreateSolid("HK.Casing.Deck.C","","SS400")
part.SetElementColor(solid3,"139","69","19","0.78999996185302734")
thicken3 = part.CreateThicken("厚み付け4",solid3,"+",[extrude_sheet6],"+","10","0","0",False,False)
skt_pl5 = part.CreateSketchPlane("HK.Az.Deck.C","","PL,Z","0",False,False,"","","",True,False)
part.BlankElement(skt_pl5,True)
skt_layer15 = part.CreateSketchLayer("Edge00",skt_pl5)
skt_ln35 = part.CreateSketchLine(skt_pl5,"","Edge00","11405.000000000002,4835","3984.9999999999995,4835",False)
skt_ln36 = part.CreateSketchLine(skt_pl5,"","Edge00","11405.000000000002,-4835","11405.000000000002,4835",False)
skt_ln37 = part.CreateSketchLine(skt_pl5,"","Edge00","3984.9999999999995,-4835","11405.000000000002,-4835",False)
skt_ln38 = part.CreateSketchLine(skt_pl5,"","Edge00","3984.9999999999995,4835","3984.9999999999995,-4835",False)
skt_layer16 = part.CreateSketchLayer("Edge01",skt_pl5)
skt_ln39 = part.CreateSketchLine(skt_pl5,"","Edge01","9770,3125","4835.0000000000009,3125",False)
skt_ln40 = part.CreateSketchLine(skt_pl5,"","Edge01","10170,-2725","10170,2725",False)
skt_ln41 = part.CreateSketchLine(skt_pl5,"","Edge01","4835.0000000000009,-3125","9770,-3125",False)
skt_ln42 = part.CreateSketchLine(skt_pl5,"","Edge01","4435.0000000000009,2725","4435.0000000000009,-2724.9999999999991",False)
skt_arc9 = part.CreateSketchArc(skt_pl5,"","Edge01","4835.0000000000009,2724.9999999999995","4835.0000000000009,3124.9999999999995","4435.0000000000009,2725",True,False)
skt_arc10 = part.CreateSketchArc(skt_pl5,"","Edge01","9770,2724.9999999999995","10170,2725","9770,3124.9999999999995",True,False)
skt_arc11 = part.CreateSketchArc(skt_pl5,"","Edge01","9770,-2724.9999999999995","9770,-3124.9999999999995","10170,-2725",True,False)
skt_arc12 = part.CreateSketchArc(skt_pl5,"","Edge01","4835.0000000000009,-2725","4435.0000000000009,-2724.9999999999995","4835.0000000000009,-3125",True,False)
extrudePram13 = part.CreateLinearSweepParam()
extrudePram13.Name="積-押し出し4"
extrudePram13.AddProfile(skt_pl5+",Edge00")
extrudePram13.DirectionType="N"
extrudePram13.DirectionParameter1="50000"
extrudePram13.SweepDirection="+Z"
extrudePram13.RefByGeometricMethod=True
extrude5 = part.CreateLinearSweep(solid3,"*",extrudePram13,False)
extrudePram14 = part.CreateLinearSweepParam()
extrudePram14.Name="削除-押し出し2"
extrudePram14.AddProfile(skt_pl5+",Edge01")
extrudePram14.DirectionType="T"
extrudePram14.RefByGeometricMethod=True
extrude6 = part.CreateLinearSweep(solid3,"-",extrudePram14,False)
ProfilePram20 = part.CreateProfileParam()
ProfilePram20.DefinitionType=1
ProfilePram20.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram20.AddAttachSurfaces(extrude_sheet5)
ProfilePram20.ProfileName="HK.Casing.Wall.Fore.DL05.BCP"
ProfilePram20.MaterialName="SS400"
ProfilePram20.ProfileType=1002
ProfilePram20.ProfileParams=["125","75","7","10","5"]
ProfilePram20.Mold="+"
ProfilePram20.ReverseDir=True
ProfilePram20.ReverseAngle=True
ProfilePram20.CalcSnipOnlyAttachLines=False
ProfilePram20.AttachDirMethod=0
ProfilePram20.CCWDefAngle=False
ProfilePram20.AddEnd1Elements(extrude_sheet6)
ProfilePram20.End1Type=1102
ProfilePram20.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram20.AddEnd2Elements(extrude_sheet1)
ProfilePram20.End2Type=1102
ProfilePram20.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram20.End1ScallopType=1121
ProfilePram20.End1ScallopTypeParams=["25","40"]
ProfilePram20.End2ScallopType=1121
ProfilePram20.End2ScallopTypeParams=["25","40"]
profile20 = part.CreateProfile(ProfilePram20,False)
part.SetElementColor(profile20[0],"255","0","0","0.19999998807907104")
ProfilePram21 = part.CreateProfileParam()
ProfilePram21.DefinitionType=1
ProfilePram21.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram21.AddAttachSurfaces(extrude_sheet3)
ProfilePram21.ProfileName="HK.Casing.Wall.Aft.DL05.BCP"
ProfilePram21.MaterialName="SS400"
ProfilePram21.ProfileType=1002
ProfilePram21.ProfileParams=["125","75","7","10","5"]
ProfilePram21.Mold="+"
ProfilePram21.ReverseDir=False
ProfilePram21.ReverseAngle=True
ProfilePram21.CalcSnipOnlyAttachLines=False
ProfilePram21.AttachDirMethod=0
ProfilePram21.CCWDefAngle=False
ProfilePram21.AddEnd1Elements(extrude_sheet6)
ProfilePram21.End1Type=1102
ProfilePram21.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram21.AddEnd2Elements(extrude_sheet1)
ProfilePram21.End2Type=1102
ProfilePram21.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram21.End1ScallopType=1121
ProfilePram21.End1ScallopTypeParams=["25","40"]
ProfilePram21.End2ScallopType=1121
ProfilePram21.End2ScallopTypeParams=["25","40"]
profile21 = part.CreateProfile(ProfilePram21,False)
part.SetElementColor(profile21[0],"255","0","0","0.19999998807907104")
ProfilePram22 = part.CreateProfileParam()
ProfilePram22.DefinitionType=1
ProfilePram22.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram22.AddAttachSurfaces(extrude_sheet6)
ProfilePram22.ProfileName="HK.Casing.Deck.C.DL05P"
ProfilePram22.MaterialName="SS400"
ProfilePram22.ProfileType=1002
ProfilePram22.ProfileParams=["125","75","7","10","5"]
ProfilePram22.Mold="+"
ProfilePram22.ReverseDir=True
ProfilePram22.ReverseAngle=True
ProfilePram22.CalcSnipOnlyAttachLines=False
ProfilePram22.AttachDirMethod=0
ProfilePram22.CCWDefAngle=False
ProfilePram22.AddEnd1Elements(profile21[0])
ProfilePram22.End1Type=1102
ProfilePram22.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram22.AddEnd2Elements(profile20[0])
ProfilePram22.End2Type=1102
ProfilePram22.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram22.End1ScallopType=1120
ProfilePram22.End1ScallopTypeParams=["50"]
ProfilePram22.End2ScallopType=1120
ProfilePram22.End2ScallopTypeParams=["50"]
profile22 = part.CreateProfile(ProfilePram22,False)
part.SetElementColor(profile22[0],"255","0","0","0.19999998807907104")
bracketPram3 = part.CreateBracketParam()
bracketPram3.DefinitionType=1
bracketPram3.BracketName="HK.Casing.Wall.Side.FR11.Deck.CP"
bracketPram3.MaterialName="SS400"
bracketPram3.BaseElement=profile19[0]
bracketPram3.UseSideSheetForPlane=False
bracketPram3.Mold="+"
bracketPram3.Thickness="9.9999999999999982"
bracketPram3.BracketType=1505
bracketPram3.BracketParams=["200"]
bracketPram3.Scallop1Type=1801
bracketPram3.Scallop1Params=["0"]
bracketPram3.Scallop2Type=0
bracketPram3.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram3.RevSf1=False
bracketPram3.Surfaces2=[profile19[0]+",FL"]
bracketPram3.RevSf2=False
bracketPram3.RevSf3=False
bracketPram3.Sf1DimensionType=1541
bracketPram3.Sf1DimensonParams=["0","100"]
bracketPram3.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile22[0]]
bracketPram3.Sf2DimensionType=1531
bracketPram3.Sf2DimensonParams=["200","15"]
bracket3 = part.CreateBracket(bracketPram3,False)
part.SetElementColor(bracket3,"0","255","255","0.19999998807907104")
mirror_copied3 = part.MirrorCopy([bracket3],"PL,Y","")
part.SetElementColor(mirror_copied3[0],"0","255","255","0.19999998807907104")
bracketPram4 = part.CreateBracketParam()
bracketPram4.DefinitionType=1
bracketPram4.BracketName="HK.Casing.Wall.Fore.DL04.Deck.CP"
bracketPram4.MaterialName="SS400"
bracketPram4.BaseElement=profile9[0]
bracketPram4.UseSideSheetForPlane=False
bracketPram4.Mold="-"
bracketPram4.Thickness="7.9999999999999964"
bracketPram4.BracketType=1501
bracketPram4.Scallop1Type=1801
bracketPram4.Scallop1Params=["0"]
bracketPram4.Scallop2Type=0
bracketPram4.Surfaces1=[profile8[0]+",FL"]
bracketPram4.RevSf1=False
bracketPram4.Surfaces2=[profile9[0]+",FL"]
bracketPram4.RevSf2=False
bracketPram4.RevSf3=False
bracketPram4.Sf1DimensionType=1531
bracketPram4.Sf1DimensonParams=["250","15"]
bracketPram4.Sf2DimensionType=1531
bracketPram4.Sf2DimensonParams=["250","15"]
bracket4 = part.CreateBracket(bracketPram4,False)
part.SetElementColor(bracket4,"0","255","255","0.19999998807907104")
ProfilePram23 = part.CreateProfileParam()
ProfilePram23.DefinitionType=1
ProfilePram23.BasePlane="PL,O,"+var_elm8+","+"PL,Y"
ProfilePram23.AddAttachSurfaces(extrude_sheet3)
ProfilePram23.ProfileName="HK.Casing.Wall.Aft.DL02.OAP"
ProfilePram23.MaterialName="SS400"
ProfilePram23.FlangeName="HK.Casing.Wall.Aft.DL02.OAP"
ProfilePram23.FlangeMaterialName="SS400"
ProfilePram23.ProfileType=1201
ProfilePram23.ProfileParams=["150","12","388","10"]
ProfilePram23.Mold="-"
ProfilePram23.ReverseDir=False
ProfilePram23.ReverseAngle=False
ProfilePram23.CalcSnipOnlyAttachLines=False
ProfilePram23.AttachDirMethod=0
ProfilePram23.CCWDefAngle=False
ProfilePram23.AddEnd1Elements(extrude_sheet2)
ProfilePram23.End1Type=1103
ProfilePram23.End1TypeParams=["0"]
ProfilePram23.AddEnd2Elements(extrude_sheet8)
ProfilePram23.End2Type=1103
ProfilePram23.End2TypeParams=["0"]
ProfilePram23.End1ScallopType=1120
ProfilePram23.End1ScallopTypeParams=["50"]
ProfilePram23.End2ScallopType=1120
ProfilePram23.End2ScallopTypeParams=["50"]
profile23 = part.CreateProfile(ProfilePram23,False)
part.SetElementColor(profile23[0],"148","0","211","0.39999997615814209")
part.SetElementColor(profile23[1],"148","0","211","0.39999997615814209")
mirror_copied4 = part.MirrorCopy([profile23[0]],"PL,Y","")
part.SetElementColor(mirror_copied4[0],"148","0","211","0.39999997615814209")
var_elm12 = part.CreateVariable("FR8","5360","mm","")
ProfilePram24 = part.CreateProfileParam()
ProfilePram24.DefinitionType=1
ProfilePram24.BasePlane="PL,O,"+var_elm12+","+"PL,X"
ProfilePram24.AddAttachSurfaces(extrude_sheet4)
ProfilePram24.ProfileName="HK.Casing.Wall.Side.FR08.CDP"
ProfilePram24.MaterialName="SS400"
ProfilePram24.ProfileType=1002
ProfilePram24.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram24.Mold="+"
ProfilePram24.ReverseDir=False
ProfilePram24.ReverseAngle=True
ProfilePram24.CalcSnipOnlyAttachLines=False
ProfilePram24.AttachDirMethod=0
ProfilePram24.CCWDefAngle=False
ProfilePram24.AddEnd1Elements(extrude_sheet7)
ProfilePram24.End1Type=1102
ProfilePram24.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram24.AddEnd2Elements(extrude_sheet6)
ProfilePram24.End2Type=1102
ProfilePram24.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram24.End1ScallopType=1121
ProfilePram24.End1ScallopTypeParams=["35","40"]
ProfilePram24.End2ScallopType=1121
ProfilePram24.End2ScallopTypeParams=["35","40"]
profile24 = part.CreateProfile(ProfilePram24,False)
part.SetElementColor(profile24[0],"255","0","0","0.19999998807907104")
var_elm13 = part.CreateVariable("FR7","4690","mm","")
ProfilePram25 = part.CreateProfileParam()
ProfilePram25.DefinitionType=1
ProfilePram25.BasePlane="PL,O,"+var_elm13+","+"PL,X"
ProfilePram25.AddAttachSurfaces(extrude_sheet4)
ProfilePram25.ProfileName="HK.Casing.Wall.Side.FR07.CDP"
ProfilePram25.MaterialName="SS400"
ProfilePram25.ProfileType=1002
ProfilePram25.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram25.Mold="+"
ProfilePram25.ReverseDir=False
ProfilePram25.ReverseAngle=True
ProfilePram25.CalcSnipOnlyAttachLines=False
ProfilePram25.AttachDirMethod=0
ProfilePram25.CCWDefAngle=False
ProfilePram25.AddEnd1Elements(extrude_sheet7)
ProfilePram25.End1Type=1102
ProfilePram25.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram25.AddEnd2Elements(extrude_sheet6)
ProfilePram25.End2Type=1102
ProfilePram25.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram25.End1ScallopType=1121
ProfilePram25.End1ScallopTypeParams=["35","40"]
ProfilePram25.End2ScallopType=1121
ProfilePram25.End2ScallopTypeParams=["35","40"]
profile25 = part.CreateProfile(ProfilePram25,False)
part.SetElementColor(profile25[0],"255","0","0","0.19999998807907104")
var_elm14 = part.CreateVariable("FR15","10570","mm","")
ProfilePram26 = part.CreateProfileParam()
ProfilePram26.DefinitionType=1
ProfilePram26.BasePlane="PL,O,"+var_elm14+","+"PL,X"
ProfilePram26.AddAttachSurfaces(extrude_sheet4)
ProfilePram26.ProfileName="HK.Casing.Wall.Side.FR15.ABP"
ProfilePram26.MaterialName="SS400"
ProfilePram26.ProfileType=1002
ProfilePram26.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram26.Mold="+"
ProfilePram26.ReverseDir=False
ProfilePram26.ReverseAngle=True
ProfilePram26.CalcSnipOnlyAttachLines=False
ProfilePram26.AttachDirMethod=0
ProfilePram26.CCWDefAngle=False
ProfilePram26.AddEnd1Elements(extrude_sheet1)
ProfilePram26.End1Type=1102
ProfilePram26.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram26.AddEnd2Elements(extrude_sheet2)
ProfilePram26.End2Type=1102
ProfilePram26.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram26.End1ScallopType=1121
ProfilePram26.End1ScallopTypeParams=["35","40"]
ProfilePram26.End2ScallopType=1121
ProfilePram26.End2ScallopTypeParams=["35","40"]
profile26 = part.CreateProfile(ProfilePram26,False)
part.SetElementColor(profile26[0],"255","0","0","0.19999998807907104")
ProfilePram27 = part.CreateProfileParam()
ProfilePram27.DefinitionType=1
ProfilePram27.BasePlane="PL,O,"+var_elm8+","+"PL,Y"
ProfilePram27.AddAttachSurfaces(extrude_sheet3)
ProfilePram27.ProfileName="HK.Casing.Wall.Aft.DL02.CDP"
ProfilePram27.MaterialName="SS400"
ProfilePram27.FlangeName="HK.Casing.Wall.Aft.DL02.CDP"
ProfilePram27.FlangeMaterialName="SS400"
ProfilePram27.ProfileType=1201
ProfilePram27.ProfileParams=["150","12","388","10"]
ProfilePram27.Mold="-"
ProfilePram27.ReverseDir=False
ProfilePram27.ReverseAngle=False
ProfilePram27.CalcSnipOnlyAttachLines=False
ProfilePram27.AttachDirMethod=0
ProfilePram27.CCWDefAngle=False
ProfilePram27.AddEnd1Elements(profile16[1])
ProfilePram27.End1Type=1102
ProfilePram27.End1TypeParams=["25","14.999999999999998","0","0"]
ProfilePram27.AddEnd2Elements(extrude_sheet6)
ProfilePram27.End2Type=1103
ProfilePram27.End2TypeParams=["0"]
ProfilePram27.End1ScallopType=1120
ProfilePram27.End1ScallopTypeParams=["50"]
ProfilePram27.End2ScallopType=1120
ProfilePram27.End2ScallopTypeParams=["50"]
profile27 = part.CreateProfile(ProfilePram27,False)
part.SetElementColor(profile27[0],"148","0","211","0.38999998569488525")
part.SetElementColor(profile27[1],"148","0","211","0.38999998569488525")
ProfilePram28 = part.CreateProfileParam()
ProfilePram28.DefinitionType=1
ProfilePram28.BasePlane="PL,O,"+var_elm7+","+"PL,X"
ProfilePram28.AddAttachSurfaces(extrude_sheet4)
ProfilePram28.ProfileName="HK.Casing.Wall.Side.FR12.OAP"
ProfilePram28.MaterialName="SS400"
ProfilePram28.ProfileType=1002
ProfilePram28.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram28.Mold="+"
ProfilePram28.ReverseDir=False
ProfilePram28.ReverseAngle=True
ProfilePram28.CalcSnipOnlyAttachLines=False
ProfilePram28.AttachDirMethod=0
ProfilePram28.CCWDefAngle=False
ProfilePram28.AddEnd1Elements(extrude_sheet2)
ProfilePram28.End1Type=1102
ProfilePram28.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram28.AddEnd2Elements(extrude_sheet8)
ProfilePram28.End2Type=1102
ProfilePram28.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram28.End1ScallopType=1121
ProfilePram28.End1ScallopTypeParams=["35","40"]
ProfilePram28.End2ScallopType=1121
ProfilePram28.End2ScallopTypeParams=["35","40"]
profile28 = part.CreateProfile(ProfilePram28,False)
part.SetElementColor(profile28[0],"255","0","0","0.19999998807907104")
ProfilePram29 = part.CreateProfileParam()
ProfilePram29.DefinitionType=1
ProfilePram29.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram29.AddAttachSurfaces(extrude_sheet5)
ProfilePram29.ProfileName="HK.Casing.Wall.Fore.DL03.ABP"
ProfilePram29.MaterialName="SS400"
ProfilePram29.ProfileType=1002
ProfilePram29.ProfileParams=["125","75","7","10","5"]
ProfilePram29.Mold="+"
ProfilePram29.ReverseDir=True
ProfilePram29.ReverseAngle=True
ProfilePram29.CalcSnipOnlyAttachLines=False
ProfilePram29.AttachDirMethod=0
ProfilePram29.CCWDefAngle=False
ProfilePram29.AddEnd1Elements(extrude_sheet1)
ProfilePram29.End1Type=1102
ProfilePram29.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram29.AddEnd2Elements(extrude_sheet2)
ProfilePram29.End2Type=1102
ProfilePram29.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram29.End1ScallopType=1121
ProfilePram29.End1ScallopTypeParams=["25","40"]
ProfilePram29.End2ScallopType=1121
ProfilePram29.End2ScallopTypeParams=["25","40"]
profile29 = part.CreateProfile(ProfilePram29,False)
part.SetElementColor(profile29[0],"255","0","0","0.19999998807907104")
ProfilePram30 = part.CreateProfileParam()
ProfilePram30.DefinitionType=1
ProfilePram30.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram30.AddAttachSurfaces(extrude_sheet7)
ProfilePram30.ProfileName="HK.Casing.Deck.D.DL01.AP"
ProfilePram30.MaterialName="SS400"
ProfilePram30.ProfileType=1002
ProfilePram30.ProfileParams=["125","75","7","10","5"]
ProfilePram30.Mold="+"
ProfilePram30.ReverseDir=True
ProfilePram30.ReverseAngle=True
ProfilePram30.CalcSnipOnlyAttachLines=False
ProfilePram30.AttachDirMethod=0
ProfilePram30.CCWDefAngle=False
ProfilePram30.AddEnd1Elements(extrude_sheet3)
ProfilePram30.End1Type=1102
ProfilePram30.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram30.AddEnd2Elements(profile17[0])
ProfilePram30.End2Type=1102
ProfilePram30.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram30.End1ScallopType=1120
ProfilePram30.End1ScallopTypeParams=["50"]
ProfilePram30.End2ScallopType=1120
ProfilePram30.End2ScallopTypeParams=["50"]
profile30 = part.CreateProfile(ProfilePram30,False)
part.SetElementColor(profile30[0],"255","0","0","0.19999998807907104")
ProfilePram31 = part.CreateProfileParam()
ProfilePram31.DefinitionType=1
ProfilePram31.BasePlane="PL,O,"+var_elm2+","+"PL,X"
ProfilePram31.AddAttachSurfaces(extrude_sheet4)
ProfilePram31.ProfileName="HK.Casing.Wall.Side.FR14.BCP"
ProfilePram31.MaterialName="SS400"
ProfilePram31.ProfileType=1002
ProfilePram31.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram31.Mold="+"
ProfilePram31.ReverseDir=False
ProfilePram31.ReverseAngle=True
ProfilePram31.CalcSnipOnlyAttachLines=False
ProfilePram31.AttachDirMethod=0
ProfilePram31.CCWDefAngle=False
ProfilePram31.AddEnd1Elements(extrude_sheet6)
ProfilePram31.End1Type=1102
ProfilePram31.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram31.AddEnd2Elements(extrude_sheet1)
ProfilePram31.End2Type=1102
ProfilePram31.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram31.End1ScallopType=1121
ProfilePram31.End1ScallopTypeParams=["35","40"]
ProfilePram31.End2ScallopType=1121
ProfilePram31.End2ScallopTypeParams=["35","40"]
profile31 = part.CreateProfile(ProfilePram31,False)
part.SetElementColor(profile31[0],"255","0","0","0.19999998807907104")
ProfilePram32 = part.CreateProfileParam()
ProfilePram32.DefinitionType=1
ProfilePram32.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram32.AddAttachSurfaces(extrude_sheet5)
ProfilePram32.ProfileName="HK.Casing.Wall.Fore.DL04.ABP"
ProfilePram32.MaterialName="SS400"
ProfilePram32.ProfileType=1003
ProfilePram32.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram32.Mold="+"
ProfilePram32.ReverseDir=True
ProfilePram32.ReverseAngle=True
ProfilePram32.CalcSnipOnlyAttachLines=False
ProfilePram32.AttachDirMethod=0
ProfilePram32.CCWDefAngle=False
ProfilePram32.AddEnd1Elements(extrude_sheet1)
ProfilePram32.End1Type=1102
ProfilePram32.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram32.AddEnd2Elements(extrude_sheet2)
ProfilePram32.End2Type=1102
ProfilePram32.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram32.End1ScallopType=1120
ProfilePram32.End1ScallopTypeParams=["50"]
ProfilePram32.End2ScallopType=1120
ProfilePram32.End2ScallopTypeParams=["50"]
profile32 = part.CreateProfile(ProfilePram32,False)
part.SetElementColor(profile32[0],"148","0","211","0.39999997615814209")
ProfilePram33 = part.CreateProfileParam()
ProfilePram33.DefinitionType=1
ProfilePram33.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram33.AddAttachSurfaces(extrude_sheet1)
ProfilePram33.ProfileName="HK.Casing.Deck.B.DL04P"
ProfilePram33.MaterialName="SS400"
ProfilePram33.ProfileType=1003
ProfilePram33.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram33.Mold="-"
ProfilePram33.ReverseDir=True
ProfilePram33.ReverseAngle=False
ProfilePram33.CalcSnipOnlyAttachLines=False
ProfilePram33.AttachDirMethod=0
ProfilePram33.CCWDefAngle=False
ProfilePram33.AddEnd1Elements(profile1[0])
ProfilePram33.End1Type=1102
ProfilePram33.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram33.AddEnd2Elements(profile32[0])
ProfilePram33.End2Type=1102
ProfilePram33.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram33.End1ScallopType=0
ProfilePram33.End2ScallopType=0
profile33 = part.CreateProfile(ProfilePram33,False)
part.SetElementColor(profile33[0],"148","0","211","0.39999997615814209")
mirror_copied5 = part.MirrorCopy([profile33[0]],"PL,Y","")
part.SetElementColor(mirror_copied5[0],"148","0","211","0.39999997615814209")
ProfilePram34 = part.CreateProfileParam()
ProfilePram34.DefinitionType=1
ProfilePram34.BasePlane="PL,O,"+"FR6 + 400 mm"+","+"PL,X"
ProfilePram34.AddAttachSurfaces(extrude_sheet1)
ProfilePram34.ProfileName="HK.Casing.Deck.B.FR06F400"
ProfilePram34.MaterialName="SS400"
ProfilePram34.ProfileType=1007
ProfilePram34.ProfileParams=["150","12"]
ProfilePram34.Mold="+"
ProfilePram34.ReverseDir=True
ProfilePram34.ReverseAngle=False
ProfilePram34.CalcSnipOnlyAttachLines=False
ProfilePram34.AttachDirMethod=0
ProfilePram34.CCWDefAngle=False
ProfilePram34.AddEnd1Elements(mirror_copied5[0])
ProfilePram34.End1Type=1102
ProfilePram34.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram34.AddEnd2Elements(profile33[0])
ProfilePram34.End2Type=1102
ProfilePram34.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram34.End1ScallopType=-1
ProfilePram34.End2ScallopType=-1
profile34 = part.CreateProfile(ProfilePram34,False)
part.SetElementColor(profile34[0],"255","0","0","0.19999998807907104")
bracketPram5 = part.CreateBracketParam()
bracketPram5.DefinitionType=1
bracketPram5.BracketName="HK.Casing.Wall.Aft.DL03.Deck.BP"
bracketPram5.MaterialName="SS400"
bracketPram5.BaseElement=profile18[0]
bracketPram5.UseSideSheetForPlane=False
bracketPram5.Mold="+"
bracketPram5.Thickness="7.9999999999999964"
bracketPram5.BracketType=1505
bracketPram5.BracketParams=["200"]
bracketPram5.Scallop1Type=1801
bracketPram5.Scallop1Params=["0"]
bracketPram5.Scallop2Type=0
bracketPram5.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram5.RevSf1=False
bracketPram5.Surfaces2=[profile18[0]+",FL"]
bracketPram5.RevSf2=False
bracketPram5.RevSf3=False
bracketPram5.Sf1DimensionType=1541
bracketPram5.Sf1DimensonParams=["0","100"]
bracketPram5.Sf1EndElements=["PLS","False","False","-1","0","-0",profile34[0]]
bracketPram5.Sf2DimensionType=1531
bracketPram5.Sf2DimensonParams=["200","15"]
bracket5 = part.CreateBracket(bracketPram5,False)
part.SetElementColor(bracket5,"0","255","255","0.19999998807907104")
ProfilePram35 = part.CreateProfileParam()
ProfilePram35.DefinitionType=1
ProfilePram35.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram35.AddAttachSurfaces(extrude_sheet5)
ProfilePram35.ProfileName="HK.Casing.Wall.Fore.DL05.CDP"
ProfilePram35.MaterialName="SS400"
ProfilePram35.ProfileType=1002
ProfilePram35.ProfileParams=["125","75","7","10","5"]
ProfilePram35.Mold="+"
ProfilePram35.ReverseDir=True
ProfilePram35.ReverseAngle=True
ProfilePram35.CalcSnipOnlyAttachLines=False
ProfilePram35.AttachDirMethod=0
ProfilePram35.CCWDefAngle=False
ProfilePram35.AddEnd1Elements(profile15[0])
ProfilePram35.End1Type=1102
ProfilePram35.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram35.AddEnd2Elements(extrude_sheet6)
ProfilePram35.End2Type=1102
ProfilePram35.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram35.End1ScallopType=1120
ProfilePram35.End1ScallopTypeParams=["50"]
ProfilePram35.End2ScallopType=1120
ProfilePram35.End2ScallopTypeParams=["50"]
profile35 = part.CreateProfile(ProfilePram35,False)
part.SetElementColor(profile35[0],"255","0","0","0.19999998807907104")
ProfilePram36 = part.CreateProfileParam()
ProfilePram36.DefinitionType=1
ProfilePram36.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram36.AddAttachSurfaces(extrude_sheet7)
ProfilePram36.ProfileName="HK.Casing.Deck.D.DL00.A"
ProfilePram36.MaterialName="SS400"
ProfilePram36.ProfileType=1002
ProfilePram36.ProfileParams=["125","75","7","10","5"]
ProfilePram36.ReverseDir=True
ProfilePram36.ReverseAngle=True
ProfilePram36.CalcSnipOnlyAttachLines=False
ProfilePram36.AttachDirMethod=0
ProfilePram36.CCWDefAngle=False
ProfilePram36.AddEnd1Elements(extrude_sheet3)
ProfilePram36.End1Type=1102
ProfilePram36.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram36.AddEnd2Elements(profile17[0])
ProfilePram36.End2Type=1102
ProfilePram36.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram36.End1ScallopType=1120
ProfilePram36.End1ScallopTypeParams=["50"]
ProfilePram36.End2ScallopType=1120
ProfilePram36.End2ScallopTypeParams=["50"]
profile36 = part.CreateProfile(ProfilePram36,False)
part.SetElementColor(profile36[0],"255","0","0","0.19999998807907104")
ProfilePram37 = part.CreateProfileParam()
ProfilePram37.DefinitionType=1
ProfilePram37.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram37.AddAttachSurfaces(extrude_sheet7)
ProfilePram37.ProfileName="HK.Casing.Deck.D.DL03P"
ProfilePram37.MaterialName="SS400"
ProfilePram37.ProfileType=1002
ProfilePram37.ProfileParams=["125","75","7","10","5"]
ProfilePram37.Mold="+"
ProfilePram37.ReverseDir=True
ProfilePram37.ReverseAngle=True
ProfilePram37.CalcSnipOnlyAttachLines=False
ProfilePram37.AttachDirMethod=0
ProfilePram37.CCWDefAngle=False
ProfilePram37.AddEnd1Elements(extrude_sheet3)
ProfilePram37.End1Type=1102
ProfilePram37.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram37.AddEnd2Elements(extrude_sheet5)
ProfilePram37.End2Type=1102
ProfilePram37.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram37.End1ScallopType=1120
ProfilePram37.End1ScallopTypeParams=["50"]
ProfilePram37.End2ScallopType=1120
ProfilePram37.End2ScallopTypeParams=["50"]
profile37 = part.CreateProfile(ProfilePram37,False)
part.SetElementColor(profile37[0],"255","0","0","0.19999998807907104")
ProfilePram38 = part.CreateProfileParam()
ProfilePram38.DefinitionType=1
ProfilePram38.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram38.AddAttachSurfaces(extrude_sheet3)
ProfilePram38.ProfileName="HK.Casing.Wall.Aft.DL03.CDP"
ProfilePram38.MaterialName="SS400"
ProfilePram38.ProfileType=1002
ProfilePram38.ProfileParams=["125","75","7","10","5"]
ProfilePram38.Mold="+"
ProfilePram38.ReverseDir=False
ProfilePram38.ReverseAngle=True
ProfilePram38.CalcSnipOnlyAttachLines=False
ProfilePram38.AttachDirMethod=0
ProfilePram38.CCWDefAngle=False
ProfilePram38.AddEnd1Elements(profile37[0])
ProfilePram38.End1Type=1102
ProfilePram38.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram38.AddEnd2Elements(extrude_sheet6)
ProfilePram38.End2Type=1102
ProfilePram38.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram38.End1ScallopType=1120
ProfilePram38.End1ScallopTypeParams=["50"]
ProfilePram38.End2ScallopType=1120
ProfilePram38.End2ScallopTypeParams=["50"]
profile38 = part.CreateProfile(ProfilePram38,False)
part.SetElementColor(profile38[0],"255","0","0","0.19999998807907104")
bracketPram6 = part.CreateBracketParam()
bracketPram6.DefinitionType=1
bracketPram6.BracketName="HK.Casing.Wall.Aft.DL03.Deck.DP"
bracketPram6.MaterialName="SS400"
bracketPram6.BaseElement=profile38[0]
bracketPram6.UseSideSheetForPlane=False
bracketPram6.Mold="+"
bracketPram6.Thickness="7.9999999999999964"
bracketPram6.BracketType=1501
bracketPram6.Scallop1Type=1801
bracketPram6.Scallop1Params=["0"]
bracketPram6.Scallop2Type=0
bracketPram6.Surfaces1=[profile38[0]+",FL"]
bracketPram6.RevSf1=False
bracketPram6.Surfaces2=[profile37[0]+",FL"]
bracketPram6.RevSf2=False
bracketPram6.RevSf3=False
bracketPram6.Sf1DimensionType=1531
bracketPram6.Sf1DimensonParams=["200","15"]
bracketPram6.Sf2DimensionType=1531
bracketPram6.Sf2DimensonParams=["200","15"]
bracket6 = part.CreateBracket(bracketPram6,False)
part.SetElementColor(bracket6,"0","255","255","0.19999998807907104")
ProfilePram39 = part.CreateProfileParam()
ProfilePram39.DefinitionType=1
ProfilePram39.BasePlane="PL,O,"+var_elm13+","+"PL,X"
ProfilePram39.AddAttachSurfaces(extrude_sheet4)
ProfilePram39.ProfileName="HK.Casing.Wall.Side.FR07.OAP"
ProfilePram39.MaterialName="SS400"
ProfilePram39.ProfileType=1002
ProfilePram39.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram39.Mold="+"
ProfilePram39.ReverseDir=False
ProfilePram39.ReverseAngle=True
ProfilePram39.CalcSnipOnlyAttachLines=False
ProfilePram39.AttachDirMethod=0
ProfilePram39.CCWDefAngle=False
ProfilePram39.AddEnd1Elements(extrude_sheet2)
ProfilePram39.End1Type=1102
ProfilePram39.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram39.AddEnd2Elements(extrude_sheet8)
ProfilePram39.End2Type=1102
ProfilePram39.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram39.End1ScallopType=1121
ProfilePram39.End1ScallopTypeParams=["35","40"]
ProfilePram39.End2ScallopType=1121
ProfilePram39.End2ScallopTypeParams=["35","40"]
profile39 = part.CreateProfile(ProfilePram39,False)
part.SetElementColor(profile39[0],"255","0","0","0.19999998807907104")
mirror_copied6 = part.MirrorCopy([profile39[0]],"PL,Y","")
part.SetElementColor(mirror_copied6[0],"255","0","0","0.19999998807907104")
var_elm15 = part.CreateVariable("FR13","8970","mm","")
ProfilePram40 = part.CreateProfileParam()
ProfilePram40.DefinitionType=1
ProfilePram40.BasePlane="PL,O,"+var_elm15+","+"PL,X"
ProfilePram40.AddAttachSurfaces(extrude_sheet4)
ProfilePram40.ProfileName="HK.Casing.Wall.Side.FR13.OAP"
ProfilePram40.MaterialName="SS400"
ProfilePram40.ProfileType=1003
ProfilePram40.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram40.Mold="+"
ProfilePram40.ReverseDir=False
ProfilePram40.ReverseAngle=True
ProfilePram40.CalcSnipOnlyAttachLines=False
ProfilePram40.AttachDirMethod=0
ProfilePram40.CCWDefAngle=False
ProfilePram40.AddEnd1Elements(extrude_sheet2)
ProfilePram40.End1Type=1103
ProfilePram40.End1TypeParams=["0"]
ProfilePram40.AddEnd2Elements(extrude_sheet8)
ProfilePram40.End2Type=1103
ProfilePram40.End2TypeParams=["0"]
ProfilePram40.End1ScallopType=1120
ProfilePram40.End1ScallopTypeParams=["50"]
ProfilePram40.End2ScallopType=1120
ProfilePram40.End2ScallopTypeParams=["50"]
profile40 = part.CreateProfile(ProfilePram40,False)
part.SetElementColor(profile40[0],"148","0","211","0.39999997615814209")
ProfilePram41 = part.CreateProfileParam()
ProfilePram41.DefinitionType=1
ProfilePram41.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram41.AddAttachSurfaces(extrude_sheet3)
ProfilePram41.ProfileName="HK.Casing.Wall.Aft.DL04.OAP"
ProfilePram41.MaterialName="SS400"
ProfilePram41.ProfileType=1003
ProfilePram41.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram41.Mold="+"
ProfilePram41.ReverseDir=False
ProfilePram41.ReverseAngle=True
ProfilePram41.CalcSnipOnlyAttachLines=False
ProfilePram41.AttachDirMethod=0
ProfilePram41.CCWDefAngle=False
ProfilePram41.AddEnd1Elements(extrude_sheet2)
ProfilePram41.End1Type=1102
ProfilePram41.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram41.AddEnd2Elements(extrude_sheet8)
ProfilePram41.End2Type=1102
ProfilePram41.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram41.End1ScallopType=1120
ProfilePram41.End1ScallopTypeParams=["50"]
ProfilePram41.End2ScallopType=1120
ProfilePram41.End2ScallopTypeParams=["50"]
profile41 = part.CreateProfile(ProfilePram41,False)
part.SetElementColor(profile41[0],"148","0","211","0.39999997615814209")
ProfilePram42 = part.CreateProfileParam()
ProfilePram42.DefinitionType=1
ProfilePram42.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram42.AddAttachSurfaces(extrude_sheet5)
ProfilePram42.ProfileName="HK.Casing.Wall.Fore.DL04.OAP"
ProfilePram42.MaterialName="SS400"
ProfilePram42.ProfileType=1003
ProfilePram42.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram42.Mold="+"
ProfilePram42.ReverseDir=True
ProfilePram42.ReverseAngle=True
ProfilePram42.CalcSnipOnlyAttachLines=False
ProfilePram42.AttachDirMethod=0
ProfilePram42.CCWDefAngle=False
ProfilePram42.AddEnd1Elements(extrude_sheet2)
ProfilePram42.End1Type=1102
ProfilePram42.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram42.AddEnd2Elements(extrude_sheet8)
ProfilePram42.End2Type=1102
ProfilePram42.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram42.End1ScallopType=1120
ProfilePram42.End1ScallopTypeParams=["50"]
ProfilePram42.End2ScallopType=1120
ProfilePram42.End2ScallopTypeParams=["50"]
profile42 = part.CreateProfile(ProfilePram42,False)
part.SetElementColor(profile42[0],"148","0","211","0.39999997615814209")
ProfilePram43 = part.CreateProfileParam()
ProfilePram43.DefinitionType=1
ProfilePram43.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram43.AddAttachSurfaces(extrude_sheet2)
ProfilePram43.ProfileName="HK.Casing.Deck.A.DL04P"
ProfilePram43.MaterialName="SS400"
ProfilePram43.ProfileType=1003
ProfilePram43.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram43.Mold="-"
ProfilePram43.ReverseDir=True
ProfilePram43.ReverseAngle=False
ProfilePram43.CalcSnipOnlyAttachLines=False
ProfilePram43.AttachDirMethod=0
ProfilePram43.CCWDefAngle=False
ProfilePram43.AddEnd1Elements(profile41[0])
ProfilePram43.End1Type=1102
ProfilePram43.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram43.AddEnd2Elements(profile42[0])
ProfilePram43.End2Type=1102
ProfilePram43.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram43.End1ScallopType=0
ProfilePram43.End2ScallopType=0
profile43 = part.CreateProfile(ProfilePram43,False)
part.SetElementColor(profile43[0],"148","0","211","0.39999997615814209")
ProfilePram44 = part.CreateProfileParam()
ProfilePram44.DefinitionType=1
ProfilePram44.BasePlane="PL,O,"+var_elm15+","+"PL,X"
ProfilePram44.AddAttachSurfaces(extrude_sheet2)
ProfilePram44.ProfileName="HK.Casing.Deck.A.FR13P"
ProfilePram44.MaterialName="SS400"
ProfilePram44.ProfileType=1003
ProfilePram44.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram44.Mold="+"
ProfilePram44.ReverseDir=True
ProfilePram44.ReverseAngle=False
ProfilePram44.CalcSnipOnlyAttachLines=False
ProfilePram44.AttachDirMethod=0
ProfilePram44.CCWDefAngle=False
ProfilePram44.AddEnd1Elements(profile43[0])
ProfilePram44.End1Type=1113
ProfilePram44.End1TypeParams=["0","79"]
ProfilePram44.AddEnd2Elements(profile40[0])
ProfilePram44.End2Type=1102
ProfilePram44.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram44.End1ScallopType=1120
ProfilePram44.End1ScallopTypeParams=["50"]
ProfilePram44.End2ScallopType=1120
ProfilePram44.End2ScallopTypeParams=["50"]
profile44 = part.CreateProfile(ProfilePram44,False)
part.SetElementColor(profile44[0],"148","0","211","0.39999997615814209")
ProfilePram45 = part.CreateProfileParam()
ProfilePram45.DefinitionType=1
ProfilePram45.BasePlane="PL,O,"+var_elm15+","+"PL,X"
ProfilePram45.AddAttachSurfaces(extrude_sheet7)
ProfilePram45.ProfileName="HK.Casing.Deck.D.FR13P"
ProfilePram45.MaterialName="SS400"
ProfilePram45.ProfileType=1003
ProfilePram45.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram45.Mold="+"
ProfilePram45.ReverseDir=True
ProfilePram45.ReverseAngle=False
ProfilePram45.CalcSnipOnlyAttachLines=False
ProfilePram45.AttachDirMethod=0
ProfilePram45.CCWDefAngle=False
ProfilePram45.AddEnd1Elements(profile16[0])
ProfilePram45.End1Type=1102
ProfilePram45.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram45.AddEnd2Elements(extrude_sheet4)
ProfilePram45.End2Type=1102
ProfilePram45.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram45.End1ScallopType=1120
ProfilePram45.End1ScallopTypeParams=["50"]
ProfilePram45.End2ScallopType=1120
ProfilePram45.End2ScallopTypeParams=["50"]
profile45 = part.CreateProfile(ProfilePram45,False)
part.SetElementColor(profile45[0],"148","0","211","0.39999997615814209")
ProfilePram46 = part.CreateProfileParam()
ProfilePram46.DefinitionType=1
ProfilePram46.BasePlane="PL,O,"+var_elm15+","+"PL,X"
ProfilePram46.AddAttachSurfaces(extrude_sheet4)
ProfilePram46.ProfileName="HK.Casing.Wall.Side.FR13.CDP"
ProfilePram46.MaterialName="SS400"
ProfilePram46.ProfileType=1003
ProfilePram46.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram46.Mold="+"
ProfilePram46.ReverseDir=False
ProfilePram46.ReverseAngle=True
ProfilePram46.CalcSnipOnlyAttachLines=False
ProfilePram46.AttachDirMethod=0
ProfilePram46.CCWDefAngle=False
ProfilePram46.AddEnd1Elements(profile45[0])
ProfilePram46.End1Type=1102
ProfilePram46.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram46.AddEnd2Elements(extrude_sheet6)
ProfilePram46.End2Type=1103
ProfilePram46.End2TypeParams=["0"]
ProfilePram46.End1ScallopType=1120
ProfilePram46.End1ScallopTypeParams=["50"]
ProfilePram46.End2ScallopType=1120
ProfilePram46.End2ScallopTypeParams=["50"]
profile46 = part.CreateProfile(ProfilePram46,False)
part.SetElementColor(profile46[0],"148","0","211","0.39999997615814209")
var_elm16 = part.CreateVariable("FR10","6700","mm","")
ProfilePram47 = part.CreateProfileParam()
ProfilePram47.DefinitionType=1
ProfilePram47.BasePlane="PL,O,"+var_elm16+","+"PL,X"
ProfilePram47.AddAttachSurfaces(extrude_sheet4)
ProfilePram47.ProfileName="HK.Casing.Wall.Side.FR10.CDP"
ProfilePram47.MaterialName="SS400"
ProfilePram47.ProfileType=1002
ProfilePram47.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram47.Mold="+"
ProfilePram47.ReverseDir=False
ProfilePram47.ReverseAngle=True
ProfilePram47.CalcSnipOnlyAttachLines=False
ProfilePram47.AttachDirMethod=0
ProfilePram47.CCWDefAngle=False
ProfilePram47.AddEnd1Elements(extrude_sheet7)
ProfilePram47.End1Type=1102
ProfilePram47.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram47.AddEnd2Elements(extrude_sheet6)
ProfilePram47.End2Type=1102
ProfilePram47.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram47.End1ScallopType=1121
ProfilePram47.End1ScallopTypeParams=["35","40"]
ProfilePram47.End2ScallopType=1121
ProfilePram47.End2ScallopTypeParams=["35","40"]
profile47 = part.CreateProfile(ProfilePram47,False)
part.SetElementColor(profile47[0],"255","0","0","0.19999998807907104")
ProfilePram48 = part.CreateProfileParam()
ProfilePram48.DefinitionType=1
ProfilePram48.BasePlane="PL,O,"+var_elm2+","+"PL,X"
ProfilePram48.AddAttachSurfaces(extrude_sheet4)
ProfilePram48.ProfileName="HK.Casing.Wall.Side.FR14.OAP"
ProfilePram48.MaterialName="SS400"
ProfilePram48.ProfileType=1002
ProfilePram48.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram48.Mold="+"
ProfilePram48.ReverseDir=False
ProfilePram48.ReverseAngle=True
ProfilePram48.CalcSnipOnlyAttachLines=False
ProfilePram48.AttachDirMethod=0
ProfilePram48.CCWDefAngle=False
ProfilePram48.AddEnd1Elements(extrude_sheet2)
ProfilePram48.End1Type=1102
ProfilePram48.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram48.AddEnd2Elements(extrude_sheet8)
ProfilePram48.End2Type=1102
ProfilePram48.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram48.End1ScallopType=1121
ProfilePram48.End1ScallopTypeParams=["35","40"]
ProfilePram48.End2ScallopType=1121
ProfilePram48.End2ScallopTypeParams=["35","40"]
profile48 = part.CreateProfile(ProfilePram48,False)
part.SetElementColor(profile48[0],"255","0","0","0.19999998807907104")
skt_pl6 = part.CreateSketchPlane("HK.Az.Deck.A","","PL,Z","0",False,False,"","","",True,False)
part.BlankElement(skt_pl6,True)
skt_layer17 = part.CreateSketchLayer("Edge00",skt_pl6)
skt_ln43 = part.CreateSketchLine(skt_pl6,"","Edge00","11405.000000000002,4835","3984.9999999999995,4835",False)
skt_ln44 = part.CreateSketchLine(skt_pl6,"","Edge00","11405.000000000002,-4835","11405.000000000002,4835",False)
skt_ln45 = part.CreateSketchLine(skt_pl6,"","Edge00","3984.9999999999995,-4835","11405.000000000002,-4835",False)
skt_ln46 = part.CreateSketchLine(skt_pl6,"","Edge00","3984.9999999999995,4835","3984.9999999999995,-4835",False)
skt_layer18 = part.CreateSketchLayer("Edge01",skt_pl6)
skt_ln47 = part.CreateSketchLine(skt_pl6,"","Edge01","9770,3125","4835.0000000000009,3125",False)
skt_ln48 = part.CreateSketchLine(skt_pl6,"","Edge01","10170,-2725","10170,2725",False)
skt_ln49 = part.CreateSketchLine(skt_pl6,"","Edge01","4835.0000000000009,-3125","9770,-3125",False)
skt_ln50 = part.CreateSketchLine(skt_pl6,"","Edge01","4435.0000000000009,2725","4435.0000000000009,-2724.9999999999991",False)
skt_arc13 = part.CreateSketchArc(skt_pl6,"","Edge01","4835.0000000000009,2724.9999999999995","4835.0000000000009,3124.9999999999995","4435.0000000000009,2725",True,False)
skt_arc14 = part.CreateSketchArc(skt_pl6,"","Edge01","9770,2724.9999999999995","10170,2725","9770,3124.9999999999995",True,False)
skt_arc15 = part.CreateSketchArc(skt_pl6,"","Edge01","9770,-2724.9999999999995","9770,-3124.9999999999995","10170,-2725",True,False)
skt_arc16 = part.CreateSketchArc(skt_pl6,"","Edge01","4835.0000000000009,-2725","4435.0000000000009,-2724.9999999999995","4835.0000000000009,-3125",True,False)
solid4 = part.CreateSolid("HK.Casing.Deck.A","","SS400")
part.SetElementColor(solid4,"139","69","19","0.78999996185302734")
thicken4 = part.CreateThicken("厚み付け6",solid4,"+",[extrude_sheet2],"+","10","0","0",False,False)
extrudePram15 = part.CreateLinearSweepParam()
extrudePram15.Name="積-押し出し6"
extrudePram15.AddProfile(skt_pl6+",Edge00")
extrudePram15.DirectionType="N"
extrudePram15.DirectionParameter1="50000"
extrudePram15.SweepDirection="+Z"
extrudePram15.RefByGeometricMethod=True
extrude7 = part.CreateLinearSweep(solid4,"*",extrudePram15,False)
extrudePram16 = part.CreateLinearSweepParam()
extrudePram16.Name="削除-押し出し4"
extrudePram16.AddProfile(skt_pl6+",Edge01")
extrudePram16.DirectionType="T"
extrudePram16.RefByGeometricMethod=True
extrude8 = part.CreateLinearSweep(solid4,"-",extrudePram16,False)
ProfilePram49 = part.CreateProfileParam()
ProfilePram49.DefinitionType=1
ProfilePram49.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram49.AddAttachSurfaces(extrude_sheet3)
ProfilePram49.ProfileName="HK.Casing.Wall.Aft.DL05.OAP"
ProfilePram49.MaterialName="SS400"
ProfilePram49.ProfileType=1002
ProfilePram49.ProfileParams=["125","75","7","10","5"]
ProfilePram49.Mold="+"
ProfilePram49.ReverseDir=False
ProfilePram49.ReverseAngle=True
ProfilePram49.CalcSnipOnlyAttachLines=False
ProfilePram49.AttachDirMethod=0
ProfilePram49.CCWDefAngle=False
ProfilePram49.AddEnd1Elements(extrude_sheet2)
ProfilePram49.End1Type=1102
ProfilePram49.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram49.AddEnd2Elements(extrude_sheet8)
ProfilePram49.End2Type=1102
ProfilePram49.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram49.End1ScallopType=1121
ProfilePram49.End1ScallopTypeParams=["25","40"]
ProfilePram49.End2ScallopType=1121
ProfilePram49.End2ScallopTypeParams=["25","40"]
profile49 = part.CreateProfile(ProfilePram49,False)
part.SetElementColor(profile49[0],"255","0","0","0.19999998807907104")
ProfilePram50 = part.CreateProfileParam()
ProfilePram50.DefinitionType=1
ProfilePram50.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram50.AddAttachSurfaces(extrude_sheet5)
ProfilePram50.ProfileName="HK.Casing.Wall.Fore.DL05.OAP"
ProfilePram50.MaterialName="SS400"
ProfilePram50.ProfileType=1002
ProfilePram50.ProfileParams=["125","75","7","10","5"]
ProfilePram50.Mold="+"
ProfilePram50.ReverseDir=True
ProfilePram50.ReverseAngle=True
ProfilePram50.CalcSnipOnlyAttachLines=False
ProfilePram50.AttachDirMethod=0
ProfilePram50.CCWDefAngle=False
ProfilePram50.AddEnd1Elements(extrude_sheet2)
ProfilePram50.End1Type=1102
ProfilePram50.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram50.AddEnd2Elements(extrude_sheet8)
ProfilePram50.End2Type=1102
ProfilePram50.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram50.End1ScallopType=1121
ProfilePram50.End1ScallopTypeParams=["25","40"]
ProfilePram50.End2ScallopType=1121
ProfilePram50.End2ScallopTypeParams=["25","40"]
profile50 = part.CreateProfile(ProfilePram50,False)
part.SetElementColor(profile50[0],"255","0","0","0.19999998807907104")
ProfilePram51 = part.CreateProfileParam()
ProfilePram51.DefinitionType=1
ProfilePram51.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram51.AddAttachSurfaces(extrude_sheet2)
ProfilePram51.ProfileName="HK.Casing.Deck.A.DL05P"
ProfilePram51.MaterialName="SS400"
ProfilePram51.ProfileType=1002
ProfilePram51.ProfileParams=["125","75","7","10","5"]
ProfilePram51.Mold="+"
ProfilePram51.ReverseDir=True
ProfilePram51.ReverseAngle=True
ProfilePram51.CalcSnipOnlyAttachLines=False
ProfilePram51.AttachDirMethod=0
ProfilePram51.CCWDefAngle=False
ProfilePram51.AddEnd1Elements(profile49[0])
ProfilePram51.End1Type=1102
ProfilePram51.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram51.AddEnd2Elements(profile50[0])
ProfilePram51.End2Type=1102
ProfilePram51.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram51.End1ScallopType=1120
ProfilePram51.End1ScallopTypeParams=["50"]
ProfilePram51.End2ScallopType=1120
ProfilePram51.End2ScallopTypeParams=["50"]
profile51 = part.CreateProfile(ProfilePram51,False)
part.SetElementColor(profile51[0],"255","0","0","0.19999998807907104")
bracketPram7 = part.CreateBracketParam()
bracketPram7.DefinitionType=1
bracketPram7.BracketName="HK.Casing.Wall.Side.FR14.Deck.AP"
bracketPram7.MaterialName="SS400"
bracketPram7.BaseElement=profile48[0]
bracketPram7.UseSideSheetForPlane=False
bracketPram7.Mold="+"
bracketPram7.Thickness="9.9999999999999982"
bracketPram7.BracketType=1505
bracketPram7.BracketParams=["200"]
bracketPram7.Scallop1Type=1801
bracketPram7.Scallop1Params=["0"]
bracketPram7.Scallop2Type=0
bracketPram7.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram7.RevSf1=False
bracketPram7.Surfaces2=[profile48[0]+",FL"]
bracketPram7.RevSf2=False
bracketPram7.RevSf3=False
bracketPram7.Sf1DimensionType=1541
bracketPram7.Sf1DimensonParams=["0","100"]
bracketPram7.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile51[0]]
bracketPram7.Sf2DimensionType=1531
bracketPram7.Sf2DimensonParams=["200","15"]
bracket7 = part.CreateBracket(bracketPram7,False)
part.SetElementColor(bracket7,"0","255","255","0.19999998807907104")
ProfilePram52 = part.CreateProfileParam()
ProfilePram52.DefinitionType=1
ProfilePram52.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram52.AddAttachSurfaces(extrude_sheet5)
ProfilePram52.ProfileName="HK.Casing.Wall.Fore.DL00.OA"
ProfilePram52.MaterialName="SS400"
ProfilePram52.ProfileType=1002
ProfilePram52.ProfileParams=["125","75","7","10","5"]
ProfilePram52.ReverseDir=True
ProfilePram52.ReverseAngle=True
ProfilePram52.CalcSnipOnlyAttachLines=False
ProfilePram52.AttachDirMethod=0
ProfilePram52.CCWDefAngle=False
ProfilePram52.AddEnd1Elements(extrude_sheet2)
ProfilePram52.End1Type=1102
ProfilePram52.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram52.AddEnd2Elements(extrude_sheet8)
ProfilePram52.End2Type=1102
ProfilePram52.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram52.End1ScallopType=1121
ProfilePram52.End1ScallopTypeParams=["25","40"]
ProfilePram52.End2ScallopType=1121
ProfilePram52.End2ScallopTypeParams=["25","40"]
profile52 = part.CreateProfile(ProfilePram52,False)
part.SetElementColor(profile52[0],"255","0","0","0.19999998807907104")
mirror_copied7 = part.MirrorCopy([profile43[0]],"PL,Y","")
part.SetElementColor(mirror_copied7[0],"148","0","211","0.39999997615814209")
ProfilePram53 = part.CreateProfileParam()
ProfilePram53.DefinitionType=1
ProfilePram53.BasePlane="PL,O,"+"FR14 + 415 mm"+","+"PL,X"
ProfilePram53.AddAttachSurfaces(extrude_sheet2)
ProfilePram53.ProfileName="HK.Casing.Deck.A.FR14F415"
ProfilePram53.MaterialName="SS400"
ProfilePram53.ProfileType=1003
ProfilePram53.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram53.Mold="+"
ProfilePram53.ReverseDir=True
ProfilePram53.ReverseAngle=True
ProfilePram53.CalcSnipOnlyAttachLines=False
ProfilePram53.AttachDirMethod=0
ProfilePram53.CCWDefAngle=False
ProfilePram53.AddEnd1Elements(mirror_copied7[0])
ProfilePram53.End1Type=1111
ProfilePram53.End1TypeParams=["0","35","50","50","25","29.999999999999996","0"]
ProfilePram53.AddEnd2Elements(profile43[0])
ProfilePram53.End2Type=1111
ProfilePram53.End2TypeParams=["0","35","50","50","25","29.999999999999996","0"]
ProfilePram53.End1ScallopType=1120
ProfilePram53.End1ScallopTypeParams=["50"]
ProfilePram53.End2ScallopType=1120
ProfilePram53.End2ScallopTypeParams=["50"]
profile53 = part.CreateProfile(ProfilePram53,False)
part.SetElementColor(profile53[0],"255","0","0","0.19999998807907104")
ProfilePram54 = part.CreateProfileParam()
ProfilePram54.DefinitionType=1
ProfilePram54.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram54.AddAttachSurfaces(extrude_sheet2)
ProfilePram54.ProfileName="HK.Casing.Deck.A.DL00.F"
ProfilePram54.MaterialName="SS400"
ProfilePram54.ProfileType=1002
ProfilePram54.ProfileParams=["125","75","7","10","5"]
ProfilePram54.ReverseDir=True
ProfilePram54.ReverseAngle=True
ProfilePram54.CalcSnipOnlyAttachLines=False
ProfilePram54.AttachDirMethod=0
ProfilePram54.CCWDefAngle=False
ProfilePram54.AddEnd1Elements(profile53[0])
ProfilePram54.End1Type=1102
ProfilePram54.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram54.AddEnd2Elements(profile52[0])
ProfilePram54.End2Type=1102
ProfilePram54.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram54.End1ScallopType=1121
ProfilePram54.End1ScallopTypeParams=["25","40"]
ProfilePram54.End2ScallopType=1121
ProfilePram54.End2ScallopTypeParams=["25","40"]
profile54 = part.CreateProfile(ProfilePram54,False)
part.SetElementColor(profile54[0],"255","0","0","0.19999998807907104")
ProfilePram55 = part.CreateProfileParam()
ProfilePram55.DefinitionType=1
ProfilePram55.BasePlane="PL,O,"+var_elm13+","+"PL,X"
ProfilePram55.AddAttachSurfaces(extrude_sheet4)
ProfilePram55.ProfileName="HK.Casing.Wall.Side.FR07.BCP"
ProfilePram55.MaterialName="SS400"
ProfilePram55.ProfileType=1002
ProfilePram55.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram55.Mold="+"
ProfilePram55.ReverseDir=False
ProfilePram55.ReverseAngle=True
ProfilePram55.CalcSnipOnlyAttachLines=False
ProfilePram55.AttachDirMethod=0
ProfilePram55.CCWDefAngle=False
ProfilePram55.AddEnd1Elements(extrude_sheet6)
ProfilePram55.End1Type=1102
ProfilePram55.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram55.AddEnd2Elements(extrude_sheet1)
ProfilePram55.End2Type=1102
ProfilePram55.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram55.End1ScallopType=1121
ProfilePram55.End1ScallopTypeParams=["35","40"]
ProfilePram55.End2ScallopType=1121
ProfilePram55.End2ScallopTypeParams=["35","40"]
profile55 = part.CreateProfile(ProfilePram55,False)
part.SetElementColor(profile55[0],"255","0","0","0.19999998807907104")
bracketPram8 = part.CreateBracketParam()
bracketPram8.DefinitionType=1
bracketPram8.BracketName="HK.Casing.Wall.Fore.DL04.Deck.BP"
bracketPram8.MaterialName="SS400"
bracketPram8.BaseElement=profile33[0]
bracketPram8.UseSideSheetForPlane=False
bracketPram8.Mold="-"
bracketPram8.Thickness="7.9999999999999964"
bracketPram8.BracketType=1501
bracketPram8.Scallop1Type=1801
bracketPram8.Scallop1Params=["0"]
bracketPram8.Scallop2Type=0
bracketPram8.Surfaces1=[profile32[0]+",FL"]
bracketPram8.RevSf1=False
bracketPram8.Surfaces2=[profile33[0]+",FL"]
bracketPram8.RevSf2=False
bracketPram8.RevSf3=False
bracketPram8.Sf1DimensionType=1531
bracketPram8.Sf1DimensonParams=["250","15"]
bracketPram8.Sf2DimensionType=1531
bracketPram8.Sf2DimensonParams=["250","15"]
bracket8 = part.CreateBracket(bracketPram8,False)
part.SetElementColor(bracket8,"0","255","255","0.19999998807907104")
mirror_copied8 = part.MirrorCopy([bracket8],"PL,Y","")
part.SetElementColor(mirror_copied8[0],"0","255","255","0.19999998807907104")
ProfilePram56 = part.CreateProfileParam()
ProfilePram56.DefinitionType=1
ProfilePram56.BasePlane="PL,O,"+var_elm12+","+"PL,X"
ProfilePram56.AddAttachSurfaces(extrude_sheet4)
ProfilePram56.ProfileName="HK.Casing.Wall.Side.FR08.BCP"
ProfilePram56.MaterialName="SS400"
ProfilePram56.ProfileType=1002
ProfilePram56.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram56.Mold="+"
ProfilePram56.ReverseDir=False
ProfilePram56.ReverseAngle=True
ProfilePram56.CalcSnipOnlyAttachLines=False
ProfilePram56.AttachDirMethod=0
ProfilePram56.CCWDefAngle=False
ProfilePram56.AddEnd1Elements(extrude_sheet6)
ProfilePram56.End1Type=1102
ProfilePram56.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram56.AddEnd2Elements(extrude_sheet1)
ProfilePram56.End2Type=1102
ProfilePram56.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram56.End1ScallopType=1121
ProfilePram56.End1ScallopTypeParams=["35","40"]
ProfilePram56.End2ScallopType=1121
ProfilePram56.End2ScallopTypeParams=["35","40"]
profile56 = part.CreateProfile(ProfilePram56,False)
part.SetElementColor(profile56[0],"255","0","0","0.19999998807907104")
bracketPram9 = part.CreateBracketParam()
bracketPram9.DefinitionType=1
bracketPram9.BracketName="HK.Casing.Wall.Side.FR08.Deck.CP"
bracketPram9.MaterialName="SS400"
bracketPram9.BaseElement=profile56[0]
bracketPram9.UseSideSheetForPlane=False
bracketPram9.Mold="+"
bracketPram9.Thickness="9.9999999999999982"
bracketPram9.BracketType=1505
bracketPram9.BracketParams=["200"]
bracketPram9.Scallop1Type=1801
bracketPram9.Scallop1Params=["0"]
bracketPram9.Scallop2Type=0
bracketPram9.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram9.RevSf1=False
bracketPram9.Surfaces2=[profile56[0]+",FL"]
bracketPram9.RevSf2=False
bracketPram9.RevSf3=False
bracketPram9.Sf1DimensionType=1541
bracketPram9.Sf1DimensonParams=["0","100"]
bracketPram9.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile22[0]]
bracketPram9.Sf2DimensionType=1531
bracketPram9.Sf2DimensonParams=["200","15"]
bracket9 = part.CreateBracket(bracketPram9,False)
part.SetElementColor(bracket9,"0","255","255","0.19999998807907104")
mirror_copied9 = part.MirrorCopy([bracket4],"PL,Y","")
part.SetElementColor(mirror_copied9[0],"0","255","255","0.19999998807907104")
ProfilePram57 = part.CreateProfileParam()
ProfilePram57.DefinitionType=1
ProfilePram57.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram57.AddAttachSurfaces(extrude_sheet5)
ProfilePram57.ProfileName="HK.Casing.Wall.Fore.DL03.BCP"
ProfilePram57.MaterialName="SS400"
ProfilePram57.ProfileType=1002
ProfilePram57.ProfileParams=["125","75","7","10","5"]
ProfilePram57.Mold="+"
ProfilePram57.ReverseDir=True
ProfilePram57.ReverseAngle=True
ProfilePram57.CalcSnipOnlyAttachLines=False
ProfilePram57.AttachDirMethod=0
ProfilePram57.CCWDefAngle=False
ProfilePram57.AddEnd1Elements(extrude_sheet6)
ProfilePram57.End1Type=1102
ProfilePram57.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram57.AddEnd2Elements(extrude_sheet1)
ProfilePram57.End2Type=1102
ProfilePram57.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram57.End1ScallopType=1121
ProfilePram57.End1ScallopTypeParams=["25","40"]
ProfilePram57.End2ScallopType=1121
ProfilePram57.End2ScallopTypeParams=["25","40"]
profile57 = part.CreateProfile(ProfilePram57,False)
part.SetElementColor(profile57[0],"255","0","0","0.19999998807907104")
ProfilePram58 = part.CreateProfileParam()
ProfilePram58.DefinitionType=1
ProfilePram58.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram58.AddAttachSurfaces(extrude_sheet6)
ProfilePram58.ProfileName="HK.Casing.Deck.C.DL03.FP"
ProfilePram58.MaterialName="SS400"
ProfilePram58.ProfileType=1002
ProfilePram58.ProfileParams=["125","75","7","10","5"]
ProfilePram58.Mold="+"
ProfilePram58.ReverseDir=True
ProfilePram58.ReverseAngle=True
ProfilePram58.CalcSnipOnlyAttachLines=False
ProfilePram58.AttachDirMethod=0
ProfilePram58.CCWDefAngle=False
ProfilePram58.AddEnd1Elements(profile10[0])
ProfilePram58.End1Type=1102
ProfilePram58.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram58.AddEnd2Elements(profile57[0])
ProfilePram58.End2Type=1102
ProfilePram58.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram58.End1ScallopType=1121
ProfilePram58.End1ScallopTypeParams=["25","40"]
ProfilePram58.End2ScallopType=1121
ProfilePram58.End2ScallopTypeParams=["25","40"]
profile58 = part.CreateProfile(ProfilePram58,False)
part.SetElementColor(profile58[0],"255","0","0","0.19999998807907104")
bracketPram10 = part.CreateBracketParam()
bracketPram10.DefinitionType=1
bracketPram10.BracketName="HK.Casing.Wall.Fore.DL03.Deck.CP"
bracketPram10.MaterialName="SS400"
bracketPram10.BaseElement=profile57[0]
bracketPram10.UseSideSheetForPlane=False
bracketPram10.Mold="+"
bracketPram10.Thickness="7.9999999999999964"
bracketPram10.BracketType=1501
bracketPram10.Scallop1Type=1801
bracketPram10.Scallop1Params=["0"]
bracketPram10.Scallop2Type=0
bracketPram10.Surfaces1=[profile57[0]+",FL"]
bracketPram10.RevSf1=False
bracketPram10.Surfaces2=[profile58[0]+",FL"]
bracketPram10.RevSf2=False
bracketPram10.RevSf3=False
bracketPram10.Sf1DimensionType=1531
bracketPram10.Sf1DimensonParams=["200","15"]
bracketPram10.Sf2DimensionType=1531
bracketPram10.Sf2DimensonParams=["200","15"]
bracket10 = part.CreateBracket(bracketPram10,False)
part.SetElementColor(bracket10,"0","255","255","0.19999998807907104")
bracketPram11 = part.CreateBracketParam()
bracketPram11.DefinitionType=1
bracketPram11.BracketName="HK.Casing.Deck.D.FR13P"
bracketPram11.MaterialName="SS400"
bracketPram11.BaseElement=profile45[0]
bracketPram11.UseSideSheetForPlane=False
bracketPram11.Mold="+"
bracketPram11.Thickness="8.9999999999999982"
bracketPram11.BracketType=1501
bracketPram11.Scallop1Type=1801
bracketPram11.Scallop1Params=["50"]
bracketPram11.Scallop2Type=0
bracketPram11.Surfaces1=[profile16[0]+",WF"]
bracketPram11.RevSf1=False
bracketPram11.Surfaces2=[profile45[0]+",FL"]
bracketPram11.RevSf2=False
bracketPram11.RevSf3=False
bracketPram11.FlangeType=262
bracketPram11.FlangeParams=["75","30","29.999999999999996","30","50","1"]
bracketPram11.RevFlange=False
bracketPram11.Sf1DimensionType=1541
bracketPram11.Sf1DimensonParams=["0","80"]
bracketPram11.Sf1EndElements=[profile16[1]+",FR"]
bracketPram11.Sf2DimensionType=1531
bracketPram11.Sf2DimensonParams=["300","15"]
bracket11 = part.CreateBracket(bracketPram11,False)
part.SetElementColor(bracket11,"0","255","255","0.19999998807907104")
ProfilePram59 = part.CreateProfileParam()
ProfilePram59.DefinitionType=1
ProfilePram59.BasePlane="PL,O,"+var_elm12+","+"PL,X"
ProfilePram59.AddAttachSurfaces(extrude_sheet4)
ProfilePram59.ProfileName="HK.Casing.Wall.Side.FR08.OAP"
ProfilePram59.MaterialName="SS400"
ProfilePram59.ProfileType=1002
ProfilePram59.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram59.Mold="+"
ProfilePram59.ReverseDir=False
ProfilePram59.ReverseAngle=True
ProfilePram59.CalcSnipOnlyAttachLines=False
ProfilePram59.AttachDirMethod=0
ProfilePram59.CCWDefAngle=False
ProfilePram59.AddEnd1Elements(extrude_sheet2)
ProfilePram59.End1Type=1102
ProfilePram59.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram59.AddEnd2Elements(extrude_sheet8)
ProfilePram59.End2Type=1102
ProfilePram59.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram59.End1ScallopType=1121
ProfilePram59.End1ScallopTypeParams=["35","40"]
ProfilePram59.End2ScallopType=1121
ProfilePram59.End2ScallopTypeParams=["35","40"]
profile59 = part.CreateProfile(ProfilePram59,False)
part.SetElementColor(profile59[0],"255","0","0","0.19999998807907104")
ProfilePram60 = part.CreateProfileParam()
ProfilePram60.DefinitionType=1
ProfilePram60.BasePlane="PL,O,"+var_elm9+","+"PL,X"
ProfilePram60.AddAttachSurfaces(extrude_sheet4)
ProfilePram60.ProfileName="HK.Casing.Wall.Side.FR09.OAP"
ProfilePram60.MaterialName="SS400"
ProfilePram60.ProfileType=1003
ProfilePram60.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram60.Mold="+"
ProfilePram60.ReverseDir=False
ProfilePram60.ReverseAngle=True
ProfilePram60.CalcSnipOnlyAttachLines=False
ProfilePram60.AttachDirMethod=0
ProfilePram60.CCWDefAngle=False
ProfilePram60.AddEnd1Elements(extrude_sheet2)
ProfilePram60.End1Type=1103
ProfilePram60.End1TypeParams=["0"]
ProfilePram60.AddEnd2Elements(extrude_sheet8)
ProfilePram60.End2Type=1103
ProfilePram60.End2TypeParams=["0"]
ProfilePram60.End1ScallopType=1120
ProfilePram60.End1ScallopTypeParams=["50"]
ProfilePram60.End2ScallopType=1120
ProfilePram60.End2ScallopTypeParams=["50"]
profile60 = part.CreateProfile(ProfilePram60,False)
part.SetElementColor(profile60[0],"148","0","211","0.39999997615814209")
mirror_copied10 = part.MirrorCopy([profile60[0]],"PL,Y","")
part.SetElementColor(mirror_copied10[0],"148","0","211","0.39999997615814209")
ProfilePram61 = part.CreateProfileParam()
ProfilePram61.DefinitionType=1
ProfilePram61.BasePlane="PL,O,"+var_elm8+","+"PL,Y"
ProfilePram61.AddAttachSurfaces(extrude_sheet5)
ProfilePram61.ProfileName="HK.Casing.Wall.Fore.DL02.CDP"
ProfilePram61.MaterialName="SS400"
ProfilePram61.FlangeName="HK.Casing.Wall.Fore.DL02.CDP"
ProfilePram61.FlangeMaterialName="SS400"
ProfilePram61.ProfileType=1201
ProfilePram61.ProfileParams=["150","12","388","10"]
ProfilePram61.Mold="-"
ProfilePram61.ReverseDir=True
ProfilePram61.ReverseAngle=False
ProfilePram61.CalcSnipOnlyAttachLines=False
ProfilePram61.AttachDirMethod=0
ProfilePram61.CCWDefAngle=False
ProfilePram61.AddEnd1Elements(profile16[1])
ProfilePram61.End1Type=1102
ProfilePram61.End1TypeParams=["25","14.999999999999998","0","0"]
ProfilePram61.AddEnd2Elements(extrude_sheet6)
ProfilePram61.End2Type=1102
ProfilePram61.End2TypeParams=["25","14.999999999999998","0","0"]
ProfilePram61.End1ScallopType=1120
ProfilePram61.End1ScallopTypeParams=["50"]
ProfilePram61.End2ScallopType=1120
ProfilePram61.End2ScallopTypeParams=["50"]
profile61 = part.CreateProfile(ProfilePram61,False)
part.SetElementColor(profile61[0],"148","0","211","0.39999997615814209")
part.SetElementColor(profile61[1],"148","0","211","0.39999997615814209")
bracketPram12 = part.CreateBracketParam()
bracketPram12.DefinitionType=1
bracketPram12.BracketName="HK.Casing.Wall.Fore.DL02.Deck.DP"
bracketPram12.MaterialName="SS400"
bracketPram12.BaseElement=profile61[0]
bracketPram12.UseSideSheetForPlane=False
bracketPram12.Mold="-"
bracketPram12.Thickness="12"
bracketPram12.BracketType=1501
bracketPram12.Scallop1Type=1801
bracketPram12.Scallop1Params=["50"]
bracketPram12.Scallop2Type=0
bracketPram12.Surfaces1=["PLS","False","False","-1","-0","0",profile61[1]]
bracketPram12.RevSf1=False
bracketPram12.Surfaces2=["PLS","False","False","-0","-0","-1",profile16[1]]
bracketPram12.RevSf2=False
bracketPram12.RevSf3=False
bracketPram12.FlangeType=262
bracketPram12.FlangeParams=["100","30","29.999999999999996","30","30","1"]
bracketPram12.RevFlange=False
bracketPram12.Sf1DimensionType=1531
bracketPram12.Sf1DimensonParams=["800","15"]
bracketPram12.Sf2DimensionType=1531
bracketPram12.Sf2DimensonParams=["800","15"]
bracket12 = part.CreateBracket(bracketPram12,False)
part.SetElementColor(bracket12,"0","255","255","0.19999998807907104")
bracketPram13 = part.CreateBracketParam()
bracketPram13.DefinitionType=1
bracketPram13.BracketName="HK.Casing.Wall.Aft.DL05.Deck.CP"
bracketPram13.MaterialName="SS400"
bracketPram13.BaseElement=profile22[0]
bracketPram13.UseSideSheetForPlane=False
bracketPram13.Mold="+"
bracketPram13.Thickness="7.9999999999999964"
bracketPram13.BracketType=1501
bracketPram13.Scallop1Type=1801
bracketPram13.Scallop1Params=["0"]
bracketPram13.Scallop2Type=0
bracketPram13.Surfaces1=[profile21[0]+",FL"]
bracketPram13.RevSf1=False
bracketPram13.Surfaces2=[profile22[0]+",FL"]
bracketPram13.RevSf2=False
bracketPram13.RevSf3=False
bracketPram13.Sf1DimensionType=1531
bracketPram13.Sf1DimensonParams=["200","15"]
bracketPram13.Sf2DimensionType=1531
bracketPram13.Sf2DimensonParams=["200","15"]
bracket13 = part.CreateBracket(bracketPram13,False)
part.SetElementColor(bracket13,"0","255","255","0.19999998807907104")
ProfilePram62 = part.CreateProfileParam()
ProfilePram62.DefinitionType=1
ProfilePram62.BasePlane="PL,O,"+var_elm16+","+"PL,X"
ProfilePram62.AddAttachSurfaces(extrude_sheet4)
ProfilePram62.ProfileName="HK.Casing.Wall.Side.FR10.OAP"
ProfilePram62.MaterialName="SS400"
ProfilePram62.ProfileType=1002
ProfilePram62.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram62.Mold="+"
ProfilePram62.ReverseDir=False
ProfilePram62.ReverseAngle=True
ProfilePram62.CalcSnipOnlyAttachLines=False
ProfilePram62.AttachDirMethod=0
ProfilePram62.CCWDefAngle=False
ProfilePram62.AddEnd1Elements(extrude_sheet2)
ProfilePram62.End1Type=1102
ProfilePram62.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram62.AddEnd2Elements(extrude_sheet8)
ProfilePram62.End2Type=1102
ProfilePram62.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram62.End1ScallopType=1121
ProfilePram62.End1ScallopTypeParams=["35","40"]
ProfilePram62.End2ScallopType=1121
ProfilePram62.End2ScallopTypeParams=["35","40"]
profile62 = part.CreateProfile(ProfilePram62,False)
part.SetElementColor(profile62[0],"255","0","0","0.19999998807907104")
bracketPram14 = part.CreateBracketParam()
bracketPram14.DefinitionType=1
bracketPram14.BracketName="HK.Casing.Wall.Side.FR10.Deck.AP"
bracketPram14.MaterialName="SS400"
bracketPram14.BaseElement=profile62[0]
bracketPram14.UseSideSheetForPlane=False
bracketPram14.Mold="+"
bracketPram14.Thickness="9.9999999999999982"
bracketPram14.BracketType=1505
bracketPram14.BracketParams=["200"]
bracketPram14.Scallop1Type=1801
bracketPram14.Scallop1Params=["0"]
bracketPram14.Scallop2Type=0
bracketPram14.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram14.RevSf1=False
bracketPram14.Surfaces2=[profile62[0]+",FL"]
bracketPram14.RevSf2=False
bracketPram14.RevSf3=False
bracketPram14.Sf1DimensionType=1541
bracketPram14.Sf1DimensonParams=["0","100"]
bracketPram14.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile51[0]]
bracketPram14.Sf2DimensionType=1531
bracketPram14.Sf2DimensonParams=["200","15"]
bracket14 = part.CreateBracket(bracketPram14,False)
part.SetElementColor(bracket14,"0","255","255","0.19999998807907104")
ProfilePram63 = part.CreateProfileParam()
ProfilePram63.DefinitionType=1
ProfilePram63.BasePlane="PL,O,"+"FR6 + 400 mm"+","+"PL,X"
ProfilePram63.AddAttachSurfaces(extrude_sheet2)
ProfilePram63.ProfileName="HK.Casing.Deck.A.FR06F400"
ProfilePram63.MaterialName="SS400"
ProfilePram63.ProfileType=1007
ProfilePram63.ProfileParams=["150","12"]
ProfilePram63.Mold="+"
ProfilePram63.ReverseDir=True
ProfilePram63.ReverseAngle=False
ProfilePram63.CalcSnipOnlyAttachLines=False
ProfilePram63.AttachDirMethod=0
ProfilePram63.CCWDefAngle=False
ProfilePram63.AddEnd1Elements(mirror_copied7[0])
ProfilePram63.End1Type=1102
ProfilePram63.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram63.AddEnd2Elements(profile43[0])
ProfilePram63.End2Type=1102
ProfilePram63.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram63.End1ScallopType=-1
ProfilePram63.End2ScallopType=-1
profile63 = part.CreateProfile(ProfilePram63,False)
part.SetElementColor(profile63[0],"255","0","0","0.19999998807907104")
ProfilePram64 = part.CreateProfileParam()
ProfilePram64.DefinitionType=1
ProfilePram64.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram64.AddAttachSurfaces(extrude_sheet3)
ProfilePram64.ProfileName="HK.Casing.Wall.Aft.DL03.BCP"
ProfilePram64.MaterialName="SS400"
ProfilePram64.ProfileType=1002
ProfilePram64.ProfileParams=["125","75","7","10","5"]
ProfilePram64.Mold="+"
ProfilePram64.ReverseDir=False
ProfilePram64.ReverseAngle=True
ProfilePram64.CalcSnipOnlyAttachLines=False
ProfilePram64.AttachDirMethod=0
ProfilePram64.CCWDefAngle=False
ProfilePram64.AddEnd1Elements(extrude_sheet6)
ProfilePram64.End1Type=1102
ProfilePram64.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram64.AddEnd2Elements(extrude_sheet1)
ProfilePram64.End2Type=1102
ProfilePram64.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram64.End1ScallopType=1121
ProfilePram64.End1ScallopTypeParams=["25","40"]
ProfilePram64.End2ScallopType=1121
ProfilePram64.End2ScallopTypeParams=["25","40"]
profile64 = part.CreateProfile(ProfilePram64,False)
part.SetElementColor(profile64[0],"255","0","0","0.19999998807907104")
ProfilePram65 = part.CreateProfileParam()
ProfilePram65.DefinitionType=1
ProfilePram65.BasePlane="PL,O,"+var_elm15+","+"PL,X"
ProfilePram65.AddAttachSurfaces(extrude_sheet7)
ProfilePram65.ProfileName="HK.Casing.Deck.D.FR13C"
ProfilePram65.MaterialName="SS400"
ProfilePram65.ProfileType=1003
ProfilePram65.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram65.Mold="+"
ProfilePram65.ReverseDir=True
ProfilePram65.ReverseAngle=False
ProfilePram65.CalcSnipOnlyAttachLines=False
ProfilePram65.AttachDirMethod=0
ProfilePram65.CCWDefAngle=False
ProfilePram65.AddEnd1Elements(mirror_copied2[0])
ProfilePram65.End1Type=1102
ProfilePram65.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram65.AddEnd2Elements(profile16[0])
ProfilePram65.End2Type=1102
ProfilePram65.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram65.End1ScallopType=1120
ProfilePram65.End1ScallopTypeParams=["50"]
ProfilePram65.End2ScallopType=1120
ProfilePram65.End2ScallopTypeParams=["50"]
profile65 = part.CreateProfile(ProfilePram65,False)
part.SetElementColor(profile65[0],"148","0","211","0.39999997615814209")
ProfilePram66 = part.CreateProfileParam()
ProfilePram66.DefinitionType=1
ProfilePram66.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram66.AddAttachSurfaces(extrude_sheet7)
ProfilePram66.ProfileName="HK.Casing.Deck.D.DL01.FP"
ProfilePram66.MaterialName="SS400"
ProfilePram66.ProfileType=1002
ProfilePram66.ProfileParams=["125","75","7","10","5"]
ProfilePram66.Mold="+"
ProfilePram66.ReverseDir=True
ProfilePram66.ReverseAngle=True
ProfilePram66.CalcSnipOnlyAttachLines=False
ProfilePram66.AttachDirMethod=0
ProfilePram66.CCWDefAngle=False
ProfilePram66.AddEnd1Elements(profile65[0])
ProfilePram66.End1Type=1102
ProfilePram66.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram66.AddEnd2Elements(extrude_sheet5)
ProfilePram66.End2Type=1102
ProfilePram66.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram66.End1ScallopType=1121
ProfilePram66.End1ScallopTypeParams=["25","40"]
ProfilePram66.End2ScallopType=1121
ProfilePram66.End2ScallopTypeParams=["25","40"]
profile66 = part.CreateProfile(ProfilePram66,False)
part.SetElementColor(profile66[0],"255","0","0","0.19999998807907104")
ProfilePram67 = part.CreateProfileParam()
ProfilePram67.DefinitionType=1
ProfilePram67.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram67.AddAttachSurfaces(extrude_sheet5)
ProfilePram67.ProfileName="HK.Casing.Wall.Fore.DL01.CDP"
ProfilePram67.MaterialName="SS400"
ProfilePram67.ProfileType=1002
ProfilePram67.ProfileParams=["125","75","7","10","5"]
ProfilePram67.Mold="+"
ProfilePram67.ReverseDir=True
ProfilePram67.ReverseAngle=True
ProfilePram67.CalcSnipOnlyAttachLines=False
ProfilePram67.AttachDirMethod=0
ProfilePram67.CCWDefAngle=False
ProfilePram67.AddEnd1Elements(profile66[0])
ProfilePram67.End1Type=1102
ProfilePram67.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram67.AddEnd2Elements(extrude_sheet6)
ProfilePram67.End2Type=1102
ProfilePram67.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram67.End1ScallopType=1120
ProfilePram67.End1ScallopTypeParams=["50"]
ProfilePram67.End2ScallopType=1120
ProfilePram67.End2ScallopTypeParams=["50"]
profile67 = part.CreateProfile(ProfilePram67,False)
part.SetElementColor(profile67[0],"255","0","0","0.19999998807907104")
extrudePram17 = part.CreateLinearSweepParam()
extrudePram17.AddProfile(skt_pl2+",Casing.Side.S")
extrudePram17.DirectionType=2
extrudePram17.DirectionParameter1="50000"
extrudePram17.DirectionParameter2="10000"
extrudePram17.SweepDirection="+Z"
extrudePram17.Name="HK.Casing.Wall.SideS"
extrudePram17.MaterialName="SS400"
extrudePram17.IntervalSweep=False
extrude_sheet9 = part.CreateLinearSweepSheet(extrudePram17,False)
part.SheetAlignNormal(extrude_sheet9,0,-1,0)
part.BlankElement(extrude_sheet9,True)
part.SetElementColor(extrude_sheet9,"225","225","225","1")
ProfilePram68 = part.CreateProfileParam()
ProfilePram68.DefinitionType=1
ProfilePram68.BasePlane="PL,O,"+var_elm9+","+"PL,X"
ProfilePram68.AddAttachSurfaces(extrude_sheet7)
ProfilePram68.ProfileName="HK.Casing.Deck.D.FR09P"
ProfilePram68.MaterialName="SS400"
ProfilePram68.ProfileType=1003
ProfilePram68.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram68.Mold="+"
ProfilePram68.ReverseDir=True
ProfilePram68.ReverseAngle=False
ProfilePram68.CalcSnipOnlyAttachLines=False
ProfilePram68.AttachDirMethod=0
ProfilePram68.CCWDefAngle=False
ProfilePram68.AddEnd1Elements(profile16[0])
ProfilePram68.End1Type=1102
ProfilePram68.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram68.AddEnd2Elements(extrude_sheet4)
ProfilePram68.End2Type=1102
ProfilePram68.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram68.End1ScallopType=1120
ProfilePram68.End1ScallopTypeParams=["50"]
ProfilePram68.End2ScallopType=1120
ProfilePram68.End2ScallopTypeParams=["50"]
profile68 = part.CreateProfile(ProfilePram68,False)
part.SetElementColor(profile68[0],"148","0","211","0.39999997615814209")
solid5 = part.CreateSolid("HK.Casing.Wall.Aft.CD","","SS400")
part.SetElementColor(solid5,"139","69","19","0.79999995231628418")
thicken5 = part.CreateThicken("厚み付け11",solid5,"+",[extrude_sheet3],"-","10","0","0",False,False)
extrudePram18 = part.CreateLinearSweepParam()
extrudePram18.Name="積-押し出し19"
extrudePram18.AddProfile(extrude_sheet4)
extrudePram18.DirectionType="R"
extrudePram18.DirectionParameter1="50000"
extrudePram18.SweepDirection="+Y"
extrudePram18.RefByGeometricMethod=True
extrude9 = part.CreateLinearSweep(solid5,"*",extrudePram18,False)
ProfilePram69 = part.CreateProfileParam()
ProfilePram69.DefinitionType=1
ProfilePram69.BasePlane="PL,O,"+var_elm9+","+"PL,X"
ProfilePram69.AddAttachSurfaces(extrude_sheet4)
ProfilePram69.ProfileName="HK.Casing.Wall.Side.FR09.CDP"
ProfilePram69.MaterialName="SS400"
ProfilePram69.ProfileType=1003
ProfilePram69.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram69.Mold="+"
ProfilePram69.ReverseDir=False
ProfilePram69.ReverseAngle=True
ProfilePram69.CalcSnipOnlyAttachLines=False
ProfilePram69.AttachDirMethod=0
ProfilePram69.CCWDefAngle=False
ProfilePram69.AddEnd1Elements(profile68[0])
ProfilePram69.End1Type=1102
ProfilePram69.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram69.AddEnd2Elements(extrude_sheet6)
ProfilePram69.End2Type=1103
ProfilePram69.End2TypeParams=["0"]
ProfilePram69.End1ScallopType=1120
ProfilePram69.End1ScallopTypeParams=["50"]
ProfilePram69.End2ScallopType=1120
ProfilePram69.End2ScallopTypeParams=["50"]
profile69 = part.CreateProfile(ProfilePram69,False)
part.SetElementColor(profile69[0],"148","0","211","0.39999997615814209")
bracketPram15 = part.CreateBracketParam()
bracketPram15.DefinitionType=1
bracketPram15.BracketName="HK.Casing.Wall.Side.FR09.Deck.DP"
bracketPram15.MaterialName="SS400"
bracketPram15.BaseElement=profile69[0]
bracketPram15.UseSideSheetForPlane=False
bracketPram15.Mold="+"
bracketPram15.Thickness="7.9999999999999964"
bracketPram15.BracketType=1501
bracketPram15.Scallop1Type=1801
bracketPram15.Scallop1Params=["0"]
bracketPram15.Scallop2Type=0
bracketPram15.Surfaces1=[profile69[0]+",FL"]
bracketPram15.RevSf1=False
bracketPram15.Surfaces2=[profile68[0]+",FL"]
bracketPram15.RevSf2=False
bracketPram15.RevSf3=False
bracketPram15.Sf1DimensionType=1531
bracketPram15.Sf1DimensonParams=["250","15"]
bracketPram15.Sf2DimensionType=1531
bracketPram15.Sf2DimensonParams=["250","15"]
bracket15 = part.CreateBracket(bracketPram15,False)
part.SetElementColor(bracket15,"0","255","255","0.19999998807907104")
ProfilePram70 = part.CreateProfileParam()
ProfilePram70.DefinitionType=1
ProfilePram70.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram70.AddAttachSurfaces(extrude_sheet5)
ProfilePram70.ProfileName="HK.Casing.Wall.Fore.DL01.ABP"
ProfilePram70.MaterialName="SS400"
ProfilePram70.ProfileType=1002
ProfilePram70.ProfileParams=["125","75","7","10","5"]
ProfilePram70.Mold="+"
ProfilePram70.ReverseDir=True
ProfilePram70.ReverseAngle=True
ProfilePram70.CalcSnipOnlyAttachLines=False
ProfilePram70.AttachDirMethod=0
ProfilePram70.CCWDefAngle=False
ProfilePram70.AddEnd1Elements(extrude_sheet1)
ProfilePram70.End1Type=1102
ProfilePram70.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram70.AddEnd2Elements(extrude_sheet2)
ProfilePram70.End2Type=1102
ProfilePram70.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram70.End1ScallopType=1121
ProfilePram70.End1ScallopTypeParams=["25","40"]
ProfilePram70.End2ScallopType=1121
ProfilePram70.End2ScallopTypeParams=["25","40"]
profile70 = part.CreateProfile(ProfilePram70,False)
part.SetElementColor(profile70[0],"255","0","0","0.19999998807907104")
ProfilePram71 = part.CreateProfileParam()
ProfilePram71.DefinitionType=1
ProfilePram71.BasePlane="PL,O,"+"FR14 + 415 mm"+","+"PL,X"
ProfilePram71.AddAttachSurfaces(extrude_sheet1)
ProfilePram71.ProfileName="HK.Casing.Deck.B.FR14F415"
ProfilePram71.MaterialName="SS400"
ProfilePram71.ProfileType=1003
ProfilePram71.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram71.Mold="+"
ProfilePram71.ReverseDir=True
ProfilePram71.ReverseAngle=True
ProfilePram71.CalcSnipOnlyAttachLines=False
ProfilePram71.AttachDirMethod=0
ProfilePram71.CCWDefAngle=False
ProfilePram71.AddEnd1Elements(mirror_copied5[0])
ProfilePram71.End1Type=1111
ProfilePram71.End1TypeParams=["0","35","50","50","25","29.999999999999996","0"]
ProfilePram71.AddEnd2Elements(profile33[0])
ProfilePram71.End2Type=1111
ProfilePram71.End2TypeParams=["0","35","50","50","25","29.999999999999996","0"]
ProfilePram71.End1ScallopType=1120
ProfilePram71.End1ScallopTypeParams=["50"]
ProfilePram71.End2ScallopType=1120
ProfilePram71.End2ScallopTypeParams=["50"]
profile71 = part.CreateProfile(ProfilePram71,False)
part.SetElementColor(profile71[0],"255","0","0","0.19999998807907104")
ProfilePram72 = part.CreateProfileParam()
ProfilePram72.DefinitionType=1
ProfilePram72.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram72.AddAttachSurfaces(extrude_sheet1)
ProfilePram72.ProfileName="HK.Casing.Deck.B.DL01.FP"
ProfilePram72.MaterialName="SS400"
ProfilePram72.ProfileType=1002
ProfilePram72.ProfileParams=["125","75","7","10","5"]
ProfilePram72.Mold="+"
ProfilePram72.ReverseDir=True
ProfilePram72.ReverseAngle=True
ProfilePram72.CalcSnipOnlyAttachLines=False
ProfilePram72.AttachDirMethod=0
ProfilePram72.CCWDefAngle=False
ProfilePram72.AddEnd1Elements(profile71[0])
ProfilePram72.End1Type=1102
ProfilePram72.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram72.AddEnd2Elements(profile70[0])
ProfilePram72.End2Type=1102
ProfilePram72.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram72.End1ScallopType=1121
ProfilePram72.End1ScallopTypeParams=["25","40"]
ProfilePram72.End2ScallopType=1121
ProfilePram72.End2ScallopTypeParams=["25","40"]
profile72 = part.CreateProfile(ProfilePram72,False)
part.SetElementColor(profile72[0],"255","0","0","0.19999998807907104")
mirror_copied11 = part.MirrorCopy([profile64[0]],"PL,Y","")
part.SetElementColor(mirror_copied11[0],"255","0","0","0.19999998807907104")
mirror_copied12 = part.MirrorCopy([profile41[0]],"PL,Y","")
part.SetElementColor(mirror_copied12[0],"148","0","211","0.39999997615814209")
ProfilePram73 = part.CreateProfileParam()
ProfilePram73.DefinitionType=1
ProfilePram73.BasePlane="PL,O,"+var_elm3+","+"PL,Y"
ProfilePram73.AddAttachSurfaces(extrude_sheet3)
ProfilePram73.ProfileName="HK.Casing.Wall.Aft.DL05.CDP"
ProfilePram73.MaterialName="SS400"
ProfilePram73.ProfileType=1002
ProfilePram73.ProfileParams=["125","75","7","10","5"]
ProfilePram73.Mold="+"
ProfilePram73.ReverseDir=False
ProfilePram73.ReverseAngle=True
ProfilePram73.CalcSnipOnlyAttachLines=False
ProfilePram73.AttachDirMethod=0
ProfilePram73.CCWDefAngle=False
ProfilePram73.AddEnd1Elements(profile15[0])
ProfilePram73.End1Type=1102
ProfilePram73.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram73.AddEnd2Elements(extrude_sheet6)
ProfilePram73.End2Type=1102
ProfilePram73.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram73.End1ScallopType=1120
ProfilePram73.End1ScallopTypeParams=["50"]
ProfilePram73.End2ScallopType=1120
ProfilePram73.End2ScallopTypeParams=["50"]
profile73 = part.CreateProfile(ProfilePram73,False)
part.SetElementColor(profile73[0],"255","0","0","0.19999998807907104")
bracketPram16 = part.CreateBracketParam()
bracketPram16.DefinitionType=1
bracketPram16.BracketName="HK.Casing.Wall.Aft.DL05.Deck.AP"
bracketPram16.MaterialName="SS400"
bracketPram16.BaseElement=profile51[0]
bracketPram16.UseSideSheetForPlane=False
bracketPram16.Mold="+"
bracketPram16.Thickness="7.9999999999999964"
bracketPram16.BracketType=1501
bracketPram16.Scallop1Type=1801
bracketPram16.Scallop1Params=["0"]
bracketPram16.Scallop2Type=0
bracketPram16.Surfaces1=[profile49[0]+",FL"]
bracketPram16.RevSf1=False
bracketPram16.Surfaces2=[profile51[0]+",FL"]
bracketPram16.RevSf2=False
bracketPram16.RevSf3=False
bracketPram16.Sf1DimensionType=1531
bracketPram16.Sf1DimensonParams=["200","15"]
bracketPram16.Sf2DimensionType=1531
bracketPram16.Sf2DimensonParams=["200","15"]
bracket16 = part.CreateBracket(bracketPram16,False)
part.SetElementColor(bracket16,"0","255","255","0.19999998807907104")
ProfilePram74 = part.CreateProfileParam()
ProfilePram74.DefinitionType=1
ProfilePram74.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram74.AddAttachSurfaces(extrude_sheet5)
ProfilePram74.ProfileName="HK.Casing.Wall.Fore.DL00.BC"
ProfilePram74.MaterialName="SS400"
ProfilePram74.ProfileType=1002
ProfilePram74.ProfileParams=["125","75","7","10","5"]
ProfilePram74.ReverseDir=True
ProfilePram74.ReverseAngle=True
ProfilePram74.CalcSnipOnlyAttachLines=False
ProfilePram74.AttachDirMethod=0
ProfilePram74.CCWDefAngle=False
ProfilePram74.AddEnd1Elements(extrude_sheet6)
ProfilePram74.End1Type=1102
ProfilePram74.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram74.AddEnd2Elements(extrude_sheet1)
ProfilePram74.End2Type=1102
ProfilePram74.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram74.End1ScallopType=1121
ProfilePram74.End1ScallopTypeParams=["25","40"]
ProfilePram74.End2ScallopType=1121
ProfilePram74.End2ScallopTypeParams=["25","40"]
profile74 = part.CreateProfile(ProfilePram74,False)
part.SetElementColor(profile74[0],"255","0","0","0.19999998807907104")
ProfilePram75 = part.CreateProfileParam()
ProfilePram75.DefinitionType=1
ProfilePram75.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram75.AddAttachSurfaces(extrude_sheet6)
ProfilePram75.ProfileName="HK.Casing.Deck.C.DL00.F"
ProfilePram75.MaterialName="SS400"
ProfilePram75.ProfileType=1002
ProfilePram75.ProfileParams=["125","75","7","10","5"]
ProfilePram75.ReverseDir=True
ProfilePram75.ReverseAngle=True
ProfilePram75.CalcSnipOnlyAttachLines=False
ProfilePram75.AttachDirMethod=0
ProfilePram75.CCWDefAngle=False
ProfilePram75.AddEnd1Elements(profile10[0])
ProfilePram75.End1Type=1102
ProfilePram75.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram75.AddEnd2Elements(profile74[0])
ProfilePram75.End2Type=1102
ProfilePram75.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram75.End1ScallopType=1121
ProfilePram75.End1ScallopTypeParams=["25","40"]
ProfilePram75.End2ScallopType=1121
ProfilePram75.End2ScallopTypeParams=["25","40"]
profile75 = part.CreateProfile(ProfilePram75,False)
part.SetElementColor(profile75[0],"255","0","0","0.19999998807907104")
ProfilePram76 = part.CreateProfileParam()
ProfilePram76.DefinitionType=1
ProfilePram76.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram76.AddAttachSurfaces(extrude_sheet3)
ProfilePram76.ProfileName="HK.Casing.Wall.Aft.DL01.CDP"
ProfilePram76.MaterialName="SS400"
ProfilePram76.ProfileType=1002
ProfilePram76.ProfileParams=["125","75","7","10","5"]
ProfilePram76.Mold="+"
ProfilePram76.ReverseDir=False
ProfilePram76.ReverseAngle=True
ProfilePram76.CalcSnipOnlyAttachLines=False
ProfilePram76.AttachDirMethod=0
ProfilePram76.CCWDefAngle=False
ProfilePram76.AddEnd1Elements(profile30[0])
ProfilePram76.End1Type=1102
ProfilePram76.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram76.AddEnd2Elements(extrude_sheet6)
ProfilePram76.End2Type=1102
ProfilePram76.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram76.End1ScallopType=1120
ProfilePram76.End1ScallopTypeParams=["50"]
ProfilePram76.End2ScallopType=1120
ProfilePram76.End2ScallopTypeParams=["50"]
profile76 = part.CreateProfile(ProfilePram76,False)
part.SetElementColor(profile76[0],"255","0","0","0.19999998807907104")
ProfilePram77 = part.CreateProfileParam()
ProfilePram77.DefinitionType=1
ProfilePram77.BasePlane="PL,O,"+var_elm15+","+"PL,X"
ProfilePram77.AddAttachSurfaces(extrude_sheet4)
ProfilePram77.ProfileName="HK.Casing.Wall.Side.FR13.ABP"
ProfilePram77.MaterialName="SS400"
ProfilePram77.ProfileType=1003
ProfilePram77.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram77.Mold="+"
ProfilePram77.ReverseDir=False
ProfilePram77.ReverseAngle=True
ProfilePram77.CalcSnipOnlyAttachLines=False
ProfilePram77.AttachDirMethod=0
ProfilePram77.CCWDefAngle=False
ProfilePram77.AddEnd1Elements(extrude_sheet1)
ProfilePram77.End1Type=1103
ProfilePram77.End1TypeParams=["0"]
ProfilePram77.AddEnd2Elements(extrude_sheet2)
ProfilePram77.End2Type=1103
ProfilePram77.End2TypeParams=["0"]
ProfilePram77.End1ScallopType=1120
ProfilePram77.End1ScallopTypeParams=["50"]
ProfilePram77.End2ScallopType=1120
ProfilePram77.End2ScallopTypeParams=["50"]
profile77 = part.CreateProfile(ProfilePram77,False)
part.SetElementColor(profile77[0],"148","0","211","0.39999997615814209")
ProfilePram78 = part.CreateProfileParam()
ProfilePram78.DefinitionType=1
ProfilePram78.BasePlane="PL,O,"+var_elm15+","+"PL,X"
ProfilePram78.AddAttachSurfaces(extrude_sheet1)
ProfilePram78.ProfileName="HK.Casing.Deck.B.FR13P"
ProfilePram78.MaterialName="SS400"
ProfilePram78.ProfileType=1003
ProfilePram78.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram78.Mold="+"
ProfilePram78.ReverseDir=True
ProfilePram78.ReverseAngle=False
ProfilePram78.CalcSnipOnlyAttachLines=False
ProfilePram78.AttachDirMethod=0
ProfilePram78.CCWDefAngle=False
ProfilePram78.AddEnd1Elements(profile33[0])
ProfilePram78.End1Type=1113
ProfilePram78.End1TypeParams=["0","79"]
ProfilePram78.AddEnd2Elements(profile77[0])
ProfilePram78.End2Type=1102
ProfilePram78.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram78.End1ScallopType=1120
ProfilePram78.End1ScallopTypeParams=["50"]
ProfilePram78.End2ScallopType=1120
ProfilePram78.End2ScallopTypeParams=["50"]
profile78 = part.CreateProfile(ProfilePram78,False)
part.SetElementColor(profile78[0],"148","0","211","0.39999997615814209")
bracketPram17 = part.CreateBracketParam()
bracketPram17.DefinitionType=1
bracketPram17.BracketName="HK.Casing.Wall.Side.FR13.Deck.BP"
bracketPram17.MaterialName="SS400"
bracketPram17.BaseElement=profile78[0]
bracketPram17.UseSideSheetForPlane=False
bracketPram17.Mold="+"
bracketPram17.Thickness="7.9999999999999964"
bracketPram17.BracketType=1501
bracketPram17.Scallop1Type=1801
bracketPram17.Scallop1Params=["0"]
bracketPram17.Scallop2Type=0
bracketPram17.Surfaces1=[profile77[0]+",FL"]
bracketPram17.RevSf1=False
bracketPram17.Surfaces2=[profile78[0]+",FL"]
bracketPram17.RevSf2=False
bracketPram17.RevSf3=False
bracketPram17.Sf1DimensionType=1531
bracketPram17.Sf1DimensonParams=["250","15"]
bracketPram17.Sf2DimensionType=1531
bracketPram17.Sf2DimensonParams=["250","15"]
bracket17 = part.CreateBracket(bracketPram17,False)
part.SetElementColor(bracket17,"0","255","255","0.19999998807907104")
ProfilePram79 = part.CreateProfileParam()
ProfilePram79.DefinitionType=1
ProfilePram79.BasePlane="PL,O,"+var_elm7+","+"PL,X"
ProfilePram79.AddAttachSurfaces(extrude_sheet4)
ProfilePram79.ProfileName="HK.Casing.Wall.Side.FR12.BCP"
ProfilePram79.MaterialName="SS400"
ProfilePram79.ProfileType=1002
ProfilePram79.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram79.Mold="+"
ProfilePram79.ReverseDir=False
ProfilePram79.ReverseAngle=True
ProfilePram79.CalcSnipOnlyAttachLines=False
ProfilePram79.AttachDirMethod=0
ProfilePram79.CCWDefAngle=False
ProfilePram79.AddEnd1Elements(extrude_sheet6)
ProfilePram79.End1Type=1102
ProfilePram79.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram79.AddEnd2Elements(extrude_sheet1)
ProfilePram79.End2Type=1102
ProfilePram79.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram79.End1ScallopType=1121
ProfilePram79.End1ScallopTypeParams=["35","40"]
ProfilePram79.End2ScallopType=1121
ProfilePram79.End2ScallopTypeParams=["35","40"]
profile79 = part.CreateProfile(ProfilePram79,False)
part.SetElementColor(profile79[0],"255","0","0","0.19999998807907104")
bracketPram18 = part.CreateBracketParam()
bracketPram18.DefinitionType=1
bracketPram18.BracketName="HK.Casing.Wall.Side.FR12.Deck.DP"
bracketPram18.MaterialName="SS400"
bracketPram18.BaseElement=profile14[0]
bracketPram18.UseSideSheetForPlane=False
bracketPram18.Mold="+"
bracketPram18.Thickness="9.9999999999999982"
bracketPram18.BracketType=1505
bracketPram18.BracketParams=["200"]
bracketPram18.Scallop1Type=1801
bracketPram18.Scallop1Params=["0"]
bracketPram18.Scallop2Type=0
bracketPram18.Surfaces1=["PLS","False","False","0","-0","-1",solid2]
bracketPram18.RevSf1=False
bracketPram18.Surfaces2=[profile14[0]+",FL"]
bracketPram18.RevSf2=False
bracketPram18.RevSf3=False
bracketPram18.Sf1DimensionType=1541
bracketPram18.Sf1DimensonParams=["0","100"]
bracketPram18.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile15[0]]
bracketPram18.Sf2DimensionType=1531
bracketPram18.Sf2DimensonParams=["200","15"]
bracket18 = part.CreateBracket(bracketPram18,False)
part.SetElementColor(bracket18,"0","255","255","0.19999998807907104")
bracketPram19 = part.CreateBracketParam()
bracketPram19.DefinitionType=1
bracketPram19.BracketName="HK.Casing.Wall.Fore.DL05.Deck.CP"
bracketPram19.MaterialName="SS400"
bracketPram19.BaseElement=profile22[0]
bracketPram19.UseSideSheetForPlane=False
bracketPram19.Mold="+"
bracketPram19.Thickness="7.9999999999999964"
bracketPram19.BracketType=1501
bracketPram19.Scallop1Type=1801
bracketPram19.Scallop1Params=["0"]
bracketPram19.Scallop2Type=0
bracketPram19.Surfaces1=[profile20[0]+",FL"]
bracketPram19.RevSf1=False
bracketPram19.Surfaces2=[profile22[0]+",FL"]
bracketPram19.RevSf2=False
bracketPram19.RevSf3=False
bracketPram19.Sf1DimensionType=1531
bracketPram19.Sf1DimensonParams=["200","15"]
bracketPram19.Sf2DimensionType=1531
bracketPram19.Sf2DimensonParams=["200","15"]
bracket19 = part.CreateBracket(bracketPram19,False)
part.SetElementColor(bracket19,"0","255","255","0.19999998807907104")
bracketPram20 = part.CreateBracketParam()
bracketPram20.DefinitionType=1
bracketPram20.BracketName="HK.Casing.Wall.Fore.DL04.Deck.AP"
bracketPram20.MaterialName="SS400"
bracketPram20.BaseElement=profile43[0]
bracketPram20.UseSideSheetForPlane=False
bracketPram20.Mold="-"
bracketPram20.Thickness="7.9999999999999964"
bracketPram20.BracketType=1501
bracketPram20.Scallop1Type=1801
bracketPram20.Scallop1Params=["0"]
bracketPram20.Scallop2Type=0
bracketPram20.Surfaces1=[profile42[0]+",FL"]
bracketPram20.RevSf1=False
bracketPram20.Surfaces2=[profile43[0]+",FL"]
bracketPram20.RevSf2=False
bracketPram20.RevSf3=False
bracketPram20.Sf1DimensionType=1531
bracketPram20.Sf1DimensonParams=["250","15"]
bracketPram20.Sf2DimensionType=1531
bracketPram20.Sf2DimensonParams=["250","15"]
bracket20 = part.CreateBracket(bracketPram20,False)
part.SetElementColor(bracket20,"0","255","255","0.19999998807907104")
bracketPram21 = part.CreateBracketParam()
bracketPram21.DefinitionType=1
bracketPram21.BracketName="HK.Casing.Wall.Side.FR07.Deck.CP"
bracketPram21.MaterialName="SS400"
bracketPram21.BaseElement=profile55[0]
bracketPram21.UseSideSheetForPlane=False
bracketPram21.Mold="+"
bracketPram21.Thickness="9.9999999999999982"
bracketPram21.BracketType=1505
bracketPram21.BracketParams=["200"]
bracketPram21.Scallop1Type=1801
bracketPram21.Scallop1Params=["0"]
bracketPram21.Scallop2Type=0
bracketPram21.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram21.RevSf1=False
bracketPram21.Surfaces2=[profile55[0]+",FL"]
bracketPram21.RevSf2=False
bracketPram21.RevSf3=False
bracketPram21.Sf1DimensionType=1541
bracketPram21.Sf1DimensonParams=["0","100"]
bracketPram21.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile22[0]]
bracketPram21.Sf2DimensionType=1531
bracketPram21.Sf2DimensonParams=["200","15"]
bracket21 = part.CreateBracket(bracketPram21,False)
part.SetElementColor(bracket21,"0","255","255","0.19999998807907104")
ProfilePram80 = part.CreateProfileParam()
ProfilePram80.DefinitionType=1
ProfilePram80.BasePlane="PL,O,"+var_elm8+","+"PL,Y"
ProfilePram80.AddAttachSurfaces(extrude_sheet3)
ProfilePram80.ProfileName="HK.Casing.Wall.Aft.DL02.BCP"
ProfilePram80.MaterialName="SS400"
ProfilePram80.FlangeName="HK.Casing.Wall.Aft.DL02.BCP"
ProfilePram80.FlangeMaterialName="SS400"
ProfilePram80.ProfileType=1201
ProfilePram80.ProfileParams=["150","12","388","10"]
ProfilePram80.Mold="-"
ProfilePram80.ReverseDir=False
ProfilePram80.ReverseAngle=False
ProfilePram80.CalcSnipOnlyAttachLines=False
ProfilePram80.AttachDirMethod=0
ProfilePram80.CCWDefAngle=False
ProfilePram80.AddEnd1Elements(extrude_sheet6)
ProfilePram80.End1Type=1103
ProfilePram80.End1TypeParams=["0"]
ProfilePram80.AddEnd2Elements(extrude_sheet1)
ProfilePram80.End2Type=1103
ProfilePram80.End2TypeParams=["0"]
ProfilePram80.End1ScallopType=1120
ProfilePram80.End1ScallopTypeParams=["50"]
ProfilePram80.End2ScallopType=1120
ProfilePram80.End2ScallopTypeParams=["50"]
profile80 = part.CreateProfile(ProfilePram80,False)
part.SetElementColor(profile80[0],"148","0","211","0.39999997615814209")
part.SetElementColor(profile80[1],"148","0","211","0.39999997615814209")
mirror_copied13 = part.MirrorCopy([profile80[0]],"PL,Y","")
part.SetElementColor(mirror_copied13[0],"148","0","211","0.39999997615814209")
ProfilePram81 = part.CreateProfileParam()
ProfilePram81.DefinitionType=1
ProfilePram81.BasePlane="PL,O,"+var_elm14+","+"PL,X"
ProfilePram81.AddAttachSurfaces(extrude_sheet4)
ProfilePram81.ProfileName="HK.Casing.Wall.Side.FR15.CDP"
ProfilePram81.MaterialName="SS400"
ProfilePram81.ProfileType=1002
ProfilePram81.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram81.Mold="+"
ProfilePram81.ReverseDir=False
ProfilePram81.ReverseAngle=True
ProfilePram81.CalcSnipOnlyAttachLines=False
ProfilePram81.AttachDirMethod=0
ProfilePram81.CCWDefAngle=False
ProfilePram81.AddEnd1Elements(extrude_sheet7)
ProfilePram81.End1Type=1102
ProfilePram81.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram81.AddEnd2Elements(extrude_sheet6)
ProfilePram81.End2Type=1102
ProfilePram81.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram81.End1ScallopType=1121
ProfilePram81.End1ScallopTypeParams=["35","40"]
ProfilePram81.End2ScallopType=1121
ProfilePram81.End2ScallopTypeParams=["35","40"]
profile81 = part.CreateProfile(ProfilePram81,False)
part.SetElementColor(profile81[0],"255","0","0","0.19999998807907104")
mirror_copied14 = part.MirrorCopy([profile81[0]],"PL,Y","")
part.SetElementColor(mirror_copied14[0],"255","0","0","0.19999998807907104")
ProfilePram82 = part.CreateProfileParam()
ProfilePram82.DefinitionType=1
ProfilePram82.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram82.AddAttachSurfaces(extrude_sheet3)
ProfilePram82.ProfileName="HK.Casing.Wall.Aft.DL01.OAP"
ProfilePram82.MaterialName="SS400"
ProfilePram82.ProfileType=1002
ProfilePram82.ProfileParams=["125","75","7","10","5"]
ProfilePram82.Mold="+"
ProfilePram82.ReverseDir=False
ProfilePram82.ReverseAngle=True
ProfilePram82.CalcSnipOnlyAttachLines=False
ProfilePram82.AttachDirMethod=0
ProfilePram82.CCWDefAngle=False
ProfilePram82.AddEnd1Elements(extrude_sheet2)
ProfilePram82.End1Type=1102
ProfilePram82.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram82.AddEnd2Elements(extrude_sheet8)
ProfilePram82.End2Type=1102
ProfilePram82.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram82.End1ScallopType=1121
ProfilePram82.End1ScallopTypeParams=["25","40"]
ProfilePram82.End2ScallopType=1121
ProfilePram82.End2ScallopTypeParams=["25","40"]
profile82 = part.CreateProfile(ProfilePram82,False)
part.SetElementColor(profile82[0],"255","0","0","0.19999998807907104")
ProfilePram83 = part.CreateProfileParam()
ProfilePram83.DefinitionType=1
ProfilePram83.BasePlane="PL,O,"+var_elm16+","+"PL,X"
ProfilePram83.AddAttachSurfaces(extrude_sheet4)
ProfilePram83.ProfileName="HK.Casing.Wall.Side.FR10.ABP"
ProfilePram83.MaterialName="SS400"
ProfilePram83.ProfileType=1002
ProfilePram83.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram83.Mold="+"
ProfilePram83.ReverseDir=False
ProfilePram83.ReverseAngle=True
ProfilePram83.CalcSnipOnlyAttachLines=False
ProfilePram83.AttachDirMethod=0
ProfilePram83.CCWDefAngle=False
ProfilePram83.AddEnd1Elements(extrude_sheet1)
ProfilePram83.End1Type=1102
ProfilePram83.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram83.AddEnd2Elements(extrude_sheet2)
ProfilePram83.End2Type=1102
ProfilePram83.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram83.End1ScallopType=1121
ProfilePram83.End1ScallopTypeParams=["35","40"]
ProfilePram83.End2ScallopType=1121
ProfilePram83.End2ScallopTypeParams=["35","40"]
profile83 = part.CreateProfile(ProfilePram83,False)
part.SetElementColor(profile83[0],"255","0","0","0.19999998807907104")
ProfilePram84 = part.CreateProfileParam()
ProfilePram84.DefinitionType=1
ProfilePram84.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram84.AddAttachSurfaces(extrude_sheet5)
ProfilePram84.ProfileName="HK.Casing.Wall.Fore.DL00.AB"
ProfilePram84.MaterialName="SS400"
ProfilePram84.ProfileType=1002
ProfilePram84.ProfileParams=["125","75","7","10","5"]
ProfilePram84.ReverseDir=True
ProfilePram84.ReverseAngle=True
ProfilePram84.CalcSnipOnlyAttachLines=False
ProfilePram84.AttachDirMethod=0
ProfilePram84.CCWDefAngle=False
ProfilePram84.AddEnd1Elements(extrude_sheet1)
ProfilePram84.End1Type=1102
ProfilePram84.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram84.AddEnd2Elements(extrude_sheet2)
ProfilePram84.End2Type=1102
ProfilePram84.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram84.End1ScallopType=1121
ProfilePram84.End1ScallopTypeParams=["25","40"]
ProfilePram84.End2ScallopType=1121
ProfilePram84.End2ScallopTypeParams=["25","40"]
profile84 = part.CreateProfile(ProfilePram84,False)
part.SetElementColor(profile84[0],"255","0","0","0.19999998807907104")
ProfilePram85 = part.CreateProfileParam()
ProfilePram85.DefinitionType=1
ProfilePram85.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram85.AddAttachSurfaces(extrude_sheet1)
ProfilePram85.ProfileName="HK.Casing.Deck.B.DL00.F"
ProfilePram85.MaterialName="SS400"
ProfilePram85.ProfileType=1002
ProfilePram85.ProfileParams=["125","75","7","10","5"]
ProfilePram85.ReverseDir=True
ProfilePram85.ReverseAngle=True
ProfilePram85.CalcSnipOnlyAttachLines=False
ProfilePram85.AttachDirMethod=0
ProfilePram85.CCWDefAngle=False
ProfilePram85.AddEnd1Elements(profile71[0])
ProfilePram85.End1Type=1102
ProfilePram85.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram85.AddEnd2Elements(profile84[0])
ProfilePram85.End2Type=1102
ProfilePram85.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram85.End1ScallopType=1121
ProfilePram85.End1ScallopTypeParams=["25","40"]
ProfilePram85.End2ScallopType=1121
ProfilePram85.End2ScallopTypeParams=["25","40"]
profile85 = part.CreateProfile(ProfilePram85,False)
part.SetElementColor(profile85[0],"255","0","0","0.19999998807907104")
bracketPram22 = part.CreateBracketParam()
bracketPram22.DefinitionType=1
bracketPram22.BracketName="HK.Casing.Wall.Side.FR08.Deck.DP"
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
bracketPram22.Surfaces1=["PLS","False","False","0","-0","-1",solid2]
bracketPram22.RevSf1=False
bracketPram22.Surfaces2=[profile24[0]+",FL"]
bracketPram22.RevSf2=False
bracketPram22.RevSf3=False
bracketPram22.Sf1DimensionType=1541
bracketPram22.Sf1DimensonParams=["0","100"]
bracketPram22.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile15[0]]
bracketPram22.Sf2DimensionType=1531
bracketPram22.Sf2DimensonParams=["200","15"]
bracket22 = part.CreateBracket(bracketPram22,False)
part.SetElementColor(bracket22,"0","255","255","0.19999998807907104")
mirror_copied15 = part.MirrorCopy([bracket22],"PL,Y","")
part.SetElementColor(mirror_copied15[0],"0","255","255","0.19999998807907104")
bracketPram23 = part.CreateBracketParam()
bracketPram23.DefinitionType=1
bracketPram23.BracketName="HK.Casing.Wall.Aft.DL02.Deck.DP"
bracketPram23.MaterialName="SS400"
bracketPram23.BaseElement=profile27[0]
bracketPram23.UseSideSheetForPlane=False
bracketPram23.Mold="-"
bracketPram23.Thickness="12"
bracketPram23.BracketType=1501
bracketPram23.Scallop1Type=1801
bracketPram23.Scallop1Params=["50"]
bracketPram23.Scallop2Type=0
bracketPram23.Surfaces1=["PLS","False","False","1","0","-0",profile27[1]]
bracketPram23.RevSf1=False
bracketPram23.Surfaces2=["PLS","False","False","-0","-0","-1",profile16[1]]
bracketPram23.RevSf2=False
bracketPram23.RevSf3=False
bracketPram23.FlangeType=262
bracketPram23.FlangeParams=["100","30","29.999999999999996","30","30","1"]
bracketPram23.RevFlange=False
bracketPram23.Sf1DimensionType=1531
bracketPram23.Sf1DimensonParams=["800","15"]
bracketPram23.Sf2DimensionType=1531
bracketPram23.Sf2DimensonParams=["800","15"]
bracket23 = part.CreateBracket(bracketPram23,False)
part.SetElementColor(bracket23,"0","255","255","0.19999998807907104")
ProfilePram86 = part.CreateProfileParam()
ProfilePram86.DefinitionType=1
ProfilePram86.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram86.AddAttachSurfaces(extrude_sheet7)
ProfilePram86.ProfileName="HK.Casing.Deck.D.DL04P"
ProfilePram86.MaterialName="SS400"
ProfilePram86.ProfileType=1002
ProfilePram86.ProfileParams=["125","75","7","10","5"]
ProfilePram86.Mold="+"
ProfilePram86.ReverseDir=True
ProfilePram86.ReverseAngle=True
ProfilePram86.CalcSnipOnlyAttachLines=False
ProfilePram86.AttachDirMethod=0
ProfilePram86.CCWDefAngle=False
ProfilePram86.AddEnd1Elements(extrude_sheet3)
ProfilePram86.End1Type=1102
ProfilePram86.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram86.AddEnd2Elements(extrude_sheet5)
ProfilePram86.End2Type=1102
ProfilePram86.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram86.End1ScallopType=1120
ProfilePram86.End1ScallopTypeParams=["50"]
ProfilePram86.End2ScallopType=1120
ProfilePram86.End2ScallopTypeParams=["50"]
profile86 = part.CreateProfile(ProfilePram86,False)
part.SetElementColor(profile86[0],"255","0","0","0.19999998807907104")
ProfilePram87 = part.CreateProfileParam()
ProfilePram87.DefinitionType=1
ProfilePram87.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram87.AddAttachSurfaces(extrude_sheet3)
ProfilePram87.ProfileName="HK.Casing.Wall.Aft.DL04.CDP"
ProfilePram87.MaterialName="SS400"
ProfilePram87.ProfileType=1002
ProfilePram87.ProfileParams=["125","75","7","10","5"]
ProfilePram87.Mold="+"
ProfilePram87.ReverseDir=False
ProfilePram87.ReverseAngle=True
ProfilePram87.CalcSnipOnlyAttachLines=False
ProfilePram87.AttachDirMethod=0
ProfilePram87.CCWDefAngle=False
ProfilePram87.AddEnd1Elements(profile86[0])
ProfilePram87.End1Type=1102
ProfilePram87.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram87.AddEnd2Elements(extrude_sheet6)
ProfilePram87.End2Type=1102
ProfilePram87.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram87.End1ScallopType=1120
ProfilePram87.End1ScallopTypeParams=["50"]
ProfilePram87.End2ScallopType=1120
ProfilePram87.End2ScallopTypeParams=["50"]
profile87 = part.CreateProfile(ProfilePram87,False)
part.SetElementColor(profile87[0],"255","0","0","0.19999998807907104")
bracketPram24 = part.CreateBracketParam()
bracketPram24.DefinitionType=1
bracketPram24.BracketName="HK.Casing.Wall.Aft.DL04.Deck.DP"
bracketPram24.MaterialName="SS400"
bracketPram24.BaseElement=profile87[0]
bracketPram24.UseSideSheetForPlane=False
bracketPram24.Mold="+"
bracketPram24.Thickness="7.9999999999999964"
bracketPram24.BracketType=1501
bracketPram24.Scallop1Type=1801
bracketPram24.Scallop1Params=["0"]
bracketPram24.Scallop2Type=0
bracketPram24.Surfaces1=[profile87[0]+",FL"]
bracketPram24.RevSf1=False
bracketPram24.Surfaces2=[profile86[0]+",FL"]
bracketPram24.RevSf2=False
bracketPram24.RevSf3=False
bracketPram24.Sf1DimensionType=1531
bracketPram24.Sf1DimensonParams=["200","15"]
bracketPram24.Sf2DimensionType=1531
bracketPram24.Sf2DimensonParams=["200","15"]
bracket24 = part.CreateBracket(bracketPram24,False)
part.SetElementColor(bracket24,"0","255","255","0.19999998807907104")
mirror_copied16 = part.MirrorCopy([bracket24],"PL,Y","")
part.SetElementColor(mirror_copied16[0],"0","255","255","0.19999998807907104")
solid6 = part.CreateSolid("HK.Casing.Wall.Fore.AB","","SS400")
part.SetElementColor(solid6,"139","69","19","0.79999995231628418")
thicken6 = part.CreateThicken("厚み付け17",solid6,"+",[extrude_sheet5],"+","10","0","0",False,False)
ProfilePram88 = part.CreateProfileParam()
ProfilePram88.DefinitionType=1
ProfilePram88.BasePlane="PL,O,"+var_elm8+","+"PL,Y"
ProfilePram88.AddAttachSurfaces(extrude_sheet5)
ProfilePram88.ProfileName="HK.Casing.Wall.Fore.DL02.ABP"
ProfilePram88.MaterialName="SS400"
ProfilePram88.FlangeName="HK.Casing.Wall.Fore.DL02.ABP"
ProfilePram88.FlangeMaterialName="SS400"
ProfilePram88.ProfileType=1201
ProfilePram88.ProfileParams=["150","12","388","10"]
ProfilePram88.Mold="-"
ProfilePram88.ReverseDir=True
ProfilePram88.ReverseAngle=False
ProfilePram88.CalcSnipOnlyAttachLines=False
ProfilePram88.AttachDirMethod=0
ProfilePram88.CCWDefAngle=False
ProfilePram88.AddEnd1Elements(extrude_sheet1)
ProfilePram88.End1Type=1102
ProfilePram88.End1TypeParams=["25","14.999999999999998","0","0"]
ProfilePram88.AddEnd2Elements(extrude_sheet2)
ProfilePram88.End2Type=1102
ProfilePram88.End2TypeParams=["25","14.999999999999998","0","0"]
ProfilePram88.End1ScallopType=1120
ProfilePram88.End1ScallopTypeParams=["50"]
ProfilePram88.End2ScallopType=1120
ProfilePram88.End2ScallopTypeParams=["50"]
profile88 = part.CreateProfile(ProfilePram88,False)
part.SetElementColor(profile88[0],"148","0","211","0.39999997615814209")
part.SetElementColor(profile88[1],"148","0","211","0.39999997615814209")
extrudePram19 = part.CreateLinearSweepParam()
extrudePram19.Name="積-押し出し20"
extrudePram19.AddProfile(extrude_sheet9)
extrudePram19.DirectionType="N"
extrudePram19.DirectionParameter1="50000"
extrudePram19.SweepDirection="+Y"
extrudePram19.RefByGeometricMethod=True
extrude10 = part.CreateLinearSweep(solid5,"*",extrudePram19,False)
extrudePram20 = part.CreateLinearSweepParam()
extrudePram20.Name="積-押し出し21"
extrudePram20.AddProfile(extrude_sheet7)
extrudePram20.DirectionType="R"
extrudePram20.DirectionParameter1="50000"
extrudePram20.SweepDirection="+Z"
extrudePram20.RefByGeometricMethod=True
extrude11 = part.CreateLinearSweep(solid5,"*",extrudePram20,False)
solid7 = part.CreateSolid("HK.Casing.Wall.Fore.OA","","SS400")
part.SetElementColor(solid7,"139","69","19","0.79999995231628418")
thicken7 = part.CreateThicken("厚み付け18",solid7,"+",[extrude_sheet5],"+","10","0","0",False,False)
extrudePram21 = part.CreateLinearSweepParam()
extrudePram21.Name="積-押し出し47"
extrudePram21.AddProfile(extrude_sheet4)
extrudePram21.DirectionType="R"
extrudePram21.DirectionParameter1="50000"
extrudePram21.SweepDirection="+Y"
extrudePram21.RefByGeometricMethod=True
extrude12 = part.CreateLinearSweep(solid7,"*",extrudePram21,False)
extrudePram22 = part.CreateLinearSweepParam()
extrudePram22.Name="積-押し出し48"
extrudePram22.AddProfile(extrude_sheet9)
extrudePram22.DirectionType="N"
extrudePram22.DirectionParameter1="50000"
extrudePram22.SweepDirection="+Y"
extrudePram22.RefByGeometricMethod=True
extrude13 = part.CreateLinearSweep(solid7,"*",extrudePram22,False)
extrudePram23 = part.CreateLinearSweepParam()
extrudePram23.Name="積-押し出し49"
extrudePram23.AddProfile(extrude_sheet2)
extrudePram23.DirectionType="R"
extrudePram23.DirectionParameter1="50000"
extrudePram23.SweepDirection="+Z"
extrudePram23.RefByGeometricMethod=True
extrude14 = part.CreateLinearSweep(solid7,"*",extrudePram23,False)
extrudePram24 = part.CreateLinearSweepParam()
extrudePram24.Name="積-押し出し50"
extrudePram24.AddProfile(extrude_sheet8)
extrudePram24.DirectionType="N"
extrudePram24.DirectionParameter1="50000"
extrudePram24.SweepDirection="+Z"
extrudePram24.RefByGeometricMethod=True
extrude15 = part.CreateLinearSweep(solid7,"*",extrudePram24,False)
mirror_copied17 = part.MirrorCopy([profile24[0]],"PL,Y","")
part.SetElementColor(mirror_copied17[0],"255","0","0","0.19999998807907104")
ProfilePram89 = part.CreateProfileParam()
ProfilePram89.DefinitionType=1
ProfilePram89.BasePlane="PL,O,"+var_elm14+","+"PL,X"
ProfilePram89.AddAttachSurfaces(extrude_sheet4)
ProfilePram89.ProfileName="HK.Casing.Wall.Side.FR15.BCP"
ProfilePram89.MaterialName="SS400"
ProfilePram89.ProfileType=1002
ProfilePram89.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram89.Mold="+"
ProfilePram89.ReverseDir=False
ProfilePram89.ReverseAngle=True
ProfilePram89.CalcSnipOnlyAttachLines=False
ProfilePram89.AttachDirMethod=0
ProfilePram89.CCWDefAngle=False
ProfilePram89.AddEnd1Elements(extrude_sheet6)
ProfilePram89.End1Type=1102
ProfilePram89.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram89.AddEnd2Elements(extrude_sheet1)
ProfilePram89.End2Type=1102
ProfilePram89.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram89.End1ScallopType=1121
ProfilePram89.End1ScallopTypeParams=["35","40"]
ProfilePram89.End2ScallopType=1121
ProfilePram89.End2ScallopTypeParams=["35","40"]
profile89 = part.CreateProfile(ProfilePram89,False)
part.SetElementColor(profile89[0],"255","0","0","0.19999998807907104")
bracketPram25 = part.CreateBracketParam()
bracketPram25.DefinitionType=1
bracketPram25.BracketName="HK.Casing.Wall.Side.FR14.Deck.CP"
bracketPram25.MaterialName="SS400"
bracketPram25.BaseElement=profile31[0]
bracketPram25.UseSideSheetForPlane=False
bracketPram25.Mold="+"
bracketPram25.Thickness="9.9999999999999982"
bracketPram25.BracketType=1505
bracketPram25.BracketParams=["200"]
bracketPram25.Scallop1Type=1801
bracketPram25.Scallop1Params=["0"]
bracketPram25.Scallop2Type=0
bracketPram25.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram25.RevSf1=False
bracketPram25.Surfaces2=[profile31[0]+",FL"]
bracketPram25.RevSf2=False
bracketPram25.RevSf3=False
bracketPram25.Sf1DimensionType=1541
bracketPram25.Sf1DimensonParams=["0","100"]
bracketPram25.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile22[0]]
bracketPram25.Sf2DimensionType=1531
bracketPram25.Sf2DimensonParams=["200","15"]
bracket25 = part.CreateBracket(bracketPram25,False)
part.SetElementColor(bracket25,"0","255","255","0.19999998807907104")
ProfilePram90 = part.CreateProfileParam()
ProfilePram90.DefinitionType=1
ProfilePram90.BasePlane="PL,O,"+var_elm9+","+"PL,X"
ProfilePram90.AddAttachSurfaces(extrude_sheet2)
ProfilePram90.ProfileName="HK.Casing.Deck.A.FR09P"
ProfilePram90.MaterialName="SS400"
ProfilePram90.ProfileType=1003
ProfilePram90.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram90.Mold="+"
ProfilePram90.ReverseDir=True
ProfilePram90.ReverseAngle=False
ProfilePram90.CalcSnipOnlyAttachLines=False
ProfilePram90.AttachDirMethod=0
ProfilePram90.CCWDefAngle=False
ProfilePram90.AddEnd1Elements(profile43[0])
ProfilePram90.End1Type=1113
ProfilePram90.End1TypeParams=["0","79"]
ProfilePram90.AddEnd2Elements(profile60[0])
ProfilePram90.End2Type=1102
ProfilePram90.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram90.End1ScallopType=1120
ProfilePram90.End1ScallopTypeParams=["50"]
ProfilePram90.End2ScallopType=1120
ProfilePram90.End2ScallopTypeParams=["50"]
profile90 = part.CreateProfile(ProfilePram90,False)
part.SetElementColor(profile90[0],"148","0","211","0.39999997615814209")
bracketPram26 = part.CreateBracketParam()
bracketPram26.DefinitionType=1
bracketPram26.BracketName="HK.Casing.Wall.Side.FR09.Deck.AP"
bracketPram26.MaterialName="SS400"
bracketPram26.BaseElement=profile90[0]
bracketPram26.UseSideSheetForPlane=False
bracketPram26.Mold="+"
bracketPram26.Thickness="7.9999999999999964"
bracketPram26.BracketType=1501
bracketPram26.Scallop1Type=1801
bracketPram26.Scallop1Params=["0"]
bracketPram26.Scallop2Type=0
bracketPram26.Surfaces1=[profile60[0]+",FL"]
bracketPram26.RevSf1=False
bracketPram26.Surfaces2=[profile90[0]+",FL"]
bracketPram26.RevSf2=False
bracketPram26.RevSf3=False
bracketPram26.Sf1DimensionType=1531
bracketPram26.Sf1DimensonParams=["250","15"]
bracketPram26.Sf2DimensionType=1531
bracketPram26.Sf2DimensonParams=["250","15"]
bracket26 = part.CreateBracket(bracketPram26,False)
part.SetElementColor(bracket26,"0","255","255","0.19999998807907104")
solid8 = part.CreateSolid("HK.Casing.Wall.Side.OAP","","SS400")
part.SetElementColor(solid8,"139","69","19","0.79999995231628418")
thicken8 = part.CreateThicken("厚み付け10",solid8,"+",[extrude_sheet4],"-","10","0","0",False,False)
extrudePram25 = part.CreateLinearSweepParam()
extrudePram25.Name="積-押し出し16"
extrudePram25.AddProfile(skt_pl4+",Edge00")
extrudePram25.DirectionType="N"
extrudePram25.DirectionParameter1="50000"
extrudePram25.SweepDirection="+Z"
extrudePram25.RefByGeometricMethod=True
extrude16 = part.CreateLinearSweep(solid8,"*",extrudePram25,False)
extrudePram26 = part.CreateLinearSweepParam()
extrudePram26.Name="積-押し出し17"
extrudePram26.AddProfile(extrude_sheet2)
extrudePram26.DirectionType="R"
extrudePram26.DirectionParameter1="50000"
extrudePram26.SweepDirection="+Z"
extrudePram26.RefByGeometricMethod=True
extrude17 = part.CreateLinearSweep(solid8,"*",extrudePram26,False)
extrudePram27 = part.CreateLinearSweepParam()
extrudePram27.Name="積-押し出し18"
extrudePram27.AddProfile(extrude_sheet8)
extrudePram27.DirectionType="N"
extrudePram27.DirectionParameter1="50000"
extrudePram27.SweepDirection="+Z"
extrudePram27.RefByGeometricMethod=True
extrude18 = part.CreateLinearSweep(solid8,"*",extrudePram27,False)
mirror_copied18 = part.MirrorCopy([solid8],"PL,Y","")
part.SetElementColor(mirror_copied18[0],"139","69","19","0.79999995231628418")
ProfilePram91 = part.CreateProfileParam()
ProfilePram91.DefinitionType=1
ProfilePram91.BasePlane="PL,O,"+var_elm13+","+"PL,X"
ProfilePram91.AddAttachSurfaces(extrude_sheet4)
ProfilePram91.ProfileName="HK.Casing.Wall.Side.FR07.ABP"
ProfilePram91.MaterialName="SS400"
ProfilePram91.ProfileType=1002
ProfilePram91.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram91.Mold="+"
ProfilePram91.ReverseDir=False
ProfilePram91.ReverseAngle=True
ProfilePram91.CalcSnipOnlyAttachLines=False
ProfilePram91.AttachDirMethod=0
ProfilePram91.CCWDefAngle=False
ProfilePram91.AddEnd1Elements(extrude_sheet1)
ProfilePram91.End1Type=1102
ProfilePram91.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram91.AddEnd2Elements(extrude_sheet2)
ProfilePram91.End2Type=1102
ProfilePram91.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram91.End1ScallopType=1121
ProfilePram91.End1ScallopTypeParams=["35","40"]
ProfilePram91.End2ScallopType=1121
ProfilePram91.End2ScallopTypeParams=["35","40"]
profile91 = part.CreateProfile(ProfilePram91,False)
part.SetElementColor(profile91[0],"255","0","0","0.19999998807907104")
bracketPram27 = part.CreateBracketParam()
bracketPram27.DefinitionType=1
bracketPram27.BracketName="HK.Casing.Wall.Side.FR15.Deck.CP"
bracketPram27.MaterialName="SS400"
bracketPram27.BaseElement=profile89[0]
bracketPram27.UseSideSheetForPlane=False
bracketPram27.Mold="+"
bracketPram27.Thickness="9.9999999999999982"
bracketPram27.BracketType=1505
bracketPram27.BracketParams=["200"]
bracketPram27.Scallop1Type=1801
bracketPram27.Scallop1Params=["0"]
bracketPram27.Scallop2Type=0
bracketPram27.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram27.RevSf1=False
bracketPram27.Surfaces2=[profile89[0]+",FL"]
bracketPram27.RevSf2=False
bracketPram27.RevSf3=False
bracketPram27.Sf1DimensionType=1541
bracketPram27.Sf1DimensonParams=["0","100"]
bracketPram27.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile22[0]]
bracketPram27.Sf2DimensionType=1531
bracketPram27.Sf2DimensonParams=["200","15"]
bracket27 = part.CreateBracket(bracketPram27,False)
part.SetElementColor(bracket27,"0","255","255","0.19999998807907104")
mirror_copied19 = part.MirrorCopy([profile5[0]],"PL,Y","")
part.SetElementColor(mirror_copied19[0],"255","0","0","0.19999998807907104")
ProfilePram92 = part.CreateProfileParam()
ProfilePram92.DefinitionType=1
ProfilePram92.BasePlane="PL,O,"+var_elm16+","+"PL,X"
ProfilePram92.AddAttachSurfaces(extrude_sheet4)
ProfilePram92.ProfileName="HK.Casing.Wall.Side.FR10.BCP"
ProfilePram92.MaterialName="SS400"
ProfilePram92.ProfileType=1002
ProfilePram92.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram92.Mold="+"
ProfilePram92.ReverseDir=False
ProfilePram92.ReverseAngle=True
ProfilePram92.CalcSnipOnlyAttachLines=False
ProfilePram92.AttachDirMethod=0
ProfilePram92.CCWDefAngle=False
ProfilePram92.AddEnd1Elements(extrude_sheet6)
ProfilePram92.End1Type=1102
ProfilePram92.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram92.AddEnd2Elements(extrude_sheet1)
ProfilePram92.End2Type=1102
ProfilePram92.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram92.End1ScallopType=1121
ProfilePram92.End1ScallopTypeParams=["35","40"]
ProfilePram92.End2ScallopType=1121
ProfilePram92.End2ScallopTypeParams=["35","40"]
profile92 = part.CreateProfile(ProfilePram92,False)
part.SetElementColor(profile92[0],"255","0","0","0.19999998807907104")
ProfilePram93 = part.CreateProfileParam()
ProfilePram93.DefinitionType=1
ProfilePram93.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram93.AddAttachSurfaces(extrude_sheet7)
ProfilePram93.ProfileName="HK.Casing.Deck.D.DL00.F"
ProfilePram93.MaterialName="SS400"
ProfilePram93.ProfileType=1002
ProfilePram93.ProfileParams=["125","75","7","10","5"]
ProfilePram93.ReverseDir=True
ProfilePram93.ReverseAngle=True
ProfilePram93.CalcSnipOnlyAttachLines=False
ProfilePram93.AttachDirMethod=0
ProfilePram93.CCWDefAngle=False
ProfilePram93.AddEnd1Elements(profile65[0])
ProfilePram93.End1Type=1102
ProfilePram93.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram93.AddEnd2Elements(extrude_sheet5)
ProfilePram93.End2Type=1102
ProfilePram93.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram93.End1ScallopType=1121
ProfilePram93.End1ScallopTypeParams=["25","40"]
ProfilePram93.End2ScallopType=1121
ProfilePram93.End2ScallopTypeParams=["25","40"]
profile93 = part.CreateProfile(ProfilePram93,False)
part.SetElementColor(profile93[0],"255","0","0","0.19999998807907104")
ProfilePram94 = part.CreateProfileParam()
ProfilePram94.DefinitionType=1
ProfilePram94.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram94.AddAttachSurfaces(extrude_sheet5)
ProfilePram94.ProfileName="HK.Casing.Wall.Fore.DL00.CD"
ProfilePram94.MaterialName="SS400"
ProfilePram94.ProfileType=1002
ProfilePram94.ProfileParams=["125","75","7","10","5"]
ProfilePram94.ReverseDir=True
ProfilePram94.ReverseAngle=True
ProfilePram94.CalcSnipOnlyAttachLines=False
ProfilePram94.AttachDirMethod=0
ProfilePram94.CCWDefAngle=False
ProfilePram94.AddEnd1Elements(profile93[0])
ProfilePram94.End1Type=1102
ProfilePram94.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram94.AddEnd2Elements(extrude_sheet6)
ProfilePram94.End2Type=1102
ProfilePram94.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram94.End1ScallopType=1120
ProfilePram94.End1ScallopTypeParams=["50"]
ProfilePram94.End2ScallopType=1120
ProfilePram94.End2ScallopTypeParams=["50"]
profile94 = part.CreateProfile(ProfilePram94,False)
part.SetElementColor(profile94[0],"255","0","0","0.19999998807907104")
mirror_copied20 = part.MirrorCopy([profile82[0]],"PL,Y","")
part.SetElementColor(mirror_copied20[0],"255","0","0","0.19999998807907104")
ProfilePram95 = part.CreateProfileParam()
ProfilePram95.DefinitionType=1
ProfilePram95.BasePlane="PL,O,"+var_elm9+","+"PL,X"
ProfilePram95.AddAttachSurfaces(extrude_sheet4)
ProfilePram95.ProfileName="HK.Casing.Wall.Side.FR09.BCP"
ProfilePram95.MaterialName="SS400"
ProfilePram95.ProfileType=1003
ProfilePram95.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram95.Mold="+"
ProfilePram95.ReverseDir=False
ProfilePram95.ReverseAngle=True
ProfilePram95.CalcSnipOnlyAttachLines=False
ProfilePram95.AttachDirMethod=0
ProfilePram95.CCWDefAngle=False
ProfilePram95.AddEnd1Elements(extrude_sheet6)
ProfilePram95.End1Type=1103
ProfilePram95.End1TypeParams=["0"]
ProfilePram95.AddEnd2Elements(extrude_sheet1)
ProfilePram95.End2Type=1103
ProfilePram95.End2TypeParams=["0"]
ProfilePram95.End1ScallopType=1120
ProfilePram95.End1ScallopTypeParams=["50"]
ProfilePram95.End2ScallopType=1120
ProfilePram95.End2ScallopTypeParams=["50"]
profile95 = part.CreateProfile(ProfilePram95,False)
part.SetElementColor(profile95[0],"148","0","211","0.39999997615814209")
ProfilePram96 = part.CreateProfileParam()
ProfilePram96.DefinitionType=1
ProfilePram96.BasePlane="PL,O,"+var_elm9+","+"PL,X"
ProfilePram96.AddAttachSurfaces(extrude_sheet6)
ProfilePram96.ProfileName="HK.Casing.Deck.C.FR09P"
ProfilePram96.MaterialName="SS400"
ProfilePram96.ProfileType=1003
ProfilePram96.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram96.Mold="+"
ProfilePram96.ReverseDir=True
ProfilePram96.ReverseAngle=False
ProfilePram96.CalcSnipOnlyAttachLines=False
ProfilePram96.AttachDirMethod=0
ProfilePram96.CCWDefAngle=False
ProfilePram96.AddEnd1Elements(profile9[0])
ProfilePram96.End1Type=1113
ProfilePram96.End1TypeParams=["0","79"]
ProfilePram96.AddEnd2Elements(profile95[0])
ProfilePram96.End2Type=1102
ProfilePram96.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram96.End1ScallopType=1120
ProfilePram96.End1ScallopTypeParams=["50"]
ProfilePram96.End2ScallopType=1120
ProfilePram96.End2ScallopTypeParams=["50"]
profile96 = part.CreateProfile(ProfilePram96,False)
part.SetElementColor(profile96[0],"148","0","211","0.39999997615814209")
bracketPram28 = part.CreateBracketParam()
bracketPram28.DefinitionType=1
bracketPram28.BracketName="HK.Casing.Wall.Side.FR09.Deck.CP"
bracketPram28.MaterialName="SS400"
bracketPram28.BaseElement=profile96[0]
bracketPram28.UseSideSheetForPlane=False
bracketPram28.Mold="+"
bracketPram28.Thickness="7.9999999999999964"
bracketPram28.BracketType=1501
bracketPram28.Scallop1Type=1801
bracketPram28.Scallop1Params=["0"]
bracketPram28.Scallop2Type=0
bracketPram28.Surfaces1=[profile95[0]+",FL"]
bracketPram28.RevSf1=False
bracketPram28.Surfaces2=[profile96[0]+",FL"]
bracketPram28.RevSf2=False
bracketPram28.RevSf3=False
bracketPram28.Sf1DimensionType=1531
bracketPram28.Sf1DimensonParams=["250","15"]
bracketPram28.Sf2DimensionType=1531
bracketPram28.Sf2DimensonParams=["250","15"]
bracket28 = part.CreateBracket(bracketPram28,False)
part.SetElementColor(bracket28,"0","255","255","0.19999998807907104")
mirror_copied21 = part.MirrorCopy([profile87[0]],"PL,Y","")
part.SetElementColor(mirror_copied21[0],"255","0","0","0.19999998807907104")
solid9 = part.CreateSolid("HK.Casing.Wall.Aft.OA","","SS400")
part.SetElementColor(solid9,"139","69","19","0.79999995231628418")
thicken9 = part.CreateThicken("厚み付け14",solid9,"+",[extrude_sheet3],"-","10","0","0",False,False)
extrudePram28 = part.CreateLinearSweepParam()
extrudePram28.Name="積-押し出し31"
extrudePram28.AddProfile(extrude_sheet4)
extrudePram28.DirectionType="R"
extrudePram28.DirectionParameter1="50000"
extrudePram28.SweepDirection="+Y"
extrudePram28.RefByGeometricMethod=True
extrude19 = part.CreateLinearSweep(solid9,"*",extrudePram28,False)
extrudePram29 = part.CreateLinearSweepParam()
extrudePram29.Name="積-押し出し32"
extrudePram29.AddProfile(extrude_sheet9)
extrudePram29.DirectionType="N"
extrudePram29.DirectionParameter1="50000"
extrudePram29.SweepDirection="+Y"
extrudePram29.RefByGeometricMethod=True
extrude20 = part.CreateLinearSweep(solid9,"*",extrudePram29,False)
extrudePram30 = part.CreateLinearSweepParam()
extrudePram30.Name="積-押し出し33"
extrudePram30.AddProfile(extrude_sheet2)
extrudePram30.DirectionType="R"
extrudePram30.DirectionParameter1="50000"
extrudePram30.SweepDirection="+Z"
extrudePram30.RefByGeometricMethod=True
extrude21 = part.CreateLinearSweep(solid9,"*",extrudePram30,False)
extrudePram31 = part.CreateLinearSweepParam()
extrudePram31.Name="積-押し出し34"
extrudePram31.AddProfile(extrude_sheet8)
extrudePram31.DirectionType="N"
extrudePram31.DirectionParameter1="50000"
extrudePram31.SweepDirection="+Z"
extrudePram31.RefByGeometricMethod=True
extrude22 = part.CreateLinearSweep(solid9,"*",extrudePram31,False)
mirror_copied22 = part.MirrorCopy([profile78[0]],"PL,Y","")
part.SetElementColor(mirror_copied22[0],"148","0","211","0.39999997615814209")
mirror_copied23 = part.MirrorCopy([profile95[0]],"PL,Y","")
part.SetElementColor(mirror_copied23[0],"148","0","211","0.39999997615814209")
mirror_copied24 = part.MirrorCopy([bracket20],"PL,Y","")
part.SetElementColor(mirror_copied24[0],"0","255","255","0.19999998807907104")
bracketPram29 = part.CreateBracketParam()
bracketPram29.DefinitionType=1
bracketPram29.BracketName="HK.Casing.Wall.Aft.DL05.Deck.BP"
bracketPram29.MaterialName="SS400"
bracketPram29.BaseElement=profile5[0]
bracketPram29.UseSideSheetForPlane=False
bracketPram29.Mold="+"
bracketPram29.Thickness="7.9999999999999964"
bracketPram29.BracketType=1501
bracketPram29.Scallop1Type=1801
bracketPram29.Scallop1Params=["0"]
bracketPram29.Scallop2Type=0
bracketPram29.Surfaces1=[profile3[0]+",FL"]
bracketPram29.RevSf1=False
bracketPram29.Surfaces2=[profile5[0]+",FL"]
bracketPram29.RevSf2=False
bracketPram29.RevSf3=False
bracketPram29.Sf1DimensionType=1531
bracketPram29.Sf1DimensonParams=["200","15"]
bracketPram29.Sf2DimensionType=1531
bracketPram29.Sf2DimensonParams=["200","15"]
bracket29 = part.CreateBracket(bracketPram29,False)
part.SetElementColor(bracket29,"0","255","255","0.19999998807907104")
mirror_copied25 = part.MirrorCopy([bracket29],"PL,Y","")
part.SetElementColor(mirror_copied25[0],"0","255","255","0.19999998807907104")
ProfilePram97 = part.CreateProfileParam()
ProfilePram97.DefinitionType=1
ProfilePram97.BasePlane="PL,O,"+var_elm8+","+"PL,Y"
ProfilePram97.AddAttachSurfaces(extrude_sheet5)
ProfilePram97.ProfileName="HK.Casing.Wall.Fore.DL02.BCP"
ProfilePram97.MaterialName="SS400"
ProfilePram97.FlangeName="HK.Casing.Wall.Fore.DL02.BCP"
ProfilePram97.FlangeMaterialName="SS400"
ProfilePram97.ProfileType=1201
ProfilePram97.ProfileParams=["150","12","388","10"]
ProfilePram97.Mold="-"
ProfilePram97.ReverseDir=True
ProfilePram97.ReverseAngle=False
ProfilePram97.CalcSnipOnlyAttachLines=False
ProfilePram97.AttachDirMethod=0
ProfilePram97.CCWDefAngle=False
ProfilePram97.AddEnd1Elements(extrude_sheet6)
ProfilePram97.End1Type=1102
ProfilePram97.End1TypeParams=["25","14.999999999999998","0","0"]
ProfilePram97.AddEnd2Elements(extrude_sheet1)
ProfilePram97.End2Type=1102
ProfilePram97.End2TypeParams=["25","14.999999999999998","0","0"]
ProfilePram97.End1ScallopType=1120
ProfilePram97.End1ScallopTypeParams=["50"]
ProfilePram97.End2ScallopType=1120
ProfilePram97.End2ScallopTypeParams=["50"]
profile97 = part.CreateProfile(ProfilePram97,False)
part.SetElementColor(profile97[0],"148","0","211","0.39999997615814209")
part.SetElementColor(profile97[1],"148","0","211","0.39999997615814209")
mirror_copied26 = part.MirrorCopy([profile97[0]],"PL,Y","")
part.SetElementColor(mirror_copied26[0],"148","0","211","0.39999997615814209")
mirror_copied27 = part.MirrorCopy([profile28[0]],"PL,Y","")
part.SetElementColor(mirror_copied27[0],"255","0","0","0.19999998807907104")
ProfilePram98 = part.CreateProfileParam()
ProfilePram98.DefinitionType=1
ProfilePram98.BasePlane="PL,O,"+var_elm8+","+"PL,Y"
ProfilePram98.AddAttachSurfaces(extrude_sheet5)
ProfilePram98.ProfileName="HK.Casing.Wall.Fore.DL02.OAP"
ProfilePram98.MaterialName="SS400"
ProfilePram98.FlangeName="HK.Casing.Wall.Fore.DL02.OAP"
ProfilePram98.FlangeMaterialName="SS400"
ProfilePram98.ProfileType=1201
ProfilePram98.ProfileParams=["150","12","388","10"]
ProfilePram98.Mold="-"
ProfilePram98.ReverseDir=True
ProfilePram98.ReverseAngle=False
ProfilePram98.CalcSnipOnlyAttachLines=False
ProfilePram98.AttachDirMethod=0
ProfilePram98.CCWDefAngle=False
ProfilePram98.AddEnd1Elements(extrude_sheet2)
ProfilePram98.End1Type=1102
ProfilePram98.End1TypeParams=["25","14.999999999999998","0","0"]
ProfilePram98.AddEnd2Elements(extrude_sheet8)
ProfilePram98.End2Type=1102
ProfilePram98.End2TypeParams=["25","14.999999999999998","0","0"]
ProfilePram98.End1ScallopType=1120
ProfilePram98.End1ScallopTypeParams=["50"]
ProfilePram98.End2ScallopType=1120
ProfilePram98.End2ScallopTypeParams=["50"]
profile98 = part.CreateProfile(ProfilePram98,False)
part.SetElementColor(profile98[0],"148","0","211","0.39999997615814209")
part.SetElementColor(profile98[1],"148","0","211","0.39999997615814209")
bracketPram30 = part.CreateBracketParam()
bracketPram30.DefinitionType=1
bracketPram30.BracketName="HK.Casing.Wall.Fore.DL02.Deck.AP"
bracketPram30.MaterialName="SS400"
bracketPram30.BaseElement=profile98[0]
bracketPram30.UseSideSheetForPlane=False
bracketPram30.Mold="-"
bracketPram30.Thickness="9.9999999999999982"
bracketPram30.BracketType=1501
bracketPram30.Scallop1Type=1801
bracketPram30.Scallop1Params=["50"]
bracketPram30.Scallop2Type=0
bracketPram30.Surfaces1=["PLS","False","False","-1","-0","0",profile98[1]]
bracketPram30.RevSf1=False
bracketPram30.Surfaces2=["PLS","False","False","0","-0","-1",solid4]
bracketPram30.RevSf2=False
bracketPram30.RevSf3=False
bracketPram30.FlangeType=265
bracketPram30.FlangeParams=["75","30","29.999999999999996","30","30","30","30","150","30"]
bracketPram30.RevFlange=False
bracketPram30.Sf1DimensionType=1531
bracketPram30.Sf1DimensonParams=["500","15"]
bracketPram30.Sf2DimensionType=1541
bracketPram30.Sf2DimensonParams=["0","200"]
bracketPram30.Sf2EndElements=["PLS","False","False","1","-0","0",profile53[0]]
bracketPram30.ScallopEnd2LowerType=1801
bracketPram30.ScallopEnd2LowerParams=["50"]
bracket30 = part.CreateBracket(bracketPram30,False)
part.SetElementColor(bracket30,"0","255","255","0.19999998807907104")
mirror_copied28 = part.MirrorCopy([bracket30],"PL,Y","")
part.SetElementColor(mirror_copied28[0],"0","255","255","0.19999998807907104")
solid10 = part.CreateSolid("HK.Casing.Wall.Fore.CD","","SS400")
part.SetElementColor(solid10,"139","69","19","0.79999995231628418")
thicken10 = part.CreateThicken("厚み付け15",solid10,"+",[extrude_sheet5],"+","10","0","0",False,False)
extrudePram32 = part.CreateLinearSweepParam()
extrudePram32.Name="積-押し出し35"
extrudePram32.AddProfile(extrude_sheet4)
extrudePram32.DirectionType="R"
extrudePram32.DirectionParameter1="50000"
extrudePram32.SweepDirection="+Y"
extrudePram32.RefByGeometricMethod=True
extrude23 = part.CreateLinearSweep(solid10,"*",extrudePram32,False)
extrudePram33 = part.CreateLinearSweepParam()
extrudePram33.Name="積-押し出し36"
extrudePram33.AddProfile(extrude_sheet9)
extrudePram33.DirectionType="N"
extrudePram33.DirectionParameter1="50000"
extrudePram33.SweepDirection="+Y"
extrudePram33.RefByGeometricMethod=True
extrude24 = part.CreateLinearSweep(solid10,"*",extrudePram33,False)
extrudePram34 = part.CreateLinearSweepParam()
extrudePram34.Name="積-押し出し37"
extrudePram34.AddProfile(extrude_sheet7)
extrudePram34.DirectionType="R"
extrudePram34.DirectionParameter1="50000"
extrudePram34.SweepDirection="+Z"
extrudePram34.RefByGeometricMethod=True
extrude25 = part.CreateLinearSweep(solid10,"*",extrudePram34,False)
extrudePram35 = part.CreateLinearSweepParam()
extrudePram35.Name="積-押し出し38"
extrudePram35.AddProfile(extrude_sheet6)
extrudePram35.DirectionType="N"
extrudePram35.DirectionParameter1="50000"
extrudePram35.SweepDirection="+Z"
extrudePram35.RefByGeometricMethod=True
extrude26 = part.CreateLinearSweep(solid10,"*",extrudePram35,False)
ProfilePram99 = part.CreateProfileParam()
ProfilePram99.DefinitionType=1
ProfilePram99.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram99.AddAttachSurfaces(extrude_sheet3)
ProfilePram99.ProfileName="HK.Casing.Wall.Aft.DL00.AB"
ProfilePram99.MaterialName="SS400"
ProfilePram99.ProfileType=1002
ProfilePram99.ProfileParams=["125","75","7","10","5"]
ProfilePram99.ReverseDir=False
ProfilePram99.ReverseAngle=True
ProfilePram99.CalcSnipOnlyAttachLines=False
ProfilePram99.AttachDirMethod=0
ProfilePram99.CCWDefAngle=False
ProfilePram99.AddEnd1Elements(extrude_sheet1)
ProfilePram99.End1Type=1102
ProfilePram99.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram99.AddEnd2Elements(extrude_sheet2)
ProfilePram99.End2Type=1102
ProfilePram99.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram99.End1ScallopType=1121
ProfilePram99.End1ScallopTypeParams=["25","40"]
ProfilePram99.End2ScallopType=1121
ProfilePram99.End2ScallopTypeParams=["25","40"]
profile99 = part.CreateProfile(ProfilePram99,False)
part.SetElementColor(profile99[0],"255","0","0","0.19999998807907104")
solid11 = part.CreateSolid("HK.Casing.Wall.Aft.AB","","SS400")
part.SetElementColor(solid11,"139","69","19","0.79999995231628418")
thicken11 = part.CreateThicken("厚み付け13",solid11,"+",[extrude_sheet3],"-","10","0","0",False,False)
extrudePram36 = part.CreateLinearSweepParam()
extrudePram36.Name="積-押し出し27"
extrudePram36.AddProfile(extrude_sheet4)
extrudePram36.DirectionType="R"
extrudePram36.DirectionParameter1="50000"
extrudePram36.SweepDirection="+Y"
extrudePram36.RefByGeometricMethod=True
extrude27 = part.CreateLinearSweep(solid11,"*",extrudePram36,False)
extrudePram37 = part.CreateLinearSweepParam()
extrudePram37.Name="積-押し出し28"
extrudePram37.AddProfile(extrude_sheet9)
extrudePram37.DirectionType="N"
extrudePram37.DirectionParameter1="50000"
extrudePram37.SweepDirection="+Y"
extrudePram37.RefByGeometricMethod=True
extrude28 = part.CreateLinearSweep(solid11,"*",extrudePram37,False)
extrudePram38 = part.CreateLinearSweepParam()
extrudePram38.Name="積-押し出し29"
extrudePram38.AddProfile(extrude_sheet1)
extrudePram38.DirectionType="R"
extrudePram38.DirectionParameter1="50000"
extrudePram38.SweepDirection="+Z"
extrudePram38.RefByGeometricMethod=True
extrude29 = part.CreateLinearSweep(solid11,"*",extrudePram38,False)
extrudePram39 = part.CreateLinearSweepParam()
extrudePram39.Name="積-押し出し30"
extrudePram39.AddProfile(extrude_sheet2)
extrudePram39.DirectionType="N"
extrudePram39.DirectionParameter1="50000"
extrudePram39.SweepDirection="+Z"
extrudePram39.RefByGeometricMethod=True
extrude30 = part.CreateLinearSweep(solid11,"*",extrudePram39,False)
ProfilePram100 = part.CreateProfileParam()
ProfilePram100.DefinitionType=1
ProfilePram100.BasePlane="PL,O,"+var_elm1+","+"PL,Y"
ProfilePram100.AddAttachSurfaces(extrude_sheet5)
ProfilePram100.ProfileName="HK.Casing.Wall.Fore.DL04.CDP"
ProfilePram100.MaterialName="SS400"
ProfilePram100.ProfileType=1002
ProfilePram100.ProfileParams=["125","75","7","10","5"]
ProfilePram100.Mold="+"
ProfilePram100.ReverseDir=True
ProfilePram100.ReverseAngle=True
ProfilePram100.CalcSnipOnlyAttachLines=False
ProfilePram100.AttachDirMethod=0
ProfilePram100.CCWDefAngle=False
ProfilePram100.AddEnd1Elements(profile86[0])
ProfilePram100.End1Type=1102
ProfilePram100.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram100.AddEnd2Elements(extrude_sheet6)
ProfilePram100.End2Type=1102
ProfilePram100.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram100.End1ScallopType=1120
ProfilePram100.End1ScallopTypeParams=["50"]
ProfilePram100.End2ScallopType=1120
ProfilePram100.End2ScallopTypeParams=["50"]
profile100 = part.CreateProfile(ProfilePram100,False)
part.SetElementColor(profile100[0],"255","0","0","0.19999998807907104")
bracketPram31 = part.CreateBracketParam()
bracketPram31.DefinitionType=1
bracketPram31.BracketName="HK.Casing.Wall.Fore.DL04.Deck.DP"
bracketPram31.MaterialName="SS400"
bracketPram31.BaseElement=profile100[0]
bracketPram31.UseSideSheetForPlane=False
bracketPram31.Mold="+"
bracketPram31.Thickness="7.9999999999999964"
bracketPram31.BracketType=1501
bracketPram31.Scallop1Type=1801
bracketPram31.Scallop1Params=["0"]
bracketPram31.Scallop2Type=0
bracketPram31.Surfaces1=[profile100[0]+",FL"]
bracketPram31.RevSf1=False
bracketPram31.Surfaces2=[profile86[0]+",FL"]
bracketPram31.RevSf2=False
bracketPram31.RevSf3=False
bracketPram31.Sf1DimensionType=1531
bracketPram31.Sf1DimensonParams=["200","15"]
bracketPram31.Sf2DimensionType=1531
bracketPram31.Sf2DimensonParams=["200","15"]
bracket31 = part.CreateBracket(bracketPram31,False)
part.SetElementColor(bracket31,"0","255","255","0.19999998807907104")
bracketPram32 = part.CreateBracketParam()
bracketPram32.DefinitionType=1
bracketPram32.BracketName="HK.Casing.Wall.Fore.DL00.Deck.A"
bracketPram32.MaterialName="SS400"
bracketPram32.BaseElement=profile52[0]
bracketPram32.UseSideSheetForPlane=False
bracketPram32.Mold="+"
bracketPram32.Thickness="7.9999999999999964"
bracketPram32.BracketType=1501
bracketPram32.Scallop1Type=1801
bracketPram32.Scallop1Params=["0"]
bracketPram32.Scallop2Type=0
bracketPram32.Surfaces1=[profile52[0]+",FL"]
bracketPram32.RevSf1=False
bracketPram32.Surfaces2=[profile54[0]+",FL"]
bracketPram32.RevSf2=False
bracketPram32.RevSf3=False
bracketPram32.Sf1DimensionType=1531
bracketPram32.Sf1DimensonParams=["200","15"]
bracketPram32.Sf2DimensionType=1531
bracketPram32.Sf2DimensonParams=["200","15"]
bracket32 = part.CreateBracket(bracketPram32,False)
part.SetElementColor(bracket32,"0","255","255","0.19999998807907104")
ProfilePram101 = part.CreateProfileParam()
ProfilePram101.DefinitionType=1
ProfilePram101.BasePlane="PL,O,"+var_elm15+","+"PL,X"
ProfilePram101.AddAttachSurfaces(extrude_sheet4)
ProfilePram101.ProfileName="HK.Casing.Wall.Side.FR13.BCP"
ProfilePram101.MaterialName="SS400"
ProfilePram101.ProfileType=1003
ProfilePram101.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram101.Mold="+"
ProfilePram101.ReverseDir=False
ProfilePram101.ReverseAngle=True
ProfilePram101.CalcSnipOnlyAttachLines=False
ProfilePram101.AttachDirMethod=0
ProfilePram101.CCWDefAngle=False
ProfilePram101.AddEnd1Elements(extrude_sheet6)
ProfilePram101.End1Type=1103
ProfilePram101.End1TypeParams=["0"]
ProfilePram101.AddEnd2Elements(extrude_sheet1)
ProfilePram101.End2Type=1103
ProfilePram101.End2TypeParams=["0"]
ProfilePram101.End1ScallopType=1120
ProfilePram101.End1ScallopTypeParams=["50"]
ProfilePram101.End2ScallopType=1120
ProfilePram101.End2ScallopTypeParams=["50"]
profile101 = part.CreateProfile(ProfilePram101,False)
part.SetElementColor(profile101[0],"148","0","211","0.39999997615814209")
mirror_copied29 = part.MirrorCopy([profile101[0]],"PL,Y","")
part.SetElementColor(mirror_copied29[0],"148","0","211","0.39999997615814209")
ProfilePram102 = part.CreateProfileParam()
ProfilePram102.DefinitionType=1
ProfilePram102.BasePlane="PL,O,"+var_elm11+","+"PL,X"
ProfilePram102.AddAttachSurfaces(extrude_sheet4)
ProfilePram102.ProfileName="HK.Casing.Wall.Side.FR11.ABP"
ProfilePram102.MaterialName="SS400"
ProfilePram102.ProfileType=1002
ProfilePram102.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram102.Mold="+"
ProfilePram102.ReverseDir=False
ProfilePram102.ReverseAngle=True
ProfilePram102.CalcSnipOnlyAttachLines=False
ProfilePram102.AttachDirMethod=0
ProfilePram102.CCWDefAngle=False
ProfilePram102.AddEnd1Elements(extrude_sheet1)
ProfilePram102.End1Type=1102
ProfilePram102.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram102.AddEnd2Elements(extrude_sheet2)
ProfilePram102.End2Type=1102
ProfilePram102.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram102.End1ScallopType=1121
ProfilePram102.End1ScallopTypeParams=["35","40"]
ProfilePram102.End2ScallopType=1121
ProfilePram102.End2ScallopTypeParams=["35","40"]
profile102 = part.CreateProfile(ProfilePram102,False)
part.SetElementColor(profile102[0],"255","0","0","0.19999998807907104")
mirror_copied30 = part.MirrorCopy([profile56[0]],"PL,Y","")
part.SetElementColor(mirror_copied30[0],"255","0","0","0.19999998807907104")
ProfilePram103 = part.CreateProfileParam()
ProfilePram103.DefinitionType=1
ProfilePram103.BasePlane="PL,O,"+var_elm12+","+"PL,X"
ProfilePram103.AddAttachSurfaces(extrude_sheet4)
ProfilePram103.ProfileName="HK.Casing.Wall.Side.FR08.ABP"
ProfilePram103.MaterialName="SS400"
ProfilePram103.ProfileType=1002
ProfilePram103.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram103.Mold="+"
ProfilePram103.ReverseDir=False
ProfilePram103.ReverseAngle=True
ProfilePram103.CalcSnipOnlyAttachLines=False
ProfilePram103.AttachDirMethod=0
ProfilePram103.CCWDefAngle=False
ProfilePram103.AddEnd1Elements(extrude_sheet1)
ProfilePram103.End1Type=1102
ProfilePram103.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram103.AddEnd2Elements(extrude_sheet2)
ProfilePram103.End2Type=1102
ProfilePram103.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram103.End1ScallopType=1121
ProfilePram103.End1ScallopTypeParams=["35","40"]
ProfilePram103.End2ScallopType=1121
ProfilePram103.End2ScallopTypeParams=["35","40"]
profile103 = part.CreateProfile(ProfilePram103,False)
part.SetElementColor(profile103[0],"255","0","0","0.19999998807907104")
mirror_copied31 = part.MirrorCopy([profile103[0]],"PL,Y","")
part.SetElementColor(mirror_copied31[0],"255","0","0","0.19999998807907104")
ProfilePram104 = part.CreateProfileParam()
ProfilePram104.DefinitionType=1
ProfilePram104.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram104.AddAttachSurfaces(extrude_sheet5)
ProfilePram104.ProfileName="HK.Casing.Wall.Fore.DL01.OAP"
ProfilePram104.MaterialName="SS400"
ProfilePram104.ProfileType=1002
ProfilePram104.ProfileParams=["125","75","7","10","5"]
ProfilePram104.Mold="+"
ProfilePram104.ReverseDir=True
ProfilePram104.ReverseAngle=True
ProfilePram104.CalcSnipOnlyAttachLines=False
ProfilePram104.AttachDirMethod=0
ProfilePram104.CCWDefAngle=False
ProfilePram104.AddEnd1Elements(extrude_sheet2)
ProfilePram104.End1Type=1102
ProfilePram104.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram104.AddEnd2Elements(extrude_sheet8)
ProfilePram104.End2Type=1102
ProfilePram104.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram104.End1ScallopType=1121
ProfilePram104.End1ScallopTypeParams=["25","40"]
ProfilePram104.End2ScallopType=1121
ProfilePram104.End2ScallopTypeParams=["25","40"]
profile104 = part.CreateProfile(ProfilePram104,False)
part.SetElementColor(profile104[0],"255","0","0","0.19999998807907104")
solid12 = part.CreateSolid("HK.Casing.Wall.Side.CDP","","SS400")
part.SetElementColor(solid12,"139","69","19","0.79999995231628418")
thicken12 = part.CreateThicken("厚み付け7",solid12,"+",[extrude_sheet4],"-","10","0","0",False,False)
solid13 = part.CreateSolid("HK.Casing.Wall.Aft.BC","","SS400")
part.SetElementColor(solid13,"139","69","19","0.79999995231628418")
thicken13 = part.CreateThicken("厚み付け12",solid13,"+",[extrude_sheet3],"-","10","0","0",False,False)
extrudePram40 = part.CreateLinearSweepParam()
extrudePram40.Name="積-押し出し23"
extrudePram40.AddProfile(extrude_sheet4)
extrudePram40.DirectionType="R"
extrudePram40.DirectionParameter1="50000"
extrudePram40.SweepDirection="+Y"
extrudePram40.RefByGeometricMethod=True
extrude31 = part.CreateLinearSweep(solid13,"*",extrudePram40,False)
extrudePram41 = part.CreateLinearSweepParam()
extrudePram41.Name="積-押し出し24"
extrudePram41.AddProfile(extrude_sheet9)
extrudePram41.DirectionType="N"
extrudePram41.DirectionParameter1="50000"
extrudePram41.SweepDirection="+Y"
extrudePram41.RefByGeometricMethod=True
extrude32 = part.CreateLinearSweep(solid13,"*",extrudePram41,False)
ProfilePram105 = part.CreateProfileParam()
ProfilePram105.DefinitionType=1
ProfilePram105.BasePlane="PL,O,"+var_elm9+","+"PL,X"
ProfilePram105.AddAttachSurfaces(extrude_sheet4)
ProfilePram105.ProfileName="HK.Casing.Wall.Side.FR09.ABP"
ProfilePram105.MaterialName="SS400"
ProfilePram105.ProfileType=1003
ProfilePram105.ProfileParams=["200","90","9.0000000000000018","14","14","7"]
ProfilePram105.Mold="+"
ProfilePram105.ReverseDir=False
ProfilePram105.ReverseAngle=True
ProfilePram105.CalcSnipOnlyAttachLines=False
ProfilePram105.AttachDirMethod=0
ProfilePram105.CCWDefAngle=False
ProfilePram105.AddEnd1Elements(extrude_sheet1)
ProfilePram105.End1Type=1103
ProfilePram105.End1TypeParams=["0"]
ProfilePram105.AddEnd2Elements(extrude_sheet2)
ProfilePram105.End2Type=1103
ProfilePram105.End2TypeParams=["0"]
ProfilePram105.End1ScallopType=1120
ProfilePram105.End1ScallopTypeParams=["50"]
ProfilePram105.End2ScallopType=1120
ProfilePram105.End2ScallopTypeParams=["50"]
profile105 = part.CreateProfile(ProfilePram105,False)
part.SetElementColor(profile105[0],"148","0","211","0.39999997615814209")
ProfilePram106 = part.CreateProfileParam()
ProfilePram106.DefinitionType=1
ProfilePram106.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram106.AddAttachSurfaces(extrude_sheet3)
ProfilePram106.ProfileName="HK.Casing.Wall.Aft.DL01.BCP"
ProfilePram106.MaterialName="SS400"
ProfilePram106.ProfileType=1002
ProfilePram106.ProfileParams=["125","75","7","10","5"]
ProfilePram106.Mold="+"
ProfilePram106.ReverseDir=False
ProfilePram106.ReverseAngle=True
ProfilePram106.CalcSnipOnlyAttachLines=False
ProfilePram106.AttachDirMethod=0
ProfilePram106.CCWDefAngle=False
ProfilePram106.AddEnd1Elements(extrude_sheet6)
ProfilePram106.End1Type=1102
ProfilePram106.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram106.AddEnd2Elements(extrude_sheet1)
ProfilePram106.End2Type=1102
ProfilePram106.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram106.End1ScallopType=1121
ProfilePram106.End1ScallopTypeParams=["25","40"]
ProfilePram106.End2ScallopType=1121
ProfilePram106.End2ScallopTypeParams=["25","40"]
profile106 = part.CreateProfile(ProfilePram106,False)
part.SetElementColor(profile106[0],"255","0","0","0.19999998807907104")
bracketPram33 = part.CreateBracketParam()
bracketPram33.DefinitionType=1
bracketPram33.BracketName="HK.Casing.Wall.Aft.DL01.Deck.CP"
bracketPram33.MaterialName="SS400"
bracketPram33.BaseElement=profile106[0]
bracketPram33.UseSideSheetForPlane=False
bracketPram33.Mold="+"
bracketPram33.Thickness="9.9999999999999982"
bracketPram33.BracketType=1505
bracketPram33.BracketParams=["200"]
bracketPram33.Scallop1Type=1801
bracketPram33.Scallop1Params=["0"]
bracketPram33.Scallop2Type=0
bracketPram33.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram33.RevSf1=False
bracketPram33.Surfaces2=[profile106[0]+",FL"]
bracketPram33.RevSf2=False
bracketPram33.RevSf3=False
bracketPram33.Sf1DimensionType=1541
bracketPram33.Sf1DimensonParams=["0","100"]
bracketPram33.Sf1EndElements=["PLS","False","False","-1","0","-0",profile12[0]]
bracketPram33.Sf2DimensionType=1531
bracketPram33.Sf2DimensonParams=["200","15"]
bracket33 = part.CreateBracket(bracketPram33,False)
part.SetElementColor(bracket33,"0","255","255","0.19999998807907104")
ProfilePram107 = part.CreateProfileParam()
ProfilePram107.DefinitionType=1
ProfilePram107.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram107.AddAttachSurfaces(extrude_sheet5)
ProfilePram107.ProfileName="HK.Casing.Wall.Fore.DL03.OAP"
ProfilePram107.MaterialName="SS400"
ProfilePram107.ProfileType=1002
ProfilePram107.ProfileParams=["125","75","7","10","5"]
ProfilePram107.Mold="+"
ProfilePram107.ReverseDir=True
ProfilePram107.ReverseAngle=True
ProfilePram107.CalcSnipOnlyAttachLines=False
ProfilePram107.AttachDirMethod=0
ProfilePram107.CCWDefAngle=False
ProfilePram107.AddEnd1Elements(extrude_sheet2)
ProfilePram107.End1Type=1102
ProfilePram107.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram107.AddEnd2Elements(extrude_sheet8)
ProfilePram107.End2Type=1102
ProfilePram107.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram107.End1ScallopType=1121
ProfilePram107.End1ScallopTypeParams=["25","40"]
ProfilePram107.End2ScallopType=1121
ProfilePram107.End2ScallopTypeParams=["25","40"]
profile107 = part.CreateProfile(ProfilePram107,False)
part.SetElementColor(profile107[0],"255","0","0","0.19999998807907104")
ProfilePram108 = part.CreateProfileParam()
ProfilePram108.DefinitionType=1
ProfilePram108.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram108.AddAttachSurfaces(extrude_sheet2)
ProfilePram108.ProfileName="HK.Casing.Deck.A.DL03.FP"
ProfilePram108.MaterialName="SS400"
ProfilePram108.ProfileType=1002
ProfilePram108.ProfileParams=["125","75","7","10","5"]
ProfilePram108.Mold="+"
ProfilePram108.ReverseDir=True
ProfilePram108.ReverseAngle=True
ProfilePram108.CalcSnipOnlyAttachLines=False
ProfilePram108.AttachDirMethod=0
ProfilePram108.CCWDefAngle=False
ProfilePram108.AddEnd1Elements(profile53[0])
ProfilePram108.End1Type=1102
ProfilePram108.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram108.AddEnd2Elements(profile107[0])
ProfilePram108.End2Type=1102
ProfilePram108.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram108.End1ScallopType=1121
ProfilePram108.End1ScallopTypeParams=["25","40"]
ProfilePram108.End2ScallopType=1121
ProfilePram108.End2ScallopTypeParams=["25","40"]
profile108 = part.CreateProfile(ProfilePram108,False)
part.SetElementColor(profile108[0],"255","0","0","0.19999998807907104")
bracketPram34 = part.CreateBracketParam()
bracketPram34.DefinitionType=1
bracketPram34.BracketName="HK.Casing.Wall.Aft.DL04.Deck.BP"
bracketPram34.MaterialName="SS400"
bracketPram34.BaseElement=profile33[0]
bracketPram34.UseSideSheetForPlane=False
bracketPram34.Mold="-"
bracketPram34.Thickness="7.9999999999999964"
bracketPram34.BracketType=1501
bracketPram34.Scallop1Type=1801
bracketPram34.Scallop1Params=["0"]
bracketPram34.Scallop2Type=0
bracketPram34.Surfaces1=[profile1[0]+",FL"]
bracketPram34.RevSf1=False
bracketPram34.Surfaces2=[profile33[0]+",FL"]
bracketPram34.RevSf2=False
bracketPram34.RevSf3=False
bracketPram34.Sf1DimensionType=1531
bracketPram34.Sf1DimensonParams=["250","15"]
bracketPram34.Sf2DimensionType=1531
bracketPram34.Sf2DimensonParams=["250","15"]
bracket34 = part.CreateBracket(bracketPram34,False)
part.SetElementColor(bracket34,"0","255","255","0.19999998807907104")
ProfilePram109 = part.CreateProfileParam()
ProfilePram109.DefinitionType=1
ProfilePram109.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram109.AddAttachSurfaces(extrude_sheet2)
ProfilePram109.ProfileName="HK.Casing.Deck.A.DL01.FP"
ProfilePram109.MaterialName="SS400"
ProfilePram109.ProfileType=1002
ProfilePram109.ProfileParams=["125","75","7","10","5"]
ProfilePram109.Mold="+"
ProfilePram109.ReverseDir=True
ProfilePram109.ReverseAngle=True
ProfilePram109.CalcSnipOnlyAttachLines=False
ProfilePram109.AttachDirMethod=0
ProfilePram109.CCWDefAngle=False
ProfilePram109.AddEnd1Elements(profile53[0])
ProfilePram109.End1Type=1102
ProfilePram109.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram109.AddEnd2Elements(profile104[0])
ProfilePram109.End2Type=1102
ProfilePram109.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram109.End1ScallopType=1121
ProfilePram109.End1ScallopTypeParams=["25","40"]
ProfilePram109.End2ScallopType=1121
ProfilePram109.End2ScallopTypeParams=["25","40"]
profile109 = part.CreateProfile(ProfilePram109,False)
part.SetElementColor(profile109[0],"255","0","0","0.19999998807907104")
mirror_copied32 = part.MirrorCopy([profile47[0]],"PL,Y","")
part.SetElementColor(mirror_copied32[0],"255","0","0","0.19999998807907104")
bracketPram35 = part.CreateBracketParam()
bracketPram35.DefinitionType=1
bracketPram35.BracketName="HK.Casing.Wall.Fore.DL05.Deck.DP"
bracketPram35.MaterialName="SS400"
bracketPram35.BaseElement=profile35[0]
bracketPram35.UseSideSheetForPlane=False
bracketPram35.Mold="+"
bracketPram35.Thickness="7.9999999999999964"
bracketPram35.BracketType=1501
bracketPram35.Scallop1Type=1801
bracketPram35.Scallop1Params=["0"]
bracketPram35.Scallop2Type=0
bracketPram35.Surfaces1=[profile35[0]+",FL"]
bracketPram35.RevSf1=False
bracketPram35.Surfaces2=[profile15[0]+",FL"]
bracketPram35.RevSf2=False
bracketPram35.RevSf3=False
bracketPram35.Sf1DimensionType=1531
bracketPram35.Sf1DimensonParams=["200","15"]
bracketPram35.Sf2DimensionType=1531
bracketPram35.Sf2DimensonParams=["200","15"]
bracket35 = part.CreateBracket(bracketPram35,False)
part.SetElementColor(bracket35,"0","255","255","0.19999998807907104")
mirror_copied33 = part.MirrorCopy([bracket35],"PL,Y","")
part.SetElementColor(mirror_copied33[0],"0","255","255","0.19999998807907104")
mirror_copied34 = part.MirrorCopy([bracket14],"PL,Y","")
part.SetElementColor(mirror_copied34[0],"0","255","255","0.19999998807907104")
ProfilePram110 = part.CreateProfileParam()
ProfilePram110.DefinitionType=1
ProfilePram110.BasePlane="PL,O,"+var_elm15+","+"PL,X"
ProfilePram110.AddAttachSurfaces(extrude_sheet6)
ProfilePram110.ProfileName="HK.Casing.Deck.C.FR13P"
ProfilePram110.MaterialName="SS400"
ProfilePram110.ProfileType=1003
ProfilePram110.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram110.Mold="+"
ProfilePram110.ReverseDir=True
ProfilePram110.ReverseAngle=False
ProfilePram110.CalcSnipOnlyAttachLines=False
ProfilePram110.AttachDirMethod=0
ProfilePram110.CCWDefAngle=False
ProfilePram110.AddEnd1Elements(profile9[0])
ProfilePram110.End1Type=1113
ProfilePram110.End1TypeParams=["0","79"]
ProfilePram110.AddEnd2Elements(profile101[0])
ProfilePram110.End2Type=1102
ProfilePram110.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram110.End1ScallopType=1120
ProfilePram110.End1ScallopTypeParams=["50"]
ProfilePram110.End2ScallopType=1120
ProfilePram110.End2ScallopTypeParams=["50"]
profile110 = part.CreateProfile(ProfilePram110,False)
part.SetElementColor(profile110[0],"148","0","211","0.39999997615814209")
solid14 = part.CreateSolid("HK.Casing.Wall.Fore.BC","","SS400")
part.SetElementColor(solid14,"139","69","19","0.79999995231628418")
thicken14 = part.CreateThicken("厚み付け16",solid14,"+",[extrude_sheet5],"+","10","0","0",False,False)
extrudePram42 = part.CreateLinearSweepParam()
extrudePram42.Name="積-押し出し39"
extrudePram42.AddProfile(extrude_sheet4)
extrudePram42.DirectionType="R"
extrudePram42.DirectionParameter1="50000"
extrudePram42.SweepDirection="+Y"
extrudePram42.RefByGeometricMethod=True
extrude33 = part.CreateLinearSweep(solid14,"*",extrudePram42,False)
extrudePram43 = part.CreateLinearSweepParam()
extrudePram43.Name="積-押し出し40"
extrudePram43.AddProfile(extrude_sheet9)
extrudePram43.DirectionType="N"
extrudePram43.DirectionParameter1="50000"
extrudePram43.SweepDirection="+Y"
extrudePram43.RefByGeometricMethod=True
extrude34 = part.CreateLinearSweep(solid14,"*",extrudePram43,False)
bracketPram36 = part.CreateBracketParam()
bracketPram36.DefinitionType=1
bracketPram36.BracketName="HK.Casing.Deck.D.FR09P"
bracketPram36.MaterialName="SS400"
bracketPram36.BaseElement=profile68[0]
bracketPram36.UseSideSheetForPlane=False
bracketPram36.Mold="+"
bracketPram36.Thickness="8.9999999999999982"
bracketPram36.BracketType=1501
bracketPram36.Scallop1Type=1801
bracketPram36.Scallop1Params=["50"]
bracketPram36.Scallop2Type=0
bracketPram36.Surfaces1=[profile16[0]+",WF"]
bracketPram36.RevSf1=False
bracketPram36.Surfaces2=[profile68[0]+",FL"]
bracketPram36.RevSf2=False
bracketPram36.RevSf3=False
bracketPram36.FlangeType=262
bracketPram36.FlangeParams=["75","30","29.999999999999996","30","50","1"]
bracketPram36.RevFlange=False
bracketPram36.Sf1DimensionType=1541
bracketPram36.Sf1DimensonParams=["0","80"]
bracketPram36.Sf1EndElements=[profile16[1]+",FR"]
bracketPram36.Sf2DimensionType=1531
bracketPram36.Sf2DimensonParams=["300","15"]
bracket36 = part.CreateBracket(bracketPram36,False)
part.SetElementColor(bracket36,"0","255","255","0.19999998807907104")
mirror_copied35 = part.MirrorCopy([bracket27],"PL,Y","")
part.SetElementColor(mirror_copied35[0],"0","255","255","0.19999998807907104")
bracketPram37 = part.CreateBracketParam()
bracketPram37.DefinitionType=1
bracketPram37.BracketName="HK.Casing.Wall.Side.FR08.Deck.BP"
bracketPram37.MaterialName="SS400"
bracketPram37.BaseElement=profile103[0]
bracketPram37.UseSideSheetForPlane=False
bracketPram37.Mold="+"
bracketPram37.Thickness="9.9999999999999982"
bracketPram37.BracketType=1505
bracketPram37.BracketParams=["200"]
bracketPram37.Scallop1Type=1801
bracketPram37.Scallop1Params=["0"]
bracketPram37.Scallop2Type=0
bracketPram37.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram37.RevSf1=False
bracketPram37.Surfaces2=[profile103[0]+",FL"]
bracketPram37.RevSf2=False
bracketPram37.RevSf3=False
bracketPram37.Sf1DimensionType=1541
bracketPram37.Sf1DimensonParams=["0","100"]
bracketPram37.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram37.Sf2DimensionType=1531
bracketPram37.Sf2DimensonParams=["200","15"]
bracket37 = part.CreateBracket(bracketPram37,False)
part.SetElementColor(bracket37,"0","255","255","0.19999998807907104")
bracketPram38 = part.CreateBracketParam()
bracketPram38.DefinitionType=1
bracketPram38.BracketName="HK.Casing.Deck.D.FR13P"
bracketPram38.MaterialName="SS400"
bracketPram38.BaseElement=profile65[0]
bracketPram38.UseSideSheetForPlane=False
bracketPram38.Mold="+"
bracketPram38.Thickness="7.9999999999999964"
bracketPram38.BracketType=1501
bracketPram38.Scallop1Type=1801
bracketPram38.Scallop1Params=["0"]
bracketPram38.Scallop2Type=0
bracketPram38.Surfaces1=[profile16[0]+",WB"]
bracketPram38.RevSf1=False
bracketPram38.Surfaces2=[profile65[0]+",FL"]
bracketPram38.RevSf2=False
bracketPram38.RevSf3=False
bracketPram38.Sf1DimensionType=1531
bracketPram38.Sf1DimensonParams=["250","15"]
bracketPram38.Sf2DimensionType=1531
bracketPram38.Sf2DimensonParams=["250","15"]
bracket38 = part.CreateBracket(bracketPram38,False)
part.SetElementColor(bracket38,"0","255","255","0.19999998807907104")
mirror_copied36 = part.MirrorCopy([bracket38],"PL,Y","")
part.SetElementColor(mirror_copied36[0],"0","255","255","0.19999998807907104")
mirror_copied37 = part.MirrorCopy([profile76[0]],"PL,Y","")
part.SetElementColor(mirror_copied37[0],"255","0","0","0.19999998807907104")
bracketPram39 = part.CreateBracketParam()
bracketPram39.DefinitionType=1
bracketPram39.BracketName="HK.Casing.Wall.Fore.DL02.Deck.BP"
bracketPram39.MaterialName="SS400"
bracketPram39.BaseElement=profile88[0]
bracketPram39.UseSideSheetForPlane=False
bracketPram39.Mold="-"
bracketPram39.Thickness="9.9999999999999982"
bracketPram39.BracketType=1501
bracketPram39.Scallop1Type=1801
bracketPram39.Scallop1Params=["50"]
bracketPram39.Scallop2Type=0
bracketPram39.Surfaces1=["PLS","False","False","-1","-0","0",profile88[1]]
bracketPram39.RevSf1=False
bracketPram39.Surfaces2=["PLS","False","False","0","-0","-1",solid1]
bracketPram39.RevSf2=False
bracketPram39.RevSf3=False
bracketPram39.FlangeType=265
bracketPram39.FlangeParams=["75","30","29.999999999999996","30","30","30","30","150","30"]
bracketPram39.RevFlange=False
bracketPram39.Sf1DimensionType=1531
bracketPram39.Sf1DimensonParams=["500","15"]
bracketPram39.Sf2DimensionType=1541
bracketPram39.Sf2DimensonParams=["0","200"]
bracketPram39.Sf2EndElements=["PLS","False","False","1","-0","0",profile71[0]]
bracketPram39.ScallopEnd2LowerType=1801
bracketPram39.ScallopEnd2LowerParams=["50"]
bracket39 = part.CreateBracket(bracketPram39,False)
part.SetElementColor(bracket39,"0","255","255","0.19999998807907104")
ProfilePram111 = part.CreateProfileParam()
ProfilePram111.DefinitionType=1
ProfilePram111.BasePlane="PL,O,"+var_elm11+","+"PL,X"
ProfilePram111.AddAttachSurfaces(extrude_sheet4)
ProfilePram111.ProfileName="HK.Casing.Wall.Side.FR11.CDP"
ProfilePram111.MaterialName="SS400"
ProfilePram111.ProfileType=1002
ProfilePram111.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram111.Mold="+"
ProfilePram111.ReverseDir=False
ProfilePram111.ReverseAngle=True
ProfilePram111.CalcSnipOnlyAttachLines=False
ProfilePram111.AttachDirMethod=0
ProfilePram111.CCWDefAngle=False
ProfilePram111.AddEnd1Elements(extrude_sheet7)
ProfilePram111.End1Type=1102
ProfilePram111.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram111.AddEnd2Elements(extrude_sheet6)
ProfilePram111.End2Type=1102
ProfilePram111.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram111.End1ScallopType=1121
ProfilePram111.End1ScallopTypeParams=["35","40"]
ProfilePram111.End2ScallopType=1121
ProfilePram111.End2ScallopTypeParams=["35","40"]
profile111 = part.CreateProfile(ProfilePram111,False)
part.SetElementColor(profile111[0],"255","0","0","0.19999998807907104")
mirror_copied38 = part.MirrorCopy([bracket9],"PL,Y","")
part.SetElementColor(mirror_copied38[0],"0","255","255","0.19999998807907104")
bracketPram40 = part.CreateBracketParam()
bracketPram40.DefinitionType=1
bracketPram40.BracketName="HK.Casing.Wall.Side.FR07.Deck.BP"
bracketPram40.MaterialName="SS400"
bracketPram40.BaseElement=profile91[0]
bracketPram40.UseSideSheetForPlane=False
bracketPram40.Mold="+"
bracketPram40.Thickness="9.9999999999999982"
bracketPram40.BracketType=1505
bracketPram40.BracketParams=["200"]
bracketPram40.Scallop1Type=1801
bracketPram40.Scallop1Params=["0"]
bracketPram40.Scallop2Type=0
bracketPram40.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram40.RevSf1=False
bracketPram40.Surfaces2=[profile91[0]+",FL"]
bracketPram40.RevSf2=False
bracketPram40.RevSf3=False
bracketPram40.Sf1DimensionType=1541
bracketPram40.Sf1DimensonParams=["0","100"]
bracketPram40.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram40.Sf2DimensionType=1531
bracketPram40.Sf2DimensonParams=["200","15"]
bracket40 = part.CreateBracket(bracketPram40,False)
part.SetElementColor(bracket40,"0","255","255","0.19999998807907104")
bracketPram41 = part.CreateBracketParam()
bracketPram41.DefinitionType=1
bracketPram41.BracketName="HK.Casing.Wall.Fore.DL05.Deck.AP"
bracketPram41.MaterialName="SS400"
bracketPram41.BaseElement=profile51[0]
bracketPram41.UseSideSheetForPlane=False
bracketPram41.Mold="+"
bracketPram41.Thickness="7.9999999999999964"
bracketPram41.BracketType=1501
bracketPram41.Scallop1Type=1801
bracketPram41.Scallop1Params=["0"]
bracketPram41.Scallop2Type=0
bracketPram41.Surfaces1=[profile50[0]+",FL"]
bracketPram41.RevSf1=False
bracketPram41.Surfaces2=[profile51[0]+",FL"]
bracketPram41.RevSf2=False
bracketPram41.RevSf3=False
bracketPram41.Sf1DimensionType=1531
bracketPram41.Sf1DimensonParams=["200","15"]
bracketPram41.Sf2DimensionType=1531
bracketPram41.Sf2DimensonParams=["200","15"]
bracket41 = part.CreateBracket(bracketPram41,False)
part.SetElementColor(bracket41,"0","255","255","0.19999998807907104")
mirror_copied39 = part.MirrorCopy([bracket41],"PL,Y","")
part.SetElementColor(mirror_copied39[0],"0","255","255","0.19999998807907104")
mirror_copied40 = part.MirrorCopy([profile4[0]],"PL,Y","")
part.SetElementColor(mirror_copied40[0],"255","0","0","0.19999998807907104")
mirror_copied41 = part.MirrorCopy([profile18[0]],"PL,Y","")
part.SetElementColor(mirror_copied41[0],"255","0","0","0.19999998807907104")
ProfilePram112 = part.CreateProfileParam()
ProfilePram112.DefinitionType=1
ProfilePram112.BasePlane="PL,O,"+var_elm9+","+"PL,X"
ProfilePram112.AddAttachSurfaces(extrude_sheet1)
ProfilePram112.ProfileName="HK.Casing.Deck.B.FR09P"
ProfilePram112.MaterialName="SS400"
ProfilePram112.ProfileType=1003
ProfilePram112.ProfileParams=["300","90","11","16","19","9.5"]
ProfilePram112.Mold="+"
ProfilePram112.ReverseDir=True
ProfilePram112.ReverseAngle=False
ProfilePram112.CalcSnipOnlyAttachLines=False
ProfilePram112.AttachDirMethod=0
ProfilePram112.CCWDefAngle=False
ProfilePram112.AddEnd1Elements(profile33[0])
ProfilePram112.End1Type=1113
ProfilePram112.End1TypeParams=["0","79"]
ProfilePram112.AddEnd2Elements(profile105[0])
ProfilePram112.End2Type=1102
ProfilePram112.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram112.End1ScallopType=1120
ProfilePram112.End1ScallopTypeParams=["50"]
ProfilePram112.End2ScallopType=1120
ProfilePram112.End2ScallopTypeParams=["50"]
profile112 = part.CreateProfile(ProfilePram112,False)
part.SetElementColor(profile112[0],"148","0","211","0.39999997615814209")
bracketPram42 = part.CreateBracketParam()
bracketPram42.DefinitionType=1
bracketPram42.BracketName="HK.Casing.Wall.Side.FR11.Deck.BP"
bracketPram42.MaterialName="SS400"
bracketPram42.BaseElement=profile102[0]
bracketPram42.UseSideSheetForPlane=False
bracketPram42.Mold="+"
bracketPram42.Thickness="9.9999999999999982"
bracketPram42.BracketType=1505
bracketPram42.BracketParams=["200"]
bracketPram42.Scallop1Type=1801
bracketPram42.Scallop1Params=["0"]
bracketPram42.Scallop2Type=0
bracketPram42.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram42.RevSf1=False
bracketPram42.Surfaces2=[profile102[0]+",FL"]
bracketPram42.RevSf2=False
bracketPram42.RevSf3=False
bracketPram42.Sf1DimensionType=1541
bracketPram42.Sf1DimensonParams=["0","100"]
bracketPram42.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram42.Sf2DimensionType=1531
bracketPram42.Sf2DimensonParams=["200","15"]
bracket42 = part.CreateBracket(bracketPram42,False)
part.SetElementColor(bracket42,"0","255","255","0.19999998807907104")
mirror_copied42 = part.MirrorCopy([bracket42],"PL,Y","")
part.SetElementColor(mirror_copied42[0],"0","255","255","0.19999998807907104")
bracketPram43 = part.CreateBracketParam()
bracketPram43.DefinitionType=1
bracketPram43.BracketName="HK.Casing.Wall.Aft.DL01.Deck.DP"
bracketPram43.MaterialName="SS400"
bracketPram43.BaseElement=profile76[0]
bracketPram43.UseSideSheetForPlane=False
bracketPram43.Mold="+"
bracketPram43.Thickness="7.9999999999999964"
bracketPram43.BracketType=1501
bracketPram43.Scallop1Type=1801
bracketPram43.Scallop1Params=["0"]
bracketPram43.Scallop2Type=0
bracketPram43.Surfaces1=[profile76[0]+",FL"]
bracketPram43.RevSf1=False
bracketPram43.Surfaces2=[profile30[0]+",FL"]
bracketPram43.RevSf2=False
bracketPram43.RevSf3=False
bracketPram43.Sf1DimensionType=1531
bracketPram43.Sf1DimensonParams=["200","15"]
bracketPram43.Sf2DimensionType=1531
bracketPram43.Sf2DimensonParams=["200","15"]
bracket43 = part.CreateBracket(bracketPram43,False)
part.SetElementColor(bracket43,"0","255","255","0.19999998807907104")
mirror_copied43 = part.MirrorCopy([bracket43],"PL,Y","")
part.SetElementColor(mirror_copied43[0],"0","255","255","0.19999998807907104")
mirror_copied44 = part.MirrorCopy([profile91[0]],"PL,Y","")
part.SetElementColor(mirror_copied44[0],"255","0","0","0.19999998807907104")
bracketPram44 = part.CreateBracketParam()
bracketPram44.DefinitionType=1
bracketPram44.BracketName="HK.Casing.Wall.Fore.DL01.Deck.DP"
bracketPram44.MaterialName="SS400"
bracketPram44.BaseElement=profile67[0]
bracketPram44.UseSideSheetForPlane=False
bracketPram44.Mold="+"
bracketPram44.Thickness="7.9999999999999964"
bracketPram44.BracketType=1501
bracketPram44.Scallop1Type=1801
bracketPram44.Scallop1Params=["0"]
bracketPram44.Scallop2Type=0
bracketPram44.Surfaces1=[profile67[0]+",FL"]
bracketPram44.RevSf1=False
bracketPram44.Surfaces2=[profile66[0]+",FL"]
bracketPram44.RevSf2=False
bracketPram44.RevSf3=False
bracketPram44.Sf1DimensionType=1531
bracketPram44.Sf1DimensonParams=["200","15"]
bracketPram44.Sf2DimensionType=1531
bracketPram44.Sf2DimensonParams=["200","15"]
bracket44 = part.CreateBracket(bracketPram44,False)
part.SetElementColor(bracket44,"0","255","255","0.19999998807907104")
mirror_copied45 = part.MirrorCopy([bracket44],"PL,Y","")
part.SetElementColor(mirror_copied45[0],"0","255","255","0.19999998807907104")
bracketPram45 = part.CreateBracketParam()
bracketPram45.DefinitionType=1
bracketPram45.BracketName="HK.Casing.Wall.Aft.DL05.Deck.DP"
bracketPram45.MaterialName="SS400"
bracketPram45.BaseElement=profile73[0]
bracketPram45.UseSideSheetForPlane=False
bracketPram45.Mold="+"
bracketPram45.Thickness="7.9999999999999964"
bracketPram45.BracketType=1501
bracketPram45.Scallop1Type=1801
bracketPram45.Scallop1Params=["0"]
bracketPram45.Scallop2Type=0
bracketPram45.Surfaces1=[profile73[0]+",FL"]
bracketPram45.RevSf1=False
bracketPram45.Surfaces2=[profile15[0]+",FL"]
bracketPram45.RevSf2=False
bracketPram45.RevSf3=False
bracketPram45.Sf1DimensionType=1531
bracketPram45.Sf1DimensonParams=["200","15"]
bracketPram45.Sf2DimensionType=1531
bracketPram45.Sf2DimensonParams=["200","15"]
bracket45 = part.CreateBracket(bracketPram45,False)
part.SetElementColor(bracket45,"0","255","255","0.19999998807907104")
mirror_copied46 = part.MirrorCopy([bracket45],"PL,Y","")
part.SetElementColor(mirror_copied46[0],"0","255","255","0.19999998807907104")
mirror_copied47 = part.MirrorCopy([profile31[0]],"PL,Y","")
part.SetElementColor(mirror_copied47[0],"255","0","0","0.19999998807907104")
mirror_copied48 = part.MirrorCopy([bracket13],"PL,Y","")
part.SetElementColor(mirror_copied48[0],"0","255","255","0.19999998807907104")
mirror_copied49 = part.MirrorCopy([profile69[0]],"PL,Y","")
part.SetElementColor(mirror_copied49[0],"148","0","211","0.39999997615814209")
mirror_copied50 = part.MirrorCopy([profile62[0]],"PL,Y","")
part.SetElementColor(mirror_copied50[0],"255","0","0","0.19999998807907104")
bracketPram46 = part.CreateBracketParam()
bracketPram46.DefinitionType=1
bracketPram46.BracketName="HK.Casing.Wall.Aft.DL03.Deck.CP"
bracketPram46.MaterialName="SS400"
bracketPram46.BaseElement=profile64[0]
bracketPram46.UseSideSheetForPlane=False
bracketPram46.Mold="+"
bracketPram46.Thickness="9.9999999999999982"
bracketPram46.BracketType=1505
bracketPram46.BracketParams=["200"]
bracketPram46.Scallop1Type=1801
bracketPram46.Scallop1Params=["0"]
bracketPram46.Scallop2Type=0
bracketPram46.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram46.RevSf1=False
bracketPram46.Surfaces2=[profile64[0]+",FL"]
bracketPram46.RevSf2=False
bracketPram46.RevSf3=False
bracketPram46.Sf1DimensionType=1541
bracketPram46.Sf1DimensonParams=["0","100"]
bracketPram46.Sf1EndElements=["PLS","False","False","-1","0","-0",profile12[0]]
bracketPram46.Sf2DimensionType=1531
bracketPram46.Sf2DimensonParams=["200","15"]
bracket46 = part.CreateBracket(bracketPram46,False)
part.SetElementColor(bracket46,"0","255","255","0.19999998807907104")
bracketPram47 = part.CreateBracketParam()
bracketPram47.DefinitionType=1
bracketPram47.BracketName="HK.Casing.Wall.Aft.DL01.Deck.AP"
bracketPram47.MaterialName="SS400"
bracketPram47.BaseElement=profile82[0]
bracketPram47.UseSideSheetForPlane=False
bracketPram47.Mold="+"
bracketPram47.Thickness="7.9999999999999964"
bracketPram47.BracketType=1505
bracketPram47.BracketParams=["200"]
bracketPram47.Scallop1Type=1801
bracketPram47.Scallop1Params=["0"]
bracketPram47.Scallop2Type=0
bracketPram47.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram47.RevSf1=False
bracketPram47.Surfaces2=[profile82[0]+",FL"]
bracketPram47.RevSf2=False
bracketPram47.RevSf3=False
bracketPram47.Sf1DimensionType=1541
bracketPram47.Sf1DimensonParams=["0","100"]
bracketPram47.Sf1EndElements=["PLS","False","False","-1","0","-0",profile63[0]]
bracketPram47.Sf2DimensionType=1531
bracketPram47.Sf2DimensonParams=["200","15"]
bracket47 = part.CreateBracket(bracketPram47,False)
part.SetElementColor(bracket47,"0","255","255","0.19999998807907104")
mirror_copied51 = part.MirrorCopy([profile107[0]],"PL,Y","")
part.SetElementColor(mirror_copied51[0],"255","0","0","0.19999998807907104")
bracketPram48 = part.CreateBracketParam()
bracketPram48.DefinitionType=1
bracketPram48.BracketName="HK.Casing.Wall.Side.FR13.Deck.DP"
bracketPram48.MaterialName="SS400"
bracketPram48.BaseElement=profile46[0]
bracketPram48.UseSideSheetForPlane=False
bracketPram48.Mold="+"
bracketPram48.Thickness="7.9999999999999964"
bracketPram48.BracketType=1501
bracketPram48.Scallop1Type=1801
bracketPram48.Scallop1Params=["0"]
bracketPram48.Scallop2Type=0
bracketPram48.Surfaces1=[profile46[0]+",FL"]
bracketPram48.RevSf1=False
bracketPram48.Surfaces2=[profile45[0]+",FL"]
bracketPram48.RevSf2=False
bracketPram48.RevSf3=False
bracketPram48.Sf1DimensionType=1531
bracketPram48.Sf1DimensonParams=["250","15"]
bracketPram48.Sf2DimensionType=1531
bracketPram48.Sf2DimensonParams=["250","15"]
bracket48 = part.CreateBracket(bracketPram48,False)
part.SetElementColor(bracket48,"0","255","255","0.19999998807907104")
bracketPram49 = part.CreateBracketParam()
bracketPram49.DefinitionType=1
bracketPram49.BracketName="HK.Casing.Wall.Side.FR07.Deck.AP"
bracketPram49.MaterialName="SS400"
bracketPram49.BaseElement=profile39[0]
bracketPram49.UseSideSheetForPlane=False
bracketPram49.Mold="+"
bracketPram49.Thickness="9.9999999999999982"
bracketPram49.BracketType=1505
bracketPram49.BracketParams=["200"]
bracketPram49.Scallop1Type=1801
bracketPram49.Scallop1Params=["0"]
bracketPram49.Scallop2Type=0
bracketPram49.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram49.RevSf1=False
bracketPram49.Surfaces2=[profile39[0]+",FL"]
bracketPram49.RevSf2=False
bracketPram49.RevSf3=False
bracketPram49.Sf1DimensionType=1541
bracketPram49.Sf1DimensonParams=["0","100"]
bracketPram49.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile51[0]]
bracketPram49.Sf2DimensionType=1531
bracketPram49.Sf2DimensonParams=["200","15"]
bracket49 = part.CreateBracket(bracketPram49,False)
part.SetElementColor(bracket49,"0","255","255","0.19999998807907104")
mirror_copied52 = part.MirrorCopy([bracket49],"PL,Y","")
part.SetElementColor(mirror_copied52[0],"0","255","255","0.19999998807907104")
extrudePram44 = part.CreateLinearSweepParam()
extrudePram44.Name="積-押し出し22"
extrudePram44.AddProfile(extrude_sheet6)
extrudePram44.DirectionType="N"
extrudePram44.DirectionParameter1="50000"
extrudePram44.SweepDirection="+Z"
extrudePram44.RefByGeometricMethod=True
extrude35 = part.CreateLinearSweep(solid5,"*",extrudePram44,False)
ProfilePram113 = part.CreateProfileParam()
ProfilePram113.DefinitionType=1
ProfilePram113.BasePlane="PL,O,"+var_elm2+","+"PL,X"
ProfilePram113.AddAttachSurfaces(extrude_sheet4)
ProfilePram113.ProfileName="HK.Casing.Wall.Side.FR14.CDP"
ProfilePram113.MaterialName="SS400"
ProfilePram113.ProfileType=1002
ProfilePram113.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram113.Mold="+"
ProfilePram113.ReverseDir=False
ProfilePram113.ReverseAngle=True
ProfilePram113.CalcSnipOnlyAttachLines=False
ProfilePram113.AttachDirMethod=0
ProfilePram113.CCWDefAngle=False
ProfilePram113.AddEnd1Elements(extrude_sheet7)
ProfilePram113.End1Type=1102
ProfilePram113.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram113.AddEnd2Elements(extrude_sheet6)
ProfilePram113.End2Type=1102
ProfilePram113.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram113.End1ScallopType=1121
ProfilePram113.End1ScallopTypeParams=["35","40"]
ProfilePram113.End2ScallopType=1121
ProfilePram113.End2ScallopTypeParams=["35","40"]
profile113 = part.CreateProfile(ProfilePram113,False)
part.SetElementColor(profile113[0],"255","0","0","0.19999998807907104")
bracketPram50 = part.CreateBracketParam()
bracketPram50.DefinitionType=1
bracketPram50.BracketName="HK.Casing.Wall.Side.FR14.Deck.DP"
bracketPram50.MaterialName="SS400"
bracketPram50.BaseElement=profile113[0]
bracketPram50.UseSideSheetForPlane=False
bracketPram50.Mold="+"
bracketPram50.Thickness="9.9999999999999982"
bracketPram50.BracketType=1505
bracketPram50.BracketParams=["200"]
bracketPram50.Scallop1Type=1801
bracketPram50.Scallop1Params=["0"]
bracketPram50.Scallop2Type=0
bracketPram50.Surfaces1=["PLS","False","False","0","-0","-1",solid2]
bracketPram50.RevSf1=False
bracketPram50.Surfaces2=[profile113[0]+",FL"]
bracketPram50.RevSf2=False
bracketPram50.RevSf3=False
bracketPram50.Sf1DimensionType=1541
bracketPram50.Sf1DimensonParams=["0","100"]
bracketPram50.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile15[0]]
bracketPram50.Sf2DimensionType=1531
bracketPram50.Sf2DimensonParams=["200","15"]
bracket50 = part.CreateBracket(bracketPram50,False)
part.SetElementColor(bracket50,"0","255","255","0.19999998807907104")
mirror_copied53 = part.MirrorCopy([profile90[0]],"PL,Y","")
part.SetElementColor(mirror_copied53[0],"148","0","211","0.39999997615814209")
bracketPram51 = part.CreateBracketParam()
bracketPram51.DefinitionType=1
bracketPram51.BracketName="HK.Casing.Wall.Fore.DL03.Deck.AP"
bracketPram51.MaterialName="SS400"
bracketPram51.BaseElement=profile107[0]
bracketPram51.UseSideSheetForPlane=False
bracketPram51.Mold="+"
bracketPram51.Thickness="7.9999999999999964"
bracketPram51.BracketType=1501
bracketPram51.Scallop1Type=1801
bracketPram51.Scallop1Params=["0"]
bracketPram51.Scallop2Type=0
bracketPram51.Surfaces1=[profile107[0]+",FL"]
bracketPram51.RevSf1=False
bracketPram51.Surfaces2=[profile108[0]+",FL"]
bracketPram51.RevSf2=False
bracketPram51.RevSf3=False
bracketPram51.Sf1DimensionType=1531
bracketPram51.Sf1DimensonParams=["200","15"]
bracketPram51.Sf2DimensionType=1531
bracketPram51.Sf2DimensonParams=["200","15"]
bracket51 = part.CreateBracket(bracketPram51,False)
part.SetElementColor(bracket51,"0","255","255","0.19999998807907104")
ProfilePram114 = part.CreateProfileParam()
ProfilePram114.DefinitionType=1
ProfilePram114.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram114.AddAttachSurfaces(extrude_sheet1)
ProfilePram114.ProfileName="HK.Casing.Deck.B.DL03.FP"
ProfilePram114.MaterialName="SS400"
ProfilePram114.ProfileType=1002
ProfilePram114.ProfileParams=["125","75","7","10","5"]
ProfilePram114.Mold="+"
ProfilePram114.ReverseDir=True
ProfilePram114.ReverseAngle=True
ProfilePram114.CalcSnipOnlyAttachLines=False
ProfilePram114.AttachDirMethod=0
ProfilePram114.CCWDefAngle=False
ProfilePram114.AddEnd1Elements(profile71[0])
ProfilePram114.End1Type=1102
ProfilePram114.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram114.AddEnd2Elements(profile29[0])
ProfilePram114.End2Type=1102
ProfilePram114.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram114.End1ScallopType=1121
ProfilePram114.End1ScallopTypeParams=["25","40"]
ProfilePram114.End2ScallopType=1121
ProfilePram114.End2ScallopTypeParams=["25","40"]
profile114 = part.CreateProfile(ProfilePram114,False)
part.SetElementColor(profile114[0],"255","0","0","0.19999998807907104")
bracketPram52 = part.CreateBracketParam()
bracketPram52.DefinitionType=1
bracketPram52.BracketName="HK.Casing.Wall.Side.FR13.Deck.CP"
bracketPram52.MaterialName="SS400"
bracketPram52.BaseElement=profile110[0]
bracketPram52.UseSideSheetForPlane=False
bracketPram52.Mold="+"
bracketPram52.Thickness="7.9999999999999964"
bracketPram52.BracketType=1501
bracketPram52.Scallop1Type=1801
bracketPram52.Scallop1Params=["0"]
bracketPram52.Scallop2Type=0
bracketPram52.Surfaces1=[profile101[0]+",FL"]
bracketPram52.RevSf1=False
bracketPram52.Surfaces2=[profile110[0]+",FL"]
bracketPram52.RevSf2=False
bracketPram52.RevSf3=False
bracketPram52.Sf1DimensionType=1531
bracketPram52.Sf1DimensonParams=["250","15"]
bracketPram52.Sf2DimensionType=1531
bracketPram52.Sf2DimensonParams=["250","15"]
bracket52 = part.CreateBracket(bracketPram52,False)
part.SetElementColor(bracket52,"0","255","255","0.19999998807907104")
mirror_copied54 = part.MirrorCopy([profile55[0]],"PL,Y","")
part.SetElementColor(mirror_copied54[0],"255","0","0","0.19999998807907104")
mirror_copied55 = part.MirrorCopy([bracket47],"PL,Y","")
part.SetElementColor(mirror_copied55[0],"0","255","255","0.19999998807907104")
ProfilePram115 = part.CreateProfileParam()
ProfilePram115.DefinitionType=1
ProfilePram115.BasePlane="PL,O,"+var_elm4+","+"PL,Y"
ProfilePram115.AddAttachSurfaces(extrude_sheet3)
ProfilePram115.ProfileName="HK.Casing.Wall.Aft.DL01.ABP"
ProfilePram115.MaterialName="SS400"
ProfilePram115.ProfileType=1002
ProfilePram115.ProfileParams=["125","75","7","10","5"]
ProfilePram115.Mold="+"
ProfilePram115.ReverseDir=False
ProfilePram115.ReverseAngle=True
ProfilePram115.CalcSnipOnlyAttachLines=False
ProfilePram115.AttachDirMethod=0
ProfilePram115.CCWDefAngle=False
ProfilePram115.AddEnd1Elements(extrude_sheet1)
ProfilePram115.End1Type=1102
ProfilePram115.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram115.AddEnd2Elements(extrude_sheet2)
ProfilePram115.End2Type=1102
ProfilePram115.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram115.End1ScallopType=1121
ProfilePram115.End1ScallopTypeParams=["25","40"]
ProfilePram115.End2ScallopType=1121
ProfilePram115.End2ScallopTypeParams=["25","40"]
profile115 = part.CreateProfile(ProfilePram115,False)
part.SetElementColor(profile115[0],"255","0","0","0.19999998807907104")
bracketPram53 = part.CreateBracketParam()
bracketPram53.DefinitionType=1
bracketPram53.BracketName="HK.Casing.Wall.Aft.DL01.Deck.BP"
bracketPram53.MaterialName="SS400"
bracketPram53.BaseElement=profile115[0]
bracketPram53.UseSideSheetForPlane=False
bracketPram53.Mold="+"
bracketPram53.Thickness="7.9999999999999964"
bracketPram53.BracketType=1505
bracketPram53.BracketParams=["200"]
bracketPram53.Scallop1Type=1801
bracketPram53.Scallop1Params=["0"]
bracketPram53.Scallop2Type=0
bracketPram53.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram53.RevSf1=False
bracketPram53.Surfaces2=[profile115[0]+",FL"]
bracketPram53.RevSf2=False
bracketPram53.RevSf3=False
bracketPram53.Sf1DimensionType=1541
bracketPram53.Sf1DimensonParams=["0","100"]
bracketPram53.Sf1EndElements=["PLS","False","False","-1","0","-0",profile34[0]]
bracketPram53.Sf2DimensionType=1531
bracketPram53.Sf2DimensonParams=["200","15"]
bracket53 = part.CreateBracket(bracketPram53,False)
part.SetElementColor(bracket53,"0","255","255","0.19999998807907104")
mirror_copied56 = part.MirrorCopy([bracket21],"PL,Y","")
part.SetElementColor(mirror_copied56[0],"0","255","255","0.19999998807907104")
bracketPram54 = part.CreateBracketParam()
bracketPram54.DefinitionType=1
bracketPram54.BracketName="HK.Casing.Wall.Side.FR09.Deck.BP"
bracketPram54.MaterialName="SS400"
bracketPram54.BaseElement=profile112[0]
bracketPram54.UseSideSheetForPlane=False
bracketPram54.Mold="+"
bracketPram54.Thickness="7.9999999999999964"
bracketPram54.BracketType=1501
bracketPram54.Scallop1Type=1801
bracketPram54.Scallop1Params=["0"]
bracketPram54.Scallop2Type=0
bracketPram54.Surfaces1=[profile105[0]+",FL"]
bracketPram54.RevSf1=False
bracketPram54.Surfaces2=[profile112[0]+",FL"]
bracketPram54.RevSf2=False
bracketPram54.RevSf3=False
bracketPram54.Sf1DimensionType=1531
bracketPram54.Sf1DimensonParams=["250","15"]
bracketPram54.Sf2DimensionType=1531
bracketPram54.Sf2DimensonParams=["250","15"]
bracket54 = part.CreateBracket(bracketPram54,False)
part.SetElementColor(bracket54,"0","255","255","0.19999998807907104")
mirror_copied57 = part.MirrorCopy([bracket54],"PL,Y","")
part.SetElementColor(mirror_copied57[0],"0","255","255","0.19999998807907104")
mirror_copied58 = part.MirrorCopy([bracket34],"PL,Y","")
part.SetElementColor(mirror_copied58[0],"0","255","255","0.19999998807907104")
bracketPram55 = part.CreateBracketParam()
bracketPram55.DefinitionType=1
bracketPram55.BracketName="HK.Casing.Wall.Fore.DL03.Deck.BP"
bracketPram55.MaterialName="SS400"
bracketPram55.BaseElement=profile29[0]
bracketPram55.UseSideSheetForPlane=False
bracketPram55.Mold="+"
bracketPram55.Thickness="7.9999999999999964"
bracketPram55.BracketType=1501
bracketPram55.Scallop1Type=1801
bracketPram55.Scallop1Params=["0"]
bracketPram55.Scallop2Type=0
bracketPram55.Surfaces1=[profile29[0]+",FL"]
bracketPram55.RevSf1=False
bracketPram55.Surfaces2=[profile114[0]+",FL"]
bracketPram55.RevSf2=False
bracketPram55.RevSf3=False
bracketPram55.Sf1DimensionType=1531
bracketPram55.Sf1DimensonParams=["200","15"]
bracketPram55.Sf2DimensionType=1531
bracketPram55.Sf2DimensonParams=["200","15"]
bracket55 = part.CreateBracket(bracketPram55,False)
part.SetElementColor(bracket55,"0","255","255","0.19999998807907104")
bracketPram56 = part.CreateBracketParam()
bracketPram56.DefinitionType=1
bracketPram56.BracketName="HK.Casing.Wall.Fore.DL00.Deck.D"
bracketPram56.MaterialName="SS400"
bracketPram56.BaseElement=profile94[0]
bracketPram56.UseSideSheetForPlane=False
bracketPram56.Mold="+"
bracketPram56.Thickness="7.9999999999999964"
bracketPram56.BracketType=1501
bracketPram56.Scallop1Type=1801
bracketPram56.Scallop1Params=["0"]
bracketPram56.Scallop2Type=0
bracketPram56.Surfaces1=[profile94[0]+",FL"]
bracketPram56.RevSf1=False
bracketPram56.Surfaces2=[profile93[0]+",FL"]
bracketPram56.RevSf2=False
bracketPram56.RevSf3=False
bracketPram56.Sf1DimensionType=1531
bracketPram56.Sf1DimensonParams=["200","15"]
bracketPram56.Sf2DimensionType=1531
bracketPram56.Sf2DimensonParams=["200","15"]
bracket56 = part.CreateBracket(bracketPram56,False)
part.SetElementColor(bracket56,"0","255","255","0.19999998807907104")
mirror_copied59 = part.MirrorCopy([profile29[0]],"PL,Y","")
part.SetElementColor(mirror_copied59[0],"255","0","0","0.19999998807907104")
bracketPram57 = part.CreateBracketParam()
bracketPram57.DefinitionType=1
bracketPram57.BracketName="HK.Casing.Wall.Side.FR11.Deck.DP"
bracketPram57.MaterialName="SS400"
bracketPram57.BaseElement=profile111[0]
bracketPram57.UseSideSheetForPlane=False
bracketPram57.Mold="+"
bracketPram57.Thickness="9.9999999999999982"
bracketPram57.BracketType=1505
bracketPram57.BracketParams=["200"]
bracketPram57.Scallop1Type=1801
bracketPram57.Scallop1Params=["0"]
bracketPram57.Scallop2Type=0
bracketPram57.Surfaces1=["PLS","False","False","0","-0","-1",solid2]
bracketPram57.RevSf1=False
bracketPram57.Surfaces2=[profile111[0]+",FL"]
bracketPram57.RevSf2=False
bracketPram57.RevSf3=False
bracketPram57.Sf1DimensionType=1541
bracketPram57.Sf1DimensonParams=["0","100"]
bracketPram57.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile15[0]]
bracketPram57.Sf2DimensionType=1531
bracketPram57.Sf2DimensonParams=["200","15"]
bracket57 = part.CreateBracket(bracketPram57,False)
part.SetElementColor(bracket57,"0","255","255","0.19999998807907104")
mirror_copied60 = part.MirrorCopy([profile48[0]],"PL,Y","")
part.SetElementColor(mirror_copied60[0],"255","0","0","0.19999998807907104")
ProfilePram116 = part.CreateProfileParam()
ProfilePram116.DefinitionType=1
ProfilePram116.BasePlane="PL,O,"+var_elm11+","+"PL,X"
ProfilePram116.AddAttachSurfaces(extrude_sheet4)
ProfilePram116.ProfileName="HK.Casing.Wall.Side.FR11.OAP"
ProfilePram116.MaterialName="SS400"
ProfilePram116.ProfileType=1002
ProfilePram116.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram116.Mold="+"
ProfilePram116.ReverseDir=False
ProfilePram116.ReverseAngle=True
ProfilePram116.CalcSnipOnlyAttachLines=False
ProfilePram116.AttachDirMethod=0
ProfilePram116.CCWDefAngle=False
ProfilePram116.AddEnd1Elements(extrude_sheet2)
ProfilePram116.End1Type=1102
ProfilePram116.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram116.AddEnd2Elements(extrude_sheet8)
ProfilePram116.End2Type=1102
ProfilePram116.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram116.End1ScallopType=1121
ProfilePram116.End1ScallopTypeParams=["35","40"]
ProfilePram116.End2ScallopType=1121
ProfilePram116.End2ScallopTypeParams=["35","40"]
profile116 = part.CreateProfile(ProfilePram116,False)
part.SetElementColor(profile116[0],"255","0","0","0.19999998807907104")
ProfilePram117 = part.CreateProfileParam()
ProfilePram117.DefinitionType=1
ProfilePram117.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram117.AddAttachSurfaces(extrude_sheet5)
ProfilePram117.ProfileName="HK.Casing.Wall.Fore.DL03.CDP"
ProfilePram117.MaterialName="SS400"
ProfilePram117.ProfileType=1002
ProfilePram117.ProfileParams=["125","75","7","10","5"]
ProfilePram117.Mold="+"
ProfilePram117.ReverseDir=True
ProfilePram117.ReverseAngle=True
ProfilePram117.CalcSnipOnlyAttachLines=False
ProfilePram117.AttachDirMethod=0
ProfilePram117.CCWDefAngle=False
ProfilePram117.AddEnd1Elements(profile37[0])
ProfilePram117.End1Type=1102
ProfilePram117.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram117.AddEnd2Elements(extrude_sheet6)
ProfilePram117.End2Type=1102
ProfilePram117.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram117.End1ScallopType=1120
ProfilePram117.End1ScallopTypeParams=["50"]
ProfilePram117.End2ScallopType=1120
ProfilePram117.End2ScallopTypeParams=["50"]
profile117 = part.CreateProfile(ProfilePram117,False)
part.SetElementColor(profile117[0],"255","0","0","0.19999998807907104")
bracketPram58 = part.CreateBracketParam()
bracketPram58.DefinitionType=1
bracketPram58.BracketName="HK.Casing.Wall.Fore.DL03.Deck.DP"
bracketPram58.MaterialName="SS400"
bracketPram58.BaseElement=profile117[0]
bracketPram58.UseSideSheetForPlane=False
bracketPram58.Mold="+"
bracketPram58.Thickness="7.9999999999999964"
bracketPram58.BracketType=1501
bracketPram58.Scallop1Type=1801
bracketPram58.Scallop1Params=["0"]
bracketPram58.Scallop2Type=0
bracketPram58.Surfaces1=[profile117[0]+",FL"]
bracketPram58.RevSf1=False
bracketPram58.Surfaces2=[profile37[0]+",FL"]
bracketPram58.RevSf2=False
bracketPram58.RevSf3=False
bracketPram58.Sf1DimensionType=1531
bracketPram58.Sf1DimensonParams=["200","15"]
bracketPram58.Sf2DimensionType=1531
bracketPram58.Sf2DimensonParams=["200","15"]
bracket58 = part.CreateBracket(bracketPram58,False)
part.SetElementColor(bracket58,"0","255","255","0.19999998807907104")
mirror_copied61 = part.MirrorCopy([profile25[0]],"PL,Y","")
part.SetElementColor(mirror_copied61[0],"255","0","0","0.19999998807907104")
bracketPram59 = part.CreateBracketParam()
bracketPram59.DefinitionType=1
bracketPram59.BracketName="HK.Casing.Wall.Aft.DL04.Deck.AP"
bracketPram59.MaterialName="SS400"
bracketPram59.BaseElement=profile43[0]
bracketPram59.UseSideSheetForPlane=False
bracketPram59.Mold="-"
bracketPram59.Thickness="7.9999999999999964"
bracketPram59.BracketType=1501
bracketPram59.Scallop1Type=1801
bracketPram59.Scallop1Params=["0"]
bracketPram59.Scallop2Type=0
bracketPram59.Surfaces1=[profile41[0]+",FL"]
bracketPram59.RevSf1=False
bracketPram59.Surfaces2=[profile43[0]+",FL"]
bracketPram59.RevSf2=False
bracketPram59.RevSf3=False
bracketPram59.Sf1DimensionType=1531
bracketPram59.Sf1DimensonParams=["250","15"]
bracketPram59.Sf2DimensionType=1531
bracketPram59.Sf2DimensonParams=["250","15"]
bracket59 = part.CreateBracket(bracketPram59,False)
part.SetElementColor(bracket59,"0","255","255","0.19999998807907104")
bracketPram60 = part.CreateBracketParam()
bracketPram60.DefinitionType=1
bracketPram60.BracketName="HK.Casing.Wall.Side.FR12.Deck.AP"
bracketPram60.MaterialName="SS400"
bracketPram60.BaseElement=profile28[0]
bracketPram60.UseSideSheetForPlane=False
bracketPram60.Mold="+"
bracketPram60.Thickness="9.9999999999999982"
bracketPram60.BracketType=1505
bracketPram60.BracketParams=["200"]
bracketPram60.Scallop1Type=1801
bracketPram60.Scallop1Params=["0"]
bracketPram60.Scallop2Type=0
bracketPram60.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram60.RevSf1=False
bracketPram60.Surfaces2=[profile28[0]+",FL"]
bracketPram60.RevSf2=False
bracketPram60.RevSf3=False
bracketPram60.Sf1DimensionType=1541
bracketPram60.Sf1DimensonParams=["0","100"]
bracketPram60.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile51[0]]
bracketPram60.Sf2DimensionType=1531
bracketPram60.Sf2DimensonParams=["200","15"]
bracket60 = part.CreateBracket(bracketPram60,False)
part.SetElementColor(bracket60,"0","255","255","0.19999998807907104")
mirror_copied62 = part.MirrorCopy([bracket60],"PL,Y","")
part.SetElementColor(mirror_copied62[0],"0","255","255","0.19999998807907104")
mirror_copied63 = part.MirrorCopy([profile57[0]],"PL,Y","")
part.SetElementColor(mirror_copied63[0],"255","0","0","0.19999998807907104")
mirror_copied64 = part.MirrorCopy([profile50[0]],"PL,Y","")
part.SetElementColor(mirror_copied64[0],"255","0","0","0.19999998807907104")
ProfilePram118 = part.CreateProfileParam()
ProfilePram118.DefinitionType=1
ProfilePram118.BasePlane="PL,O,"+var_elm14+","+"PL,X"
ProfilePram118.AddAttachSurfaces(extrude_sheet4)
ProfilePram118.ProfileName="HK.Casing.Wall.Side.FR15.OAP"
ProfilePram118.MaterialName="SS400"
ProfilePram118.ProfileType=1002
ProfilePram118.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram118.Mold="+"
ProfilePram118.ReverseDir=False
ProfilePram118.ReverseAngle=True
ProfilePram118.CalcSnipOnlyAttachLines=False
ProfilePram118.AttachDirMethod=0
ProfilePram118.CCWDefAngle=False
ProfilePram118.AddEnd1Elements(extrude_sheet2)
ProfilePram118.End1Type=1102
ProfilePram118.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram118.AddEnd2Elements(extrude_sheet8)
ProfilePram118.End2Type=1102
ProfilePram118.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram118.End1ScallopType=1121
ProfilePram118.End1ScallopTypeParams=["35","40"]
ProfilePram118.End2ScallopType=1121
ProfilePram118.End2ScallopTypeParams=["35","40"]
profile118 = part.CreateProfile(ProfilePram118,False)
part.SetElementColor(profile118[0],"255","0","0","0.19999998807907104")
bracketPram61 = part.CreateBracketParam()
bracketPram61.DefinitionType=1
bracketPram61.BracketName="HK.Casing.Wall.Side.FR15.Deck.AP"
bracketPram61.MaterialName="SS400"
bracketPram61.BaseElement=profile118[0]
bracketPram61.UseSideSheetForPlane=False
bracketPram61.Mold="+"
bracketPram61.Thickness="9.9999999999999982"
bracketPram61.BracketType=1505
bracketPram61.BracketParams=["200"]
bracketPram61.Scallop1Type=1801
bracketPram61.Scallop1Params=["0"]
bracketPram61.Scallop2Type=0
bracketPram61.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram61.RevSf1=False
bracketPram61.Surfaces2=[profile118[0]+",FL"]
bracketPram61.RevSf2=False
bracketPram61.RevSf3=False
bracketPram61.Sf1DimensionType=1541
bracketPram61.Sf1DimensonParams=["0","100"]
bracketPram61.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile51[0]]
bracketPram61.Sf2DimensionType=1531
bracketPram61.Sf2DimensonParams=["200","15"]
bracket61 = part.CreateBracket(bracketPram61,False)
part.SetElementColor(bracket61,"0","255","255","0.19999998807907104")
mirror_copied65 = part.MirrorCopy([bracket61],"PL,Y","")
part.SetElementColor(mirror_copied65[0],"0","255","255","0.19999998807907104")
mirror_copied66 = part.MirrorCopy([profile68[0]],"PL,Y","")
part.SetElementColor(mirror_copied66[0],"148","0","211","0.39999997615814209")
mirror_copied67 = part.MirrorCopy([profile105[0]],"PL,Y","")
part.SetElementColor(mirror_copied67[0],"148","0","211","0.39999997615814209")
ProfilePram119 = part.CreateProfileParam()
ProfilePram119.DefinitionType=1
ProfilePram119.BasePlane="PL,O,"+var_elm10+","+"PL,Y"
ProfilePram119.AddAttachSurfaces(extrude_sheet3)
ProfilePram119.ProfileName="HK.Casing.Wall.Aft.DL03.OAP"
ProfilePram119.MaterialName="SS400"
ProfilePram119.ProfileType=1002
ProfilePram119.ProfileParams=["125","75","7","10","5"]
ProfilePram119.Mold="+"
ProfilePram119.ReverseDir=False
ProfilePram119.ReverseAngle=True
ProfilePram119.CalcSnipOnlyAttachLines=False
ProfilePram119.AttachDirMethod=0
ProfilePram119.CCWDefAngle=False
ProfilePram119.AddEnd1Elements(extrude_sheet2)
ProfilePram119.End1Type=1102
ProfilePram119.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram119.AddEnd2Elements(extrude_sheet8)
ProfilePram119.End2Type=1102
ProfilePram119.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram119.End1ScallopType=1121
ProfilePram119.End1ScallopTypeParams=["25","40"]
ProfilePram119.End2ScallopType=1121
ProfilePram119.End2ScallopTypeParams=["25","40"]
profile119 = part.CreateProfile(ProfilePram119,False)
part.SetElementColor(profile119[0],"255","0","0","0.19999998807907104")
mirror_copied68 = part.MirrorCopy([profile119[0]],"PL,Y","")
part.SetElementColor(mirror_copied68[0],"255","0","0","0.19999998807907104")
mirror_copied69 = part.MirrorCopy([profile8[0]],"PL,Y","")
part.SetElementColor(mirror_copied69[0],"148","0","211","0.39999997615814209")
ProfilePram120 = part.CreateProfileParam()
ProfilePram120.DefinitionType=1
ProfilePram120.BasePlane="PL,O,"+var_elm8+","+"PL,Y"
ProfilePram120.AddAttachSurfaces(extrude_sheet3)
ProfilePram120.ProfileName="HK.Casing.Wall.Aft.DL02.ABP"
ProfilePram120.MaterialName="SS400"
ProfilePram120.FlangeName="HK.Casing.Wall.Aft.DL02.ABP"
ProfilePram120.FlangeMaterialName="SS400"
ProfilePram120.ProfileType=1201
ProfilePram120.ProfileParams=["150","12","388","10"]
ProfilePram120.Mold="-"
ProfilePram120.ReverseDir=False
ProfilePram120.ReverseAngle=False
ProfilePram120.CalcSnipOnlyAttachLines=False
ProfilePram120.AttachDirMethod=0
ProfilePram120.CCWDefAngle=False
ProfilePram120.AddEnd1Elements(extrude_sheet1)
ProfilePram120.End1Type=1103
ProfilePram120.End1TypeParams=["0"]
ProfilePram120.AddEnd2Elements(extrude_sheet2)
ProfilePram120.End2Type=1103
ProfilePram120.End2TypeParams=["0"]
ProfilePram120.End1ScallopType=1120
ProfilePram120.End1ScallopTypeParams=["50"]
ProfilePram120.End2ScallopType=1120
ProfilePram120.End2ScallopTypeParams=["50"]
profile120 = part.CreateProfile(ProfilePram120,False)
part.SetElementColor(profile120[0],"148","0","211","0.39999997615814209")
part.SetElementColor(profile120[1],"148","0","211","0.39999997615814209")
bracketPram62 = part.CreateBracketParam()
bracketPram62.DefinitionType=1
bracketPram62.BracketName="HK.Casing.Wall.Side.FR10.Deck.DP"
bracketPram62.MaterialName="SS400"
bracketPram62.BaseElement=profile47[0]
bracketPram62.UseSideSheetForPlane=False
bracketPram62.Mold="+"
bracketPram62.Thickness="9.9999999999999982"
bracketPram62.BracketType=1505
bracketPram62.BracketParams=["200"]
bracketPram62.Scallop1Type=1801
bracketPram62.Scallop1Params=["0"]
bracketPram62.Scallop2Type=0
bracketPram62.Surfaces1=["PLS","False","False","0","-0","-1",solid2]
bracketPram62.RevSf1=False
bracketPram62.Surfaces2=[profile47[0]+",FL"]
bracketPram62.RevSf2=False
bracketPram62.RevSf3=False
bracketPram62.Sf1DimensionType=1541
bracketPram62.Sf1DimensonParams=["0","100"]
bracketPram62.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile15[0]]
bracketPram62.Sf2DimensionType=1531
bracketPram62.Sf2DimensonParams=["200","15"]
bracket62 = part.CreateBracket(bracketPram62,False)
part.SetElementColor(bracket62,"0","255","255","0.19999998807907104")
bracketPram63 = part.CreateBracketParam()
bracketPram63.DefinitionType=1
bracketPram63.BracketName="HK.Casing.Wall.Fore.DL00.Deck.C"
bracketPram63.MaterialName="SS400"
bracketPram63.BaseElement=profile74[0]
bracketPram63.UseSideSheetForPlane=False
bracketPram63.Mold="+"
bracketPram63.Thickness="7.9999999999999964"
bracketPram63.BracketType=1501
bracketPram63.Scallop1Type=1801
bracketPram63.Scallop1Params=["0"]
bracketPram63.Scallop2Type=0
bracketPram63.Surfaces1=[profile74[0]+",FL"]
bracketPram63.RevSf1=False
bracketPram63.Surfaces2=[profile75[0]+",FL"]
bracketPram63.RevSf2=False
bracketPram63.RevSf3=False
bracketPram63.Sf1DimensionType=1531
bracketPram63.Sf1DimensonParams=["200","15"]
bracketPram63.Sf2DimensionType=1531
bracketPram63.Sf2DimensonParams=["200","15"]
bracket63 = part.CreateBracket(bracketPram63,False)
part.SetElementColor(bracket63,"0","255","255","0.19999998807907104")
extrudePram45 = part.CreateLinearSweepParam()
extrudePram45.Name="積-押し出し7"
extrudePram45.AddProfile(skt_pl4+",Edge00")
extrudePram45.DirectionType="N"
extrudePram45.DirectionParameter1="50000"
extrudePram45.SweepDirection="+Z"
extrudePram45.RefByGeometricMethod=True
extrude36 = part.CreateLinearSweep(solid12,"*",extrudePram45,False)
extrudePram46 = part.CreateLinearSweepParam()
extrudePram46.Name="積-押し出し8"
extrudePram46.AddProfile(extrude_sheet7)
extrudePram46.DirectionType="R"
extrudePram46.DirectionParameter1="50000"
extrudePram46.SweepDirection="+Z"
extrudePram46.RefByGeometricMethod=True
extrude37 = part.CreateLinearSweep(solid12,"*",extrudePram46,False)
extrudePram47 = part.CreateLinearSweepParam()
extrudePram47.Name="積-押し出し9"
extrudePram47.AddProfile(extrude_sheet6)
extrudePram47.DirectionType="N"
extrudePram47.DirectionParameter1="50000"
extrudePram47.SweepDirection="+Z"
extrudePram47.RefByGeometricMethod=True
extrude38 = part.CreateLinearSweep(solid12,"*",extrudePram47,False)
bracketPram64 = part.CreateBracketParam()
bracketPram64.DefinitionType=1
bracketPram64.BracketName="HK.Casing.Wall.Fore.DL02.Deck.AP"
bracketPram64.MaterialName="SS400"
bracketPram64.BaseElement=profile104[0]
bracketPram64.UseSideSheetForPlane=False
bracketPram64.Mold="+"
bracketPram64.Thickness="7.9999999999999964"
bracketPram64.BracketType=1501
bracketPram64.Scallop1Type=1801
bracketPram64.Scallop1Params=["0"]
bracketPram64.Scallop2Type=0
bracketPram64.Surfaces1=[profile104[0]+",FL"]
bracketPram64.RevSf1=False
bracketPram64.Surfaces2=[profile109[0]+",FL"]
bracketPram64.RevSf2=False
bracketPram64.RevSf3=False
bracketPram64.Sf1DimensionType=1531
bracketPram64.Sf1DimensonParams=["200","15"]
bracketPram64.Sf2DimensionType=1531
bracketPram64.Sf2DimensonParams=["200","15"]
bracket64 = part.CreateBracket(bracketPram64,False)
part.SetElementColor(bracket64,"0","255","255","0.19999998807907104")
bracketPram65 = part.CreateBracketParam()
bracketPram65.DefinitionType=1
bracketPram65.BracketName="HK.Casing.Wall.Side.FR10.Deck.BP"
bracketPram65.MaterialName="SS400"
bracketPram65.BaseElement=profile83[0]
bracketPram65.UseSideSheetForPlane=False
bracketPram65.Mold="+"
bracketPram65.Thickness="9.9999999999999982"
bracketPram65.BracketType=1505
bracketPram65.BracketParams=["200"]
bracketPram65.Scallop1Type=1801
bracketPram65.Scallop1Params=["0"]
bracketPram65.Scallop2Type=0
bracketPram65.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram65.RevSf1=False
bracketPram65.Surfaces2=[profile83[0]+",FL"]
bracketPram65.RevSf2=False
bracketPram65.RevSf3=False
bracketPram65.Sf1DimensionType=1541
bracketPram65.Sf1DimensonParams=["0","100"]
bracketPram65.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram65.Sf2DimensionType=1531
bracketPram65.Sf2DimensonParams=["200","15"]
bracket65 = part.CreateBracket(bracketPram65,False)
part.SetElementColor(bracket65,"0","255","255","0.19999998807907104")
mirror_copied70 = part.MirrorCopy([bracket65],"PL,Y","")
part.SetElementColor(mirror_copied70[0],"0","255","255","0.19999998807907104")
mirror_copied71 = part.MirrorCopy([bracket16],"PL,Y","")
part.SetElementColor(mirror_copied71[0],"0","255","255","0.19999998807907104")
mirror_copied72 = part.MirrorCopy([profile118[0]],"PL,Y","")
part.SetElementColor(mirror_copied72[0],"255","0","0","0.19999998807907104")
mirror_copied73 = part.MirrorCopy([profile97[1]],"PL,Y","")
part.SetElementColor(mirror_copied73[0],"148","0","211","0.39999997615814209")
mirror_copied74 = part.MirrorCopy([bracket59],"PL,Y","")
part.SetElementColor(mirror_copied74[0],"0","255","255","0.19999998807907104")
extrudePram48 = part.CreateLinearSweepParam()
extrudePram48.Name="積-押し出し25"
extrudePram48.AddProfile(extrude_sheet6)
extrudePram48.DirectionType="R"
extrudePram48.DirectionParameter1="50000"
extrudePram48.SweepDirection="+Z"
extrudePram48.RefByGeometricMethod=True
extrude39 = part.CreateLinearSweep(solid13,"*",extrudePram48,False)
extrudePram49 = part.CreateLinearSweepParam()
extrudePram49.Name="積-押し出し26"
extrudePram49.AddProfile(extrude_sheet1)
extrudePram49.DirectionType="N"
extrudePram49.DirectionParameter1="50000"
extrudePram49.SweepDirection="+Z"
extrudePram49.RefByGeometricMethod=True
extrude40 = part.CreateLinearSweep(solid13,"*",extrudePram49,False)
bracketPram66 = part.CreateBracketParam()
bracketPram66.DefinitionType=1
bracketPram66.BracketName="HK.Casing.Wall.Fore.DL05.Deck.BP"
bracketPram66.MaterialName="SS400"
bracketPram66.BaseElement=profile5[0]
bracketPram66.UseSideSheetForPlane=False
bracketPram66.Mold="+"
bracketPram66.Thickness="7.9999999999999964"
bracketPram66.BracketType=1501
bracketPram66.Scallop1Type=1801
bracketPram66.Scallop1Params=["0"]
bracketPram66.Scallop2Type=0
bracketPram66.Surfaces1=[profile4[0]+",FL"]
bracketPram66.RevSf1=False
bracketPram66.Surfaces2=[profile5[0]+",FL"]
bracketPram66.RevSf2=False
bracketPram66.RevSf3=False
bracketPram66.Sf1DimensionType=1531
bracketPram66.Sf1DimensonParams=["200","15"]
bracketPram66.Sf2DimensionType=1531
bracketPram66.Sf2DimensonParams=["200","15"]
bracket66 = part.CreateBracket(bracketPram66,False)
part.SetElementColor(bracket66,"0","255","255","0.19999998807907104")
mirror_copied75 = part.MirrorCopy([profile80[1]],"PL,Y","")
part.SetElementColor(mirror_copied75[0],"148","0","211","0.39999997615814209")
bracketPram67 = part.CreateBracketParam()
bracketPram67.DefinitionType=1
bracketPram67.BracketName="HK.Casing.Wall.Fore.DL02.Deck.CP"
bracketPram67.MaterialName="SS400"
bracketPram67.BaseElement=profile97[0]
bracketPram67.UseSideSheetForPlane=False
bracketPram67.Mold="-"
bracketPram67.Thickness="9.9999999999999982"
bracketPram67.BracketType=1501
bracketPram67.Scallop1Type=1801
bracketPram67.Scallop1Params=["50"]
bracketPram67.Scallop2Type=0
bracketPram67.Surfaces1=["PLS","False","False","-1","-0","0",profile97[1]]
bracketPram67.RevSf1=False
bracketPram67.Surfaces2=["PLS","False","False","0","-0","-1",solid3]
bracketPram67.RevSf2=False
bracketPram67.RevSf3=False
bracketPram67.FlangeType=265
bracketPram67.FlangeParams=["75","30","29.999999999999996","30","30","30","30","150","30"]
bracketPram67.RevFlange=False
bracketPram67.Sf1DimensionType=1531
bracketPram67.Sf1DimensonParams=["500","15"]
bracketPram67.Sf2DimensionType=1541
bracketPram67.Sf2DimensonParams=["0","200"]
bracketPram67.Sf2EndElements=["PLS","False","False","1","-0","0",profile10[0]]
bracketPram67.ScallopEnd2LowerType=1801
bracketPram67.ScallopEnd2LowerParams=["50"]
bracket67 = part.CreateBracket(bracketPram67,False)
part.SetElementColor(bracket67,"0","255","255","0.19999998807907104")
mirror_copied76 = part.MirrorCopy([profile38[0]],"PL,Y","")
part.SetElementColor(mirror_copied76[0],"255","0","0","0.19999998807907104")
mirror_copied77 = part.MirrorCopy([profile46[0]],"PL,Y","")
part.SetElementColor(mirror_copied77[0],"148","0","211","0.39999997615814209")
mirror_copied78 = part.MirrorCopy([profile86[0]],"PL,Y","")
part.SetElementColor(mirror_copied78[0],"255","0","0","0.19999998807907104")
mirror_copied79 = part.MirrorCopy([profile92[0]],"PL,Y","")
part.SetElementColor(mirror_copied79[0],"255","0","0","0.19999998807907104")
bracketPram68 = part.CreateBracketParam()
bracketPram68.DefinitionType=1
bracketPram68.BracketName="HK.Casing.Wall.Side.FR13.Deck.AP"
bracketPram68.MaterialName="SS400"
bracketPram68.BaseElement=profile44[0]
bracketPram68.UseSideSheetForPlane=False
bracketPram68.Mold="+"
bracketPram68.Thickness="7.9999999999999964"
bracketPram68.BracketType=1501
bracketPram68.Scallop1Type=1801
bracketPram68.Scallop1Params=["0"]
bracketPram68.Scallop2Type=0
bracketPram68.Surfaces1=[profile40[0]+",FL"]
bracketPram68.RevSf1=False
bracketPram68.Surfaces2=[profile44[0]+",FL"]
bracketPram68.RevSf2=False
bracketPram68.RevSf3=False
bracketPram68.Sf1DimensionType=1531
bracketPram68.Sf1DimensonParams=["250","15"]
bracketPram68.Sf2DimensionType=1531
bracketPram68.Sf2DimensonParams=["250","15"]
bracket68 = part.CreateBracket(bracketPram68,False)
part.SetElementColor(bracket68,"0","255","255","0.19999998807907104")
mirror_copied80 = part.MirrorCopy([bracket68],"PL,Y","")
part.SetElementColor(mirror_copied80[0],"0","255","255","0.19999998807907104")
ProfilePram121 = part.CreateProfileParam()
ProfilePram121.DefinitionType=1
ProfilePram121.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram121.AddAttachSurfaces(extrude_sheet3)
ProfilePram121.ProfileName="HK.Casing.Wall.Aft.DL00.CD"
ProfilePram121.MaterialName="SS400"
ProfilePram121.ProfileType=1002
ProfilePram121.ProfileParams=["125","75","7","10","5"]
ProfilePram121.ReverseDir=False
ProfilePram121.ReverseAngle=True
ProfilePram121.CalcSnipOnlyAttachLines=False
ProfilePram121.AttachDirMethod=0
ProfilePram121.CCWDefAngle=False
ProfilePram121.AddEnd1Elements(profile36[0])
ProfilePram121.End1Type=1102
ProfilePram121.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram121.AddEnd2Elements(extrude_sheet6)
ProfilePram121.End2Type=1102
ProfilePram121.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram121.End1ScallopType=1120
ProfilePram121.End1ScallopTypeParams=["50"]
ProfilePram121.End2ScallopType=1120
ProfilePram121.End2ScallopTypeParams=["50"]
profile121 = part.CreateProfile(ProfilePram121,False)
part.SetElementColor(profile121[0],"255","0","0","0.19999998807907104")
mirror_copied81 = part.MirrorCopy([profile110[0]],"PL,Y","")
part.SetElementColor(mirror_copied81[0],"148","0","211","0.39999997615814209")
mirror_copied82 = part.MirrorCopy([bracket50],"PL,Y","")
part.SetElementColor(mirror_copied82[0],"0","255","255","0.19999998807907104")
mirror_copied83 = part.MirrorCopy([profile72[0]],"PL,Y","")
part.SetElementColor(mirror_copied83[0],"255","0","0","0.19999998807907104")
mirror_copied84 = part.MirrorCopy([profile58[0]],"PL,Y","")
part.SetElementColor(mirror_copied84[0],"255","0","0","0.19999998807907104")
mirror_copied85 = part.MirrorCopy([bracket39],"PL,Y","")
part.SetElementColor(mirror_copied85[0],"0","255","255","0.19999998807907104")
mirror_copied86 = part.MirrorCopy([profile88[0]],"PL,Y","")
part.SetElementColor(mirror_copied86[0],"148","0","211","0.39999997615814209")
mirror_copied87 = part.MirrorCopy([profile32[0]],"PL,Y","")
part.SetElementColor(mirror_copied87[0],"148","0","211","0.39999997615814209")
mirror_copied88 = part.MirrorCopy([bracket15],"PL,Y","")
part.SetElementColor(mirror_copied88[0],"0","255","255","0.19999998807907104")
mirror_copied89 = part.MirrorCopy([profile67[0]],"PL,Y","")
part.SetElementColor(mirror_copied89[0],"255","0","0","0.19999998807907104")
mirror_copied90 = part.MirrorCopy([bracket23],"PL,Y","")
part.SetElementColor(mirror_copied90[0],"0","255","255","0.19999998807907104")
bracketPram69 = part.CreateBracketParam()
bracketPram69.DefinitionType=1
bracketPram69.BracketName="HK.Casing.Wall.Side.FR12.Deck.CP"
bracketPram69.MaterialName="SS400"
bracketPram69.BaseElement=profile79[0]
bracketPram69.UseSideSheetForPlane=False
bracketPram69.Mold="+"
bracketPram69.Thickness="9.9999999999999982"
bracketPram69.BracketType=1505
bracketPram69.BracketParams=["200"]
bracketPram69.Scallop1Type=1801
bracketPram69.Scallop1Params=["0"]
bracketPram69.Scallop2Type=0
bracketPram69.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram69.RevSf1=False
bracketPram69.Surfaces2=[profile79[0]+",FL"]
bracketPram69.RevSf2=False
bracketPram69.RevSf3=False
bracketPram69.Sf1DimensionType=1541
bracketPram69.Sf1DimensonParams=["0","100"]
bracketPram69.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile22[0]]
bracketPram69.Sf2DimensionType=1531
bracketPram69.Sf2DimensonParams=["200","15"]
bracket69 = part.CreateBracket(bracketPram69,False)
part.SetElementColor(bracket69,"0","255","255","0.19999998807907104")
mirror_copied91 = part.MirrorCopy([bracket69],"PL,Y","")
part.SetElementColor(mirror_copied91[0],"0","255","255","0.19999998807907104")
mirror_copied92 = part.MirrorCopy([profile88[1]],"PL,Y","")
part.SetElementColor(mirror_copied92[0],"148","0","211","0.39999997615814209")
ProfilePram122 = part.CreateProfileParam()
ProfilePram122.DefinitionType=1
ProfilePram122.BasePlane="PL,O,"+var_elm7+","+"PL,X"
ProfilePram122.AddAttachSurfaces(extrude_sheet4)
ProfilePram122.ProfileName="HK.Casing.Wall.Side.FR12.ABP"
ProfilePram122.MaterialName="SS400"
ProfilePram122.ProfileType=1002
ProfilePram122.ProfileParams=["150","90","9.0000000000000018","12","6"]
ProfilePram122.Mold="+"
ProfilePram122.ReverseDir=False
ProfilePram122.ReverseAngle=True
ProfilePram122.CalcSnipOnlyAttachLines=False
ProfilePram122.AttachDirMethod=0
ProfilePram122.CCWDefAngle=False
ProfilePram122.AddEnd1Elements(extrude_sheet1)
ProfilePram122.End1Type=1102
ProfilePram122.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram122.AddEnd2Elements(extrude_sheet2)
ProfilePram122.End2Type=1102
ProfilePram122.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram122.End1ScallopType=1121
ProfilePram122.End1ScallopTypeParams=["35","40"]
ProfilePram122.End2ScallopType=1121
ProfilePram122.End2ScallopTypeParams=["35","40"]
profile122 = part.CreateProfile(ProfilePram122,False)
part.SetElementColor(profile122[0],"255","0","0","0.19999998807907104")
mirror_copied93 = part.MirrorCopy([profile122[0]],"PL,Y","")
part.SetElementColor(mirror_copied93[0],"255","0","0","0.19999998807907104")
mirror_copied94 = part.MirrorCopy([profile61[1]],"PL,Y","")
part.SetElementColor(mirror_copied94[0],"148","0","211","0.39999997615814209")
mirror_copied95 = part.MirrorCopy([bracket10],"PL,Y","")
part.SetElementColor(mirror_copied95[0],"0","255","255","0.19999998807907104")
bracketPram70 = part.CreateBracketParam()
bracketPram70.DefinitionType=1
bracketPram70.BracketName="HK.Casing.Wall.Side.FR15.Deck.DP"
bracketPram70.MaterialName="SS400"
bracketPram70.BaseElement=profile81[0]
bracketPram70.UseSideSheetForPlane=False
bracketPram70.Mold="+"
bracketPram70.Thickness="9.9999999999999982"
bracketPram70.BracketType=1505
bracketPram70.BracketParams=["200"]
bracketPram70.Scallop1Type=1801
bracketPram70.Scallop1Params=["0"]
bracketPram70.Scallop2Type=0
bracketPram70.Surfaces1=["PLS","False","False","0","-0","-1",solid2]
bracketPram70.RevSf1=False
bracketPram70.Surfaces2=[profile81[0]+",FL"]
bracketPram70.RevSf2=False
bracketPram70.RevSf3=False
bracketPram70.Sf1DimensionType=1541
bracketPram70.Sf1DimensonParams=["0","100"]
bracketPram70.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile15[0]]
bracketPram70.Sf2DimensionType=1531
bracketPram70.Sf2DimensonParams=["200","15"]
bracket70 = part.CreateBracket(bracketPram70,False)
part.SetElementColor(bracket70,"0","255","255","0.19999998807907104")
solid15 = part.CreateSolid("HK.Casing.Wall.Side.BCP","","SS400")
part.SetElementColor(solid15,"139","69","19","0.79999995231628418")
thicken15 = part.CreateThicken("厚み付け8",solid15,"+",[extrude_sheet4],"-","10","0","0",False,False)
extrudePram50 = part.CreateLinearSweepParam()
extrudePram50.Name="積-押し出し10"
extrudePram50.AddProfile(skt_pl4+",Edge00")
extrudePram50.DirectionType="N"
extrudePram50.DirectionParameter1="50000"
extrudePram50.SweepDirection="+Z"
extrudePram50.RefByGeometricMethod=True
extrude41 = part.CreateLinearSweep(solid15,"*",extrudePram50,False)
extrudePram51 = part.CreateLinearSweepParam()
extrudePram51.Name="積-押し出し11"
extrudePram51.AddProfile(extrude_sheet6)
extrudePram51.DirectionType="R"
extrudePram51.DirectionParameter1="50000"
extrudePram51.SweepDirection="+Z"
extrudePram51.RefByGeometricMethod=True
extrude42 = part.CreateLinearSweep(solid15,"*",extrudePram51,False)
extrudePram52 = part.CreateLinearSweepParam()
extrudePram52.Name="積-押し出し12"
extrudePram52.AddProfile(extrude_sheet1)
extrudePram52.DirectionType="N"
extrudePram52.DirectionParameter1="50000"
extrudePram52.SweepDirection="+Z"
extrudePram52.RefByGeometricMethod=True
extrude43 = part.CreateLinearSweep(solid15,"*",extrudePram52,False)
mirror_copied96 = part.MirrorCopy([solid15],"PL,Y","")
part.SetElementColor(mirror_copied96[0],"139","69","19","0.79999995231628418")
bracketPram71 = part.CreateBracketParam()
bracketPram71.DefinitionType=1
bracketPram71.BracketName="HK.Casing.Deck.D.FR09P"
bracketPram71.MaterialName="SS400"
bracketPram71.BaseElement=profile17[0]
bracketPram71.UseSideSheetForPlane=False
bracketPram71.Mold="+"
bracketPram71.Thickness="7.9999999999999964"
bracketPram71.BracketType=1501
bracketPram71.Scallop1Type=1801
bracketPram71.Scallop1Params=["0"]
bracketPram71.Scallop2Type=0
bracketPram71.Surfaces1=[profile16[0]+",WB"]
bracketPram71.RevSf1=False
bracketPram71.Surfaces2=[profile17[0]+",FL"]
bracketPram71.RevSf2=False
bracketPram71.RevSf3=False
bracketPram71.Sf1DimensionType=1531
bracketPram71.Sf1DimensonParams=["250","15"]
bracketPram71.Sf2DimensionType=1531
bracketPram71.Sf2DimensonParams=["250","15"]
bracket71 = part.CreateBracket(bracketPram71,False)
part.SetElementColor(bracket71,"0","255","255","0.19999998807907104")
mirror_copied97 = part.MirrorCopy([bracket71],"PL,Y","")
part.SetElementColor(mirror_copied97[0],"0","255","255","0.19999998807907104")
mirror_copied98 = part.MirrorCopy([profile23[1]],"PL,Y","")
part.SetElementColor(mirror_copied98[0],"148","0","211","0.39999997615814209")
bracketPram72 = part.CreateBracketParam()
bracketPram72.DefinitionType=1
bracketPram72.BracketName="HK.Casing.Wall.Side.FR12.Deck.BP"
bracketPram72.MaterialName="SS400"
bracketPram72.BaseElement=profile122[0]
bracketPram72.UseSideSheetForPlane=False
bracketPram72.Mold="+"
bracketPram72.Thickness="9.9999999999999982"
bracketPram72.BracketType=1505
bracketPram72.BracketParams=["200"]
bracketPram72.Scallop1Type=1801
bracketPram72.Scallop1Params=["0"]
bracketPram72.Scallop2Type=0
bracketPram72.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram72.RevSf1=False
bracketPram72.Surfaces2=[profile122[0]+",FL"]
bracketPram72.RevSf2=False
bracketPram72.RevSf3=False
bracketPram72.Sf1DimensionType=1541
bracketPram72.Sf1DimensonParams=["0","100"]
bracketPram72.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram72.Sf2DimensionType=1531
bracketPram72.Sf2DimensonParams=["200","15"]
bracket72 = part.CreateBracket(bracketPram72,False)
part.SetElementColor(bracket72,"0","255","255","0.19999998807907104")
mirror_copied99 = part.MirrorCopy([profile44[0]],"PL,Y","")
part.SetElementColor(mirror_copied99[0],"148","0","211","0.39999997615814209")
mirror_copied100 = part.MirrorCopy([profile2[0]],"PL,Y","")
part.SetElementColor(mirror_copied100[0],"255","0","0","0.19999998807907104")
bracketPram73 = part.CreateBracketParam()
bracketPram73.DefinitionType=1
bracketPram73.BracketName="HK.Casing.Wall.Side.FR15.Deck.BP"
bracketPram73.MaterialName="SS400"
bracketPram73.BaseElement=profile26[0]
bracketPram73.UseSideSheetForPlane=False
bracketPram73.Mold="+"
bracketPram73.Thickness="9.9999999999999982"
bracketPram73.BracketType=1505
bracketPram73.BracketParams=["200"]
bracketPram73.Scallop1Type=1801
bracketPram73.Scallop1Params=["0"]
bracketPram73.Scallop2Type=0
bracketPram73.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram73.RevSf1=False
bracketPram73.Surfaces2=[profile26[0]+",FL"]
bracketPram73.RevSf2=False
bracketPram73.RevSf3=False
bracketPram73.Sf1DimensionType=1541
bracketPram73.Sf1DimensonParams=["0","100"]
bracketPram73.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile5[0]]
bracketPram73.Sf2DimensionType=1531
bracketPram73.Sf2DimensonParams=["200","15"]
bracket73 = part.CreateBracket(bracketPram73,False)
part.SetElementColor(bracket73,"0","255","255","0.19999998807907104")
bracketPram74 = part.CreateBracketParam()
bracketPram74.DefinitionType=1
bracketPram74.BracketName="HK.Casing.Wall.Side.FR11.Deck.AP"
bracketPram74.MaterialName="SS400"
bracketPram74.BaseElement=profile116[0]
bracketPram74.UseSideSheetForPlane=False
bracketPram74.Mold="+"
bracketPram74.Thickness="9.9999999999999982"
bracketPram74.BracketType=1505
bracketPram74.BracketParams=["200"]
bracketPram74.Scallop1Type=1801
bracketPram74.Scallop1Params=["0"]
bracketPram74.Scallop2Type=0
bracketPram74.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram74.RevSf1=False
bracketPram74.Surfaces2=[profile116[0]+",FL"]
bracketPram74.RevSf2=False
bracketPram74.RevSf3=False
bracketPram74.Sf1DimensionType=1541
bracketPram74.Sf1DimensonParams=["0","100"]
bracketPram74.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile51[0]]
bracketPram74.Sf2DimensionType=1531
bracketPram74.Sf2DimensonParams=["200","15"]
bracket74 = part.CreateBracket(bracketPram74,False)
part.SetElementColor(bracket74,"0","255","255","0.19999998807907104")
mirror_copied101 = part.MirrorCopy([profile27[0]],"PL,Y","")
part.SetElementColor(mirror_copied101[0],"148","0","211","0.39999997615814209")
mirror_copied102 = part.MirrorCopy([bracket37],"PL,Y","")
part.SetElementColor(mirror_copied102[0],"0","255","255","0.19999998807907104")
mirror_copied103 = part.MirrorCopy([profile112[0]],"PL,Y","")
part.SetElementColor(mirror_copied103[0],"148","0","211","0.39999997615814209")
mirror_copied104 = part.MirrorCopy([bracket7],"PL,Y","")
part.SetElementColor(mirror_copied104[0],"0","255","255","0.19999998807907104")
bracketPram75 = part.CreateBracketParam()
bracketPram75.DefinitionType=1
bracketPram75.BracketName="HK.Casing.Wall.Fore.DL02.Deck.BP"
bracketPram75.MaterialName="SS400"
bracketPram75.BaseElement=profile70[0]
bracketPram75.UseSideSheetForPlane=False
bracketPram75.Mold="+"
bracketPram75.Thickness="7.9999999999999964"
bracketPram75.BracketType=1501
bracketPram75.Scallop1Type=1801
bracketPram75.Scallop1Params=["0"]
bracketPram75.Scallop2Type=0
bracketPram75.Surfaces1=[profile70[0]+",FL"]
bracketPram75.RevSf1=False
bracketPram75.Surfaces2=[profile72[0]+",FL"]
bracketPram75.RevSf2=False
bracketPram75.RevSf3=False
bracketPram75.Sf1DimensionType=1531
bracketPram75.Sf1DimensonParams=["200","15"]
bracketPram75.Sf2DimensionType=1531
bracketPram75.Sf2DimensonParams=["200","15"]
bracket75 = part.CreateBracket(bracketPram75,False)
part.SetElementColor(bracket75,"0","255","255","0.19999998807907104")
mirror_copied105 = part.MirrorCopy([profile30[0]],"PL,Y","")
part.SetElementColor(mirror_copied105[0],"255","0","0","0.19999998807907104")
mirror_copied106 = part.MirrorCopy([profile51[0]],"PL,Y","")
part.SetElementColor(mirror_copied106[0],"255","0","0","0.19999998807907104")
mirror_copied107 = part.MirrorCopy([bracket33],"PL,Y","")
part.SetElementColor(mirror_copied107[0],"0","255","255","0.19999998807907104")
mirror_copied108 = part.MirrorCopy([profile16[1]],"PL,Y","")
part.SetElementColor(mirror_copied108[0],"148","0","211","0.39999997615814209")
mirror_copied109 = part.MirrorCopy([profile79[0]],"PL,Y","")
part.SetElementColor(mirror_copied109[0],"255","0","0","0.19999998807907104")
bracketPram76 = part.CreateBracketParam()
bracketPram76.DefinitionType=1
bracketPram76.BracketName="HK.Casing.Wall.Aft.DL04.Deck.CP"
bracketPram76.MaterialName="SS400"
bracketPram76.BaseElement=profile9[0]
bracketPram76.UseSideSheetForPlane=False
bracketPram76.Mold="-"
bracketPram76.Thickness="7.9999999999999964"
bracketPram76.BracketType=1501
bracketPram76.Scallop1Type=1801
bracketPram76.Scallop1Params=["0"]
bracketPram76.Scallop2Type=0
bracketPram76.Surfaces1=[profile7[0]+",FL"]
bracketPram76.RevSf1=False
bracketPram76.Surfaces2=[profile9[0]+",FL"]
bracketPram76.RevSf2=False
bracketPram76.RevSf3=False
bracketPram76.Sf1DimensionType=1531
bracketPram76.Sf1DimensonParams=["250","15"]
bracketPram76.Sf2DimensionType=1531
bracketPram76.Sf2DimensonParams=["250","15"]
bracket76 = part.CreateBracket(bracketPram76,False)
part.SetElementColor(bracket76,"0","255","255","0.19999998807907104")
mirror_copied110 = part.MirrorCopy([profile37[0]],"PL,Y","")
part.SetElementColor(mirror_copied110[0],"255","0","0","0.19999998807907104")
mirror_copied111 = part.MirrorCopy([profile27[1]],"PL,Y","")
part.SetElementColor(mirror_copied111[0],"148","0","211","0.38999998569488525")
mirror_copied112 = part.MirrorCopy([bracket12],"PL,Y","")
part.SetElementColor(mirror_copied112[0],"0","255","255","0.19999998807907104")
mirror_copied113 = part.MirrorCopy([profile83[0]],"PL,Y","")
part.SetElementColor(mirror_copied113[0],"255","0","0","0.19999998807907104")
mirror_copied114 = part.MirrorCopy([profile15[0]],"PL,Y","")
part.SetElementColor(mirror_copied114[0],"255","0","0","0.19999998807907104")
mirror_copied115 = part.MirrorCopy([profile20[0]],"PL,Y","")
part.SetElementColor(mirror_copied115[0],"255","0","0","0.19999998807907104")
mirror_copied116 = part.MirrorCopy([profile19[0]],"PL,Y","")
part.SetElementColor(mirror_copied116[0],"255","0","0","0.19999998807907104")
mirror_copied117 = part.MirrorCopy([bracket26],"PL,Y","")
part.SetElementColor(mirror_copied117[0],"0","255","255","0.19999998807907104")
mirror_copied118 = part.MirrorCopy([bracket5],"PL,Y","")
part.SetElementColor(mirror_copied118[0],"0","255","255","0.19999998807907104")
mirror_copied119 = part.MirrorCopy([profile114[0]],"PL,Y","")
part.SetElementColor(mirror_copied119[0],"255","0","0","0.19999998807907104")
bracketPram77 = part.CreateBracketParam()
bracketPram77.DefinitionType=1
bracketPram77.BracketName="HK.Casing.Wall.Side.FR08.Deck.AP"
bracketPram77.MaterialName="SS400"
bracketPram77.BaseElement=profile59[0]
bracketPram77.UseSideSheetForPlane=False
bracketPram77.Mold="+"
bracketPram77.Thickness="9.9999999999999982"
bracketPram77.BracketType=1505
bracketPram77.BracketParams=["200"]
bracketPram77.Scallop1Type=1801
bracketPram77.Scallop1Params=["0"]
bracketPram77.Scallop2Type=0
bracketPram77.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram77.RevSf1=False
bracketPram77.Surfaces2=[profile59[0]+",FL"]
bracketPram77.RevSf2=False
bracketPram77.RevSf3=False
bracketPram77.Sf1DimensionType=1541
bracketPram77.Sf1DimensonParams=["0","100"]
bracketPram77.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile51[0]]
bracketPram77.Sf2DimensionType=1531
bracketPram77.Sf2DimensonParams=["200","15"]
bracket77 = part.CreateBracket(bracketPram77,False)
part.SetElementColor(bracket77,"0","255","255","0.19999998807907104")
mirror_copied120 = part.MirrorCopy([profile116[0]],"PL,Y","")
part.SetElementColor(mirror_copied120[0],"255","0","0","0.19999998807907104")
mirror_copied121 = part.MirrorCopy([profile98[0]],"PL,Y","")
part.SetElementColor(mirror_copied121[0],"148","0","211","0.39999997615814209")
mirror_copied122 = part.MirrorCopy([profile113[0]],"PL,Y","")
part.SetElementColor(mirror_copied122[0],"255","0","0","0.19999998807907104")
mirror_copied123 = part.MirrorCopy([bracket11],"PL,Y","")
part.SetElementColor(mirror_copied123[0],"0","255","255","0.19999998807907104")
mirror_copied124 = part.MirrorCopy([profile66[0]],"PL,Y","")
part.SetElementColor(mirror_copied124[0],"255","0","0","0.19999998807907104")
mirror_copied125 = part.MirrorCopy([bracket52],"PL,Y","")
part.SetElementColor(mirror_copied125[0],"0","255","255","0.19999998807907104")
bracketPram78 = part.CreateBracketParam()
bracketPram78.DefinitionType=1
bracketPram78.BracketName="HK.Casing.Wall.Side.FR10.Deck.CP"
bracketPram78.MaterialName="SS400"
bracketPram78.BaseElement=profile92[0]
bracketPram78.UseSideSheetForPlane=False
bracketPram78.Mold="+"
bracketPram78.Thickness="9.9999999999999982"
bracketPram78.BracketType=1505
bracketPram78.BracketParams=["200"]
bracketPram78.Scallop1Type=1801
bracketPram78.Scallop1Params=["0"]
bracketPram78.Scallop2Type=0
bracketPram78.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram78.RevSf1=False
bracketPram78.Surfaces2=[profile92[0]+",FL"]
bracketPram78.RevSf2=False
bracketPram78.RevSf3=False
bracketPram78.Sf1DimensionType=1541
bracketPram78.Sf1DimensonParams=["0","100"]
bracketPram78.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile22[0]]
bracketPram78.Sf2DimensionType=1531
bracketPram78.Sf2DimensonParams=["200","15"]
bracket78 = part.CreateBracket(bracketPram78,False)
part.SetElementColor(bracket78,"0","255","255","0.19999998807907104")
mirror_copied126 = part.MirrorCopy([bracket25],"PL,Y","")
part.SetElementColor(mirror_copied126[0],"0","255","255","0.19999998807907104")
mirror_copied127 = part.MirrorCopy([bracket78],"PL,Y","")
part.SetElementColor(mirror_copied127[0],"0","255","255","0.19999998807907104")
ProfilePram123 = part.CreateProfileParam()
ProfilePram123.DefinitionType=1
ProfilePram123.BasePlane="PL,O,"+var_elm6+","+"PL,Y"
ProfilePram123.AddAttachSurfaces(extrude_sheet3)
ProfilePram123.ProfileName="HK.Casing.Wall.Aft.DL00.OA"
ProfilePram123.MaterialName="SS400"
ProfilePram123.ProfileType=1002
ProfilePram123.ProfileParams=["125","75","7","10","5"]
ProfilePram123.ReverseDir=False
ProfilePram123.ReverseAngle=True
ProfilePram123.CalcSnipOnlyAttachLines=False
ProfilePram123.AttachDirMethod=0
ProfilePram123.CCWDefAngle=False
ProfilePram123.AddEnd1Elements(extrude_sheet2)
ProfilePram123.End1Type=1102
ProfilePram123.End1TypeParams=["25","29.999999999999996","0","0"]
ProfilePram123.AddEnd2Elements(extrude_sheet8)
ProfilePram123.End2Type=1102
ProfilePram123.End2TypeParams=["25","29.999999999999996","0","0"]
ProfilePram123.End1ScallopType=1121
ProfilePram123.End1ScallopTypeParams=["25","40"]
ProfilePram123.End2ScallopType=1121
ProfilePram123.End2ScallopTypeParams=["25","40"]
profile123 = part.CreateProfile(ProfilePram123,False)
part.SetElementColor(profile123[0],"255","0","0","0.19999998807907104")
bracketPram79 = part.CreateBracketParam()
bracketPram79.DefinitionType=1
bracketPram79.BracketName="HK.Casing.Wall.Aft.DL00.Deck.A"
bracketPram79.MaterialName="SS400"
bracketPram79.BaseElement=profile123[0]
bracketPram79.UseSideSheetForPlane=False
bracketPram79.Mold="+"
bracketPram79.Thickness="7.9999999999999964"
bracketPram79.BracketType=1505
bracketPram79.BracketParams=["200"]
bracketPram79.Scallop1Type=1801
bracketPram79.Scallop1Params=["0"]
bracketPram79.Scallop2Type=0
bracketPram79.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram79.RevSf1=False
bracketPram79.Surfaces2=[profile123[0]+",FL"]
bracketPram79.RevSf2=False
bracketPram79.RevSf3=False
bracketPram79.Sf1DimensionType=1541
bracketPram79.Sf1DimensonParams=["0","100"]
bracketPram79.Sf1EndElements=["PLS","False","False","-1","0","-0",profile63[0]]
bracketPram79.Sf2DimensionType=1531
bracketPram79.Sf2DimensonParams=["200","15"]
bracket79 = part.CreateBracket(bracketPram79,False)
part.SetElementColor(bracket79,"0","255","255","0.19999998807907104")
bracketPram80 = part.CreateBracketParam()
bracketPram80.DefinitionType=1
bracketPram80.BracketName="HK.Casing.Wall.Side.FR07.Deck.DP"
bracketPram80.MaterialName="SS400"
bracketPram80.BaseElement=profile25[0]
bracketPram80.UseSideSheetForPlane=False
bracketPram80.Mold="+"
bracketPram80.Thickness="9.9999999999999982"
bracketPram80.BracketType=1505
bracketPram80.BracketParams=["200"]
bracketPram80.Scallop1Type=1801
bracketPram80.Scallop1Params=["0"]
bracketPram80.Scallop2Type=0
bracketPram80.Surfaces1=["PLS","False","False","0","-0","-1",solid2]
bracketPram80.RevSf1=False
bracketPram80.Surfaces2=[profile25[0]+",FL"]
bracketPram80.RevSf2=False
bracketPram80.RevSf3=False
bracketPram80.Sf1DimensionType=1541
bracketPram80.Sf1DimensonParams=["0","100"]
bracketPram80.Sf1EndElements=["PLS","False","False","-0","-1","-0",profile15[0]]
bracketPram80.Sf2DimensionType=1531
bracketPram80.Sf2DimensonParams=["200","15"]
bracket80 = part.CreateBracket(bracketPram80,False)
part.SetElementColor(bracket80,"0","255","255","0.19999998807907104")
extrudePram53 = part.CreateLinearSweepParam()
extrudePram53.Name="積-押し出し43"
extrudePram53.AddProfile(extrude_sheet4)
extrudePram53.DirectionType="R"
extrudePram53.DirectionParameter1="50000"
extrudePram53.SweepDirection="+Y"
extrudePram53.RefByGeometricMethod=True
extrude44 = part.CreateLinearSweep(solid6,"*",extrudePram53,False)
extrudePram54 = part.CreateLinearSweepParam()
extrudePram54.Name="積-押し出し44"
extrudePram54.AddProfile(extrude_sheet9)
extrudePram54.DirectionType="N"
extrudePram54.DirectionParameter1="50000"
extrudePram54.SweepDirection="+Y"
extrudePram54.RefByGeometricMethod=True
extrude45 = part.CreateLinearSweep(solid6,"*",extrudePram54,False)
extrudePram55 = part.CreateLinearSweepParam()
extrudePram55.Name="積-押し出し45"
extrudePram55.AddProfile(extrude_sheet1)
extrudePram55.DirectionType="R"
extrudePram55.DirectionParameter1="50000"
extrudePram55.SweepDirection="+Z"
extrudePram55.RefByGeometricMethod=True
extrude46 = part.CreateLinearSweep(solid6,"*",extrudePram55,False)
extrudePram56 = part.CreateLinearSweepParam()
extrudePram56.Name="積-押し出し46"
extrudePram56.AddProfile(extrude_sheet2)
extrudePram56.DirectionType="N"
extrudePram56.DirectionParameter1="50000"
extrudePram56.SweepDirection="+Z"
extrudePram56.RefByGeometricMethod=True
extrude47 = part.CreateLinearSweep(solid6,"*",extrudePram56,False)
mirror_copied128 = part.MirrorCopy([profile115[0]],"PL,Y","")
part.SetElementColor(mirror_copied128[0],"255","0","0","0.19999998807907104")
mirror_copied129 = part.MirrorCopy([bracket75],"PL,Y","")
part.SetElementColor(mirror_copied129[0],"0","255","255","0.19999998807907104")
mirror_copied130 = part.MirrorCopy([bracket80],"PL,Y","")
part.SetElementColor(mirror_copied130[0],"0","255","255","0.19999998807907104")
mirror_copied131 = part.MirrorCopy([bracket31],"PL,Y","")
part.SetElementColor(mirror_copied131[0],"0","255","255","0.19999998807907104")
extrudePram57 = part.CreateLinearSweepParam()
extrudePram57.Name="積-押し出し41"
extrudePram57.AddProfile(extrude_sheet6)
extrudePram57.DirectionType="R"
extrudePram57.DirectionParameter1="50000"
extrudePram57.SweepDirection="+Z"
extrudePram57.RefByGeometricMethod=True
extrude48 = part.CreateLinearSweep(solid14,"*",extrudePram57,False)
extrudePram58 = part.CreateLinearSweepParam()
extrudePram58.Name="積-押し出し42"
extrudePram58.AddProfile(extrude_sheet1)
extrudePram58.DirectionType="N"
extrudePram58.DirectionParameter1="50000"
extrudePram58.SweepDirection="+Z"
extrudePram58.RefByGeometricMethod=True
extrude49 = part.CreateLinearSweep(solid14,"*",extrudePram58,False)
mirror_copied132 = part.MirrorCopy([profile6[0]],"PL,Y","")
part.SetElementColor(mirror_copied132[0],"255","0","0","0.19999998807907104")
solid16 = part.CreateSolid("HK.Casing.Wall.Side.ABP","","SS400")
part.SetElementColor(solid16,"139","69","19","0.79999995231628418")
thicken16 = part.CreateThicken("厚み付け9",solid16,"+",[extrude_sheet4],"-","10","0","0",False,False)
extrudePram59 = part.CreateLinearSweepParam()
extrudePram59.Name="積-押し出し13"
extrudePram59.AddProfile(skt_pl4+",Edge00")
extrudePram59.DirectionType="N"
extrudePram59.DirectionParameter1="50000"
extrudePram59.SweepDirection="+Z"
extrudePram59.RefByGeometricMethod=True
extrude50 = part.CreateLinearSweep(solid16,"*",extrudePram59,False)
extrudePram60 = part.CreateLinearSweepParam()
extrudePram60.Name="積-押し出し14"
extrudePram60.AddProfile(extrude_sheet1)
extrudePram60.DirectionType="R"
extrudePram60.DirectionParameter1="50000"
extrudePram60.SweepDirection="+Z"
extrudePram60.RefByGeometricMethod=True
extrude51 = part.CreateLinearSweep(solid16,"*",extrudePram60,False)
extrudePram61 = part.CreateLinearSweepParam()
extrudePram61.Name="積-押し出し15"
extrudePram61.AddProfile(extrude_sheet2)
extrudePram61.DirectionType="N"
extrudePram61.DirectionParameter1="50000"
extrudePram61.SweepDirection="+Z"
extrudePram61.RefByGeometricMethod=True
extrude52 = part.CreateLinearSweep(solid16,"*",extrudePram61,False)
mirror_copied133 = part.MirrorCopy([profile3[0]],"PL,Y","")
part.SetElementColor(mirror_copied133[0],"255","0","0","0.19999998807907104")
mirror_copied134 = part.MirrorCopy([bracket48],"PL,Y","")
part.SetElementColor(mirror_copied134[0],"0","255","255","0.19999998807907104")
mirror_copied135 = part.MirrorCopy([profile14[0]],"PL,Y","")
part.SetElementColor(mirror_copied135[0],"255","0","0","0.19999998807907104")
mirror_copied136 = part.MirrorCopy([profile21[0]],"PL,Y","")
part.SetElementColor(mirror_copied136[0],"255","0","0","0.19999998807907104")
bracketPram81 = part.CreateBracketParam()
bracketPram81.DefinitionType=1
bracketPram81.BracketName="HK.Casing.Wall.Aft.DL03.Deck.AP"
bracketPram81.MaterialName="SS400"
bracketPram81.BaseElement=profile119[0]
bracketPram81.UseSideSheetForPlane=False
bracketPram81.Mold="+"
bracketPram81.Thickness="7.9999999999999964"
bracketPram81.BracketType=1505
bracketPram81.BracketParams=["200"]
bracketPram81.Scallop1Type=1801
bracketPram81.Scallop1Params=["0"]
bracketPram81.Scallop2Type=0
bracketPram81.Surfaces1=["PLS","False","False","0","-0","-1",solid4]
bracketPram81.RevSf1=False
bracketPram81.Surfaces2=[profile119[0]+",FL"]
bracketPram81.RevSf2=False
bracketPram81.RevSf3=False
bracketPram81.Sf1DimensionType=1541
bracketPram81.Sf1DimensonParams=["0","100"]
bracketPram81.Sf1EndElements=["PLS","False","False","-1","0","-0",profile63[0]]
bracketPram81.Sf2DimensionType=1531
bracketPram81.Sf2DimensonParams=["200","15"]
bracket81 = part.CreateBracket(bracketPram81,False)
part.SetElementColor(bracket81,"0","255","255","0.19999998807907104")
mirror_copied137 = part.MirrorCopy([profile120[0]],"PL,Y","")
part.SetElementColor(mirror_copied137[0],"148","0","211","0.39999997615814209")
mirror_copied138 = part.MirrorCopy([profile111[0]],"PL,Y","")
part.SetElementColor(mirror_copied138[0],"255","0","0","0.19999998807907104")
mirror_copied139 = part.MirrorCopy([profile100[0]],"PL,Y","")
part.SetElementColor(mirror_copied139[0],"255","0","0","0.19999998807907104")
mirror_copied140 = part.MirrorCopy([bracket2],"PL,Y","")
part.SetElementColor(mirror_copied140[0],"0","255","255","0.19999998807907104")
mirror_copied141 = part.MirrorCopy([profile45[0]],"PL,Y","")
part.SetElementColor(mirror_copied141[0],"148","0","211","0.39999997615814209")
mirror_copied142 = part.MirrorCopy([bracket57],"PL,Y","")
part.SetElementColor(mirror_copied142[0],"0","255","255","0.19999998807907104")
mirror_copied143 = part.MirrorCopy([profile73[0]],"PL,Y","")
part.SetElementColor(mirror_copied143[0],"255","0","0","0.19999998807907104")
mirror_copied144 = part.MirrorCopy([bracket40],"PL,Y","")
part.SetElementColor(mirror_copied144[0],"0","255","255","0.19999998807907104")
bracketPram82 = part.CreateBracketParam()
bracketPram82.DefinitionType=1
bracketPram82.BracketName="HK.Casing.Wall.Aft.DL00.Deck.B"
bracketPram82.MaterialName="SS400"
bracketPram82.BaseElement=profile99[0]
bracketPram82.UseSideSheetForPlane=False
bracketPram82.Mold="+"
bracketPram82.Thickness="7.9999999999999964"
bracketPram82.BracketType=1505
bracketPram82.BracketParams=["200"]
bracketPram82.Scallop1Type=1801
bracketPram82.Scallop1Params=["0"]
bracketPram82.Scallop2Type=0
bracketPram82.Surfaces1=["PLS","False","False","0","-0","-1",solid1]
bracketPram82.RevSf1=False
bracketPram82.Surfaces2=[profile99[0]+",FL"]
bracketPram82.RevSf2=False
bracketPram82.RevSf3=False
bracketPram82.Sf1DimensionType=1541
bracketPram82.Sf1DimensonParams=["0","100"]
bracketPram82.Sf1EndElements=["PLS","False","False","-1","0","-0",profile34[0]]
bracketPram82.Sf2DimensionType=1531
bracketPram82.Sf2DimensonParams=["200","15"]
bracket82 = part.CreateBracket(bracketPram82,False)
part.SetElementColor(bracket82,"0","255","255","0.19999998807907104")
mirror_copied145 = part.MirrorCopy([bracket72],"PL,Y","")
part.SetElementColor(mirror_copied145[0],"0","255","255","0.19999998807907104")
mirror_copied146 = part.MirrorCopy([profile42[0]],"PL,Y","")
part.SetElementColor(mirror_copied146[0],"148","0","211","0.39999997615814209")
mirror_copied147 = part.MirrorCopy([profile98[1]],"PL,Y","")
part.SetElementColor(mirror_copied147[0],"148","0","211","0.39999997615814209")
mirror_copied148 = part.MirrorCopy([bracket19],"PL,Y","")
part.SetElementColor(mirror_copied148[0],"0","255","255","0.19999998807907104")
mirror_copied149 = part.MirrorCopy([profile59[0]],"PL,Y","")
part.SetElementColor(mirror_copied149[0],"255","0","0","0.19999998807907104")
mirror_copied150 = part.MirrorCopy([bracket77],"PL,Y","")
part.SetElementColor(mirror_copied150[0],"0","255","255","0.19999998807907104")
mirror_copied151 = part.MirrorCopy([bracket74],"PL,Y","")
part.SetElementColor(mirror_copied151[0],"0","255","255","0.19999998807907104")
mirror_copied152 = part.MirrorCopy([bracket17],"PL,Y","")
part.SetElementColor(mirror_copied152[0],"0","255","255","0.19999998807907104")
mirror_copied153 = part.MirrorCopy([profile117[0]],"PL,Y","")
part.SetElementColor(mirror_copied153[0],"255","0","0","0.19999998807907104")
mirror_copied154 = part.MirrorCopy([profile22[0]],"PL,Y","")
part.SetElementColor(mirror_copied154[0],"255","0","0","0.19999998807907104")
mirror_copied155 = part.MirrorCopy([solid12],"PL,Y","")
part.SetElementColor(mirror_copied155[0],"139","69","19","0.79999995231628418")
mirror_copied156 = part.MirrorCopy([bracket64],"PL,Y","")
part.SetElementColor(mirror_copied156[0],"0","255","255","0.19999998807907104")
mirror_copied157 = part.MirrorCopy([bracket76],"PL,Y","")
part.SetElementColor(mirror_copied157[0],"0","255","255","0.19999998807907104")
mirror_copied158 = part.MirrorCopy([profile40[0]],"PL,Y","")
part.SetElementColor(mirror_copied158[0],"148","0","211","0.39999997615814209")
mirror_copied159 = part.MirrorCopy([bracket28],"PL,Y","")
part.SetElementColor(mirror_copied159[0],"0","255","255","0.19999998807907104")
mirror_copied160 = part.MirrorCopy([profile96[0]],"PL,Y","")
part.SetElementColor(mirror_copied160[0],"148","0","211","0.39999997615814209")
mirror_copied161 = part.MirrorCopy([profile108[0]],"PL,Y","")
part.SetElementColor(mirror_copied161[0],"255","0","0","0.19999998807907104")
mirror_copied162 = part.MirrorCopy([profile120[1]],"PL,Y","")
part.SetElementColor(mirror_copied162[0],"148","0","211","0.39999997615814209")
mirror_copied163 = part.MirrorCopy([bracket67],"PL,Y","")
part.SetElementColor(mirror_copied163[0],"0","255","255","0.19999998807907104")
mirror_copied164 = part.MirrorCopy([bracket36],"PL,Y","")
part.SetElementColor(mirror_copied164[0],"0","255","255","0.19999998807907104")
mirror_copied165 = part.MirrorCopy([bracket51],"PL,Y","")
part.SetElementColor(mirror_copied165[0],"0","255","255","0.19999998807907104")
mirror_copied166 = part.MirrorCopy([profile89[0]],"PL,Y","")
part.SetElementColor(mirror_copied166[0],"255","0","0","0.19999998807907104")
mirror_copied167 = part.MirrorCopy([profile106[0]],"PL,Y","")
part.SetElementColor(mirror_copied167[0],"255","0","0","0.19999998807907104")
mirror_copied168 = part.MirrorCopy([bracket73],"PL,Y","")
part.SetElementColor(mirror_copied168[0],"0","255","255","0.19999998807907104")
mirror_copied169 = part.MirrorCopy([bracket81],"PL,Y","")
part.SetElementColor(mirror_copied169[0],"0","255","255","0.19999998807907104")
bracketPram83 = part.CreateBracketParam()
bracketPram83.DefinitionType=1
bracketPram83.BracketName="HK.Casing.Wall.Aft.DL00.Deck.D"
bracketPram83.MaterialName="SS400"
bracketPram83.BaseElement=profile121[0]
bracketPram83.UseSideSheetForPlane=False
bracketPram83.Mold="+"
bracketPram83.Thickness="7.9999999999999964"
bracketPram83.BracketType=1501
bracketPram83.Scallop1Type=1801
bracketPram83.Scallop1Params=["0"]
bracketPram83.Scallop2Type=0
bracketPram83.Surfaces1=[profile121[0]+",FL"]
bracketPram83.RevSf1=False
bracketPram83.Surfaces2=[profile36[0]+",FL"]
bracketPram83.RevSf2=False
bracketPram83.RevSf3=False
bracketPram83.Sf1DimensionType=1531
bracketPram83.Sf1DimensonParams=["200","15"]
bracketPram83.Sf2DimensionType=1531
bracketPram83.Sf2DimensonParams=["200","15"]
bracket83 = part.CreateBracket(bracketPram83,False)
part.SetElementColor(bracket83,"0","255","255","0.19999998807907104")
mirror_copied170 = part.MirrorCopy([profile109[0]],"PL,Y","")
part.SetElementColor(mirror_copied170[0],"255","0","0","0.19999998807907104")
mirror_copied171 = part.MirrorCopy([bracket66],"PL,Y","")
part.SetElementColor(mirror_copied171[0],"0","255","255","0.19999998807907104")
mirror_copied172 = part.MirrorCopy([profile61[0]],"PL,Y","")
part.SetElementColor(mirror_copied172[0],"148","0","211","0.39999997615814209")
mirror_copied173 = part.MirrorCopy([profile102[0]],"PL,Y","")
part.SetElementColor(mirror_copied173[0],"255","0","0","0.19999998807907104")
mirror_copied174 = part.MirrorCopy([profile26[0]],"PL,Y","")
part.SetElementColor(mirror_copied174[0],"255","0","0","0.19999998807907104")
mirror_copied175 = part.MirrorCopy([profile7[0]],"PL,Y","")
part.SetElementColor(mirror_copied175[0],"148","0","211","0.39999997615814209")
mirror_copied176 = part.MirrorCopy([bracket58],"PL,Y","")
part.SetElementColor(mirror_copied176[0],"0","255","255","0.19999998807907104")
mirror_copied177 = part.MirrorCopy([profile49[0]],"PL,Y","")
part.SetElementColor(mirror_copied177[0],"255","0","0","0.19999998807907104")
mirror_copied178 = part.MirrorCopy([bracket62],"PL,Y","")
part.SetElementColor(mirror_copied178[0],"0","255","255","0.19999998807907104")
mirror_copied179 = part.MirrorCopy([profile77[0]],"PL,Y","")
part.SetElementColor(mirror_copied179[0],"148","0","211","0.39999997615814209")
mirror_copied180 = part.MirrorCopy([profile104[0]],"PL,Y","")
part.SetElementColor(mirror_copied180[0],"255","0","0","0.19999998807907104")
mirror_copied181 = part.MirrorCopy([bracket70],"PL,Y","")
part.SetElementColor(mirror_copied181[0],"0","255","255","0.19999998807907104")
bracketPram84 = part.CreateBracketParam()
bracketPram84.DefinitionType=1
bracketPram84.BracketName="HK.Casing.Wall.Aft.DL00.Deck.C"
bracketPram84.MaterialName="SS400"
bracketPram84.BaseElement=profile13[0]
bracketPram84.UseSideSheetForPlane=False
bracketPram84.Mold="+"
bracketPram84.Thickness="7.9999999999999964"
bracketPram84.BracketType=1505
bracketPram84.BracketParams=["200"]
bracketPram84.Scallop1Type=1801
bracketPram84.Scallop1Params=["0"]
bracketPram84.Scallop2Type=0
bracketPram84.Surfaces1=["PLS","False","False","0","-0","-1",solid3]
bracketPram84.RevSf1=False
bracketPram84.Surfaces2=[profile13[0]+",FL"]
bracketPram84.RevSf2=False
bracketPram84.RevSf3=False
bracketPram84.Sf1DimensionType=1541
bracketPram84.Sf1DimensonParams=["0","100"]
bracketPram84.Sf1EndElements=["PLS","False","False","-1","0","-0",profile12[0]]
bracketPram84.Sf2DimensionType=1531
bracketPram84.Sf2DimensonParams=["200","15"]
bracket84 = part.CreateBracket(bracketPram84,False)
part.SetElementColor(bracket84,"0","255","255","0.19999998807907104")
bracketPram85 = part.CreateBracketParam()
bracketPram85.DefinitionType=1
bracketPram85.BracketName="HK.Casing.Wall.Fore.DL00.Deck.B"
bracketPram85.MaterialName="SS400"
bracketPram85.BaseElement=profile84[0]
bracketPram85.UseSideSheetForPlane=False
bracketPram85.Mold="+"
bracketPram85.Thickness="7.9999999999999964"
bracketPram85.BracketType=1501
bracketPram85.Scallop1Type=1801
bracketPram85.Scallop1Params=["0"]
bracketPram85.Scallop2Type=0
bracketPram85.Surfaces1=[profile84[0]+",FL"]
bracketPram85.RevSf1=False
bracketPram85.Surfaces2=[profile85[0]+",FL"]
bracketPram85.RevSf2=False
bracketPram85.RevSf3=False
bracketPram85.Sf1DimensionType=1531
bracketPram85.Sf1DimensonParams=["200","15"]
bracketPram85.Sf2DimensionType=1531
bracketPram85.Sf2DimensonParams=["200","15"]
bracket85 = part.CreateBracket(bracketPram85,False)
part.SetElementColor(bracket85,"0","255","255","0.19999998807907104")
mirror_copied182 = part.MirrorCopy([bracket46],"PL,Y","")
part.SetElementColor(mirror_copied182[0],"0","255","255","0.19999998807907104")
mirror_copied183 = part.MirrorCopy([profile11[0]],"PL,Y","")
part.SetElementColor(mirror_copied183[0],"255","0","0","0.19999998807907104")
mirror_copied184 = part.MirrorCopy([profile1[0]],"PL,Y","")
part.SetElementColor(mirror_copied184[0],"148","0","211","0.39999997615814209")
mirror_copied185 = part.MirrorCopy([profile35[0]],"PL,Y","")
part.SetElementColor(mirror_copied185[0],"255","0","0","0.19999998807907104")
mirror_copied186 = part.MirrorCopy([bracket53],"PL,Y","")
part.SetElementColor(mirror_copied186[0],"0","255","255","0.19999998807907104")
mirror_copied187 = part.MirrorCopy([solid16],"PL,Y","")
part.SetElementColor(mirror_copied187[0],"139","69","19","0.79999995231628418")
mirror_copied188 = part.MirrorCopy([bracket18],"PL,Y","")
part.SetElementColor(mirror_copied188[0],"0","255","255","0.19999998807907104")
mirror_copied189 = part.MirrorCopy([bracket1],"PL,Y","")
part.SetElementColor(mirror_copied189[0],"0","255","255","0.19999998807907104")
mirror_copied190 = part.MirrorCopy([profile70[0]],"PL,Y","")
part.SetElementColor(mirror_copied190[0],"255","0","0","0.19999998807907104")
mirror_copied191 = part.MirrorCopy([bracket55],"PL,Y","")
part.SetElementColor(mirror_copied191[0],"0","255","255","0.19999998807907104")
mirror_copied192 = part.MirrorCopy([bracket6],"PL,Y","")
part.SetElementColor(mirror_copied192[0],"0","255","255","0.19999998807907104")

