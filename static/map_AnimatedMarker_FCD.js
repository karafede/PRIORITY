

/*globals L $*/

// This demo is based off of cibi.me by OpenPlans and my earlier visualization
// at http://github.com/openplans/cibi_animation


(function(){

		
  var bikeIcon = L.icon({
      iconUrl: '/static/icons8-purple-circle-48.png',
      iconSize: [6, 6],  //[25, 39],  [16, 22],
      iconAnchor: [1, 1],   //[12, 39],
      shadowUrl: null
  });
  


  var config = {
      tileUrl : 'http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
      overlayTileUrl : 'http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
      tileAttrib :  '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
      initLatLng : new L.LatLng(41.90266120539129, 12.492052587659225), // ROMA
      initZoom : 11,
      minZoom : 5,
      maxZoom : 17
  };
		
  var map = L.map('map', {minZoom: config.minZoom, 
						  maxZoom: config.maxZoom}),
						  
      routeLines = route_FCD,
      markers = [];
      //route_id = trip_FCD_params;
	  map.addLayer(new L.TileLayer(config.tileUrl, {attribution: config.tileAttrib}));
	  map.addLayer(new L.TileLayer(config.overlayTileUrl));
	  map.setView(config.initLatLng, config.initZoom);
	  // const ZMU_zones_Layer = L.layerGroup();	 
 
  $.each(routeLines, function(i, routeLine) {
    var marker = L.animatedMarker(routeLine.getLatLngs(), {
      icon: bikeIcon,
	  //route_id: route_id[i],
      autoStart: false,
    //onEnd: function() {
     //   $(this._shadow).fadeOut();
     //   $(this._icon).fadeOut(3000, function(){
     //   map.removeLayer(this);
     //   });
    //}
    });
	
	
	//alert(marker);
	// alert(routeLines);
    map.addLayer(marker);
	markers.push(marker);


	

	
	 //marker.bindPopup('LatLng: ' + marker.options.route_id+"");  // OK!!!, this must be repeated below...---->

	 marker.on('mouseover', function(e){
      this.openPopup();
	  	    // alert("...current Lat, Lon..."+ e.latlng.lat);
			//marker.bindPopup('' +  marker.options.route_id+""  );    ///OK!!!!!!!!
    })
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

	

