/*********************************
   JavaScript Document
   Author: Sean,Lin
   E-mail:  xiangx.lin@intel.com
   Date:2015-09-10
   Descrption: 
**********************************/

$(function(){
	
 var allPanelGroupBodies = $('#dl_Configuration_left_nav_accordion_id > dd > div > ul');
 
  
  $('#dl_Configuration_left_nav_accordion_id > dd > div > ul').each(function(index, value){
    var activePanels = $(this).find('li > a.active');
    if(activePanels.length === 0) {
      $(this).slideUp(0);
    }
  });
  
  var myPanelGroupHeader = $(this);
	   myPanelGroupHeader.addClass("active");   
  
  
  // mark the active panel group
  var activePanel = $('#dl_Configuration_left_nav_accordion_id > dd > div > ul > li > a.active');
  
  activePanel.closest('div').find('h4').addClass('active');
  
 
  //$("#dl_Configuration_left_nav_accordion_id > dd > div > ul").eq(0).addClass('active');
   $(".div_Configuration_left_nav_li_class > a").eq(0).addClass('active');
  $("#dl_Configuration_left_nav_accordion_id > dd > div > ul").eq(0).slideDown(0);
 
  // dashboard click
  $('#dl_Configuration_left_nav_accordion_id > dt').click(function() {
   
    var myDashHeader = $(this);
    var myDashWasActive = myDashHeader.hasClass("active");

    // mark the active dashboard
    var allDashboardHeaders = $('#dl_Configuration_left_nav_accordion_id > dt');
    allDashboardHeaders.removeClass("active");

    // collapse all dashboard contents
    var allDashboardBodies = $('#dl_Configuration_left_nav_accordion_id > dd');
    allDashboardBodies.slideUp();

    // if the current dashboard was active, leave it collapsed
    if(!myDashWasActive) {
      myDashHeader.addClass("active");

      // expand the active dashboard body
      var myDashBody = myDashHeader.next();
      myDashBody.slideDown();

      var activeDashPanel = myDashBody.find("div > ul > li > a.active");
      // if the active panel is not in the expanded dashboard
      if (activeDashPanel.length === 0) {
        // expand the active panel group
        var activePanel = myDashBody.find("div:first > ul");
        activePanel.slideDown();
        activePanel.closest('div').find("h4").addClass("active");

        // collapse the inactive panel groups
        var nonActivePanels = myDashBody.find("div:not(:first) > ul");
        nonActivePanels.slideUp();
      }
      // the expanded dashboard contains the active panel
      else
      {
        // collapse the inactive panel groups
        activeDashPanel.closest('div').find("h4").addClass("active");
        allPanelGroupBodies.each(function(index, value) {
          var activePanels = $(value).find('li > a.active');
          if(activePanels.length === 0) {
            $(this).slideUp();
          }
        });
      }
    }
    return false;
  });

  // panel group click
  $('#dl_Configuration_left_nav_accordion_id > dd > div > h4').click(function() {
    var myPanelGroupHeader = $(this);
    myPanelGroupWasActive = myPanelGroupHeader.hasClass("active");

    // collapse all panel groups
    var allPanelGroupHeaders = $('#dl_Configuration_left_nav_accordion_id > dd > div > h4');
    allPanelGroupHeaders.removeClass("active");
    allPanelGroupBodies.slideUp();

    // expand the selected panel group if not already active
    if(!myPanelGroupWasActive) {
      myPanelGroupHeader.addClass("active");
      myPanelGroupHeader.closest('div').find('ul').slideDown();
    }
  });



   //panel selection
  $('#dl_Configuration_left_nav_accordion_id > dd > ul > li > a').click(function() {
      horizon.modals.modal_spinner(gettext("Loading"));
  });

  $('.div_Configuration_left_nav_li_class > a').click(function() {
      //horizon.modals.modal_spinner(gettext("Loading"));
	  var allPanelGroupHeaders = $('.div_Configuration_left_nav_li_class > a');
      allPanelGroupHeaders.removeClass("active");
	  
	   var myPanelGroupHeader = $(this);
	   myPanelGroupHeader.addClass("active");   
  });
  
  

  
});