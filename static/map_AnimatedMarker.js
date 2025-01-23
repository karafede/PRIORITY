

/*globals L $*/

// This demo is based off of cibi.me by OpenPlans and my earlier visualization
// at http://github.com/openplans/cibi_animation

(function(){

		
  var bikeIcon = L.icon({
      iconUrl: '/static/icons8_bus.png',
      iconSize: [12, 17],  //[25, 39],
      iconAnchor: [1, 1],   //[12, 39],
      shadowUrl: null
  });




  var config = {
      //tileUrl : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      // overlayTileUrl : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
	  tileUrl : 'http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
      overlayTileUrl : 'http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
      tileAttrib : 'Routing powered by <a href="http://opentripplanner.org/">OpenTripPlanner</a>, Map tiles &copy; Development Seed and OpenStreetMap ',
	  // tileAttrib : '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>'
      initLatLng : new L.LatLng(41.90266120539129, 12.492052587659225), // ROMA
      initZoom : 11,
      minZoom : 5,
      maxZoom : 17
  };
		
  var map = L.map('map', {minZoom: config.minZoom, 
						  maxZoom: config.maxZoom}),
						  
      routeLines = routeLines_GTFS,
      markers = [];
      route_id = routes_and_trips;
	  map.addLayer(new L.TileLayer(config.tileUrl, {attribution: config.tileAttrib}));
	  map.addLayer(new L.TileLayer(config.overlayTileUrl));
	  map.setView(config.initLatLng, config.initZoom);
	 
 
  $.each(routeLines, function(i, routeLine) {
    var marker = L.animatedMarker(routeLine.getLatLngs(), {
      icon: bikeIcon,
	  route_id: route_id[i],
      autoStart: false,
      onEnd: function() {
        $(this._shadow).fadeOut();
        $(this._icon).fadeOut(3000, function(){
          map.removeLayer(this);
        });
      }
    });
	
	
    map.addLayer(marker);
	markers.push(marker);

	
	// marker.bindPopup(marker.options.route_id+"");
	 marker.bindPopup('LatLng: ' + marker.options.route_id+"");  // OK!!!, this must be repeated below...---->
	 // marker.bindPopup('LatLng: ' + marker.getLatLng());  // OK!!!, this must be repeated below...---->

	 marker.on('click', function(e){
	 // marker.on('mouseover', function(e){
      this.openPopup();
	  	    // alert("...current Lat, Lon..."+ e.latlng.lat);
			// marker.bindPopup('' + marker.getLatLng()  );    ///OK!!!!!!!!
			marker.bindPopup('' +  marker.options.route_id+""  );    ///OK!!!!!!!!
    })
	//marker.on('mouseout', function (e) {
    //        this.closePopup();
	// });	
  });




	
			
 $(function() {
  $('#start').click(function() {
    console.log('start');
    $.each(markers, function(i, marker) {
      marker.start();
    });
	
    $(this).hide();
  });
 });
}());

	

