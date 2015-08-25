// JavaScript Document

function getXML(addressXML){
    $.ajax({
        type:"GET",
        url:addressXML,
        dataType:"json",
        success:function(ResponseText){
            var tableHTML = GetTableHtml(ResponseText);
            $("#div_Configuration_right_top_id").after($(tableHTML));
        }
    });//ajax  
};

function setAjaxReturnToContainer(container, addressXML){
    $.ajax({
        type:"GET",
        url:addressXML,
        dataType:"html",
        success:function(ResponseText){
            ResponseText = ResponseText.replace(/"/g,'');
            container.html(ResponseText.replace(/\\n/g,'&#013; &#010;'));
        }
    });//ajax  
};



function GetTableHtml(jsonStr){
	var tableClass = "table_class";
	var tableID = "table_id";
	var tableHtml;
	var cols;
	var rows;

	
	tableHtml =  "<table id='"+tableID+"' class='"+tableClass+"'>";
	tableHtml += "<tbody>";
	
	//table head
	tableHtml += "<tr>"; 
	      tableHtml += "<th class='checkbox_td_class'>";
		  tableHtml += "<input type='checkbox' class = 'checkbox_all_class' id= 'checkbox_all_id' onclick= 'Check_ALL()' name='checkbox_all'>";
		  tableHtml += "</th>";
		 	  
		  tableHtml += "<th>";
		  tableHtml += "Key";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "Value";
		  tableHtml += "</th>";
		  
		  tableHtml += "</th>"
	tableHtml += "</tr>";
	
	 $.each(jsonStr,function(index,val){
		
		 tableHtml += "<tr>";
	
		  tableHtml += "<td class='checkbox_td_class'>";
		  tableHtml += "<input type='checkbox' class = 'checkbox_class' id='checkbox_'+ "+index+" name='checkbox'+"+index+">";
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_key_class'>";
		  tableHtml += val.key;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_value_class' id='td_value_id_"+index+"'>";
		  tableHtml += "<label id='label_id_"+index+"'  class = 'label_class' onclick = 'Label_Click("+index+" ,&quot;"+ val.value+"&quot;)'>" + val.value;
		  tableHtml +=  "</label>";
		  tableHtml += "</td>";
		  
		tableHtml += "</tr>";
		
		return tableHtml;
	 });	
	tableHtml += "</tbody>";
	tableHtml += "</table>"
	return tableHtml;
}

function Label_Click(count,value){	
	var rowNum = count;	
    olabel = document.getElementById("label_id_"+rowNum);
	olabel.style.backgroundColor = "#cff";
	
	otd = document.getElementById("td_value_id_"+rowNum);
	otd.removeChild(olabel);
    
	var strHtml =  "<input class='text_class' id = 'text_id_"+rowNum+"' value = '"+value+"' type='text' name='fname'/>";
	    strHtml += "<input class='btn_okcancel_class' id = 'bnt_ok_id_"+rowNum+"' type='button' value='OK' onclick= 'Ok_Apply("+rowNum+")' />";
	    strHtml += "<input class='btn_okcancel_class' id = 'bnt_cancel_id_"+rowNum+"' type='button' value='Cancel' onclick= 'Cancel_Apply("+rowNum+",&quot;"+value+"&quot;)'/>";
	otd.innerHTML =strHtml;
}

function Ok_Apply(rowNum){
	
	otd = document.getElementById("td_value_id_"+rowNum);
	otext = document.getElementById("text_id_"+rowNum);
	var valueStr =  otext.value;
	otd.innerHTML =" <label id = 'label_id_"+rowNum+"' class = 'label_class' onclick='Label_Click("+rowNum+", &quot;"+ valueStr+"&quot;)' >"+ valueStr +"</label>";
}

function Cancel_Apply(rowNum,value){
	otd = document.getElementById("td_value_id_"+rowNum);
	otext = document.getElementById("text_id_"+rowNum);	
	otd.innerHTML =" <label id='label_id_"+rowNum+"' class = 'label_class' onclick='Label_Click("+rowNum+", &quot;"+ value+"&quot;)' >"+ value +"</label>";
}

function Check_ALL(){
	var oCheck = document.getElementById("checkbox_all_id");
	if(oCheck.checked == true)
	{
		 var delArray = getElementsClass("checkbox_class");
		 for(var i=0;i< delArray.length;i++)
		 {
		    delArray[i].checked = true;
		 }	
	}
	else
	{
		 var delArray = getElementsClass("checkbox_class");
		 for(var i=0;i< delArray.length;i++){
		    delArray[i].checked = false;
		 }		
	}
}



function Del(){
	var oTable = document.getElementById("table_id");
	var delArray = getElementsClass("checkbox_class");
    for(var i=0;i< delArray.length;i++){ 
		if(delArray[i].checked == true){
			delArray[i].parentNode.parentNode.parentNode.removeChild(delArray[i].parentNode.parentNode);
		}	
	}
}



function getElementsClass(classnames){ 
    var classobj= new Array(); 
    var classint=0;
    var tags=document.getElementsByTagName("*");
    for(var i in tags){ 
     if(tags[i].nodeType==1){
       if(tags[i].getAttribute("class") == classnames)
       { 
	     classobj[classint]=tags[i]; 
         classint++; 
	   } //if
     } //if
    } 
   return classobj;
} 


function GetTableRowsCount()
{
      var tab = document.getElementById("table_id") ;
      var rows = tab.rows.length ;
      return rows;
}




