dojo.require('esri.map');
dojo.require('esri.graphic');
dojo.require('esri.tasks.geometry');
dojo.require('esri.toolbars.draw');
dojo.require('esri.tasks.query');
dojo.ready(init);

var map;
var drawTool;
var geomSvc;
var printer;
var measurer;

var noticeAreas;
var highlightSymbol;

function init()
{
    /*** Initialize the app functionality.  Called when the DOM is ready. ***/
    map = new esri.Map('map', {
        sliderStyle: 'small',
        extent: new esri.geometry.Extent(-10034336.0, 3486258.0, -9977329.0, 3526049.0, new esri.SpatialReference({wkid: 3857})),
        logo: false
    });

	esri.config.defaults.map.logoLink = "http://www.nola.gov";

    var basemapURL = 'http://gis.nola.gov:6080/arcgis/rest/services/Basemaps/BasemapNOLA3/MapServer';
    map.addLayer(new esri.layers.ArcGISTiledMapServiceLayer(basemapURL));
    var geomURL = 'http://gis.nola.gov:6080/arcgis/rest/services/Utilities/Geometry/GeometryServer';
    drawTool = new esri.toolbars.Draw(map);
    geomSvc = new esri.tasks.GeometryService(geomURL);
    measurer = new mapMeasurer(drawTool, map, geomSvc);

    //Define the poly highlight
    highlightSymbol = new esri.symbol.SimpleFillSymbol(esri.symbol.SimpleFillSymbol.STYLE_SOLID)
    highlightSymbol.setOutline(new esri.symbol.SimpleLineSymbol(esri.symbol.SimpleLineSymbol.STYLE_SOLID,
                               new dojo.Color([51, 102, 204, 1.0]), 3));
    highlightSymbol.setColor(new dojo.Color([51, 102, 204, 0.4]));
    $('.navbar-brand').click(fadeCurrentMapGraphic);
    populatePredefined();
    checkLogin();
}

function populatePredefined()
{
    /*** Populate the predefined area panels. ***/
    var srnoNameField = 'Organization_Name';
    var srnoURL = 'http://gis.nola.gov:6080/arcgis/rest/services/apps/NoticeMe_Layers/MapServer/0';
    var srnoQueryTask = new esri.tasks.QueryTask(srnoURL);
    var srnoQuery = new esri.tasks.Query();
    var councilNameField = 'COUNCILDIS';
    var councilURL = 'http://gis.nola.gov:6080/arcgis/rest/services/apps/NoticeMe_Layers/MapServer/1';
    var councilQueryTask = new esri.tasks.QueryTask(councilURL);
    var councilQuery = new esri.tasks.Query();
    srnoQuery.outFields = [srnoNameField];
    srnoQuery.returnGeometry = true;
    srnoQuery.where = srnoNameField + " LIKE '%%'"
    srnoQueryTask.execute(srnoQuery, function(e){srnoListComplete.call(e, srnoNameField)}, predefListErrors);
    councilQuery.outFields = [councilNameField];
    councilQuery.returnGeometry = true;
    councilQuery.where = councilNameField + " LIKE '%%'"
    councilQueryTask.execute(councilQuery, function(e){councilListComplete.call(e, councilNameField)}, predefListErrors);
}

function srnoListComplete(nameField)
{
    /*** Handle the query results for SRNOs. ***/
    var nhoods = this;
    var idBase = 'srno';
    var destID = '#srno';
    buildList(nhoods, idBase, destID, nameField, '');
}

function councilListComplete(nameField)
{
    /*** Handle the query results for Council Districts. ***/
    var districts = this;
    var idBase = 'council';
    var destID = '#council';
    buildList(districts, idBase, destID, nameField, 'Council District ');
}

