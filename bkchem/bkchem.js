
function send_xmlhttprequest( obsluha, method, url, content, headers) {
    var xmlhttp = (window.XMLHttpRequest ? new XMLHttpRequest : (window.ActiveXObject ? new ActiveXObject("Microsoft.XMLHTTP") : false));
    if (!xmlhttp) {
	return false;
    }
    xmlhttp.open(method, url); 
    xmlhttp.onreadystatechange = function() { obsluha(xmlhttp);};

    if (headers) { 
	for (var key in headers)
	    { xmlhttp.setRequestHeader(key, headers[key]); }
    }
    
    xmlhttp.send(content);
    return true;

}




function ajax_handler( xmlhttp) {

    switch (xmlhttp.readyState) {

    case 1:
	break;
    case 2:
	break;
    case 3:
	break;
    case 4:
	img = document.getElementById( "the_pict");
	img.setAttribute( "src", "content.png?"+(new Date()).getTime());
	smiles = xmlhttp.responseXML.getElementsByTagName( "smiles")[0];
	document.getElementById( "the_smiles").innerHTML = smiles.firstChild.nodeValue;
	//alert( img.src);
       
    }
}





function click( event) {
    
    //alert( event);
    x = event.clientX;
    y = event.clientY;
    //alert( x+" "+y);
    send_xmlhttprequest( ajax_handler, 'GET', encodeURI( '/?action=click&x='+x+'&y='+y));
}



function send_action( action) {
    
    send_xmlhttprequest( ajax_handler, 'GET', encodeURI( '/?action='+action));
}


function set_symbol( symbol) {

    send_xmlhttprequest( ajax_handler, 'GET', encodeURI( '/?action=setsymbol&symbol='+symbol));

}



function set_symbol_from_entry() {

    send_xmlhttprequest( ajax_handler, 'GET', encodeURI( '/?action=setsymbol&symbol='+document.forms[0].symbol_text.value));

}


function set_template( temp) {

    send_xmlhttprequest( ajax_handler, 'GET', encodeURI( '/?action=settemplate&temp='+temp));


}



function set_mode( mode) {

    send_xmlhttprequest( ajax_handler, 'GET', encodeURI( '/?action=setmode&mode='+mode));


}

