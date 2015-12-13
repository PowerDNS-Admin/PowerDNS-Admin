var ChartsAmcharts = function() {

    var initChartSample1 = function() {
        var chart = AmCharts.makeChart("chart_1", {
            "type": "serial",
            "theme": "light",
            "pathToImages": Metronic.getGlobalPluginsPath() + "amcharts/amcharts/images/",
            "autoMargins": false,
            "marginLeft": 30,
            "marginRight": 8,
            "marginTop": 10,
            "marginBottom": 26,

            "fontFamily": 'Open Sans',            
            "color":    '#888',
            
            "dataProvider": [{
                "year": 2009,
                "income": 23.5,
                "expenses": 18.1
            }, {
                "year": 2010,
                "income": 26.2,
                "expenses": 22.8
            }, {
                "year": 2011,
                "income": 30.1,
                "expenses": 23.9
            }, {
                "year": 2012,
                "income": 29.5,
                "expenses": 25.1
            }, {
                "year": 2013,
                "income": 30.6,
                "expenses": 27.2,
                "dashLengthLine": 5
            }, {
                "year": 2014,
                "income": 34.1,
                "expenses": 29.9,
                "dashLengthColumn": 5,
                "alpha": 0.2,
                "additional": "(projection)"
            }],
            "valueAxes": [{
                "axisAlpha": 0,
                "position": "left"
            }],
            "startDuration": 1,
            "graphs": [{
                "alphaField": "alpha",
                "balloonText": "<span style='font-size:13px;'>[[title]] in [[category]]:<b>[[value]]</b> [[additional]]</span>",
                "dashLengthField": "dashLengthColumn",
                "fillAlphas": 1,
                "title": "Income",
                "type": "column",
                "valueField": "income"
            }, {
                "balloonText": "<span style='font-size:13px;'>[[title]] in [[category]]:<b>[[value]]</b> [[additional]]</span>",
                "bullet": "round",
                "dashLengthField": "dashLengthLine",
                "lineThickness": 3,
                "bulletSize": 7,
                "bulletBorderAlpha": 1,
                "bulletColor": "#FFFFFF",
                "useLineColorForBulletBorder": true,
                "bulletBorderThickness": 3,
                "fillAlphas": 0,
                "lineAlpha": 1,
                "title": "Expenses",
                "valueField": "expenses"
            }],
            "categoryField": "year",
            "categoryAxis": {
                "gridPosition": "start",
                "axisAlpha": 0,
                "tickLength": 0
            }
        });

        $('#chart_1').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    var initChartSample2 = function() {
        var chart = AmCharts.makeChart("chart_2", {
            "type": "serial",
            "theme": "light",

            "fontFamily": 'Open Sans',
            "color":    '#888888',

            "legend": {
                "equalWidths": false,
                "useGraphSettings": true,
                "valueAlign": "left",
                "valueWidth": 120
            },
            "dataProvider": [{
                "date": "2012-01-01",
                "distance": 227,
                "townName": "New York",
                "townName2": "New York",
                "townSize": 25,
                "latitude": 40.71,
                "duration": 408
            }, {
                "date": "2012-01-02",
                "distance": 371,
                "townName": "Washington",
                "townSize": 14,
                "latitude": 38.89,
                "duration": 482
            }, {
                "date": "2012-01-03",
                "distance": 433,
                "townName": "Wilmington",
                "townSize": 6,
                "latitude": 34.22,
                "duration": 562
            }, {
                "date": "2012-01-04",
                "distance": 345,
                "townName": "Jacksonville",
                "townSize": 7,
                "latitude": 30.35,
                "duration": 379
            }, {
                "date": "2012-01-05",
                "distance": 480,
                "townName": "Miami",
                "townName2": "Miami",
                "townSize": 10,
                "latitude": 25.83,
                "duration": 501
            }, {
                "date": "2012-01-06",
                "distance": 386,
                "townName": "Tallahassee",
                "townSize": 7,
                "latitude": 30.46,
                "duration": 443
            }, {
                "date": "2012-01-07",
                "distance": 348,
                "townName": "New Orleans",
                "townSize": 10,
                "latitude": 29.94,
                "duration": 405
            }, {
                "date": "2012-01-08",
                "distance": 238,
                "townName": "Houston",
                "townName2": "Houston",
                "townSize": 16,
                "latitude": 29.76,
                "duration": 309
            }, {
                "date": "2012-01-09",
                "distance": 218,
                "townName": "Dalas",
                "townSize": 17,
                "latitude": 32.8,
                "duration": 287
            }, {
                "date": "2012-01-10",
                "distance": 349,
                "townName": "Oklahoma City",
                "townSize": 11,
                "latitude": 35.49,
                "duration": 485
            }, {
                "date": "2012-01-11",
                "distance": 603,
                "townName": "Kansas City",
                "townSize": 10,
                "latitude": 39.1,
                "duration": 890
            }, {
                "date": "2012-01-12",
                "distance": 534,
                "townName": "Denver",
                "townName2": "Denver",
                "townSize": 18,
                "latitude": 39.74,
                "duration": 810
            }, {
                "date": "2012-01-13",
                "townName": "Salt Lake City",
                "townSize": 12,
                "distance": 425,
                "duration": 670,
                "latitude": 40.75,
                "dashLength": 8,
                "alpha": 0.4
            }, {
                "date": "2012-01-14",
                "latitude": 36.1,
                "duration": 470,
                "townName": "Las Vegas",
                "townName2": "Las Vegas"
            }, {
                "date": "2012-01-15"
            }, {
                "date": "2012-01-16"
            }, {
                "date": "2012-01-17"
            }, {
                "date": "2012-01-18"
            }, {
                "date": "2012-01-19"
            }],
            "valueAxes": [{
                "id": "distanceAxis",
                "axisAlpha": 0,
                "gridAlpha": 0,
                "position": "left",
                "title": "distance"
            }, {
                "id": "latitudeAxis",
                "axisAlpha": 0,
                "gridAlpha": 0,
                "labelsEnabled": false,
                "position": "right"
            }, {
                "id": "durationAxis",
                "duration": "mm",
                "durationUnits": {
                    "hh": "h ",
                    "mm": "min"
                },
                "axisAlpha": 0,
                "gridAlpha": 0,
                "inside": true,
                "position": "right",
                "title": "duration"
            }],
            "graphs": [{
                "alphaField": "alpha",
                "balloonText": "[[value]] miles",
                "dashLengthField": "dashLength",
                "fillAlphas": 0.7,
                "legendPeriodValueText": "total: [[value.sum]] mi",
                "legendValueText": "[[value]] mi",
                "title": "distance",
                "type": "column",
                "valueField": "distance",
                "valueAxis": "distanceAxis"
            }, {
                "balloonText": "latitude:[[value]]",
                "bullet": "round",
                "bulletBorderAlpha": 1,
                "useLineColorForBulletBorder": true,
                "bulletColor": "#FFFFFF",
                "bulletSizeField": "townSize",
                "dashLengthField": "dashLength",
                "descriptionField": "townName",
                "labelPosition": "right",
                "labelText": "[[townName2]]",
                "legendValueText": "[[description]]/[[value]]",
                "title": "latitude/city",
                "fillAlphas": 0,
                "valueField": "latitude",
                "valueAxis": "latitudeAxis"
            }, {
                "bullet": "square",
                "bulletBorderAlpha": 1,
                "bulletBorderThickness": 1,
                "dashLengthField": "dashLength",
                "legendValueText": "[[value]]",
                "title": "duration",
                "fillAlphas": 0,
                "valueField": "duration",
                "valueAxis": "durationAxis"
            }],
            "chartCursor": {
                "categoryBalloonDateFormat": "DD",
                "cursorAlpha": 0.1,
                "cursorColor": "#000000",
                "fullWidth": true,
                "valueBalloonsEnabled": false,
                "zoomable": false
            },
            "dataDateFormat": "YYYY-MM-DD",
            "categoryField": "date",
            "categoryAxis": {
                "dateFormats": [{
                    "period": "DD",
                    "format": "DD"
                }, {
                    "period": "WW",
                    "format": "MMM DD"
                }, {
                    "period": "MM",
                    "format": "MMM"
                }, {
                    "period": "YYYY",
                    "format": "YYYY"
                }],
                "parseDates": true,
                "autoGridCount": false,
                "axisColor": "#555555",
                "gridAlpha": 0.1,
                "gridColor": "#FFFFFF",
                "gridCount": 50
            },
            "exportConfig": {
                "menuBottom": "20px",
                "menuRight": "22px",
                "menuItems": [{
                    "icon": Metronic.getGlobalPluginsPath() + "amcharts/amcharts/images/export.png",
                    "format": 'png'
                }]
            }
        });

        $('#chart_2').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    var initChartSample3 = function() {
        var chart = AmCharts.makeChart("chart_3", {
            "type": "serial",
            "theme": "light",

            "fontFamily": 'Open Sans',            
            "color":    '#888888',
            
            "pathToImages": Metronic.getGlobalPluginsPath() + "amcharts/amcharts/images/",

            "dataProvider": [{
                "lineColor": "#b7e021",  
                "date": "2012-01-01",
                "duration": 408
            }, {
                "date": "2012-01-02",
                "duration": 482
            }, {
                "date": "2012-01-03",
                "duration": 562
            }, {
                "date": "2012-01-04",
                "duration": 379
            }, {
                "lineColor": "#fbd51a",
                "date": "2012-01-05",
                "duration": 501
            }, {
                "date": "2012-01-06",
                "duration": 443
            }, {
                "date": "2012-01-07",
                "duration": 405
            }, {
                "date": "2012-01-08",
                "duration": 309,
                "lineColor": "#2498d2"
            }, {
                "date": "2012-01-09",
                "duration": 287
            }, {
                "date": "2012-01-10",
                "duration": 485
            }, {
                "date": "2012-01-11",
                "duration": 890
            }, {
                "date": "2012-01-12",
                "duration": 810
            }],
            "balloon": {
                "cornerRadius": 6
            },
            "valueAxes": [{
                "duration": "mm",
                "durationUnits": {
                    "hh": "h ",
                    "mm": "min"
                },
                "axisAlpha": 0
            }],
            "graphs": [{
                "bullet": "square",
                "bulletBorderAlpha": 1,
                "bulletBorderThickness": 1,
                "fillAlphas": 0.3,
                "fillColorsField": "lineColor",
                "legendValueText": "[[value]]",
                "lineColorField": "lineColor",
                "title": "duration",
                "valueField": "duration"
            }],
            "chartScrollbar": {},
            "chartCursor": {
                "categoryBalloonDateFormat": "YYYY MMM DD",
                "cursorAlpha": 0,
                "zoomable": false
            },
            "dataDateFormat": "YYYY-MM-DD",
            "categoryField": "date",
            "categoryAxis": {
                "dateFormats": [{
                    "period": "DD",
                    "format": "DD"
                }, {
                    "period": "WW",
                    "format": "MMM DD"
                }, {
                    "period": "MM",
                    "format": "MMM"
                }, {
                    "period": "YYYY",
                    "format": "YYYY"
                }],
                "parseDates": true,
                "autoGridCount": false,
                "axisColor": "#555555",
                "gridAlpha": 0,
                "gridCount": 50
            }
        });

        $('#chart_3').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    var initChartSample4 = function() {
        var chart = AmCharts.makeChart("chart_4", {
            "type": "serial",
            "theme": "light",


            "handDrawn": true,
            "handDrawScatter": 3,
            "legend": {
                "useGraphSettings": true,
                "markerSize": 12,
                "valueWidth": 0,
                "verticalGap": 0
            },
            "dataProvider": [{
                "year": 2005,
                "income": 23.5,
                "expenses": 18.1
            }, {
                "year": 2006,
                "income": 26.2,
                "expenses": 22.8
            }, {
                "year": 2007,
                "income": 30.1,
                "expenses": 23.9
            }, {
                "year": 2008,
                "income": 29.5,
                "expenses": 25.1
            }, {
                "year": 2009,
                "income": 24.6,
                "expenses": 25
            }],
            "valueAxes": [{
                "minorGridAlpha": 0.08,
                "minorGridEnabled": true,
                "position": "top",
                "axisAlpha": 0
            }],
            "startDuration": 1,
            "graphs": [{
                "balloonText": "<span style='font-size:13px;'>[[title]] in [[category]]:<b>[[value]]</b></span>",
                "title": "Income",
                "type": "column",
                "fillAlphas": 0.8,

                "valueField": "income"
            }, {
                "balloonText": "<span style='font-size:13px;'>[[title]] in [[category]]:<b>[[value]]</b></span>",
                "bullet": "round",
                "bulletBorderAlpha": 1,
                "bulletColor": "#FFFFFF",
                "useLineColorForBulletBorder": true,
                "fillAlphas": 0,
                "lineThickness": 2,
                "lineAlpha": 1,
                "bulletSize": 7,
                "title": "Expenses",
                "valueField": "expenses"
            }],
            "rotate": true,
            "categoryField": "year",
            "categoryAxis": {
                "gridPosition": "start"
            }
        });

        $('#chart_4').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    var initChartSample5 = function() {
        var chart = AmCharts.makeChart("chart_5", {
            "theme": "light",
            "type": "serial",
            "startDuration": 2,

            "fontFamily": 'Open Sans',
            
            "color":    '#888',

            "dataProvider": [{
                "country": "USA",
                "visits": 4025,
                "color": "#FF0F00"
            }, {
                "country": "China",
                "visits": 1882,
                "color": "#FF6600"
            }, {
                "country": "Japan",
                "visits": 1809,
                "color": "#FF9E01"
            }, {
                "country": "Germany",
                "visits": 1322,
                "color": "#FCD202"
            }, {
                "country": "UK",
                "visits": 1122,
                "color": "#F8FF01"
            }, {
                "country": "France",
                "visits": 1114,
                "color": "#B0DE09"
            }, {
                "country": "India",
                "visits": 984,
                "color": "#04D215"
            }, {
                "country": "Spain",
                "visits": 711,
                "color": "#0D8ECF"
            }, {
                "country": "Netherlands",
                "visits": 665,
                "color": "#0D52D1"
            }, {
                "country": "Russia",
                "visits": 580,
                "color": "#2A0CD0"
            }, {
                "country": "South Korea",
                "visits": 443,
                "color": "#8A0CCF"
            }, {
                "country": "Canada",
                "visits": 441,
                "color": "#CD0D74"
            }, {
                "country": "Brazil",
                "visits": 395,
                "color": "#754DEB"
            }, {
                "country": "Italy",
                "visits": 386,
                "color": "#DDDDDD"
            }, {
                "country": "Australia",
                "visits": 384,
                "color": "#999999"
            }, {
                "country": "Taiwan",
                "visits": 338,
                "color": "#333333"
            }, {
                "country": "Poland",
                "visits": 328,
                "color": "#000000"
            }],
            "valueAxes": [{
                "position": "left",
                "axisAlpha": 0,
                "gridAlpha": 0
            }],
            "graphs": [{
                "balloonText": "[[category]]: <b>[[value]]</b>",
                "colorField": "color",
                "fillAlphas": 0.85,
                "lineAlpha": 0.1,
                "type": "column",
                "topRadius": 1,
                "valueField": "visits"
            }],
            "depth3D": 40,
            "angle": 30,
            "chartCursor": {
                "categoryBalloonEnabled": false,
                "cursorAlpha": 0,
                "zoomable": false
            },
            "categoryField": "country",
            "categoryAxis": {
                "gridPosition": "start",
                "axisAlpha": 0,
                "gridAlpha": 0

            },
            "exportConfig": {
                "menuTop": "20px",
                "menuRight": "20px",
                "menuItems": [{
                    "icon": '/lib/3/images/export.png',
                    "format": 'png'
                }]
            }
        }, 0);

        jQuery('.chart_5_chart_input').off().on('input change', function() {
            var property = jQuery(this).data('property');
            var target = chart;
            chart.startDuration = 0;

            if (property == 'topRadius') {
                target = chart.graphs[0];
            }

            target[property] = this.value;
            chart.validateNow();
        });

        $('#chart_5').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    var initChartSample6 = function() {
        var chart = AmCharts.makeChart("chart_6", {
            "type": "pie",
            "theme": "light",

            "fontFamily": 'Open Sans',
            
            "color":    '#888',

            "dataProvider": [{
                "country": "Lithuania",
                "litres": 501.9
            }, {
                "country": "Czech Republic",
                "litres": 301.9
            }, {
                "country": "Ireland",
                "litres": 201.1
            }, {
                "country": "Germany",
                "litres": 165.8
            }, {
                "country": "Australia",
                "litres": 139.9
            }, {
                "country": "Austria",
                "litres": 128.3
            }, {
                "country": "UK",
                "litres": 99
            }, {
                "country": "Belgium",
                "litres": 60
            }, {
                "country": "The Netherlands",
                "litres": 50
            }],
            "valueField": "litres",
            "titleField": "country",
            "exportConfig": {
                menuItems: [{
                    icon: Metronic.getGlobalPluginsPath() + "amcharts/amcharts/images/export.png",
                    format: 'png'
                }]
            }
        });

        $('#chart_6').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    var initChartSample7 = function() {
        var chart = AmCharts.makeChart("chart_7", {
            "type": "pie",
            "theme": "light",

            "fontFamily": 'Open Sans',
            
            "color":    '#888',

            "dataProvider": [{
                "country": "Lithuania",
                "value": 260
            }, {
                "country": "Ireland",
                "value": 201
            }, {
                "country": "Germany",
                "value": 65
            }, {
                "country": "Australia",
                "value": 39
            }, {
                "country": "UK",
                "value": 19
            }, {
                "country": "Latvia",
                "value": 10
            }],
            "valueField": "value",
            "titleField": "country",
            "outlineAlpha": 0.4,
            "depth3D": 15,
            "balloonText": "[[title]]<br><span style='font-size:14px'><b>[[value]]</b> ([[percents]]%)</span>",
            "angle": 30,
            "exportConfig": {
                menuItems: [{
                    icon: '/lib/3/images/export.png',
                    format: 'png'
                }]
            }
        });

        jQuery('.chart_7_chart_input').off().on('input change', function() {
            var property = jQuery(this).data('property');
            var target = chart;
            var value = Number(this.value);
            chart.startDuration = 0;

            if (property == 'innerRadius') {
                value += "%";
            }

            target[property] = value;
            chart.validateNow();
        });

        $('#chart_7').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    var initChartSample8 = function() {
        var chart = AmCharts.makeChart("chart_8", {
            "type": "radar",
            "theme": "light",

            "fontFamily": 'Open Sans',
            
            "color":    '#888',

            "dataProvider": [{
                "direction": "N",
                "value": 8
            }, {
                "direction": "NE",
                "value": 9
            }, {
                "direction": "E",
                "value": 4.5
            }, {
                "direction": "SE",
                "value": 3.5
            }, {
                "direction": "S",
                "value": 9.2
            }, {
                "direction": "SW",
                "value": 8.4
            }, {
                "direction": "W",
                "value": 11.1
            }, {
                "direction": "NW",
                "value": 10
            }],
            "valueAxes": [{
                "gridType": "circles",
                "minimum": 0,
                "autoGridCount": false,
                "axisAlpha": 0.2,
                "fillAlpha": 0.05,
                "fillColor": "#FFFFFF",
                "gridAlpha": 0.08,
                "guides": [{
                    "angle": 225,
                    "fillAlpha": 0.3,
                    "fillColor": "#0066CC",
                    "tickLength": 0,
                    "toAngle": 315,
                    "toValue": 14,
                    "value": 0,
                    "lineAlpha": 0,

                }, {
                    "angle": 45,
                    "fillAlpha": 0.3,
                    "fillColor": "#CC3333",
                    "tickLength": 0,
                    "toAngle": 135,
                    "toValue": 14,
                    "value": 0,
                    "lineAlpha": 0,
                }],
                "position": "left"
            }],
            "startDuration": 1,
            "graphs": [{
                "balloonText": "[[category]]: [[value]] m/s",
                "bullet": "round",
                "fillAlphas": 0.3,
                "valueField": "value"
            }],
            "categoryField": "direction"
        });

        $('#chart_8').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    var initChartSample9 = function() {
        var chart = AmCharts.makeChart("chart_9", {
            "type": "radar",
            "theme": "light",

            "fontFamily": 'Open Sans',
            
            "color":    '#888',

            "dataProvider": [{
                "country": "Czech Republic",
                "litres": 156.9
            }, {
                "country": "Ireland",
                "litres": 131.1
            }, {
                "country": "Germany",
                "litres": 115.8
            }, {
                "country": "Australia",
                "litres": 109.9
            }, {
                "country": "Austria",
                "litres": 108.3
            }, {
                "country": "UK",
                "litres": 99
            }],
            "valueAxes": [{
                "axisTitleOffset": 20,
                "minimum": 0,
                "axisAlpha": 0.15
            }],
            "startDuration": 2,
            "graphs": [{
                "balloonText": "[[value]] litres of beer per year",
                "bullet": "round",
                "valueField": "litres"
            }],
            "categoryField": "country",
            "exportConfig": {
                "menuTop": "10px",
                "menuRight": "10px",
                "menuItems": [{
                    "icon": '/lib/3/images/export.png',
                    "format": 'png'
                }]
            }
        });

        $('#chart_9').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    var initChartSample10 = function() {
        /*
            although ammap has methos like getAreaCenterLatitude and getAreaCenterLongitude,
            they are not suitable in quite a lot of cases as the center of some countries
            is even outside the country itself (like US, because of Alaska and Hawaii)
            That's why wehave the coordinates stored here
        */

        var latlong = {};
        latlong["AD"] = {
            "latitude": 42.5,
            "longitude": 1.5
        };
        latlong["AE"] = {
            "latitude": 24,
            "longitude": 54
        };
        latlong["AF"] = {
            "latitude": 33,
            "longitude": 65
        };
        latlong["AG"] = {
            "latitude": 17.05,
            "longitude": -61.8
        };
        latlong["AI"] = {
            "latitude": 18.25,
            "longitude": -63.1667
        };
        latlong["AL"] = {
            "latitude": 41,
            "longitude": 20
        };
        latlong["AM"] = {
            "latitude": 40,
            "longitude": 45
        };
        latlong["AN"] = {
            "latitude": 12.25,
            "longitude": -68.75
        };
        latlong["AO"] = {
            "latitude": -12.5,
            "longitude": 18.5
        };
        latlong["AP"] = {
            "latitude": 35,
            "longitude": 105
        };
        latlong["AQ"] = {
            "latitude": -90,
            "longitude": 0
        };
        latlong["AR"] = {
            "latitude": -34,
            "longitude": -64
        };
        latlong["AS"] = {
            "latitude": -14.3333,
            "longitude": -170
        };
        latlong["AT"] = {
            "latitude": 47.3333,
            "longitude": 13.3333
        };
        latlong["AU"] = {
            "latitude": -27,
            "longitude": 133
        };
        latlong["AW"] = {
            "latitude": 12.5,
            "longitude": -69.9667
        };
        latlong["AZ"] = {
            "latitude": 40.5,
            "longitude": 47.5
        };
        latlong["BA"] = {
            "latitude": 44,
            "longitude": 18
        };
        latlong["BB"] = {
            "latitude": 13.1667,
            "longitude": -59.5333
        };
        latlong["BD"] = {
            "latitude": 24,
            "longitude": 90
        };
        latlong["BE"] = {
            "latitude": 50.8333,
            "longitude": 4
        };
        latlong["BF"] = {
            "latitude": 13,
            "longitude": -2
        };
        latlong["BG"] = {
            "latitude": 43,
            "longitude": 25
        };
        latlong["BH"] = {
            "latitude": 26,
            "longitude": 50.55
        };
        latlong["BI"] = {
            "latitude": -3.5,
            "longitude": 30
        };
        latlong["BJ"] = {
            "latitude": 9.5,
            "longitude": 2.25
        };
        latlong["BM"] = {
            "latitude": 32.3333,
            "longitude": -64.75
        };
        latlong["BN"] = {
            "latitude": 4.5,
            "longitude": 114.6667
        };
        latlong["BO"] = {
            "latitude": -17,
            "longitude": -65
        };
        latlong["BR"] = {
            "latitude": -10,
            "longitude": -55
        };
        latlong["BS"] = {
            "latitude": 24.25,
            "longitude": -76
        };
        latlong["BT"] = {
            "latitude": 27.5,
            "longitude": 90.5
        };
        latlong["BV"] = {
            "latitude": -54.4333,
            "longitude": 3.4
        };
        latlong["BW"] = {
            "latitude": -22,
            "longitude": 24
        };
        latlong["BY"] = {
            "latitude": 53,
            "longitude": 28
        };
        latlong["BZ"] = {
            "latitude": 17.25,
            "longitude": -88.75
        };
        latlong["CA"] = {
            "latitude": 54,
            "longitude": -100
        };
        latlong["CC"] = {
            "latitude": -12.5,
            "longitude": 96.8333
        };
        latlong["CD"] = {
            "latitude": 0,
            "longitude": 25
        };
        latlong["CF"] = {
            "latitude": 7,
            "longitude": 21
        };
        latlong["CG"] = {
            "latitude": -1,
            "longitude": 15
        };
        latlong["CH"] = {
            "latitude": 47,
            "longitude": 8
        };
        latlong["CI"] = {
            "latitude": 8,
            "longitude": -5
        };
        latlong["CK"] = {
            "latitude": -21.2333,
            "longitude": -159.7667
        };
        latlong["CL"] = {
            "latitude": -30,
            "longitude": -71
        };
        latlong["CM"] = {
            "latitude": 6,
            "longitude": 12
        };
        latlong["CN"] = {
            "latitude": 35,
            "longitude": 105
        };
        latlong["CO"] = {
            "latitude": 4,
            "longitude": -72
        };
        latlong["CR"] = {
            "latitude": 10,
            "longitude": -84
        };
        latlong["CU"] = {
            "latitude": 21.5,
            "longitude": -80
        };
        latlong["CV"] = {
            "latitude": 16,
            "longitude": -24
        };
        latlong["CX"] = {
            "latitude": -10.5,
            "longitude": 105.6667
        };
        latlong["CY"] = {
            "latitude": 35,
            "longitude": 33
        };
        latlong["CZ"] = {
            "latitude": 49.75,
            "longitude": 15.5
        };
        latlong["DE"] = {
            "latitude": 51,
            "longitude": 9
        };
        latlong["DJ"] = {
            "latitude": 11.5,
            "longitude": 43
        };
        latlong["DK"] = {
            "latitude": 56,
            "longitude": 10
        };
        latlong["DM"] = {
            "latitude": 15.4167,
            "longitude": -61.3333
        };
        latlong["DO"] = {
            "latitude": 19,
            "longitude": -70.6667
        };
        latlong["DZ"] = {
            "latitude": 28,
            "longitude": 3
        };
        latlong["EC"] = {
            "latitude": -2,
            "longitude": -77.5
        };
        latlong["EE"] = {
            "latitude": 59,
            "longitude": 26
        };
        latlong["EG"] = {
            "latitude": 27,
            "longitude": 30
        };
        latlong["EH"] = {
            "latitude": 24.5,
            "longitude": -13
        };
        latlong["ER"] = {
            "latitude": 15,
            "longitude": 39
        };
        latlong["ES"] = {
            "latitude": 40,
            "longitude": -4
        };
        latlong["ET"] = {
            "latitude": 8,
            "longitude": 38
        };
        latlong["EU"] = {
            "latitude": 47,
            "longitude": 8
        };
        latlong["FI"] = {
            "latitude": 62,
            "longitude": 26
        };
        latlong["FJ"] = {
            "latitude": -18,
            "longitude": 175
        };
        latlong["FK"] = {
            "latitude": -51.75,
            "longitude": -59
        };
        latlong["FM"] = {
            "latitude": 6.9167,
            "longitude": 158.25
        };
        latlong["FO"] = {
            "latitude": 62,
            "longitude": -7
        };
        latlong["FR"] = {
            "latitude": 46,
            "longitude": 2
        };
        latlong["GA"] = {
            "latitude": -1,
            "longitude": 11.75
        };
        latlong["GB"] = {
            "latitude": 54,
            "longitude": -2
        };
        latlong["GD"] = {
            "latitude": 12.1167,
            "longitude": -61.6667
        };
        latlong["GE"] = {
            "latitude": 42,
            "longitude": 43.5
        };
        latlong["GF"] = {
            "latitude": 4,
            "longitude": -53
        };
        latlong["GH"] = {
            "latitude": 8,
            "longitude": -2
        };
        latlong["GI"] = {
            "latitude": 36.1833,
            "longitude": -5.3667
        };
        latlong["GL"] = {
            "latitude": 72,
            "longitude": -40
        };
        latlong["GM"] = {
            "latitude": 13.4667,
            "longitude": -16.5667
        };
        latlong["GN"] = {
            "latitude": 11,
            "longitude": -10
        };
        latlong["GP"] = {
            "latitude": 16.25,
            "longitude": -61.5833
        };
        latlong["GQ"] = {
            "latitude": 2,
            "longitude": 10
        };
        latlong["GR"] = {
            "latitude": 39,
            "longitude": 22
        };
        latlong["GS"] = {
            "latitude": -54.5,
            "longitude": -37
        };
        latlong["GT"] = {
            "latitude": 15.5,
            "longitude": -90.25
        };
        latlong["GU"] = {
            "latitude": 13.4667,
            "longitude": 144.7833
        };
        latlong["GW"] = {
            "latitude": 12,
            "longitude": -15
        };
        latlong["GY"] = {
            "latitude": 5,
            "longitude": -59
        };
        latlong["HK"] = {
            "latitude": 22.25,
            "longitude": 114.1667
        };
        latlong["HM"] = {
            "latitude": -53.1,
            "longitude": 72.5167
        };
        latlong["HN"] = {
            "latitude": 15,
            "longitude": -86.5
        };
        latlong["HR"] = {
            "latitude": 45.1667,
            "longitude": 15.5
        };
        latlong["HT"] = {
            "latitude": 19,
            "longitude": -72.4167
        };
        latlong["HU"] = {
            "latitude": 47,
            "longitude": 20
        };
        latlong["ID"] = {
            "latitude": -5,
            "longitude": 120
        };
        latlong["IE"] = {
            "latitude": 53,
            "longitude": -8
        };
        latlong["IL"] = {
            "latitude": 31.5,
            "longitude": 34.75
        };
        latlong["IN"] = {
            "latitude": 20,
            "longitude": 77
        };
        latlong["IO"] = {
            "latitude": -6,
            "longitude": 71.5
        };
        latlong["IQ"] = {
            "latitude": 33,
            "longitude": 44
        };
        latlong["IR"] = {
            "latitude": 32,
            "longitude": 53
        };
        latlong["IS"] = {
            "latitude": 65,
            "longitude": -18
        };
        latlong["IT"] = {
            "latitude": 42.8333,
            "longitude": 12.8333
        };
        latlong["JM"] = {
            "latitude": 18.25,
            "longitude": -77.5
        };
        latlong["JO"] = {
            "latitude": 31,
            "longitude": 36
        };
        latlong["JP"] = {
            "latitude": 36,
            "longitude": 138
        };
        latlong["KE"] = {
            "latitude": 1,
            "longitude": 38
        };
        latlong["KG"] = {
            "latitude": 41,
            "longitude": 75
        };
        latlong["KH"] = {
            "latitude": 13,
            "longitude": 105
        };
        latlong["KI"] = {
            "latitude": 1.4167,
            "longitude": 173
        };
        latlong["KM"] = {
            "latitude": -12.1667,
            "longitude": 44.25
        };
        latlong["KN"] = {
            "latitude": 17.3333,
            "longitude": -62.75
        };
        latlong["KP"] = {
            "latitude": 40,
            "longitude": 127
        };
        latlong["KR"] = {
            "latitude": 37,
            "longitude": 127.5
        };
        latlong["KW"] = {
            "latitude": 29.3375,
            "longitude": 47.6581
        };
        latlong["KY"] = {
            "latitude": 19.5,
            "longitude": -80.5
        };
        latlong["KZ"] = {
            "latitude": 48,
            "longitude": 68
        };
        latlong["LA"] = {
            "latitude": 18,
            "longitude": 105
        };
        latlong["LB"] = {
            "latitude": 33.8333,
            "longitude": 35.8333
        };
        latlong["LC"] = {
            "latitude": 13.8833,
            "longitude": -61.1333
        };
        latlong["LI"] = {
            "latitude": 47.1667,
            "longitude": 9.5333
        };
        latlong["LK"] = {
            "latitude": 7,
            "longitude": 81
        };
        latlong["LR"] = {
            "latitude": 6.5,
            "longitude": -9.5
        };
        latlong["LS"] = {
            "latitude": -29.5,
            "longitude": 28.5
        };
        latlong["LT"] = {
            "latitude": 55,
            "longitude": 24
        };
        latlong["LU"] = {
            "latitude": 49.75,
            "longitude": 6
        };
        latlong["LV"] = {
            "latitude": 57,
            "longitude": 25
        };
        latlong["LY"] = {
            "latitude": 25,
            "longitude": 17
        };
        latlong["MA"] = {
            "latitude": 32,
            "longitude": -5
        };
        latlong["MC"] = {
            "latitude": 43.7333,
            "longitude": 7.4
        };
        latlong["MD"] = {
            "latitude": 47,
            "longitude": 29
        };
        latlong["ME"] = {
            "latitude": 42.5,
            "longitude": 19.4
        };
        latlong["MG"] = {
            "latitude": -20,
            "longitude": 47
        };
        latlong["MH"] = {
            "latitude": 9,
            "longitude": 168
        };
        latlong["MK"] = {
            "latitude": 41.8333,
            "longitude": 22
        };
        latlong["ML"] = {
            "latitude": 17,
            "longitude": -4
        };
        latlong["MM"] = {
            "latitude": 22,
            "longitude": 98
        };
        latlong["MN"] = {
            "latitude": 46,
            "longitude": 105
        };
        latlong["MO"] = {
            "latitude": 22.1667,
            "longitude": 113.55
        };
        latlong["MP"] = {
            "latitude": 15.2,
            "longitude": 145.75
        };
        latlong["MQ"] = {
            "latitude": 14.6667,
            "longitude": -61
        };
        latlong["MR"] = {
            "latitude": 20,
            "longitude": -12
        };
        latlong["MS"] = {
            "latitude": 16.75,
            "longitude": -62.2
        };
        latlong["MT"] = {
            "latitude": 35.8333,
            "longitude": 14.5833
        };
        latlong["MU"] = {
            "latitude": -20.2833,
            "longitude": 57.55
        };
        latlong["MV"] = {
            "latitude": 3.25,
            "longitude": 73
        };
        latlong["MW"] = {
            "latitude": -13.5,
            "longitude": 34
        };
        latlong["MX"] = {
            "latitude": 23,
            "longitude": -102
        };
        latlong["MY"] = {
            "latitude": 2.5,
            "longitude": 112.5
        };
        latlong["MZ"] = {
            "latitude": -18.25,
            "longitude": 35
        };
        latlong["NA"] = {
            "latitude": -22,
            "longitude": 17
        };
        latlong["NC"] = {
            "latitude": -21.5,
            "longitude": 165.5
        };
        latlong["NE"] = {
            "latitude": 16,
            "longitude": 8
        };
        latlong["NF"] = {
            "latitude": -29.0333,
            "longitude": 167.95
        };
        latlong["NG"] = {
            "latitude": 10,
            "longitude": 8
        };
        latlong["NI"] = {
            "latitude": 13,
            "longitude": -85
        };
        latlong["NL"] = {
            "latitude": 52.5,
            "longitude": 5.75
        };
        latlong["NO"] = {
            "latitude": 62,
            "longitude": 10
        };
        latlong["NP"] = {
            "latitude": 28,
            "longitude": 84
        };
        latlong["NR"] = {
            "latitude": -0.5333,
            "longitude": 166.9167
        };
        latlong["NU"] = {
            "latitude": -19.0333,
            "longitude": -169.8667
        };
        latlong["NZ"] = {
            "latitude": -41,
            "longitude": 174
        };
        latlong["OM"] = {
            "latitude": 21,
            "longitude": 57
        };
        latlong["PA"] = {
            "latitude": 9,
            "longitude": -80
        };
        latlong["PE"] = {
            "latitude": -10,
            "longitude": -76
        };
        latlong["PF"] = {
            "latitude": -15,
            "longitude": -140
        };
        latlong["PG"] = {
            "latitude": -6,
            "longitude": 147
        };
        latlong["PH"] = {
            "latitude": 13,
            "longitude": 122
        };
        latlong["PK"] = {
            "latitude": 30,
            "longitude": 70
        };
        latlong["PL"] = {
            "latitude": 52,
            "longitude": 20
        };
        latlong["PM"] = {
            "latitude": 46.8333,
            "longitude": -56.3333
        };
        latlong["PR"] = {
            "latitude": 18.25,
            "longitude": -66.5
        };
        latlong["PS"] = {
            "latitude": 32,
            "longitude": 35.25
        };
        latlong["PT"] = {
            "latitude": 39.5,
            "longitude": -8
        };
        latlong["PW"] = {
            "latitude": 7.5,
            "longitude": 134.5
        };
        latlong["PY"] = {
            "latitude": -23,
            "longitude": -58
        };
        latlong["QA"] = {
            "latitude": 25.5,
            "longitude": 51.25
        };
        latlong["RE"] = {
            "latitude": -21.1,
            "longitude": 55.6
        };
        latlong["RO"] = {
            "latitude": 46,
            "longitude": 25
        };
        latlong["RS"] = {
            "latitude": 44,
            "longitude": 21
        };
        latlong["RU"] = {
            "latitude": 60,
            "longitude": 100
        };
        latlong["RW"] = {
            "latitude": -2,
            "longitude": 30
        };
        latlong["SA"] = {
            "latitude": 25,
            "longitude": 45
        };
        latlong["SB"] = {
            "latitude": -8,
            "longitude": 159
        };
        latlong["SC"] = {
            "latitude": -4.5833,
            "longitude": 55.6667
        };
        latlong["SD"] = {
            "latitude": 15,
            "longitude": 30
        };
        latlong["SE"] = {
            "latitude": 62,
            "longitude": 15
        };
        latlong["SG"] = {
            "latitude": 1.3667,
            "longitude": 103.8
        };
        latlong["SH"] = {
            "latitude": -15.9333,
            "longitude": -5.7
        };
        latlong["SI"] = {
            "latitude": 46,
            "longitude": 15
        };
        latlong["SJ"] = {
            "latitude": 78,
            "longitude": 20
        };
        latlong["SK"] = {
            "latitude": 48.6667,
            "longitude": 19.5
        };
        latlong["SL"] = {
            "latitude": 8.5,
            "longitude": -11.5
        };
        latlong["SM"] = {
            "latitude": 43.7667,
            "longitude": 12.4167
        };
        latlong["SN"] = {
            "latitude": 14,
            "longitude": -14
        };
        latlong["SO"] = {
            "latitude": 10,
            "longitude": 49
        };
        latlong["SR"] = {
            "latitude": 4,
            "longitude": -56
        };
        latlong["ST"] = {
            "latitude": 1,
            "longitude": 7
        };
        latlong["SV"] = {
            "latitude": 13.8333,
            "longitude": -88.9167
        };
        latlong["SY"] = {
            "latitude": 35,
            "longitude": 38
        };
        latlong["SZ"] = {
            "latitude": -26.5,
            "longitude": 31.5
        };
        latlong["TC"] = {
            "latitude": 21.75,
            "longitude": -71.5833
        };
        latlong["TD"] = {
            "latitude": 15,
            "longitude": 19
        };
        latlong["TF"] = {
            "latitude": -43,
            "longitude": 67
        };
        latlong["TG"] = {
            "latitude": 8,
            "longitude": 1.1667
        };
        latlong["TH"] = {
            "latitude": 15,
            "longitude": 100
        };
        latlong["TJ"] = {
            "latitude": 39,
            "longitude": 71
        };
        latlong["TK"] = {
            "latitude": -9,
            "longitude": -172
        };
        latlong["TM"] = {
            "latitude": 40,
            "longitude": 60
        };
        latlong["TN"] = {
            "latitude": 34,
            "longitude": 9
        };
        latlong["TO"] = {
            "latitude": -20,
            "longitude": -175
        };
        latlong["TR"] = {
            "latitude": 39,
            "longitude": 35
        };
        latlong["TT"] = {
            "latitude": 11,
            "longitude": -61
        };
        latlong["TV"] = {
            "latitude": -8,
            "longitude": 178
        };
        latlong["TW"] = {
            "latitude": 23.5,
            "longitude": 121
        };
        latlong["TZ"] = {
            "latitude": -6,
            "longitude": 35
        };
        latlong["UA"] = {
            "latitude": 49,
            "longitude": 32
        };
        latlong["UG"] = {
            "latitude": 1,
            "longitude": 32
        };
        latlong["UM"] = {
            "latitude": 19.2833,
            "longitude": 166.6
        };
        latlong["US"] = {
            "latitude": 38,
            "longitude": -97
        };
        latlong["UY"] = {
            "latitude": -33,
            "longitude": -56
        };
        latlong["UZ"] = {
            "latitude": 41,
            "longitude": 64
        };
        latlong["VA"] = {
            "latitude": 41.9,
            "longitude": 12.45
        };
        latlong["VC"] = {
            "latitude": 13.25,
            "longitude": -61.2
        };
        latlong["VE"] = {
            "latitude": 8,
            "longitude": -66
        };
        latlong["VG"] = {
            "latitude": 18.5,
            "longitude": -64.5
        };
        latlong["VI"] = {
            "latitude": 18.3333,
            "longitude": -64.8333
        };
        latlong["VN"] = {
            "latitude": 16,
            "longitude": 106
        };
        latlong["VU"] = {
            "latitude": -16,
            "longitude": 167
        };
        latlong["WF"] = {
            "latitude": -13.3,
            "longitude": -176.2
        };
        latlong["WS"] = {
            "latitude": -13.5833,
            "longitude": -172.3333
        };
        latlong["YE"] = {
            "latitude": 15,
            "longitude": 48
        };
        latlong["YT"] = {
            "latitude": -12.8333,
            "longitude": 45.1667
        };
        latlong["ZA"] = {
            "latitude": -29,
            "longitude": 24
        };
        latlong["ZM"] = {
            "latitude": -15,
            "longitude": 30
        };
        latlong["ZW"] = {
            "latitude": -20,
            "longitude": 30
        };

        var mapData = [{
            "code": "AF",
            "name": "Afghanistan",
            "value": 32358260,
            "color": "#eea638"
        }, {
            "code": "AL",
            "name": "Albania",
            "value": 3215988,
            "color": "#d8854f"
        }, {
            "code": "DZ",
            "name": "Algeria",
            "value": 35980193,
            "color": "#de4c4f"
        }, {
            "code": "AO",
            "name": "Angola",
            "value": 19618432,
            "color": "#de4c4f"
        }, {
            "code": "AR",
            "name": "Argentina",
            "value": 40764561,
            "color": "#86a965"
        }, {
            "code": "AM",
            "name": "Armenia",
            "value": 3100236,
            "color": "#d8854f"
        }, {
            "code": "AU",
            "name": "Australia",
            "value": 22605732,
            "color": "#8aabb0"
        }, {
            "code": "AT",
            "name": "Austria",
            "value": 8413429,
            "color": "#d8854f"
        }, {
            "code": "AZ",
            "name": "Azerbaijan",
            "value": 9306023,
            "color": "#d8854f"
        }, {
            "code": "BH",
            "name": "Bahrain",
            "value": 1323535,
            "color": "#eea638"
        }, {
            "code": "BD",
            "name": "Bangladesh",
            "value": 150493658,
            "color": "#eea638"
        }, {
            "code": "BY",
            "name": "Belarus",
            "value": 9559441,
            "color": "#d8854f"
        }, {
            "code": "BE",
            "name": "Belgium",
            "value": 10754056,
            "color": "#d8854f"
        }, {
            "code": "BJ",
            "name": "Benin",
            "value": 9099922,
            "color": "#de4c4f"
        }, {
            "code": "BT",
            "name": "Bhutan",
            "value": 738267,
            "color": "#eea638"
        }, {
            "code": "BO",
            "name": "Bolivia",
            "value": 10088108,
            "color": "#86a965"
        }, {
            "code": "BA",
            "name": "Bosnia and Herzegovina",
            "value": 3752228,
            "color": "#d8854f"
        }, {
            "code": "BW",
            "name": "Botswana",
            "value": 2030738,
            "color": "#de4c4f"
        }, {
            "code": "BR",
            "name": "Brazil",
            "value": 196655014,
            "color": "#86a965"
        }, {
            "code": "BN",
            "name": "Brunei",
            "value": 405938,
            "color": "#eea638"
        }, {
            "code": "BG",
            "name": "Bulgaria",
            "value": 7446135,
            "color": "#d8854f"
        }, {
            "code": "BF",
            "name": "Burkina Faso",
            "value": 16967845,
            "color": "#de4c4f"
        }, {
            "code": "BI",
            "name": "Burundi",
            "value": 8575172,
            "color": "#de4c4f"
        }, {
            "code": "KH",
            "name": "Cambodia",
            "value": 14305183,
            "color": "#eea638"
        }, {
            "code": "CM",
            "name": "Cameroon",
            "value": 20030362,
            "color": "#de4c4f"
        }, {
            "code": "CA",
            "name": "Canada",
            "value": 34349561,
            "color": "#a7a737"
        }, {
            "code": "CV",
            "name": "Cape Verde",
            "value": 500585,
            "color": "#de4c4f"
        }, {
            "code": "CF",
            "name": "Central African Rep.",
            "value": 4486837,
            "color": "#de4c4f"
        }, {
            "code": "TD",
            "name": "Chad",
            "value": 11525496,
            "color": "#de4c4f"
        }, {
            "code": "CL",
            "name": "Chile",
            "value": 17269525,
            "color": "#86a965"
        }, {
            "code": "CN",
            "name": "China",
            "value": 1347565324,
            "color": "#eea638"
        }, {
            "code": "CO",
            "name": "Colombia",
            "value": 46927125,
            "color": "#86a965"
        }, {
            "code": "KM",
            "name": "Comoros",
            "value": 753943,
            "color": "#de4c4f"
        }, {
            "code": "CD",
            "name": "Congo, Dem. Rep.",
            "value": 67757577,
            "color": "#de4c4f"
        }, {
            "code": "CG",
            "name": "Congo, Rep.",
            "value": 4139748,
            "color": "#de4c4f"
        }, {
            "code": "CR",
            "name": "Costa Rica",
            "value": 4726575,
            "color": "#a7a737"
        }, {
            "code": "CI",
            "name": "Cote d'Ivoire",
            "value": 20152894,
            "color": "#de4c4f"
        }, {
            "code": "HR",
            "name": "Croatia",
            "value": 4395560,
            "color": "#d8854f"
        }, {
            "code": "CU",
            "name": "Cuba",
            "value": 11253665,
            "color": "#a7a737"
        }, {
            "code": "CY",
            "name": "Cyprus",
            "value": 1116564,
            "color": "#d8854f"
        }, {
            "code": "CZ",
            "name": "Czech Rep.",
            "value": 10534293,
            "color": "#d8854f"
        }, {
            "code": "DK",
            "name": "Denmark",
            "value": 5572594,
            "color": "#d8854f"
        }, {
            "code": "DJ",
            "name": "Djibouti",
            "value": 905564,
            "color": "#de4c4f"
        }, {
            "code": "DO",
            "name": "Dominican Rep.",
            "value": 10056181,
            "color": "#a7a737"
        }, {
            "code": "EC",
            "name": "Ecuador",
            "value": 14666055,
            "color": "#86a965"
        }, {
            "code": "EG",
            "name": "Egypt",
            "value": 82536770,
            "color": "#de4c4f"
        }, {
            "code": "SV",
            "name": "El Salvador",
            "value": 6227491,
            "color": "#a7a737"
        }, {
            "code": "GQ",
            "name": "Equatorial Guinea",
            "value": 720213,
            "color": "#de4c4f"
        }, {
            "code": "ER",
            "name": "Eritrea",
            "value": 5415280,
            "color": "#de4c4f"
        }, {
            "code": "EE",
            "name": "Estonia",
            "value": 1340537,
            "color": "#d8854f"
        }, {
            "code": "ET",
            "name": "Ethiopia",
            "value": 84734262,
            "color": "#de4c4f"
        }, {
            "code": "FJ",
            "name": "Fiji",
            "value": 868406,
            "color": "#8aabb0"
        }, {
            "code": "FI",
            "name": "Finland",
            "value": 5384770,
            "color": "#d8854f"
        }, {
            "code": "FR",
            "name": "France",
            "value": 63125894,
            "color": "#d8854f"
        }, {
            "code": "GA",
            "name": "Gabon",
            "value": 1534262,
            "color": "#de4c4f"
        }, {
            "code": "GM",
            "name": "Gambia",
            "value": 1776103,
            "color": "#de4c4f"
        }, {
            "code": "GE",
            "name": "Georgia",
            "value": 4329026,
            "color": "#d8854f"
        }, {
            "code": "DE",
            "name": "Germany",
            "value": 82162512,
            "color": "#d8854f"
        }, {
            "code": "GH",
            "name": "Ghana",
            "value": 24965816,
            "color": "#de4c4f"
        }, {
            "code": "GR",
            "name": "Greece",
            "value": 11390031,
            "color": "#d8854f"
        }, {
            "code": "GT",
            "name": "Guatemala",
            "value": 14757316,
            "color": "#a7a737"
        }, {
            "code": "GN",
            "name": "Guinea",
            "value": 10221808,
            "color": "#de4c4f"
        }, {
            "code": "GW",
            "name": "Guinea-Bissau",
            "value": 1547061,
            "color": "#de4c4f"
        }, {
            "code": "GY",
            "name": "Guyana",
            "value": 756040,
            "color": "#86a965"
        }, {
            "code": "HT",
            "name": "Haiti",
            "value": 10123787,
            "color": "#a7a737"
        }, {
            "code": "HN",
            "name": "Honduras",
            "value": 7754687,
            "color": "#a7a737"
        }, {
            "code": "HK",
            "name": "Hong Kong, China",
            "value": 7122187,
            "color": "#eea638"
        }, {
            "code": "HU",
            "name": "Hungary",
            "value": 9966116,
            "color": "#d8854f"
        }, {
            "code": "IS",
            "name": "Iceland",
            "value": 324366,
            "color": "#d8854f"
        }, {
            "code": "IN",
            "name": "India",
            "value": 1241491960,
            "color": "#eea638"
        }, {
            "code": "ID",
            "name": "Indonesia",
            "value": 242325638,
            "color": "#eea638"
        }, {
            "code": "IR",
            "name": "Iran",
            "value": 74798599,
            "color": "#eea638"
        }, {
            "code": "IQ",
            "name": "Iraq",
            "value": 32664942,
            "color": "#eea638"
        }, {
            "code": "IE",
            "name": "Ireland",
            "value": 4525802,
            "color": "#d8854f"
        }, {
            "code": "IL",
            "name": "Israel",
            "value": 7562194,
            "color": "#eea638"
        }, {
            "code": "IT",
            "name": "Italy",
            "value": 60788694,
            "color": "#d8854f"
        }, {
            "code": "JM",
            "name": "Jamaica",
            "value": 2751273,
            "color": "#a7a737"
        }, {
            "code": "JP",
            "name": "Japan",
            "value": 126497241,
            "color": "#eea638"
        }, {
            "code": "JO",
            "name": "Jordan",
            "value": 6330169,
            "color": "#eea638"
        }, {
            "code": "KZ",
            "name": "Kazakhstan",
            "value": 16206750,
            "color": "#eea638"
        }, {
            "code": "KE",
            "name": "Kenya",
            "value": 41609728,
            "color": "#de4c4f"
        }, {
            "code": "KP",
            "name": "Korea, Dem. Rep.",
            "value": 24451285,
            "color": "#eea638"
        }, {
            "code": "KR",
            "name": "Korea, Rep.",
            "value": 48391343,
            "color": "#eea638"
        }, {
            "code": "KW",
            "name": "Kuwait",
            "value": 2818042,
            "color": "#eea638"
        }, {
            "code": "KG",
            "name": "Kyrgyzstan",
            "value": 5392580,
            "color": "#eea638"
        }, {
            "code": "LA",
            "name": "Laos",
            "value": 6288037,
            "color": "#eea638"
        }, {
            "code": "LV",
            "name": "Latvia",
            "value": 2243142,
            "color": "#d8854f"
        }, {
            "code": "LB",
            "name": "Lebanon",
            "value": 4259405,
            "color": "#eea638"
        }, {
            "code": "LS",
            "name": "Lesotho",
            "value": 2193843,
            "color": "#de4c4f"
        }, {
            "code": "LR",
            "name": "Liberia",
            "value": 4128572,
            "color": "#de4c4f"
        }, {
            "code": "LY",
            "name": "Libya",
            "value": 6422772,
            "color": "#de4c4f"
        }, {
            "code": "LT",
            "name": "Lithuania",
            "value": 3307481,
            "color": "#d8854f"
        }, {
            "code": "LU",
            "name": "Luxembourg",
            "value": 515941,
            "color": "#d8854f"
        }, {
            "code": "MK",
            "name": "Macedonia, FYR",
            "value": 2063893,
            "color": "#d8854f"
        }, {
            "code": "MG",
            "name": "Madagascar",
            "value": 21315135,
            "color": "#de4c4f"
        }, {
            "code": "MW",
            "name": "Malawi",
            "value": 15380888,
            "color": "#de4c4f"
        }, {
            "code": "MY",
            "name": "Malaysia",
            "value": 28859154,
            "color": "#eea638"
        }, {
            "code": "ML",
            "name": "Mali",
            "value": 15839538,
            "color": "#de4c4f"
        }, {
            "code": "MR",
            "name": "Mauritania",
            "value": 3541540,
            "color": "#de4c4f"
        }, {
            "code": "MU",
            "name": "Mauritius",
            "value": 1306593,
            "color": "#de4c4f"
        }, {
            "code": "MX",
            "name": "Mexico",
            "value": 114793341,
            "color": "#a7a737"
        }, {
            "code": "MD",
            "name": "Moldova",
            "value": 3544864,
            "color": "#d8854f"
        }, {
            "code": "MN",
            "name": "Mongolia",
            "value": 2800114,
            "color": "#eea638"
        }, {
            "code": "ME",
            "name": "Montenegro",
            "value": 632261,
            "color": "#d8854f"
        }, {
            "code": "MA",
            "name": "Morocco",
            "value": 32272974,
            "color": "#de4c4f"
        }, {
            "code": "MZ",
            "name": "Mozambique",
            "value": 23929708,
            "color": "#de4c4f"
        }, {
            "code": "MM",
            "name": "Myanmar",
            "value": 48336763,
            "color": "#eea638"
        }, {
            "code": "NA",
            "name": "Namibia",
            "value": 2324004,
            "color": "#de4c4f"
        }, {
            "code": "NP",
            "name": "Nepal",
            "value": 30485798,
            "color": "#eea638"
        }, {
            "code": "NL",
            "name": "Netherlands",
            "value": 16664746,
            "color": "#d8854f"
        }, {
            "code": "NZ",
            "name": "New Zealand",
            "value": 4414509,
            "color": "#8aabb0"
        }, {
            "code": "NI",
            "name": "Nicaragua",
            "value": 5869859,
            "color": "#a7a737"
        }, {
            "code": "NE",
            "name": "Niger",
            "value": 16068994,
            "color": "#de4c4f"
        }, {
            "code": "NG",
            "name": "Nigeria",
            "value": 162470737,
            "color": "#de4c4f"
        }, {
            "code": "NO",
            "name": "Norway",
            "value": 4924848,
            "color": "#d8854f"
        }, {
            "code": "OM",
            "name": "Oman",
            "value": 2846145,
            "color": "#eea638"
        }, {
            "code": "PK",
            "name": "Pakistan",
            "value": 176745364,
            "color": "#eea638"
        }, {
            "code": "PA",
            "name": "Panama",
            "value": 3571185,
            "color": "#a7a737"
        }, {
            "code": "PG",
            "name": "Papua New Guinea",
            "value": 7013829,
            "color": "#8aabb0"
        }, {
            "code": "PY",
            "name": "Paraguay",
            "value": 6568290,
            "color": "#86a965"
        }, {
            "code": "PE",
            "name": "Peru",
            "value": 29399817,
            "color": "#86a965"
        }, {
            "code": "PH",
            "name": "Philippines",
            "value": 94852030,
            "color": "#eea638"
        }, {
            "code": "PL",
            "name": "Poland",
            "value": 38298949,
            "color": "#d8854f"
        }, {
            "code": "PT",
            "name": "Portugal",
            "value": 10689663,
            "color": "#d8854f"
        }, {
            "code": "PR",
            "name": "Puerto Rico",
            "value": 3745526,
            "color": "#a7a737"
        }, {
            "code": "QA",
            "name": "Qatar",
            "value": 1870041,
            "color": "#eea638"
        }, {
            "code": "RO",
            "name": "Romania",
            "value": 21436495,
            "color": "#d8854f"
        }, {
            "code": "RU",
            "name": "Russia",
            "value": 142835555,
            "color": "#d8854f"
        }, {
            "code": "RW",
            "name": "Rwanda",
            "value": 10942950,
            "color": "#de4c4f"
        }, {
            "code": "SA",
            "name": "Saudi Arabia",
            "value": 28082541,
            "color": "#eea638"
        }, {
            "code": "SN",
            "name": "Senegal",
            "value": 12767556,
            "color": "#de4c4f"
        }, {
            "code": "RS",
            "name": "Serbia",
            "value": 9853969,
            "color": "#d8854f"
        }, {
            "code": "SL",
            "name": "Sierra Leone",
            "value": 5997486,
            "color": "#de4c4f"
        }, {
            "code": "SG",
            "name": "Singapore",
            "value": 5187933,
            "color": "#eea638"
        }, {
            "code": "SK",
            "name": "Slovak Republic",
            "value": 5471502,
            "color": "#d8854f"
        }, {
            "code": "SI",
            "name": "Slovenia",
            "value": 2035012,
            "color": "#d8854f"
        }, {
            "code": "SB",
            "name": "Solomon Islands",
            "value": 552267,
            "color": "#8aabb0"
        }, {
            "code": "SO",
            "name": "Somalia",
            "value": 9556873,
            "color": "#de4c4f"
        }, {
            "code": "ZA",
            "name": "South Africa",
            "value": 50459978,
            "color": "#de4c4f"
        }, {
            "code": "ES",
            "name": "Spain",
            "value": 46454895,
            "color": "#d8854f"
        }, {
            "code": "LK",
            "name": "Sri Lanka",
            "value": 21045394,
            "color": "#eea638"
        }, {
            "code": "SD",
            "name": "Sudan",
            "value": 34735288,
            "color": "#de4c4f"
        }, {
            "code": "SR",
            "name": "Suriname",
            "value": 529419,
            "color": "#86a965"
        }, {
            "code": "SZ",
            "name": "Swaziland",
            "value": 1203330,
            "color": "#de4c4f"
        }, {
            "code": "SE",
            "name": "Sweden",
            "value": 9440747,
            "color": "#d8854f"
        }, {
            "code": "CH",
            "name": "Switzerland",
            "value": 7701690,
            "color": "#d8854f"
        }, {
            "code": "SY",
            "name": "Syria",
            "value": 20766037,
            "color": "#eea638"
        }, {
            "code": "TW",
            "name": "Taiwan",
            "value": 23072000,
            "color": "#eea638"
        }, {
            "code": "TJ",
            "name": "Tajikistan",
            "value": 6976958,
            "color": "#eea638"
        }, {
            "code": "TZ",
            "name": "Tanzania",
            "value": 46218486,
            "color": "#de4c4f"
        }, {
            "code": "TH",
            "name": "Thailand",
            "value": 69518555,
            "color": "#eea638"
        }, {
            "code": "TG",
            "name": "Togo",
            "value": 6154813,
            "color": "#de4c4f"
        }, {
            "code": "TT",
            "name": "Trinidad and Tobago",
            "value": 1346350,
            "color": "#a7a737"
        }, {
            "code": "TN",
            "name": "Tunisia",
            "value": 10594057,
            "color": "#de4c4f"
        }, {
            "code": "TR",
            "name": "Turkey",
            "value": 73639596,
            "color": "#d8854f"
        }, {
            "code": "TM",
            "name": "Turkmenistan",
            "value": 5105301,
            "color": "#eea638"
        }, {
            "code": "UG",
            "name": "Uganda",
            "value": 34509205,
            "color": "#de4c4f"
        }, {
            "code": "UA",
            "name": "Ukraine",
            "value": 45190180,
            "color": "#d8854f"
        }, {
            "code": "AE",
            "name": "United Arab Emirates",
            "value": 7890924,
            "color": "#eea638"
        }, {
            "code": "GB",
            "name": "United Kingdom",
            "value": 62417431,
            "color": "#d8854f"
        }, {
            "code": "US",
            "name": "United States",
            "value": 313085380,
            "color": "#a7a737"
        }, {
            "code": "UY",
            "name": "Uruguay",
            "value": 3380008,
            "color": "#86a965"
        }, {
            "code": "UZ",
            "name": "Uzbekistan",
            "value": 27760267,
            "color": "#eea638"
        }, {
            "code": "VE",
            "name": "Venezuela",
            "value": 29436891,
            "color": "#86a965"
        }, {
            "code": "PS",
            "name": "West Bank and Gaza",
            "value": 4152369,
            "color": "#eea638"
        }, {
            "code": "VN",
            "name": "Vietnam",
            "value": 88791996,
            "color": "#eea638"
        }, {
            "code": "YE",
            "name": "Yemen, Rep.",
            "value": 24799880,
            "color": "#eea638"
        }, {
            "code": "ZM",
            "name": "Zambia",
            "value": 13474959,
            "color": "#de4c4f"
        }, {
            "code": "ZW",
            "name": "Zimbabwe",
            "value": 12754378,
            "color": "#de4c4f"
        }];


        var map;
        var minBulletSize = 3;
        var maxBulletSize = 70;
        var min = Infinity;
        var max = -Infinity;


        // get min and max values
        for (var i = 0; i < mapData.length; i++) {
            var value = mapData[i].value;
            if (value < min) {
                min = value;
            }
            if (value > max) {
                max = value;
            }
        }

        // build map
        AmCharts.ready(function() {
            AmCharts.theme = AmCharts.themes.dark;
            map = new AmCharts.AmMap();
            map.pathToImages = Metronic.getGlobalPluginsPath() + "amcharts/ammap/images/",

            map.fontFamily = 'Open Sans';
            map.fontSize = '13';
            map.color = '#888';
            
            map.addTitle("Population of the World in 2011", 14);
            map.addTitle("source: Gapminder", 11);
            map.areasSettings = {
                unlistedAreasColor: "#000000",
                unlistedAreasAlpha: 0.1
            };
            map.imagesSettings.balloonText = "<span style='font-size:14px;'><b>[[title]]</b>: [[value]]</span>";

            var dataProvider = {
                mapVar: AmCharts.maps.worldLow,
                images: []
            }

            // create circle for each country
            for (var i = 0; i < mapData.length; i++) {
                var dataItem = mapData[i];
                var value = dataItem.value;
                // calculate size of a bubble
                var size = (value - min) / (max - min) * (maxBulletSize - minBulletSize) + minBulletSize;
                if (size < minBulletSize) {
                    size = minBulletSize;
                }
                var id = dataItem.code;

                dataProvider.images.push({
                    type: "circle",
                    width: size,
                    height: size,
                    color: dataItem.color,
                    longitude: latlong[id].longitude,
                    latitude: latlong[id].latitude,
                    title: dataItem.name,
                    value: value
                });
            }

            map.dataProvider = dataProvider;

            map.write("chart_10");
        });

        $('#chart_10').closest('.portlet').find('.fullscreen').click(function() {
            map.invalidateSize();
        });
    }

    var initChartSample11 = function() {
        // svg path for target icon
        var targetSVG = "M9,0C4.029,0,0,4.029,0,9s4.029,9,9,9s9-4.029,9-9S13.971,0,9,0z M9,15.93 c-3.83,0-6.93-3.1-6.93-6.93S5.17,2.07,9,2.07s6.93,3.1,6.93,6.93S12.83,15.93,9,15.93 M12.5,9c0,1.933-1.567,3.5-3.5,3.5S5.5,10.933,5.5,9S7.067,5.5,9,5.5 S12.5,7.067,12.5,9z";
        // svg path for plane icon
        var planeSVG = "M19.671,8.11l-2.777,2.777l-3.837-0.861c0.362-0.505,0.916-1.683,0.464-2.135c-0.518-0.517-1.979,0.278-2.305,0.604l-0.913,0.913L7.614,8.804l-2.021,2.021l2.232,1.061l-0.082,0.082l1.701,1.701l0.688-0.687l3.164,1.504L9.571,18.21H6.413l-1.137,1.138l3.6,0.948l1.83,1.83l0.947,3.598l1.137-1.137V21.43l3.725-3.725l1.504,3.164l-0.687,0.687l1.702,1.701l0.081-0.081l1.062,2.231l2.02-2.02l-0.604-2.689l0.912-0.912c0.326-0.326,1.121-1.789,0.604-2.306c-0.452-0.452-1.63,0.101-2.135,0.464l-0.861-3.838l2.777-2.777c0.947-0.947,3.599-4.862,2.62-5.839C24.533,4.512,20.618,7.163,19.671,8.11z";

        var map = AmCharts.makeChart("chart_11", {
            type: "map",
            "theme": "light",
            pathToImages: Metronic.getGlobalPluginsPath() + "amcharts/ammap/images/",

            "fontFamily": 'Open Sans',
            
            "color":    '#888',
            
            dataProvider: {
                map: "worldLow",
                linkToObject: "london",
                images: [{
                        id: "london",
                        color: "#000000",
                        svgPath: targetSVG,
                        title: "London",
                        latitude: 51.5002,
                        longitude: -0.1262,
                        scale: 1.5,
                        zoomLevel: 2.74,
                        zoomLongitude: -20.1341,
                        zoomLatitude: 49.1712,

                        lines: [{
                            latitudes: [51.5002, 50.4422],
                            longitudes: [-0.1262, 30.5367]
                        }, {
                            latitudes: [51.5002, 46.9480],
                            longitudes: [-0.1262, 7.4481]
                        }, {
                            latitudes: [51.5002, 59.3328],
                            longitudes: [-0.1262, 18.0645]
                        }, {
                            latitudes: [51.5002, 40.4167],
                            longitudes: [-0.1262, -3.7033]
                        }, {
                            latitudes: [51.5002, 46.0514],
                            longitudes: [-0.1262, 14.5060]
                        }, {
                            latitudes: [51.5002, 48.2116],
                            longitudes: [-0.1262, 17.1547]
                        }, {
                            latitudes: [51.5002, 44.8048],
                            longitudes: [-0.1262, 20.4781]
                        }, {
                            latitudes: [51.5002, 55.7558],
                            longitudes: [-0.1262, 37.6176]
                        }, {
                            latitudes: [51.5002, 38.7072],
                            longitudes: [-0.1262, -9.1355]
                        }, {
                            latitudes: [51.5002, 54.6896],
                            longitudes: [-0.1262, 25.2799]
                        }, {
                            latitudes: [51.5002, 64.1353],
                            longitudes: [-0.1262, -21.8952]
                        }, {
                            latitudes: [51.5002, 40.4300],
                            longitudes: [-0.1262, -74.0000]
                        }],

                        images: [{
                            label: "Flights from London",
                            svgPath: planeSVG,
                            left: 100,
                            top: 45,
                            labelShiftY: 5,
                            color: "#CC0000",
                            labelColor: "#CC0000",
                            labelRollOverColor: "#CC0000",
                            labelFontSize: 20
                        }, {
                            label: "show flights from Vilnius",
                            left: 106,
                            top: 70,
                            labelColor: "#000000",
                            labelRollOverColor: "#CC0000",
                            labelFontSize: 11,
                            linkToObject: "vilnius"
                        }]
                    },

                    {
                        id: "vilnius",
                        color: "#000000",
                        svgPath: targetSVG,
                        title: "Vilnius",
                        latitude: 54.6896,
                        longitude: 25.2799,
                        scale: 1.5,
                        zoomLevel: 4.92,
                        zoomLongitude: 15.4492,
                        zoomLatitude: 50.2631,

                        lines: [{
                            latitudes: [54.6896, 50.8371],
                            longitudes: [25.2799, 4.3676]
                        }, {
                            latitudes: [54.6896, 59.9138],
                            longitudes: [25.2799, 10.7387]
                        }, {
                            latitudes: [54.6896, 40.4167],
                            longitudes: [25.2799, -3.7033]
                        }, {
                            latitudes: [54.6896, 50.0878],
                            longitudes: [25.2799, 14.4205]
                        }, {
                            latitudes: [54.6896, 48.2116],
                            longitudes: [25.2799, 17.1547]
                        }, {
                            latitudes: [54.6896, 44.8048],
                            longitudes: [25.2799, 20.4781]
                        }, {
                            latitudes: [54.6896, 55.7558],
                            longitudes: [25.2799, 37.6176]
                        }, {
                            latitudes: [54.6896, 37.9792],
                            longitudes: [25.2799, 23.7166]
                        }, {
                            latitudes: [54.6896, 54.6896],
                            longitudes: [25.2799, 25.2799]
                        }, {
                            latitudes: [54.6896, 51.5002],
                            longitudes: [25.2799, -0.1262]
                        }, {
                            latitudes: [54.6896, 53.3441],
                            longitudes: [25.2799, -6.2675]
                        }],

                        images: [{
                            label: "Flights from Vilnius",
                            svgPath: planeSVG,
                            left: 100,
                            top: 45,
                            labelShiftY: 5,
                            color: "#CC0000",
                            labelColor: "#CC0000",
                            labelRollOverColor: "#CC0000",
                            labelFontSize: 20
                        }, {
                            label: "show flights from London",
                            left: 106,
                            top: 70,
                            labelColor: "#000000",
                            labelRollOverColor: "#CC0000",
                            labelFontSize: 11,
                            linkToObject: "london"
                        }]
                    }, {
                        svgPath: targetSVG,
                        title: "Brussels",
                        latitude: 50.8371,
                        longitude: 4.3676
                    }, {
                        svgPath: targetSVG,
                        title: "Prague",
                        latitude: 50.0878,
                        longitude: 14.4205
                    }, {
                        svgPath: targetSVG,
                        title: "Athens",
                        latitude: 37.9792,
                        longitude: 23.7166
                    }, {
                        svgPath: targetSVG,
                        title: "Reykjavik",
                        latitude: 64.1353,
                        longitude: -21.8952
                    }, {
                        svgPath: targetSVG,
                        title: "Dublin",
                        latitude: 53.3441,
                        longitude: -6.2675
                    }, {
                        svgPath: targetSVG,
                        title: "Oslo",
                        latitude: 59.9138,
                        longitude: 10.7387
                    }, {
                        svgPath: targetSVG,
                        title: "Lisbon",
                        latitude: 38.7072,
                        longitude: -9.1355
                    }, {
                        svgPath: targetSVG,
                        title: "Moscow",
                        latitude: 55.7558,
                        longitude: 37.6176
                    }, {
                        svgPath: targetSVG,
                        title: "Belgrade",
                        latitude: 44.8048,
                        longitude: 20.4781
                    }, {
                        svgPath: targetSVG,
                        title: "Bratislava",
                        latitude: 48.2116,
                        longitude: 17.1547
                    }, {
                        svgPath: targetSVG,
                        title: "Ljubljana",
                        latitude: 46.0514,
                        longitude: 14.5060
                    }, {
                        svgPath: targetSVG,
                        title: "Madrid",
                        latitude: 40.4167,
                        longitude: -3.7033
                    }, {
                        svgPath: targetSVG,
                        title: "Stockholm",
                        latitude: 59.3328,
                        longitude: 18.0645
                    }, {
                        svgPath: targetSVG,
                        title: "Bern",
                        latitude: 46.9480,
                        longitude: 7.4481
                    }, {
                        svgPath: targetSVG,
                        title: "Kiev",
                        latitude: 50.4422,
                        longitude: 30.5367
                    }, {
                        svgPath: targetSVG,
                        title: "Paris",
                        latitude: 48.8567,
                        longitude: 2.3510
                    }, {
                        svgPath: targetSVG,
                        title: "New York",
                        latitude: 40.43,
                        longitude: -74
                    }
                ]
            },

            areasSettings: {
                unlistedAreasColor: "#FFCC00"
            },

            imagesSettings: {
                color: "#CC0000",
                rollOverColor: "#CC0000",
                selectedColor: "#000000"
            },

            linesSettings: {
                color: "#CC0000",
                alpha: 0.4
            },


            backgroundZoomsToTop: true,
            linesAboveImages: true
        });

        $('#chart_11').closest('.portlet').find('.fullscreen').click(function() {
            map.invalidateSize();
        });
    }

    var initChartSample12 = function() {
        var chartData = [];
        generateChartData();

        function generateChartData() {
            var firstDate = new Date(2012, 0, 1);
            firstDate.setDate(firstDate.getDate() - 500);
            firstDate.setHours(0, 0, 0, 0);

            for (var i = 0; i < 500; i++) {
                var newDate = new Date(firstDate);
                newDate.setDate(newDate.getDate() + i);

                var a = Math.round(Math.random() * (40 + i)) + 100 + i;
                var b = Math.round(Math.random() * 100000000);

                chartData.push({
                    date: newDate,
                    value: a,
                    volume: b
                });
            }
        }

        var chart = AmCharts.makeChart("chart_12", {
            type: "stock",
            "theme": "light",
            pathToImages: Metronic.getGlobalPluginsPath() + "amcharts/amcharts/images/",
            "fontFamily": 'Open Sans',
            
            "color":    '#888',
            dataSets: [{
                color: "#b0de09",
                fieldMappings: [{
                    fromField: "value",
                    toField: "value"
                }, {
                    fromField: "volume",
                    toField: "volume"
                }],
                dataProvider: chartData,
                categoryField: "date",
                // EVENTS
                stockEvents: [{
                    date: new Date(2010, 8, 19),
                    type: "sign",
                    backgroundColor: "#85CDE6",
                    graph: "g1",
                    text: "S",
                    description: "This is description of an event"
                }, {
                    date: new Date(2010, 10, 19),
                    type: "flag",
                    backgroundColor: "#FFFFFF",
                    backgroundAlpha: 0.5,
                    graph: "g1",
                    text: "F",
                    description: "Some longerntext can alson be added"
                }, {
                    date: new Date(2010, 11, 10),
                    showOnAxis: true,
                    backgroundColor: "#85CDE6",
                    type: "pin",
                    text: "X",
                    graph: "g1",
                    description: "This is description of an event"
                }, {
                    date: new Date(2010, 11, 26),
                    showOnAxis: true,
                    backgroundColor: "#85CDE6",
                    type: "pin",
                    text: "Z",
                    graph: "g1",
                    description: "This is description of an event"
                }, {
                    date: new Date(2011, 0, 3),
                    type: "sign",
                    backgroundColor: "#85CDE6",
                    graph: "g1",
                    text: "U",
                    description: "This is description of an event"
                }, {
                    date: new Date(2011, 1, 6),
                    type: "sign",
                    graph: "g1",
                    text: "D",
                    description: "This is description of an event"
                }, {
                    date: new Date(2011, 3, 5),
                    type: "sign",
                    graph: "g1",
                    text: "L",
                    description: "This is description of an event"
                }, {
                    date: new Date(2011, 3, 5),
                    type: "sign",
                    graph: "g1",
                    text: "R",
                    description: "This is description of an event"
                }, {
                    date: new Date(2011, 5, 15),
                    type: "arrowUp",
                    backgroundColor: "#00CC00",
                    graph: "g1",
                    description: "This is description of an event"
                }, {
                    date: new Date(2011, 6, 25),
                    type: "arrowDown",
                    backgroundColor: "#CC0000",
                    graph: "g1",
                    description: "This is description of an event"
                }, {
                    date: new Date(2011, 8, 1),
                    type: "text",
                    graph: "g1",
                    text: "Longer text can\nalso be displayed",
                    description: "This is description of an event"
                }]
            }],


            panels: [{
                title: "Value",
                percentHeight: 70,

                stockGraphs: [{
                    id: "g1",
                    valueField: "value"
                }],

                stockLegend: {
                    valueTextRegular: " ",
                    markerType: "none"
                }
            }],

            chartScrollbarSettings: {
                graph: "g1"
            },

            chartCursorSettings: {
                valueBalloonsEnabled: true,
                graphBulletSize: 1,
                valueLineBalloonEnabled:true,
                valueLineEnabled:true,
                valueLineAlpha:0.5
            },

            periodSelector: {
                periods: [{
                    period: "DD",
                    count: 10,
                    label: "10 days"
                }, {
                    period: "MM",
                    count: 1,
                    label: "1 month"
                }, {
                    period: "YYYY",
                    count: 1,
                    label: "1 year"
                }, {
                    period: "YTD",
                    label: "YTD"
                }, {
                    period: "MAX",
                    label: "MAX"
                }]
            },

            panelsSettings: {
                usePrefixes: true
            }
        });

        $('#chart_12').closest('.portlet').find('.fullscreen').click(function() {
            chart.invalidateSize();
        });
    }

    return {
        //main function to initiate the module

        init: function() {

            initChartSample1();
            initChartSample2();
            initChartSample3();
            initChartSample4();
            initChartSample5();
            initChartSample6();
            initChartSample7();
            initChartSample8();
            initChartSample9();
            initChartSample10();
            initChartSample11();
            initChartSample12();
        }

    };

}();