function buildList(featSet, idBase, destID, nameField, prepend)
{
    /*** Build a list for display in a panel. Called for SRNOs and Council Districts. ***/
    var dest = $(destID);
    var features = featSet['features'];
    //Get a sorted list of area names
    var areas = [];
    for (var i=0; i<features.length; i++)
    {
        areas.push($.trim(features[i]['attributes'][nameField]))
    }
    areas = areas.sort();
    //Now, create the items in the DOM.
    var listHTML = '';
    var newID = '';
    var icon = '';
    for (var i=0; i<areas.length; i++)
    {
        //Create the HTML and add it.
        newID = idBase + '_' + i;
        icon = 'glyphicon-plus';
        listHTML = '<li id="' + newID + '" class="list-group-item">';
        listHTML += prepend + areas[i];
        listHTML += '<span class="edit glyphicon ' + icon + '" onClick="ga(\'send\', \'event\', \'Add defined area\', \'Click\', \''+ prepend + areas[i]+'\');"></span></li>';
        dest.append(listHTML);
        //Now add the geometry and onclick methods.
        $('#'+newID).data('data-geom', getFeature(areas[i], featSet, nameField))
        $('#'+newID).click(showBoundary);
        $('#'+newID).children('span').on('click', showAdd);
    }
}

function predefListErrors(err)
{
    /*** Query error handler. ***/
    console.log(err);
}

function showBoundary()
{
	/*** Display and zoom to a geometry contained in a data-geom element, based on click location. ***/
	$('.list-group-item').removeClass("selected");
	$(this).addClass("selected");
    var bnd = $(this).data('data-geom');
    var bndExtent = bnd['geometry'].getExtent()
    var clickBound = new esri.Graphic(bnd['geometry'], highlightSymbol, bnd['attributes']);
    map.graphics.clear();
    var bndGraphic = map.graphics.add(clickBound);
    map.setExtent(bndExtent.expand(1.2), true);
	console.log(arguments[0].target)
		if ( $('.visible-xs').is(':visible'))
		{
			if (!$(arguments[0].target).hasClass('edit'))

			{
			$('#map-wrapper').addClass('in');
			}
		}

	console.log('Show Boundary');
}

function getFeature(areaname, geomVar, nameField)
{
    /*** Get a poly from a stored FeatureSet.  I don't think this is used anymore. ***/
    for (var i=0; i<geomVar['features'].length; i++)
    {
        if (geomVar['features'][i]['attributes'][nameField] == areaname)
        {
            return geomVar['features'][i];
        }
    }
}

function showAdd()
{
    /*** Show the add dialog. ***/
	var areaname = $(this).parent('li').text();
    $('#add-dialog h4.panel-title').html(areaname)
    $('#add-dialog').addClass('in');
    resize();
}

function showEdit()
{
    /*** Show the edit dialog. ***/
	var areaname = $(this).parent('li').text();
    var editID = $(this).parent('li').attr('id');
    var notices = $(this).parent('li').data('data-notices');
    for (var opt in notices)
    {
        $('#edt-'+opt).prop('checked', notices[opt])
    }
    $('#name-area').val(areaname);
    $('#edit-dialog').addClass('in');
    $('#edit-dialog').data('data-editid', editID);
    resize();
}

