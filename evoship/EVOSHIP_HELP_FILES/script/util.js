
function popupAVI(avifile,x,y,w,h){
    var wOBJ   = window.createPopup();
    var popOBJ = wOBJ.document.body;
	popOBJ.style.border = "solid black 1px";
	popOBJ.innerHTML = "<img dynsrc='"+avifile+"'/>";
    wOBJ.show(x,y,w,h,document.body);
}
