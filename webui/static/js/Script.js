// JavaScript Document
$(document).ready(function(){
	
   $(".div_tab_class").eq(0).show().siblings(".div_tab_class").hide()
   getXML("/configuration/get_group?request_type=cluster");
	
   setAjaxReturnToContainer($("#text_Status_id"),"/monitor/tail_console")

   //menu style(click  mouseover  mouseout)
   $("#div_menu_middle_id ul li").click(function(){
	    $("#div_menu_middle_id ul li").removeClass("tab_background_click");
		$(this).addClass("tab_background_click");
		//show and hide the sub div
		var index = $(this).index();
		$(".div_tab_class").eq(index).show().siblings(".div_tab_class").hide();		
	})
	.mouseover(function(){
	    $("#div_menu_middle_id ul li").removeClass("tab_background_mouseover");
		$(this).addClass("tab_background_mouseover");
		
	})
	.mouseout(function(){
		$("#div_menu_middle_id ul li").removeClass("tab_background_mouseover");
	});
	
	
	//sub menu (click  mouseover  mouseout)
	$("#div_Configuration_left_content_id ul li a").click(function(){
		//li font style change
		$("#div_Configuration_left_content_id ul li a").removeClass("SubMenu_li_a_click");
		$(this).addClass("SubMenu_li_a_click");
		//li image change
		//right content title change 
		 var title = $(this).text();
		$("#div_Configuration_right_top_titel_id").html(title); 
		
		//add table
                var request_type = $(this).attr('id')
		getXML("/configuration/get_group?request_type="+request_type);
		
	})
	.mouseover(function(){
		$("#div_Configuration_left_content_id ul li a").removeClass("SubMenu_li_a_mouseover");
		$(this).addClass("SubMenu_li_a_mouseover");
	})
	.mouseout(function(){
		$("#div_Configuration_left_content_id ul li a").removeClass("SubMenu_li_a_mouseover");
	});
});


$(function(){
	$("#table_id tr").addClass("altrow");
});


$(function(){
	$(".bnt_Confguration_tableOper_class").button();
});
