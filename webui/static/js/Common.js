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
        if(val.check == false){
            $("#td_value_id_"+index).addClass("error");
        } 
    });
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
    tableHtml += "<input type='checkbox' class = 'checkbox_all_configuration_class' id= 'checkbox_all_configuration_id' onclick= 'Check_ALL(&quot;configuration&quot;)' name='checkbox_all'>";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "Key";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "Value";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "Description";
    tableHtml += "</th>";

    tableHtml += "</th>"
    tableHtml += "</tr>";

    //table row
    $.each(jsonObj,function(index,val){

        tableHtml += "<tr id='tr_id_"+index+"'>";

        tableHtml += "<td class='checkbox_td_class'>";
        tableHtml += "<input type='checkbox' class = 'checkbox_configuration_class' id='checkbox_configuration_'+ "+index+" name='checkbox'+"+index+">";
        tableHtml += "</td>";

        tableHtml += "<td class='td_key_class'>";
        tableHtml += "<label>"
        tableHtml +=  val.key;
        tableHtml += "</label>"
        tableHtml += "</td>";

        if(val.check == false)
            tableHtml += "<td class='td_value_class error' id='td_value_id_"+index+"'>";
        else
            tableHtml += "<td class='td_value_class' id='td_value_id_"+index+"'>";
        tableHtml += "<label id='label_id_"+index+"'  class = 'label_class' onclick = 'Label_Click("+index+" ,&quot;"+ val.value+"&quot;)'>" + val.value;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_Desc_class'>";
        tableHtml += "<label>"
        tableHtml += val.dsc;
        tableHtml += "</label>"
        tableHtml += "</td>";

        tableHtml += "</tr>";

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


    tableHtml="<div id='div_benchmark_button_id'>";
    tableHtml +="<button id='bnt_benchmark_delete_id' type='button' class='btn btn-primary' data-toggle='modal'  data-target='#DeleteBenchmarkModal' data-whatever='@mdo' >Delete</button>";
    tableHtml +="<button id='bnt_benchmark_add_id' type='button' class='btn btn-primary' data-toggle='modal'  data-target='#BenchmarkModel' data-whatever='@mdo' >Add</button>";
    tableHtml +=  "</div>"

    tableHtml +=  "<table id='"+tableID+"' class='"+tableClass+"'>";
    tableHtml += "<tbody>";

//table head
    tableHtml += "<tr>"; 
    tableHtml += "<th class='checkbox_td_class'>";
    tableHtml += "<input type='checkbox' class = 'checkbox_all_benchmark_class' id= 'checkbox_all_benchmark_id' onclick= 'Check_ALL(&quot;benchmark&quot;)' name='checkbox_all'>";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "benchmark_driver";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "worker";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "container_size";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "iopattern";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "opsize";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "object_size/QD";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "rampup";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "runtime";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "device";
    tableHtml += "</th>";

    tableHtml += "<th>";
    tableHtml += "Description";
    tableHtml += "</th>";

    tableHtml += "</th>"
    tableHtml += "</tr>";

    //table row
    $.each(jsonObj,function(index,val){
        tableHtml += "<tr id='tr_benchmark_id_"+index+"'>";

        tableHtml += "<td class='checkbox_td_class'>";
        tableHtml += "<input type='checkbox' class = 'checkbox_benchmark_class' id='checkbox_benchmark_'+ "+index+" name='checkbox'+"+index+">";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class'  id='td_benchmark_id_"+index+"_1'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_1'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+" ,1,&quot;"+ val.benchmark_driver+"&quot;)'>" + val.benchmark_driver;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class' id='td_benchmark_id_"+index+"_2'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_2'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+" ,2,&quot;"+ val.worker+"&quot;)'>" + val.worker;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class' id='td_benchmark_id_"+index+"_3'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_3'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+", 3,&quot;"+ val.container_size+"&quot;)'>" + val.container_size;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class' id='td_benchmark_id_"+index+"_4'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_4'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+",4 ,&quot;"+ val.iopattern+"&quot;)'>" + val.iopattern;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class' id='td_benchmark_id_"+index+"_5'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_5'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+" ,5,&quot;"+ val.op_size+"&quot;)'>" + val.op_size;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class' id='td_benchmark_id_"+index+"_6'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_6'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+",6 ,&quot;"+ val["object_size/QD"]+"&quot;)'>" + val["object_size/QD"];
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class' id='td_benchmark_id_"+index+"_7'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_7'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+",7 ,&quot;"+ val.rampup+"&quot;)'>" + val.rampup;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class' id='td_benchmark_id_"+index+"_8'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_8'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+" ,8,&quot;"+ val.runtime+"&quot;)'>" + val.runtime;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class' id='td_benchmark_id_"+index+"_9'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_9'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+" ,9,&quot;"+ val.device+"&quot;)'>" + val.device;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "<td class='td_class' id='td_benchmark_id_"+index+"_10'>";
        tableHtml += "<label id='label_benchmark_id_"+index+"_10'  class = 'label_class' onclick = 'Label_benchmark_Click("+index+" ,10,&quot;"+ val.description+"&quot;)'>" + val.description;
        tableHtml +=  "</label>";
        tableHtml += "</td>";

        tableHtml += "</tr>";

    });

    tableHtml += "</tbody>";
    tableHtml += "</table>"
    return tableHtml;
}

//------------------------------  Events Definition ----------------------------
//label click opertion
function Label_Click(count,value){
    var rowNum = count;
    olabel = document.getElementById("label_id_"+rowNum);
    olabel.style.backgroundColor = "#cff";

    otd = document.getElementById("td_value_id_"+rowNum);
    otd.removeChild(olabel);

    var strHtml =  "<input class='text_class' id = 'text_id_"+rowNum+"' value = '"+value+"' type='text' name='fname'/>";
    strHtml += "<input class='btn btn-primary btn-xs' style='margin-left:3px' id = 'bnt_ok_id_"+rowNum+"' type='button' value='OK' onclick= 'Ok_Apply("+rowNum+")' />";
    strHtml += "<input class='btn btn-primary btn-xs' style='margin-left:3px'  id = 'bnt_cancel_id_"+rowNum+"' type='button' value='Cancel' onclick= 'Cancel_Apply("+rowNum+",&quot;"+value+"&quot;)'/>";

    otd.innerHTML =strHtml;
}

//edit value apply
function Ok_Apply(rowNum){
    otd = document.getElementById("td_value_id_"+rowNum);
    otext = document.getElementById("text_id_"+rowNum);
    var valueStr =  otext.value;
    otd.innerHTML =" <label id = 'label_id_"+rowNum+"' class = 'label_class' onclick='Label_Click("+rowNum+", &quot;"+ valueStr+"&quot;)' >"+ valueStr +"</label>";

  //--------set to ajax----------
    var request_type,key,value;//set_config?request_type= &key= &value= 
    request_type= $("#div_Configuration_right_top_titel_id").attr("title");
    key = $("#td_value_id_"+rowNum).parent().children().eq(1).children("label").text();
    value = $("#td_value_id_"+rowNum).parent().children().eq(2).children("label").text();

    var data ={};
    data.request_type= request_type;
    data.key = key;
    data.value = value;

    //need lode style
    var result = GetDataByAjax_POST(address_Configuration_Set,data);

    //if result check is false , add error sytle
    if(result.check == false){
        $("#td_value_id_"+rowNum).addClass("error");
        $("#td_value_id_"+rowNum).parent().children().eq(3).children("label").text(result.dsc);
    }else{
        $("#td_value_id_"+rowNum).removeClass("error");
        $("#td_value_id_"+rowNum).parent().children().eq(3).children("label").text("");
    }
    if(result.addition!=undefined){
        $.each(result.addition, function(index, value){
            Append_Row_to_Configuration(value)
        });
    }
	
	CheckTableDataError();
	ExecutvieCheckSync();
}

//edit value cancel
function Cancel_Apply(rowNum,value){
    otd = document.getElementById("td_value_id_"+rowNum);
    otext = document.getElementById("text_id_"+rowNum);
    otd.innerHTML =" <label id='label_id_"+rowNum+"' class = 'label_class' onclick='Label_Click("+rowNum+",&quot;"+ value+"&quot;)' >"+ value +"</label>";
}
//------------------------------------------------------------------------------------------------------
//label click opertion
function Label_benchmark_Click(rowNum , colNum , value){
    olabel = document.getElementById("label_benchmark_id_" + rowNum + "_" + colNum);
    olabel.style.backgroundColor = "#cff";
    otd = document.getElementById("td_benchmark_id_" + rowNum + "_" + colNum);
    otd.removeChild(olabel);
    var strHtml =  "<input class='text_class' id = 'text_benchmark_id_"+rowNum+"_"+ colNum +"' value = '"+value+"' type='text' name='fname'/>";
    strHtml += "<input class='btn btn-primary btn-xs' id='bnt_benchmark_ok_id_"+rowNum+"_"+colNum+"' type='button' value='OK' onclick= 'Ok_benchmark_Apply("+rowNum+","+ colNum+")' />";
    strHtml += "<input class='btn btn-primary btn-xs' id='bnt_benchmark_cancel_id_"+rowNum+"_"+colNum+"' type='button' value='Cancel' onclick= 'Cancel_benchmark_Apply("+rowNum+","+colNum+",&quot;"+value+"&quot;)'/>";
    otd.innerHTML =strHtml;
}

//edit value apply
function Ok_benchmark_Apply(rowNum , colNum ){
    otd = document.getElementById("td_benchmark_id_"+rowNum + "_" + colNum);
    otext = document.getElementById("text_benchmark_id_"+rowNum + "_" + colNum);
    var valueStr =  otext.value;
    otd.innerHTML =" <label id = 'label_benchmark_id_"+rowNum+"_" + colNum + "' class = 'label_class' onclick='Label_benchmark_Click("+rowNum+","+ colNum+", &quot;"+ valueStr+"&quot;)' >"+ valueStr +"</label>";
	Submit_Benchmark();
	CheckTableDataError();

}

//edit value cancel
function Cancel_benchmark_Apply(rowNum , colNum ,value){
    otd = document.getElementById("td_benchmark_id_"+rowNum+ "_" + colNum);
    otext = document.getElementById("text_benchmark_id_"+rowNum+ "_" + colNum);
    otd.innerHTML =" <label id='label_benchmark_id_"+rowNum+"_" + colNum +"' class = 'label_class' onclick='Label_benchmark_Click("+rowNum+", "+ colNum +" , &quot;"+ value+"&quot;)' >"+ value +"</label>";	
}

/********************************************************************************************************************************************************/
//delete row when checkbox is checked
function Del(tableType){
    if(tableType =="configuration"){
        $(".checkbox_configuration_class").each(function(index,value){
            if($(this).is(':checked')){
                var request_type, key ;//del_config?request_type=& key =     
                request_type = $("#div_Configuration_right_top_titel_id").attr("title");;
                key = $(this).parent().parent().children().eq(1).children("label").text();

                var data ={}; 
                data.request_type= request_type;
                data.key = key;

                var result = GetDataByAjax_POST(address_Delete,data);

                $(this).parent().parent().remove(); 
            }
        });
    }
//-------------------------
    else if(tableType =="benchmark"){
        $(".checkbox_benchmark_class").each(function(index,value){
            if($(this).is(':checked')){
                $(this).parent().parent().remove(); 
            }
        });
        Submit_Benchmark();
    }

}

//checked all checkboxs
function Check_ALL(tableType){
    var oCheck;
    var delArray;
    if(tableType =="configuration"){
        oCheck = document.getElementById("checkbox_all_configuration_id");
        delArray = getElementsClass("checkbox_configuration_class");
    }
    else if(tableType =="benchmark"){
        oCheck = document.getElementById("checkbox_all_benchmark_id");
        delArray = getElementsClass("checkbox_benchmark_class");
    }

    if(oCheck.checked == true){
        for(var i=0;i< delArray.length;i++){
            delArray[i].checked = true;
        }
    }else{
        for(var i=0;i< delArray.length;i++){
            delArray[i].checked = false;
        }
    }
}

//get table row counts by table element id
function GetTableRowsCount(id){
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
            if(tags[i].getAttribute("class") == classnames){
                classobj[classint]=tags[i];
                classint++;
            }//if
        }//if
    }
    return classobj;
}

