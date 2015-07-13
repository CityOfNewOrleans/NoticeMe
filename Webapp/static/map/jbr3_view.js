function mapPrinter()
{
    //var printURL = "http://gis.nola.gov/arcgis/rest/services/NOLAPrinting/GPServer/Export%20Web%20Map";
    var printURL = 'http://sampleserver6.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task';
    var title = 'City of New Orleans Planning Viewer';
    var units = 'Miles';
    this.parameters = new esri.tasks.PrintParameters();
    this.parameters.map = map;
    this.parameters.outSpatialReference = map.spatialReference;
    this.parameters.template = new esri.tasks.PrintTemplate();
    this.parameters.template.layout = "Letter ANSI A Landscape";
    this.parameters.template.format = "PDF";
    this.parameters.template.layoutOptions = {"titleText": title, "scalebarUnit": units, "legendLayers": []};
    this.parameters.template.preserveScale = false;
    this.print = new esri.tasks.PrintTask(printURL);

    this.doPrint = function()
    {
        if (dojo.byId('printmsg').innerHTML.indexOf('PDF') > -1)
        {
            var url = dojo.byId('printlink').href;
            this.restoreButton();
            window.open(url);
        }
        else
        {
            dojo.byId('printmsg').innerHTML = '';
            dojo.byId('loadimg').style.display = 'inline';
            this.print.execute(
                this.parameters, 
                function(res) {
                    dojo.byId('loadimg').style.display = 'none';
                    dojo.byId('printlink').href = res.url;
                    dojo.byId('printmsg').innerHTML = '<b>Click for PDF</b>';
                },
                function(err) {
                    dojo.byId('loadimg').style.display = 'none';
                    this.restoreButton();
                    alert(err);
                }
            );
        }
    }

    this.restoreButton = function()
    {
        dojo.byId('printmsg').innerHTML = '<b>Print</b>';
    }
}

function mapMeasurer(tb, map, geomSvc)
{
    var markerType = esri.symbol.SimpleMarkerSymbol.STYLE_X;
    var markerColor = new dojo.Color([51, 102, 204, 0.8]);
    var markerSize = 3;

    var lineType = esri.symbol.SimpleLineSymbol.STYLE_SOLID;
    var lineColor = new dojo.Color([51, 102, 204, 1.0]);
    var lineWidth = 3;

    var polyType = esri.symbol.SimpleFillSymbol.STYLE_SOLID;
    var polyColor = new dojo.Color([51, 102, 204, 0.4]);

    this.drawPolygon = false;

    this.textPosition = [0.0, 0.0];

    this.markStyle = new esri.symbol.SimpleMarkerSymbol()
    this.markStyle.setStyle(markerType);
    this.markStyle.setColor(markerColor);
    this.markStyle.setSize(markerSize);
    this.markStyle.setOutline(new esri.symbol.SimpleLineSymbol(this.lineStyle, new dojo.Color([255, 255, 255, 0.0]), 0));

    this.lineStyle = new esri.symbol.SimpleLineSymbol()
    this.lineStyle.setStyle(lineType);
    this.lineStyle.setColor(lineColor);
    this.lineStyle.setWidth(lineWidth);

    this.fillStyle = new esri.symbol.SimpleFillSymbol();
    this.fillStyle.setStyle(polyType);
    this.fillStyle.setColor(polyColor);
    this.fillStyle.setOutline(this.lineStyle);

    tb.setMarkerSymbol(this.markStyle);
    tb.setLineSymbol(this.lineStyle);
    tb.setFillSymbol(this.fillStyle);
    
    this.startStopMeasure = function()
    {
        if (dojo.byId('measuring').checked)
        {
            tb.activate(esri.toolbars.Draw.POLYLINE);
            //this.toolbar.activate(esri.toolbars.Draw.POLYGON);
        }
        else
        {
            tb.deactivate();
            //map.graphics.clear();
        }
    }
	
    this.startMeasure = function()
    {
        tb.activate(esri.toolbars.Draw.POLYGON);
        //this.toolbar.activate(esri.toolbars.Draw.POLYGON);
        this.drawPolygon = true;
    }

    this.stopMeasure = function()
    {
        tb.deactivate();
        //map.graphics.clear();
        this.drawPolygon = false;
    }


    this.endPolyDraw = function(geom)
    {
        map.graphics.clear();
        var features = []
        features.push(new esri.Graphic(geom, this.fillSymbol));
        var featureSet = new esri.tasks.FeatureSet();
        featureSet.features = features;
        //console.log(geom)
        //console.log(featureSet['features'][0])
        map.graphics.add(featureSet['features'][0]);
        //var graphic = map.graphics.add(new esri.Graphic(geom, this.fillSymbol));
    }

    this.endMeasure = function(geom)
    {
        map.graphics.clear();
        /*
            This won't work.  It draws in the correct location, but is 
            incorrectly projected, thus is the wrong length (maybe convert from 
            meters?).

            Also, the default print service does not respect the font, style, 
            and color that I'm specifying (I believe this is a known issue 
            with 10.1).
        */
        pos = [0.0, 0.0];
        for (var xy in geom.paths[0])
        {
            if (geom.paths[0][xy][1] > pos[1])
            {
                pos[0] = geom.paths[0][xy][0];
                pos[1] = geom.paths[0][xy][1];
            }
        }

        measurer.textPosition[0] = pos[0];
        measurer.textPosition[1] = pos[1];
        var graphic = map.graphics.add(new esri.Graphic(geom, this.lineSymbol));
        var lengthParams = new esri.tasks.LengthsParameters();
        lengthParams.calculationType = 'preserveShape';
        lengthParams.lengthUnit = esri.tasks.GeometryService.UNIT_FOOT;
        lengthParams.polylines = [geom];
        geomSvc.lengths(lengthParams);
    }

    this.displayMeasure = function(res)
    {
        dojo.byId('total_length').innerHTML = 'Total Length: ' + res.lengths[0].toFixed(1) + ' ft.';
        var font = new esri.symbol.Font(14, esri.symbol.Font.STYLE_ITALIC, esri.symbol.Font.VARIANT_NORMAL, esri.symbol.Font.WEIGHT_BOLD);
        var resultText = new esri.symbol.TextSymbol('Total Length: ' + res.lengths[0].toFixed(1) + ' ft.', font, new dojo.Color([51, 102, 204, 1.0]));
        textStart = new esri.geometry.Point(measurer.textPosition[0], measurer.textPosition[1], map.spatialReference);
        resultText.setAlign(esri.symbol.TextSymbol.ALIGN_START);
        var textGraphic = map.graphics.add(new esri.Graphic(textStart, resultText));
    }

    dojo.connect(geomSvc, 'onLengthsComplete', this.displayMeasure);
    //dojo.connect(tb, 'onDrawEnd', this.endMeasure);
    dojo.connect(tb, 'onDrawEnd', this.endPolyDraw);
    //dojo.connect(tb, 'onDrawStart', function() {map.graphics.clear();});

}