// JavaScript Document
 $(function() {

    var dialog, form,

      // From http://www.whatwg.org/specs/web-apps/current-work/multipage/states-of-the-type-attribute.html#e-mail-state-%28type=email%29
      emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
	  
      name = $( "#name" ),

      email = $( "#email" ),

      password = $( "#password" ),

      allFields = $( [] ).add( name ).add( email ).add( password ),

      tips = $( ".validateTips" );

 

    function updateTips( t ) {

      tips

        .text( t )

        .addClass( "ui-state-highlight" );

      setTimeout(function() {

        tips.removeClass( "ui-state-highlight", 1500 );

      }, 500 );

    }

 

    function checkLength( o, n, min, max ) {

      if ( o.val().length > max || o.val().length < min ) {

        o.addClass( "ui-state-error" );

        updateTips( "Length of " + n + " must be between " +

          min + " and " + max + "." );

        return false;

      } else {

        return true;

      }

    }

 

    function checkRegexp( o, regexp, n ) {

      if ( !( regexp.test( o.val() ) ) ) {

        o.addClass( "ui-state-error" );

        updateTips( n );

        return false;

      } else {

        return true;

      }

    }


    function addUser() {
      var valid = true;
      allFields.removeClass( "ui-state-error" );
     
	  var rows =  GetTableRowsCount()-1;
	
      if( valid ){
        $( "#table_id tbody" ).append( "<tr>" +
          "<td class='checkbox_td_class'>"+"<input type='checkbox' class = 'checkbox_class' id='checkbox_all_id'+ "+rows+" name='checkbox_all'>"+"</td>" +
          "<td class='td_key_class'>" + email.val() + "</td>" +         
          "<td class='td_value_class'id = 'td_value_id_"+rows+"'>"+"<label id = 'label_id_"+rows+"' class='label_class' onclick='Label_Click("+rows+",&quot;"+password.val()+"&quot;)'>"+ password.val() +"</label>"+"</td>" 

+  "</tr>" );
           //"<td>"+"<label  onclick='show()'>"+ password.val() +"</label>"+"</td>" +
        dialog.dialog( "close" );
      }
      return valid;
    }

    dialog = $( "#dialog-form" ).dialog({
      autoOpen: false,
      height: 300,
      width: 350,
      modal: true,
      buttons: {

        "Add a row": addUser,
        Cancel: function() {
          dialog.dialog( "close" );
        }

      },
        close: function() {
        form[ 0 ].reset();
        allFields.removeClass( "ui-state-error" );
      }
    });
    form = dialog.find( "form" ).on( "submit", function( event ) {
      event.preventDefault();
      addUser();

    });

    $("#bnt_Confguration_add_id").button().on( "click", function() {
      dialog.dialog( "open" );
    });

  });