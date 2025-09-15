import win32com.client
evoship = win32com.client.DispatchEx("EvoShip.Application")
evoship.ShowMainWindow(True)
doc = evoship.Create3DDocument()
part = doc.GetPart()
emb_elements = part.CreateElementsFromFile("C:\\Users\\akiro\\workfolder\\imabari3dcad\\evoship\\cube_dxf.x_t")
part.SetElementColor(emb_elements[0],"225","225","225","0")