function addArea(e)
{
    /*** Add a predefined area to My Areas, and save it to the server. ***/
    var currDialog = '#add-dialog';
    $(currDialog).removeClass('in');
    var areaname = $(currDialog + ' h4.panel-title').text();
    var notices = {};
    $("#noticetypes input[type='checkbox']").each(function(i){notices[$(this).attr('id').split('-')[1]] = $(this).prop('checked')});
    $("#noticetypes input[type='checkbox']").each(function(i){$(this).prop('checked', false)});
    var feature = map.graphics.graphics[0];
    var namehash = CryptoJS.MD5(areaname).toString();
    var dest = $('#userarea');
    var newIDNum = getMaxIDNum('#userarea') + 1;
    var areaID = 'user_' + newIDNum;
    icon = 'glyphicon-pencil';
    listHTML = '<li id="' + areaID + '" class="list-group-item">';
    listHTML += areaname;
    listHTML += '<span class="edit glyphicon ' + icon + '"></span></li>';
    dest.append(listHTML);
    //Now add the geometry and onclick methods, and add a hash of the name.
    $('#'+areaID).data('data-geom', feature)
    $('#'+areaID).data('data-notices', notices)
    $('#'+areaID).data('data-namehash', namehash)
    $('#'+areaID).click(showBoundary);
    $('#'+areaID).children('span').on("click", showEdit );
    submitArea(areaname, namehash, notices, feature);
	$('.list-group-item').removeClass('selected');
	$('#'+areaID).addClass('selected');
	if ($('#collapseTwo').hasClass('in')) {
		$('#collapseTwo').collapse('hide');
	}
	else if ($('#collapseThree').hasClass('in')) {
		$('#collapseThree').collapse('hide');
	}
	$('#collapseOne').collapse('show');
	$('#collapseOne').on('shown.bs.collapse', function () {
		resize();
	})
}

function updateArea(e)
{
    /*** Edit an existing area in My Areas. ***/
    // Create variable of input
    var name = $('#name-area');
    // If the input is not empty...
    if (name.val() && name.val()!=name.attr('placeholder'))
    {
        measurer.stopMeasure();
        // ...take value of input and add it to the My Areas list...
        var editID = $('#edit-dialog').data('data-editid');
        var areaname = name.val();
        var namehash = CryptoJS.MD5(areaname).toString();
        var notices = {};
        $("#editnotices input[type='checkbox']").each(function(i){notices[$(this).attr('id').split('-')[1]] = $(this).prop('checked')});
        var feature = map.graphics.graphics[0];
        if (feature.geometry.type != 'polygon')
        {
            alert('Oops! Something went wrong when saving the area you defined.\n\nPlease try drawing it again.');
            measurer.startMeasure();
            return;
        }
        if (editID)
        {
            if (dataChanged(editID, namehash, notices, feature))
            {
                var editedItem = $('#'+editID);
                var oldhash = editedItem.data('data-namehash');
                editedItem.data('data-namehash', namehash);
                editedItem.data('data-notices', notices);
                editedItem.data('data-geom', feature);
                editedItem.html(areaname +'<span class="edit glyphicon glyphicon-pencil"></span>');
                updateExisting(oldhash, areaname, namehash, notices, feature);
				$('#'+editID).children('span').on("click", showEdit );
            }
            $('#edit-dialog').data('data-editid', null);
        }
        else
        {
            insertNew(areaname, namehash, notices, feature);
        }
        //Close the drawer and clear input
        $('#edit-dialog').removeClass('in');
        $("#editnotices input[type='checkbox']").each(function(i){$(this).prop('checked', false)});
        $(name).val('');
    }
    else
    {
        //Create an error popup if the name is empty.
        alert("You must give this area a name.");
    }
}

function insertNew(areaname, namehash, notices, feature)
{
    /*** Add a drawn area to My Areas, and save it to the server. ***/
    var dest = $('#userarea');
    var newIDNum = getMaxIDNum('#userarea') + 1;
    var areaID = 'user_' + newIDNum;
    icon = 'glyphicon-pencil';
    listHTML = '<li id="' + areaID + '" class="list-group-item">';
    listHTML += areaname;
    listHTML += '<span class="edit glyphicon ' + icon + '"></span></li>';
    dest.append(listHTML);
    //Now add the geometry and onclick methods, and add a hash of the name.
    $('#'+areaID).data('data-geom', feature)
    $('#'+areaID).data('data-notices', notices)
    $('#'+areaID).data('data-namehash', namehash)
    $('#'+areaID).click(showBoundary);
    $('#'+areaID).children('span').on("click", showEdit );
    //Send the data to the server here.
    submitArea(areaname, namehash, notices, feature);
}