function DeleteModal_OK(type){
  Del(type);
  setTimeout(function(){$("#DeleteModal").modal("hide")},100);
  setTimeout(function(){$("#DeleteBenchmarkModal").modal("hide")},100);
}

function ConfigurationModal_OK(key, value, dsc){
    key = $("#recipient-key").val();
    value = $("#recipient-value").val();
    dsc = "";
    if(key == "" || value ==""){
        $("#div_configuration_message_div").show();
    }else{
        //--------set to ajax----------
        var request_type,key,value;//set_config?request_type= &key= &value= 
        request_type= $("#div_Configuration_right_top_titel_id").attr("title");

        var data ={}; 
        data.request_type= request_type;
        data.key = key;
        data.value = value;

        var result = GetDataByAjax_POST(address_Configuration_Set,data);
		$("#div_configuration_message_div").hide();
        setTimeout(function(){$("#ConfigurationModal").modal("hide")},100);
        Append_Row_to_Configuration( result );
    }
}

function Append_Row_to_Configuration(params){
    var rows =  GetTableRowsCount("table_id")-1;
    key = params.key
    value = params.value
    dsc = params.dsc
    check = params.check
    var html = "<tr>";

    html +="<td class='checkbox_td_class'>";
    html +="<input type='checkbox' class = 'checkbox_configuration_class' id='checkbox_configuration_id'+ "+rows+" name='checkbox'>";
    html +="</td>";
    
    html += "<td class='td_key_class'>";
    html += "<label>"+key+"</label>";
    html += "</td>";
    
    html += "<td class='td_value_class' id='td_value_id_"+rows+"'>"
    html +="<label id = 'label_id_"+rows+"' class='label_class' onclick='Label_Click("+rows+",&quot;"+ value+"&quot;)'>"+ value +"</label>";
    html +="</td>";
    
    html += "<td class='td_value_class'id = 'td_dsc_id_"+rows+"'>";
    html += "<label>"+dsc+"</label>";
    html += "</td>";
    
    html += "<tr>";
    $("#table_id").append(html); 
    //if result check is false , add error sytle
    if(check == false){
        $("#td_value_id_"+rows).addClass("error");
    }

    $("table.table_class tr:nth-child(odd)").addClass("altrow");
}

