// **** Accordion Resize: Function to detect height of sidebar and set for accordion
function resize() {
	$('.sidebar-offcanvas, #sidebar, #map-wrapper').each( function(){
		// set variables
		var totalHeadingHeight = 0;
		var panelHeading = $(this).find('.panel-heading');
		var panelGroup = $(this).find('.panel-group');
		var panelContent = $(this).find('.panel-content');

		// loop through each panel heading, get the height, and total them
		$(panelHeading).each( function() {
			var thisHeadingHeight = $(this).outerHeight()
			totalHeadingHeight += thisHeadingHeight;
		});

		// add panel heading height, add height of navbar, add 1 for each panel with a border-bottom (top panel has no border)
		var offset = totalHeadingHeight + $('.navbar ').outerHeight() + ($(panelHeading).length - 1);
		// establish panel height for all panels by measuring sidebar then subtracting panel height total
		var panelHeight = $(panelGroup).outerHeight() - offset;
		// set height of panel
		$(panelContent).height(panelHeight);
	});
	
	// establish map height by measuring map wrapper and subtracting navbar height
	var mapHeight = $('#map-wrapper').innerHeight() - $('.navbar ').outerHeight();
	// set height of map
	$('#map').height(mapHeight);
	
}

// Creates function for alert faders
function createAutoClosingAlert(selector, delay) {
   var alert = $(selector).alert().show();
   window.setTimeout(function() { alert.fadeOut() }, delay);
}	
// jQuery functions available when the document is ready
$(document).ready(function() {

	// fires accordion and map resize function if window resizes 
	$(window).resize(function() { resize(); });
	// fire accordion and map resize if nav toggle is activated
	if ($('.visible-xs').is(':visible')) { resize(); }
	
	// forces accordion to always have one pane open by disabling default behaviour on click
	$('.panel-heading a').on('click',function(e){
		if($(this).parents('.panel').children('.panel-collapse').hasClass('in')){ return false; }
		$('.in').collapse('hide');
	}); 
	

	

 
	// Fire preference change fader 
	$('.pref-radio').click(function(e){
		saveUserPrefs();
		createAutoClosingAlert("#alert-pref-change", 2000);
	 });
	// creates toggle function for menu
	$('[data-toggle=offcanvas]').click(function() {
		$('.row-offcanvas').toggleClass('active');
	});
	
	// Two functions happen in sequence when user clicks "Add new area"...
	// ...fires drawing instruction modal on click...
	 $('#edit-dialog-open').click(function(){
		$('#draw-modal').modal();
		resize();

	 });
	// ...when the accept button is clicked, open drawer and start drawing function
	$('#draw-modal .btn-primary').on('click', function() {
		fadeCurrentMapGraphic();
		measurer.startMeasure();
		$('#edit-dialog').addClass('in');
	});
	
	$('#view-on-map').on('click', function() {
		$('#map-wrapper').addClass('in');
		map.reposition();
		map.resize();
		resize();
	});
	$('#close-map, #drawing-cancel').on('click', function() {
		$('#map-wrapper').removeClass('in');
	});
	
	if ($('.visible-xs').is(':visible')) { 
		$('#edit-dialog-redraw,#edit-dialog-open').click(function(){
			$('#map-wrapper').addClass('in');
			map.reposition();
			map.resize();
			fadeCurrentMapGraphic();
			measurer.startMeasure();
		});
		
	} else {
		$('#edit-dialog-redraw').click(function(){fadeCurrentMapGraphic();measurer.startMeasure();});
	}
	

	$('#edit-dialog-delete').click(function(e){deleteArea(e)});
	// ** Parts of this function are temporary, and are only for demonstration purposes
	// When the "OK" button is clicked...
	$('#edit-dialog-close').click(function(e){updateArea(e);});

	// Opens notification drawer for pre-defined areas
	// Unused, handled differently - JBRIII.
	//$('#add-dialog-open').click(function(){$('#add-dialog').addClass('in');});
	// Closes notification drawer for pre-defined areas
	$('#add-dialog-close').click(function(e){addArea(e);});
	$('#add-dialog-cancel').click(function(){$('#add-dialog').removeClass('in'); $("#noticetypes input[type='checkbox']").each(function(i){$(this).prop('checked', false)});});  


	function setLeftPos(item,selector,deltax,deltay) {
		var item = $(item);
		var area = $(selector);
		var areaWidth = area.width();
		var areaOffset = area.offset();
		var posTop = areaOffset.top + deltax;
		var posLeft = areaOffset.left + areaWidth + deltay;
		item.css({"top":posTop, "left":posLeft});
		}

	function setRightPos(item,selector,deltax,deltay) {
		var item = $(item);
		var img = item.children('i');
		var imgWidth = img.width();
		var area = $(selector);
		var areaOffset = area.offset();
		var posTop = areaOffset.top + deltax;
		var posLeft = areaOffset.left - imgWidth + deltay;
		item.css({"top":posTop, "left":posLeft});
	}

	// Fire help modal 0 from Navigation
	$('#helpBtn, #help-btn-5').click(function(){
		$('.modal').modal('hide');
		$('#help-modal-0').modal();
	 });
	 
	// Fire help modal 1 from modal 0
	$('#help-btn-0').click(function(){
		$('.logged-out #userinfo').hide();	
		$('.modal').modal('hide');
		$('#accordion .in').collapse('hide').delay(500).queue(function(next){
			$('#collapseOne').collapse('show');
			$('#help-modal-1').modal();
			next();
		});
	 });
	$('#help-modal-1').on('show.bs.modal', function (e) {
		$('.logged-out #edit-dialog-open').show();
		$('.logged-out #areas-login').hide();
		setLeftPos('#help-new-areas','#heading-my-areas', 170,-220);
		setLeftPos('#help-draw-custom-area','#edit-dialog-open', -40,0);
		setRightPos('#help-use-map-control','#map_zoom_slider', 64,30);
		//setRightPos('#help-type-an-address','#map-search', 20,170);
	});

	// Fire help modal 2 from modal 1
	$('#help-btn-1').click(function(){
		$('.logged-out #edit-dialog-open').hide();
		$('.logged-out #areas-login').show();
		$('#edit-dialog').addClass('in').delay(500).queue(function(next){
			$('#help-modal-1').modal('hide');
			$('#help-modal-2').modal();
			next();
		});
	});
	$('#help-modal-2').on('show.bs.modal', function (e) {
		setLeftPos('#help-accept-changes','#edit-dialog-close', -40,20);
		setLeftPos('#help-give-area-name','#edit-dialog-accordion', 15,-50);
		setLeftPos('#help-choose-notification-type','#editnotices', 70,-100);
		setLeftPos('#help-delete-area','#edit-dialog-delete', -169,-46);
		setRightPos('#help-drawing-instructions','#map', 140,500);
		setLeftPos('#help-redraw-area','#edit-dialog-redraw', -169,-20);
		$('#help-drawing-instructions').css({
			'left':'auto',
			'right':'10px'
		});
	});
	
	// Fire help modal 3 from modal 2
	$('#help-btn-2').click(function(){
		$('#edit-dialog').removeClass('in');
		$('#collapseOne').collapse('hide');
		$('#collapseTwo').collapse('show').delay(500).queue(function(next){
			$('#help-modal-2').modal('hide');
			$('#help-modal-3').modal();
			next();
		});
	});
	$('#help-modal-3').on('show.bs.modal', function (e) {
		setLeftPos('#help-add-neighborhood-assoc','#collapseTwo', 190,-25);
		setLeftPos('#help-predefined-neighborhoods','#heading-neighborhoods', -15,-20);
	});

	// Fire help modal 4 from modal 3
	$('#help-btn-3').click(function(){
		$('#collapseTwo').collapse('hide');
		$('#collapseThree').collapse('show').delay(500).queue(function(next){
			$('#help-modal-3').modal('hide');
			$('#help-modal-4').modal();
			next();
		});
	});
	$('#help-modal-4').on('show.bs.modal', function (e) {
		setLeftPos('#help-add-council-districts','#collapseThree', 100,-15);
		setLeftPos('#help-predefined-council-districts','#heading-districts', -15,0);
	});

	// Fire help modal 5 from modal 4
	$('#help-btn-4').click(function(){
		$('#collapseThree').collapse('hide');
		$('#collapseFour').collapse('show').delay(500).queue(function(next){
			$('#help-modal-4').modal('hide');
			$('#help-modal-5').modal();
			next();
		});
	});
	$('#help-modal-5').on('show.bs.modal', function (e) {
		$('.logged-out #userinfo').show();
		setLeftPos('#help-account-prefs','#userinfo', -70,20);
		setLeftPos('#help-change-email-prefs','#email-prefs', 0,20);
	});
	
	$('.help-btn-dismiss').click(function(){
		$('.logged-out #edit-dialog-open').hide();
		$('.logged-out #areas-login').show();
		$('.logged-out #userinfo').hide();
		$('#edit-dialog').removeClass('in');
		$('#accordion .in').collapse('hide').delay(500).queue(function(next){
			$('#collapseOne').collapse('show');
			next();
		});
	});
	// fire accordion & map resize function on page load
	resize();
	
});