function submitArea(areaname, namehash, notices, feature)
{
    /*** Submit an area to the server for saving. ***/
    var data = {}
    data['namehash'] = namehash;
    data['name'] = areaname;
    data['notices'] = notices;
    data['geom'] = feature.toJson();
    $.post('/_save', JSON.stringify(data));
}

function updateExisting(oldhash, areaname, namehash, notices, feature)
{
    /*** Submit an area to the server for updating. ***/
    var data = {}
    data['oldhash'] = oldhash;
    data['namehash'] = namehash;
    data['name'] = areaname;
    data['notices'] = notices;
    data['geom'] = feature.toJson();
    $.post('/_update', JSON.stringify(data));
}

function deleteArea()
{
	/*** Delete an area from My Areas and the server. ***/
    $('#delete-confirm-modal').modal();
	$('#delete-confirm').click( function() {
		var editID = $('#edit-dialog').data('data-editid');
		var editedItem = $('#'+editID);
		map.graphics.clear();
        var delhash = {'namehash': editedItem.data('data-namehash')};
		editedItem.data('data-namehash', null);
		editedItem.data('data-notices', null);
		editedItem.data('data-geom', null);
		$('#edit-dialog').removeClass('in');
		$("#editnotices input[type='checkbox']").each(function(i){$(this).prop('checked', false)});
		editedItem.fadeOut(2000);
		$(name).val('');
		$.post('/_delete', JSON.stringify(delhash));
	});
	$('#delete-cancel').click( function() {
		$('#edit-dialog').removeClass('in');
	});
}

function dataChanged(editID, namehash, notices, feature)
{
    /*** Check to see if notices, geometry, and name have changed for an area. ***/
    var changed = true;
    var editedItem = $('#'+editID)
    if (editedItem)
    {
        var oldhash = editedItem.data('data-namehash');
        var oldnotices = editedItem.data('data-notices');
        var oldfeature = editedItem.data('data-geom');
        var cmp_hsh = _.isEqual(oldhash, namehash);
        var cmp_ntc = _.isEqual(oldnotices, notices);
        //We only really care if the geometries are equivalent.
        var cmp_ftr = _.isEqual(oldfeature['geometry'], feature['geometry']);
        if (cmp_hsh && cmp_ntc && cmp_ftr)
        {
            changed = false;
        }
    }
    return changed;
}

function getMaxIDNum(dest)
{
    /*** Get the max id number of the items in an area list. ***/
    var maxNum = -1;
    var nums = [];
    $(dest+' li').each(function(i){nums.push($(this).attr('id').split('_')[1])});
    if (nums.length > 0)
    {
        maxNum = parseInt(nums.slice(0).sort().reverse()[0]);
    }
    return maxNum;
}


function userVoice() {
	// Include the UserVoice JavaScript SDK (only needed once on a page)
	UserVoice=window.UserVoice||[];
	(function(){
		var uv=document.createElement('script');
		uv.type='text/javascript';
		uv.async=true;
		uv.src='//widget.uservoice.com/iOJ6fGk96FsCT1Fq2L8Nw.js';
		var s=document.getElementsByTagName('script')[0];
		s.parentNode.insertBefore(uv,s)
	})();
}

function signIn(data)
{
    /*** Change the UI to reflect a logged in user. ***/
    if (data.email)
    {

		userVoice();
		UserVoice.push(['identify', {
			email: data.email // User’s email address
		}]);

        document.cookie = 'noticeme_user=' + data.email;
        $('#userinfo').css('display', 'block');
        $('#suggestsignin').css('display', 'none');
        $('#emailaddr').text(data.email)
        $('#loginBtn').parent().css('display', 'none');
        $('#logoutBtn').parent().css('display', 'inline-block');
		$('#areas-login').hide();
		$('#edit-dialog-open, #userinfo').show();
		$('body').removeClass('logged-out').addClass('logged-in');
        if (data.freq == 'd')
        {
            $('#one-per-day').prop('checked', true);
        }
        else
        {
            $('#one-per-week').prop('checked', true);
        }
        if (data.autoadd)
        {
            $('#add-new').prop('checked', true);
        }
        if (data.citywide)
        {
            $('#citywide').prop('checked', true);
        }
        populateUserAreas(data['areas']);
        resize();
    }
}