function BenchMarkModel_OK(){

    var rows =  GetTableRowsCount("table_benchmark_id")-1;

    var benchmark_driver = $("#recipient-benchmark_engine").val();
    var worker = $("#recipient-worker").val();
    var container_size = $("#recipient-container_size").val();
    var iopattern = $("#recipient-io_pattern").val();
    var op_size = $("#recipient-block_size").val();
    var object_size = $("#recipient-work_depth").val();
    var rampup = $("#recipient-ramup_time").val();
    var runtime = $("#recipient-run_time").val();
    var desc = $("#recipient-desc").val();
    if(benchmark_driver == "qemurbd")
        device = "/dev/vdb"
    if(benchmark_driver == "fiorbd")
        device = "fiorbd"
    if(benchmark_driver == "cosbench")
        device = "cosbench"
    if(benchmark_driver == "generic")
        device = "generic"
    if(benchmark_driver == "hook")
        device = "hook"

    if(benchmark_driver == "" || worker== "" ||container_size  == "" || iopattern == "" || op_size == "" ||
        object_size == "" || rampup == "" || runtime == "" || device == "" ){
        $("#div_benchmark_message_div").show();
    }else{
        //$("#ModalLabel_Benchmark_Add").html("Add a new row for configuration");
        $("#div_configuration_message_div").hide();
        setTimeout(function(){$("#BenchmarkModel").modal("hide")},100);
        var html = "<tr>";

        html +="<td class='checkbox_td_class'>";
        html +="<input type='checkbox' class = 'checkbox_benchmark_class' id='checkbox_benchmark_id'+ "+rows+" name='checkbox'>";
        html +="</td>";

        var index = rows
        html += "<td class='td_value_class'  id='td_benchmark_id_"+index+"_1'>";
        html +="<label id = 'label_benchmark_id_"+rows+"_1' class='label_class' onclick='Label_benchmark_Click("+rows+",1,&quot;"+ benchmark_driver+"&quot;)'>"+ benchmark_driver +"</label>";
        html +="</td>";
        html += "<td class='td_value_class'  id='td_benchmark_id_"+index+"_2'>";
        html +="<label id = 'label_benchmark_id_"+rows+"_2' class='label_class' onclick='Label_benchmark_Click("+rows+",2,&quot;"+ worker+"&quot;)'>"+ worker +"</label>";
        html +="</td>";
        html += "<td class='td_value_class'  id='td_benchmark_id_"+index+"_3'>";
        html +="<label id = 'label_benchmark_id_"+rows+"_3' class='label_class' onclick='Label_benchmark_Click("+rows+",3,&quot;"+ container_size+"&quot;)'>"+ container_size +"</label>";
        html +="</td>";
        html += "<td class='td_value_class'  id='td_benchmark_id_"+index+"_4'>";
        html +="<label id = 'label_benchmark_id_"+rows+"_4' class='label_class' onclick='Label_Click("+rows+",4,&quot;"+ iopattern+"&quot;)'>"+ iopattern +"</label>";
        html +="</td>";
        html += "<td class='td_value_class' id='td_benchmark_id_"+index+"_5'>";
        html +="<label id = 'label_benchmark_id_"+rows+"_5' class='label_class' onclick='Label_benchmark_Click("+rows+",5,&quot;"+ op_size+"&quot;)'>"+ op_size +"</label>";
        html +="</td>";
        html += "<td class='td_value_class' id='td_benchmark_id_"+index+"_6'>";
        html +="<label id = 'label_id_"+rows+"_6' class='label_class' onclick='Label_benchmark_Click("+rows+",6,&quot;"+ object_size+"&quot;)'>"+ object_size +"</label>";
        html +="</td>";
        html += "<td class='td_value_class' id='td_benchmark_id_"+index+"_7'>";
        html +="<label id = 'label_benchmark_id_"+rows+"_7' class='label_class' onclick='Label_benchmark_Click("+rows+",7,&quot;"+ rampup+"&quot;)'>"+ rampup +"</label>";
        html +="</td>";
        html += "<td class='td_value_class' id='td_benchmark_id_"+index+"_8'>";
        html +="<label id = 'label_benchmark_id_"+rows+"_8' class='label_class' onclick='Label_benchmark_Click("+rows+",8,&quot;"+ runtime+"&quot;)'>"+ runtime +"</label>";
        html +="</td>";
        html += "<td class='td_value_class' id='td_benchmark_id_"+index+"_9'>";
        html +="<label id = 'label_benchmark_id_"+rows+"_9' class='label_class' onclick='Label_benchmark_Click("+rows+",9,&quot;"+ device+"&quot;)'>"+ device +"</label>";
        html +="</td>";
        html += "<td class='td_value_class' id='td_benchmark_id_"+index+"_10'>";
        html +="<label id = 'label_benchmark_id_"+rows+"_10' class='label_class' onclick='Label_benchmark_Click("+rows+",10,&quot;"+ desc+"&quot;)'>"+ desc +"</label>";
        html +="</td>";

        html += "<tr>";

        $("#table_benchmark_id").append(html); 
        Submit_Benchmark();
    }
}

