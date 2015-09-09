// JavaScript Document
$(document).ready(function(){
   $(".bnt_Confguration_tableOper_class").button();
    init();

   //menu style(click  mouseover  mouseout)
   $("#div_menu_id ul li").click(function(){
	    $("#div_menu_id ul li").removeClass("tab_background_click");
		$(this).addClass("tab_background_click");
		//show and hide the sub div
		var index = $(this).index();
		$(".div_tab_class").eq(index).show().siblings(".div_tab_class").hide();		
	})

	
	
	//sub menu (click)
	$("#dl_Configuration_left_nav_accordion_id ul li a").click(function(e){

	    
		var title = $(this).text();	
		$("#div_Configuration_right_top_titel_id").html(title); 	
		var id = $(e.target).attr('id');	
		GetTableDataAndInitTable(id);			
	});
	
	 $("#dl_Configuration_left_nav_accordion_id ul li a").each(function(index,value){
		 var id = this.id;
		 //处理数据
		 var jsonObj = GetConfiguationData(id);
		 var check = IsContentError(jsonObj);
		 
		 if(check == false){
			//将img中的图标改变	
			//$(this).next().attr("src","image/config_Wait.gif");
			$(this).children("img").attr("src","image/config_Wait.gif");
		 } 
     });
	
	//$("#table_id tr").addClass("altrow");
	//$("table.table_class tr:nth-child(odd)").addClass("altrow");	
	//$("#bnt_Confguration_exec_id")
	
});


//页面初始化
function init(){
	
	//指定tab
	$("#div_menu_id ul li").eq(0).addClass("tab_background_click");
    $(".div_tab_class").eq(0).show().siblings(".div_tab_class").hide();
		
	GetTableDataAndInitTable("workflow");	
	var title = $("#dl_Configuration_left_nav_accordion_id ul li").eq(0).children("a").text();
	$("#div_Configuration_right_top_titel_id").html(title);
	//alert(123);
	
}


function GetConfiguationData(request_type){
	
	var address_Config = "";
	
	switch(request_type)
	{
		//case "workflow": address_Config="workflow.txt";break;
		case "workflow": address_Config="../configuration/get_group?request_type=workflow";break;
		case "cluster": address_Config="../configuration/get_group?request_type=cluster";break;
		case "system": address_Config="../configuration/get_group?request_type=system";break;
		case "ceph": address_Config="../configuration/get_group?request_type=ceph";break;
		case "benchmark": address_Config="../configuration/get_group?request_type=benchmark";break;
		case "analyzer": address_Config="../configuration/get_group?request_type=analyzer";break;
	}	
	
	var strJSON_Config = GetData(address_Config);
	var jsonObj_Config = jQuery.parseJSON(strJSON_Config);
	return jsonObj_Config;
}



function GetTableDataAndInitTable(request_type){
	
	var address_Config = "";
	var address_Benchmark = "benchmarkTable.txt";
	
	switch(request_type)
	{
		//case "workflow": address_Config="workflow.txt";break;
		case "workflow": address_Config="../configuration/get_group?request_type=workflow";break;
		case "cluster": address_Config="../configuration/get_group?request_type=cluster";break;
		case "system": address_Config="../configuration/get_group?request_type=system";break;
		case "ceph": address_Config="../configuration/get_group?request_type=ceph";break;
		case "benchmark": address_Config="../configuration/get_group?request_type=benchmark";break;
		case "analyzer": address_Config="../configuration/get_group?request_type=analyzer";break;
	}	
	
	var strJSON_Config = GetData(address_Config);
	var strJSON_Benchmark = GetData(address_Benchmark);
	var jsonObj_Config = jQuery.parseJSON(strJSON_Config);
	var jsonObj_Benchmark =jQuery.parseJSON(strJSON_Benchmark);	
	CreateTable(jsonObj_Config , jsonObj_Benchmark ,request_type);
}


function IsContentError(jsonObj){
		
	var check = true;
	$.each(jsonObj,function(index,val){
	    if(val.check == "False"){
			check = false;
			return false;
		}		 
	});
	//alert(check);
	return check;
}

