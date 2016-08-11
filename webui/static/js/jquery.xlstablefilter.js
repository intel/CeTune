/************************************************************************
@Name    :      xlsTableFilter - jQuery Plugin
@Type		:		 jQuery UI
@Revison :      1.0.1
@Date    :      08/30/2013
@Author  :      JKELLEY - (www.myjqueryplugins.com - www.alpixel.fr)
@License :      Open Source - MIT License : http://www.opensource.org/licenses/mit-license.php
*************************************************************************/
/**
 * 
 * @description Create an excel style filter dialog on a table containing headers
 * 
 * @example $('table').xlsTableFilter();
 * @desc Create a simple xlsTableFilter interface.
 * 
 * @example $('table').xlsTableFilter({ ignoreColumns: [0, 3, 5] });
 * @desc Create an xlsTableFilter interface and but do not make the first, fourth, and sixth column headers filterable.
 * 
 * @example $('table').tablesorter({ checkStyle: "custom", rowsDisplay: "filterDisplay" });     
 * @desc Create an xlsTableFilter interface and use custom checkboxes defined in the xlsTableFilter css style sheet.  Print 
 *   		the number of rows displayed in an html element with the id "filterDisplay".
 * 
 * 
 * @param Object
 *            settings An object literal containing key/value pairs to provide
 *            optional settings.
 * 
 * 
 * @option Integer width (optional) An integer setting the width of the filter dialog. Default: 400.
 *
 * @option Integer height (optional) An integer setting the height of the filter dialog. Default: 550.
 *
 * @option Integer maxHeight (optional) An integer setting the maximum height of the filter dialog. Default: window height.
 *
 * @option Boolean ignoreCase (optional) A boolean setting whether the filter should ignore case. Default: true.
 *
 * @option String checkStyle (optional) A string defining whether the dialog should use html checkboxes or
 *				custom on/off images. "default" will use html checkboxes.  "custom" will use images.  Default: default.
 *
 * @option Array ignoreColumns (optional) An array containing zero-based column indexes that will not have filters 
 *				assigned. Default: empty.
 *
 * @option Array onlyColumns (optional) An array containing zero-based column indexes that will always have filters 
 *				assigned.  Overrides ignoreColumns. If set, then only columns in this array will be assigned filters. Default: null.
 *
 * @option String or Object rowsDisplay (optional) An element to print the number of rows displayed in.  If a string is
 *				specified, the element with that id will be used. Default: "xlsTableFilterRowsDisplay".
 *
 *
**/
 
