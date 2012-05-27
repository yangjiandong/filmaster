$(document).ready(function() {
    var confirmed = null;
    var marker = null;
    var lat = lng = 0;
    var map = null;
    var point = null;
    
    var infowindow=null;

    function change_on_enter(ev) {
        if(ev.keyCode == 13) {
            $(this).change();
            return false;
        }
        return true;
    }
    function country_change() {
        $('#id_location').val('');
        var country_code=$(this).val();
        $.getJSON('http://api.geonames.org/searchJSON?username='+settings.GEONAMES_USERNAME+'&callback=?&featureCode=PPLC&country='+country_code, function(data) {
            if(!data.geonames.length) return;
            data = data.geonames[0];
            var pt = new google.maps.LatLng(data.lat, data.lng);
            setLocation(pt, 6);
        });
    }
    function location_change() {
        var c = new google.maps.Geocoder();
        c.geocode({address:$(this).val()},function(o) {
                if(!o.length) return;
                setLocation(o[0].geometry.location);
                map.fitBounds(o[0].geometry.bounds);
        })
    }
    function locationChanged(point, pt) {
        if(point && FM.geo.distance(pt, point)<10) return false;
        if(confirmed!=null) return confirmed;
        return (confirmed=confirm(gettext('New location detected. Should we use it as your new default?')));
    }
    tm = null;
    function update_fields(point) {
        $("#id_latitude").val(point.lat().toFixed(6));
        $("#id_longitude").val(point.lng().toFixed(6));
        clearTimeout(tm);
        tm = setTimeout(function() {
            FM.geo.cities_around(point, 15, function(data) {
                if(data.geonames.length>0) {
                        var name = data.geonames[0].name;
                        if(name=='Warsaw') name='Warszawa';
                        $('#id_location').val(name);
                        $('#id_country').val(data.geonames[0].countrycode);
                }
            });
            /*
            FM.geo.timezone(point, function(data) {
                $('#id_timezone_id').val(data.timezoneId);
            })*/

        }, 1000)
    }
    marker=null;
    function setLocation(pt, zoom) {
        map.panTo(pt);
        if(zoom) map.setZoom(zoom);
        if(!marker) {
            marker = new google.maps.Marker({position:pt, map:map});
            marker.setDraggable(true);
            google.maps.event.addListener(marker, 'position_changed', function() {
                update_fields(this.position)
            });
            google.maps.event.addListener(marker, 'dragstart', function() {
                $('#id_location').val('');
                infowindow && infowindow.close();
            });
        } else {
            marker.setPosition(pt);
        }
        return marker;
    }

    window.usersettings_map_init = function() {
        var current_location, detected_location, zoom;
        $('#map').show()
        if ($("#id_latitude").val() && $("#id_longitude").val()) {
            lat = $("#id_latitude").val();
            lng = $("#id_longitude").val();
            current_location = new google.maps.LatLng(lat, lng)
        } else {
            // TODO
            current_location = null;
        }
        var DEFAULT_ZOOM = 12;
        var LOW_ZOOM = 8
        var zoom = DEFAULT_ZOOM;

        if(window.geo && (geo.latitude || geo.longitude)) {
            detected_location = new google.maps.LatLng(geo.latitude, geo.longitude)
        } else {
            if(settings.MAIN_CITY) {
                detected_location = new google.maps.LatLng(settings.MAIN_CITY['latitude'], settings.MAIN_CITY['longitude'])
            } else {
                detected_location = new google.maps.LatLng(52, 22);
            }
            zoom = LOW_ZOOM
        }

        $("#id_country").change(country_change).keydown(change_on_enter)
        $("#id_location").change(location_change).keydown(change_on_enter)

        map = new google.maps.Map(document.getElementById("map"), {
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            disableDoubleClickZoom: true,
        });

        google.maps.event.addListener(map, 'dblclick', function(ev) {
            $('#id_location').val('');
            infowindow && infowindow.close();
            setLocation(ev.latLng);
        });
        if(!current_location) {
            map.setCenter(detected_location)
            setLocation(detected_location, zoom)
            update_fields(detected_location)
            infowindow = new google.maps.InfoWindow({
                content:gettext("Autodetected location"),
                position:detected_location
            })
            infowindow.open(map);
        } else {
            map.setCenter(current_location)
            setLocation(current_location, zoom)
        }
        var initial_tiles_loaded = false;
        google.maps.event.addListener(map, 'tilesloaded', function(ev) {
            if(!initial_tiles_loaded && current_location) {
                setTimeout(function() {
                    var dist = FM.geo.distance(current_location, detected_location)
                    if(dist > 0.5) {
                        var bounds = new google.maps.LatLngBounds();
                        bounds.extend(current_location);
                        bounds.extend(detected_location);
                        map.fitBounds(bounds)

                        var content = gettext("Autodetected location. <a href='#' class='sl'>Click to change</a>.")
                        infowindow = new google.maps.InfoWindow({
                                content: content,
                                position: detected_location,
                            })
                        google.maps.event.addListener(infowindow, 'domready', function() {
                            $('a.sl').click(function() {
                                    setLocation(detected_location, Math.max(map.getZoom(), zoom));
                                    update_fields(detected_location);
                                    infowindow.close();
                                    return false;
                            });
                        });

                    infowindow.open(map)
                    } else {
                        map.panTo(detected_location);
                    }
                }, 1000);
            }
            initial_tiles_loaded=true;
        });
    }
    $.getScript("http://maps.google.com/maps/api/js?sensor=false&callback=usersettings_map_init");
});
