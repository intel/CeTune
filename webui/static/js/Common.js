// JavaScript Document

function GetData(addressURL){
	var jsonStr="";
	$.ajax({
	   type:"GET",
	   url:addressURL,
	   dataType:"text",
	   async:false,
	   
	   success:function(ResponseText){
		  //alert(ResponseText);
		  //getAjaxResult(ResponseText);
		  jsonStr=ResponseText;
		  
	   } 
	});
	return jsonStr;
}

function CreateTable(jsonObj_Config , jsonObj_benchmark , request_type){
	 
	
	        $("#div_Configuration_right_table_id").children("table").remove();
			$("#div_Configuration_right_table_id").children("div").remove();
		    var tableHTML = GetTableHtml(jsonObj_Config);
		    //if this select is benchmark
			//var table2 = GetBenchmarkTable(jsonStr_benchmark);
			if(request_type == "benchmark"){
				tableHTML += GetBenchmarkTable(jsonObj_benchmark);
			}

			
			$("#div_Configuration_right_table_id").append($(tableHTML));	
			$("table.table_class tr:nth-child(odd)").addClass("altrow");
			
						
			$.each(jsonObj_Config,function(index,val){
				 if(val.check == "False"){
					$("#td_value_id_"+index).addClass("error");
				 }		 
			});
			$(".bnt_Confguration_tableOper_class").button();
}


function getXML(addressXML){
   $.ajax({
	   type:"GET",
	   url:addressXML,
	   dataType:"text",
	   
	   success:function(ResponseText)
	   {
		   $(ResponseText).find('member').each(function(){
		  	 var oMember="",sName="",sClass="",sBirth="",sConstell="",sMobile="";
	         sName = $(this).find("name").text();
	         sClass = $(this).find("class").text();			 
	       });	 		
		   
		    var jsonStr = [
			{"key":"volume_size","value":"40960","dsc":"This is a value","check":"True"},
			{"key":"rbd_volume_count","value":"80","dsc":"This is a value","check":"True"},
			{"key":"run_vm_num","value":"80","dsc":"This is a value","check":"True"},
			{"key":"run_warmup_time","value":"0","dsc":"This is a value","check":"True"},
			{"key":"run_record_size","value":"64k 4k","dsc":"This is a value","check":"True"},
			{"key":"run_io_pattern","value":"sequrite  seqread  randwrite  randread","dsc":"This is a value","check":"True"},
	        {"key":"funfile","value":"/dev/vdb","dsc":"This is a value","check":"True"},
			{"key":"fun_size","value":"40g","dsc":"This is a value","check":"True"},
	        {"key":"run_time","value":"400","dsc":"This is a value","check":"True"},
			{"key":"dest_dir","value":"/mnt/data/","dsc":"This is a value","check":"False"},
	        {"key":"run_vm_num","value":"80","dsc":"This is a value","check":"True"},
			{"key":"dest_dir_remote_bak","value":"192.168.101:/data4/Chendi/performance/raw/","dsc":"This is a value","check":"True"},
	        {"key":"rdb_num_per_client","value":"40  40","dsc":"This is a value","check":"True"}
			];
			
			
			
			var jsonStr_benchmark = [
			 {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"},
			  
			   {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"},
			  
			   {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"},
			  
			   {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"},
			  
			   {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"},
			  
			   {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"},
			  
			   {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"},
			  
			   {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"},
			  
			   {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"},
			  
			   {"benchmark_engine":"qemurbd","worker":"140","container_size":"40g",
			  "io_pattern":"seqwrite","block_size":"64k","object_size":"64","ramup_time":"0","run_time":"400","devcie":"/dev/vdb"}
						
			];
			
			
	
		    $("#div_Configuration_right_table_id").children("table").remove();
			$("#div_Configuration_right_table_id").children("div").remove();
		    var tableHTML = GetTableHtml(jsonStr);
		    //if this select is benchmark
			//var table2 = GetBenchmarkTable(jsonStr_benchmark);
			//alert(table2);
			tableHTML += GetBenchmarkTable(jsonStr_benchmark);

			$("#div_Configuration_right_table_id").append($(tableHTML));	
			$("table.table_class tr:nth-child(odd)").addClass("altrow");
			
						
			$.each(jsonStr,function(index,val){
				 if(val.check == "False"){
					$("#td_value_id_"+index).addClass("error");
				 }		 
			});
			$(".bnt_Confguration_tableOper_class").button();
			
			
	   }
   });//ajax  
};


function GetTableHtml(jsonObj){
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
		  tableHtml += "Describe";
		  tableHtml += "</th>";
		  
		  tableHtml += "<th>";
		  tableHtml += "Value";
		  tableHtml += "</th>";
		  
		  tableHtml += "</th>"
	tableHtml += "</tr>";
	 
	 
	 $.each(jsonObj,function(index,val){
	
		 tableHtml += "<tr id='tr_id_"+index+"'>";
	
		  tableHtml += "<td class='checkbox_td_class'>";
		  tableHtml += "<input type='checkbox' class = 'checkbox_class' id='checkbox_'+ "+index+" name='checkbox'+"+index+">";
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_key_class'>";
		  tableHtml += val.key;
		  tableHtml += "</td>";
		  
		  tableHtml += "<td class='td_Desc_class'>";
		  tableHtml += val.dsc;
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

function CheckValue(key,value,desc){
	var jsonStr=[{"key":"volume_size","value":"40960","Desc":"This is a value"}];
	 $.ajax({
	   type:"GET",
	   url:addressXML,
	   data:jsonStr,
	   dataType:"xml",
	   success:function(ResponseText) 
	   {
		   //
	   }
	  });
}



function GetBenchmarkTable(jsonObj){

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

