/*********************************
   JavaScript Document
   Author: Sean,Lin
   E-mail:  xiangx.lin@intel.com
   Date:2015-09-10
   Descrption: 
**********************************/

//Create Data Table for Configuration
function CreateDataTableForConfiguration(jsonObj_Config,jsonObj_benchmark,request_type){	
       
	   //(1) remove the elements    	
	   $("#div_Configuration_right_table_id").children("table").remove();
	   $("#div_Configuration_right_table_id").children("div").remove();
	   
	   //(2) get the configuration table html, and get the benchmark table html when the request_type is benchmark 
	   var tableHTML = CreateTableHtml_Configuation(jsonObj_Config);
	   //if this request_type is benchmark	   
	   if(request_type == "benchmark"){
		  tableHTML += CreateTableHTML_Benchmark(jsonObj_benchmark); 
	   }
	   
       //(3) add the table elemnet 
	   $("#div_Configuration_right_table_id").append($(tableHTML));
	   
	   //(4) set the tr's style	
	   $("table.table_class tr:nth-child(odd)").addClass("altrow");
							
	   //(5) traverse the json data ,if the check  value is "false" ,set the "error" style for this td;
	   $.each(jsonObj_Config,function(index,val){
	        if(val.check == "False"){
			  $("#td_value_id_"+index).addClass("error");
			}		 
	   });
	   
	   //(6) set button style by jquery ui
	   $(".bnt_Confguration_tableOper_class").button();
}

//create table html for configuation
function CreateTableHtml_Configuation(jsonObj){
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
		  
		  tableHtml += "<th>";
		  tableHtml += "Describe";
		  tableHtml += "</th>";
		  
		  tableHtml += "</th>"
	tableHtml += "</tr>";
	 
	//table row
    $.each(jsonObj,function(index,val){
	
		 tableHtml += "<tr id='tr_id_"+index+"'>";
	
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
		  
		  tableHtml += "<td class='td_Desc_class'>";
		  tableHtml += val.dsc;
		  tableHtml += "</td>";
		  
		tableHtml += "</tr>";
		
		return tableHtml;
	 });	
	 
	 
	tableHtml += "</tbody>";
	tableHtml += "</table>"
	return tableHtml;
}

//create table html from benchmark
function CreateTableHTML_Benchmark(jsonObj){

	var tableClass = "table_class";
	var tableID = "table_benchmark_id";
	var tableHtml;
	var cols;
	var rows;
	
	
	tableHtml=   "<div id='div_benchmark_button_id'>";             
    tableHtml +=   "<input id='bnt_benchmark_Submit_id' class='bnt_Confguration_tableOper_class' type='button' value='Submit'/>";
    tableHtml +=   "<input id='bnt_benchmark_delete_id' class='bnt_Confguration_tableOper_class' type='button' value='Delete' onclick='Del()'/>";
    tableHtml +=   "<input id='bnt_benchmark_add_id'    class='bnt_Confguration_tableOper_class' type='button' value='Add'/>";
    tableHtml +=  "</div>"

	tableHtml +=  "<table id='"+tableID+"' class='"+tableClass+"'>";
	tableHtml += "<tbody>";
	
	//table head
	tableHtml += "<tr>"; 
	      tableHtml += "<th class='checkbox_td_class'>";
		  tableHtml += "<input type='checkbox' class = 'checkbox_all_class' id= 'checkbox_all_benchmark_id' onclick= 'Check_ALL()' name='checkbox_all'>";
		  tableHtml += "</th>";
		 	  
		  tableHtml += "<th>";
		  tableHtml += "benchmark_engine";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "worker";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "container size";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "io pattern";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "block size";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "work depth";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "ramup time";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "run time";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "devcie";
		  tableHtml += "</th>";
		  
		  tableHtml += "</th>"
	tableHtml += "</tr>";
	
	//table row
	$.each(jsonObj,function(index,val){
		
		 tableHtml += "<tr id='tr_id_"+index+"'>";
	
		  tableHtml += "<td class='checkbox_td_class'>";
		  tableHtml += "<input type='checkbox' class = 'checkbox_class' id='checkbox_benchmark_'+ "+index+" name='checkbox'+"+index+">";
		  tableHtml += "</td>";
		  	  
		  tableHtml += "<td class='td_class'>";
		  tableHtml += val.benchmark_engine;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_class'>";
		  tableHtml += val.worker;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_class'>";
		  tableHtml += val.container_size;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_class'>";
		  tableHtml += val.io_pattern;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_class'>";
		  tableHtml += val.block_size;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_class'>";
		  tableHtml += val.object_size;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_class'>";
		  tableHtml += val.ramup_time;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_class'>";
		  tableHtml += val.run_time;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_class'>";
		  tableHtml += val.devcie;
		  tableHtml += "</td>";
			  
		tableHtml += "</tr>";
		
		return tableHtml;
	 });	
	 
	tableHtml += "</tbody>";
	tableHtml += "</table>"
	return tableHtml;
}



//label click opertion
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

//edit value apply
function Ok_Apply(rowNum){
	
	otd = document.getElementById("td_value_id_"+rowNum);
	otext = document.getElementById("text_id_"+rowNum);
	var valueStr =  otext.value;
	otd.innerHTML =" <label id = 'label_id_"+rowNum+"' class = 'label_class' onclick='Label_Click("+rowNum+", &quot;"+ valueStr+"&quot;)' >"+ valueStr +"</label>";
}

//edit value cancel
function Cancel_Apply(rowNum,value){
	otd = document.getElementById("td_value_id_"+rowNum);
	otext = document.getElementById("text_id_"+rowNum);	
	otd.innerHTML =" <label id='label_id_"+rowNum+"' class = 'label_class' onclick='Label_Click("+rowNum+", &quot;"+ value+"&quot;)' >"+ value +"</label>";
}

//delete row when checkbox is checked
function Del(){
	var oTable = document.getElementById("table_id");
	var delArray = getElementsClass("checkbox_class");
    for(var i=0;i< delArray.length;i++){ 
		if(delArray[i].checked == true){
			delArray[i].parentNode.parentNode.parentNode.removeChild(delArray[i].parentNode.parentNode);
		}	
	}
}

//checked all checkboxs
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

//get table row counts by table element id
function GetTableRowsCount(id)
{
      var tab = document.getElementById(id) ;
      var rows = tab.rows.length ;
      return rows;
}

//select elements for classname by js code
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