function checkLogin()
{
    /*** Function to test if we are logged in when the page loads.
          This way, the list of user areas does not disappear if the user reloads
          the page. ***/
    var cookieVals = document.cookie.split(';');
    for (var i=0; i<cookieVals.length; i++)
    {
        if ($.trim(cookieVals[i].split('=')[0]) == 'noticeme_user')
        {
            var userEmail = $.trim(cookieVals[i].split('=')[1]);
        }
        else
        {
            var userEmail = null;
        }
    }
    if (userEmail)
    {
       $.getJSON('/_user', function (data) {signIn(data);})
    }
}

function populateUserAreas(data)
{
    /*** Populate the My Areas list using data obtained after login. ***/
    var dest = $('#userarea');
    var icon = 'glyphicon-pencil';
    var newIDNum;
    var areaID;
    var areaname;
    var namehash;
    var notices;
    var geom;
    var feature;

    for (var i=0; i<data.length; i++)
    {
        newIDNum = getMaxIDNum('#userarea') + 1;
        areaID = 'user_' + newIDNum;
        areaname = data[i]['name'];
        namehash = data[i]['namehash'];
        notices = JSON.parse(data[i]['notices']);
        geom = data[i]['geom'];
        feature = new esri.Graphic(JSON.parse(geom));
        listHTML = '<li id="' + areaID + '" class="list-group-item">';
        listHTML += areaname;
        listHTML += '<span class="edit glyphicon ' + icon + '"></span></li>';
        dest.append(listHTML);
        //Now add the geometry and onclick methods, and add a hash of the name.
        $('#'+areaID).data('data-geom', feature)
        $('#'+areaID).data('data-notices', notices)
        $('#'+areaID).data('data-namehash', namehash)
        $('#'+areaID).click(showBoundary);
        $('#'+areaID).children('span').on("click", showEdit);
    }
}

function fadeCurrentMapGraphic()
{
    /*** Fade out the currently displayed graphic to serve as a touchpoint for new drawing ***/
    //First, get the currently displayed map graphic
    var currFeature = map.graphics.graphics[0];

    //Define the faded poly highlight
    var fadedSymbol = new esri.symbol.SimpleFillSymbol(esri.symbol.SimpleFillSymbol.STYLE_SOLID)

    fadedSymbol.setOutline(new esri.symbol.SimpleLineSymbol(esri.symbol.SimpleLineSymbol.STYLE_DOT,
                               new dojo.Color([51, 102, 204, 0.55]), 2));
    fadedSymbol.setColor(new dojo.Color([51, 102, 204, 0.15]));

    //Set the new faded symbol
    currFeature.setSymbol(fadedSymbol);
}

function saveUserPrefs()
{
    /*** Get and save user preferences on change ***/
    var weekly = $('#one-per-week').prop('checked');
    var daily = $('#one-per-day').prop('checked');
    var autoadd = $('#add-new').prop('checked');
    var citywide = $('#citywide').prop('checked');
    var data = {};
    if (daily)
    {
        data['freq'] = 'd';
    }
    else if (weekly)
    {
        data['freq'] = 'w';
    }
    else
    {
        data['freq'] = 'w';
    }

    if (autoadd)
    {
        data['auto'] = 1;
    }
    else
    {
        data['auto'] = 0;
    }

    if (citywide)
    {
        data['citywide'] = 1;
    }
    else
    {
        data['citywide'] = 0;
    }
    $.post('/_user', JSON.stringify(data));
}