/** xlsTableFilter Plugin **/
;(function($) {
	$.widget("ui.xlsTableFilter", {
		
		/**************
      * OPTIONS
      **************/
		options: {
			width: 400,
			height: 550,
			maxHeight: $(window).height(),
			ignoreCase: true,
			checkStyle: "default",
			ignoreColumns: [],
			onlyColumns: null,
			rowsDisplay: "xlsTableFilterRowsDisplay",
		},
		
		/* object stores current filter settings */
		filters: {},
		
		/* id of the element the plugin was called on */
		elid: null,

		/*****************
      * Constructor Method
      *****************/
		_create: function() {
			/* vars **/
			var self = this,
			el = self.element,
			headers = $(el).find("th");
			
			/* Set up the filters storage for this element */
			self.elid = el.prop("id");
			self.filters[self.elid] = {};
			
			/* Add filter method to table headers */
			$.each(headers, function(i, h) {
				var filterable = ((self.options.onlyColumns == null && jQuery.inArray(i, self.options.ignoreColumns) == -1) || jQuery.inArray(i, self.options.onlyColumns) !== -1 ? true : false);
				if (filterable == true) {
					$(this).addClass("xlsFilterHeader").click(function(e) {
						self._openFilter($(this));
					});
				}
				else {
					$(this).addClass("xlsNoFilterHeader");	
				}
			});
			self._printRowsDisplayed();
		},
		
		/****************************
		* xlsTableFilter Methods Below
		****************************/

		/* Open the Filter Dialog */
		_openFilter: function(header) {
			var self = this;
			var colNum = (header.index() + 1);
			var filterContent = this._getFilterContent(header);
			var filterDiv = this._createDialogDiv("divXlsFilter", "Filter - " + header.text(), filterContent);
			this._setupFilter();
			
			$(filterDiv).dialog({
        		resizable: false,
        		autoOpen: true,
        		width: self.options.width,
        		height: self.options.height,
        		maxHeight: self.options.maxHeight,
        		modal: true,
        		show: 400,
        		hide: 400,
        		buttons: {
        			"Filter": function () {
        				self._filterTable(colNum);
						$(this).dialog("close");
					},
					"Cancel": function () {
						$(this).dialog("close");
						return false;
					}
        		},
       		close: function() {
					$( this ).dialog( "destroy" );
					$(this).remove();
				}
   		});
		},
		
		/* Build the html content of the filter dialog */
		_getFilterContent: function(header) {
			var self = this;
			var colNum = (header.index() + 1);
			var vals = new Array;

			$.each($(self.element).find("tr td:nth-of-type(" + colNum + ")"), function(i, el) {
				vals[vals.length] = $(el).text();
			});
			vals = this.sortUnique(vals);
			
			var filter = '<form id="xlsFilterForm">';
			filter = filter + '<div>Text Search <input type="text" id="filterSearch" style="width: 200px;"></div>';
			filter = filter + '<div id="xlsFilterAllNone"><span id="xlsFilterAll">All</span> | <span id="xlsFilterNone">None</span></div>';
			filter = filter + '<div id="xlsFilterRows">';
			
			$.each(vals, function (i, val) {
				filter = filter + self._addFilterRow(val, colNum);
			});
			filter = filter + '</div></form>';
			return filter;
		},
		
		/* Add the select and search methods to the filter dialog */
		_setupFilter: function() {
			var self = this;
			
			$("#xlsFilterAll").click(function() {
				$.each($("div.xlsFilterRow"), function() {
					self.checkRow($(this), true);
				});
			});
			
			$("#xlsFilterNone").click(function() {
				$.each($("div.xlsFilterRow"), function() {
					self.checkRow($(this), false);
				});
			});
			
			$("div.xlsFilterRow input").on('click', function (e) {
				e.stopPropagation();
			});
			$("div.xlsFilterRow").click(function() {
				self.checkRow($(this));
			});
			
			$("#filterSearch").blur(self._filterBySearchField);
			$("#filterSearch").focus(self._filterBySearchField);
			$("#filterSearch").keyup(self._filterBySearchField);
		},
		
		/* Add a checkbox value row to the filter dialog */
		_addFilterRow: function(val, colNum) {
			var text = (val.length == 0 ? "<i>&lt;blank&gt;</i>" : val);
			val = this._adjustCase(val);

			if (this.filters[this.elid]["col" + colNum]) {
				var checked = (jQuery.inArray(val, this.filters[this.elid]["col" + colNum]) == -1 ? false : true);
			}
			else {
				var checked = true;	
			}

			var row = '<div class="xlsFilterRow"><input type="checkbox" style="' + (this.options.checkStyle == "default" ? "" : "display: none;") + '" value="' + val + '" ' + (checked == true ? 'checked ' : '') + 'name="selFilter[]">' + (this.options.checkStyle == "default" ? '' : '<div class="xlsFilterCheck xlsFilterCheckO' + (checked == true ? 'n' : 'ff') + '"></div>') + '<span>' + text + '</span></div>';
			return row;
		},
		
		/* Check or uncheck  a value row in the filter dialog */
		checkRow: function(row, check) {
			var checkbox = $(row).find("input");
			check = (arguments.length == 2 ? check : (checkbox.prop("checked") == true ? false : true));
			checkbox.prop("checked", check);
			if (this.options.checkStyle == "custom") {
				var checkdiv = row.find(".xlsFilterCheck");
				checkdiv.addClass(check == true ? "xlsFilterCheckOn" : "xlsFilterCheckOff");
				checkdiv.removeClass(check == true ? "xlsFilterCheckOff" : "xlsFilterCheckOn");
			}
		},
		
		/* Search for matching value row in the filter dialog */
		_filterBySearchField: function() {
			if ($("#filterSearch").val().length == 0) {
				$("div.xlsFilterRow").show();	
			}
			else {
				$.each($("div.xlsFilterRow input"), function() {
					if ($(this).val().toLowerCase().indexOf($("#filterSearch").val().toLowerCase()) === -1) {
						$(this).parent().hide();	
					}
					else {
						$(this).parent().show();
					}
				});
			}
		},
		
		/* Create the filter dialog div */
		_createDialogDiv: function(divid, title, contents) {
			if ($("#" + divid).length > 0) {
				$("#" + divid).html(contents).attr("title", title);
			}
			else {
				$("body").append('<div id="' + divid + '" title="' + title + '" style="display: none;">' + contents + "</div>");
			}
			return $("#" + divid);
		},	
		
		/* Filter the table based on the selected settings */
		_filterTable: function(colNum) {
			var self = this;
			
			var filterRow = "col" + colNum
			self.filters[self.elid][filterRow] = new Array;
			$.each($("div.xlsFilterRow input:checked"), function() {
				self.filters[self.elid][filterRow][self.filters[self.elid][filterRow].length] = $(this).val();
			});
			
			if ($("div.xlsFilterRow input").not(":checked").length === 0) {
				self.element.find("tbody th:nth-of-type(" + colNum + ")").removeClass("xlsFilteredColumn");
			}
			else {
				self.element.find("tbody th:nth-of-type(" + colNum + ")").addClass("xlsFilteredColumn");
			}
			
			$.each(self.element.find("tbody tr"), function() {
				var $row = $(this);
				var visible = true;
				$row.show();
				
				$.each(self.filters[self.elid], function(key, val) {
					var i = key.substr(3);
                    //alert(i);
					if (visible == true) {
                        var value = $row.children("th:nth-of-type(" + i + ")").text();
                        if (value == ""){
                            if (jQuery.inArray(self._adjustCase($row.children("td:nth-of-type(" + i + ")").text()), val) == -1) {
                                $row.hide();
                                return false;
                            }
                        }
					}
				});
			});
			self._printRowsDisplayed();
		},
		
		_printRowsDisplayed: function() {
			if (this.options.rowsDisplay !== false) {
				var VisibleCount = this.element.find("tbody tr:visible").length;
				var TotalRows = this.element.find("tbody tr").length;
				var rowDisplay = (typeof(this.options.rowsDisplay) == "object" ? this.options.rowsDisplay : $("#" + this.options.rowsDisplay));
				rowDisplay.html('Displaying ' + VisibleCount + (VisibleCount != TotalRows ? ' of ' + TotalRows + ' row' + (TotalRows == 1 ? '' : 's') : ' row' + (VisibleCount == 1 ? '' : 's')) + '.');	
			}
		},
		
		/* Adjust the case of a string based on the ignoreCase option */
		_adjustCase: function(val) {
            //var a = this.options.ignoreCase == true ? val.toLowerCase() : val;
            //alert(val.toLowerCase());
            //alert(this.options.ignoreCase);
            if(this.options.ignoreCase == "Description"){
                alert(this.options.ignoreCase);
            }
			return (this.options.ignoreCase == true ? val.toLowerCase() : val);
		},
		
		/* Sort through column values for unique strings */
		sortUnique: function(arr) {
			var self = this;
			arr.sort(function(a, b){
				a = self._adjustCase(a);
				b = self._adjustCase(b);	
				if (a == b) return 0;
				return a > b ? 1 : -1;
			});
			
			var ret = [arr[0]];
			for (var i = 1; i < arr.length; i++) { // start loop at 1 as element 0 can never be a duplicate
				if (self._adjustCase(arr[i-1]) !== self._adjustCase(arr[i])) {
					ret.push(arr[i]);
				}
			}
			return ret;
		},
		
		/* Set an xlsTableFilter option */
		_setOption: function( key, value ) {
			options.key = value;
		},

	});
})(jQuery);