function Submit_Benchmark(){
    var post_json = {}//set_config?request_type=testcase &key=testcase &value=  
    var table_data= [];

    var benchmark_driver,worker,container_size,io_pattern,block_size,work_depth,ramup_time,run_time,device,desc;

    $(".checkbox_benchmark_class").each(function(){
        benchmark_driver = $(this).parent().parent().children().eq(1).children("label").text();
        worker = $(this).parent().parent().children().eq(2).children("label").text();
        container_size = $(this).parent().parent().children().eq(3).children("label").text();
        iopattern = $(this).parent().parent().children().eq(4).children("label").text();
        op_size = $(this).parent().parent().children().eq(5).children("label").text();
        object_size = $(this).parent().parent().children().eq(6).children("label").text();
        rampup = $(this).parent().parent().children().eq(7).children("label").text();
        runtime = $(this).parent().parent().children().eq(8).children("label").text();
        device = $(this).parent().parent().children().eq(9).children("label").text();
        desc = $(this).parent().parent().children().eq(10).children("label").text();

        var data ={}; 
        data.benchmark_driver = benchmark_driver;
        data.worker = worker;
        data.container_size = container_size;
        data.iopattern = iopattern;
        data.op_size = op_size;
        data["object_size/QD"] = object_size;
        data.rampup = rampup;
        data.runtime = runtime;
        data.device = device;
        data.desc = desc;

        table_data.push(data);
    });

    post_json["request_type"]="testcase";
    post_json.value = JSON.stringify(table_data);
    post_json.key="testcase";
    var address_Configuration_Set="../configuration/set_config";
    var result = GetDataByAjax_POST(address_Configuration_Set,post_json); 
    //--------------------------------------------------------------------
    // check benchmark_driver type and load more benchmark configurations
    /*engine_type_list = [];
    $.each(table_data, function(index, value){
        if($.inArray( value.benchmark_driver, engine_type_list ) < 0 ){
            engine_type_list.push(value.benchmark_driver)
        }
    });
    post_json = {};
    post_json.engine_list = engine_type_list.join();
    */
    post_json = {};
    var result = GetDataByAjax_POST(address_BenchmarkEngine_Check, post_json);
    $.each(result, function(index, value){
        Append_Row_to_Configuration(value);
    });

    // set the tr's style
    $("table.table_class tr:nth-child(odd)").addClass("altrow");
}
