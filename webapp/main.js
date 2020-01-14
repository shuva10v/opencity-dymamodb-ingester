const apiUrl = "%%OPENCITY_API_ENDPOINT%%";

const OpenLocationCode = require('open-location-code').OpenLocationCode;
const openLocationCode = new OpenLocationCode();
const highlightStyle = {
	color: '#ff0000',
	fillColor: '#00ff00'
};

function render_buildings(data) {
	$.each(data, function (index, item) {
		if (!known.has(item['ubid'])) {
			var featureGroup = L.featureGroup([])
				.addTo(map);
			featureGroup.on('click', function(e) {
				$("#obj-info").show();
				$("#results").empty();
				$("#history").empty();
				let row = $("<tr/>");
				row.append($("<td/>").text("UBID"));
				row.append($("<td/>").text(item['ubid']));
				$("#results").append(row);
				row = $("<tr/>");
				row.append($("<td/>").text("Height"));
				row.append($("<td/>").text(item['height']));
				$("#results").append(row);
				row = $("<tr/>");
				row.append($("<td/>").text("Area"));
				row.append($("<td/>").text(item['area']));
				$("#results").append(row);
				row = $("<tr/>");
				row.append($("<td/>").text("Last Edited"));
				row.append($("<td/>").text(item['last_updated']));
				$("#results").append(row);

				$("#add-tag").on('click', function(e) {
						$('#comments').modal('show')
						$('#save-comment').on('click', function (e) {
							e.preventDefault();
							add_tag(item['grid'], item['ubid'], $('#key').val(), $('#value').val());
							featureGroup.setStyle(highlightStyle);
						})
					}
				);
				if (item['updated']) {
					load_history(item['ubid']);
				}
			});

			var wkt = new Wkt.Wkt();
			wkt.read(item['fp']);
			featureGroup.addLayer(wkt.toObject());
			if (item['updated']) {
				featureGroup.setStyle(highlightStyle);
			}
			known.add(item['ubid']);
		}
	})
}

function render_history(data) {
	$("#obj-info").show();
	$("#history").empty();
	$.each(data, function (index, item) {
		let row = $("<tr/>");
		row.append($("<td/>").text(item['key']));
		row.append($("<td/>").text(item['value']));
		row.append($("<td/>").text(new Date(item['timestamp'] / 1000)));
		row.append($("<td/>").text(item['ip']));

		$("#history").append(row);
	})
}

function add_tag(grid, ubid, key, value) {
	const request = {
		"grid": grid,
		"ubid": ubid,
		"key": key,
		"value": value,
	};
	$.ajax({
		url: apiUrl + "/tags/add",
		type: "POST",
		data: JSON.stringify(request),
		contentType: "application/json; charset=utf-8",
		success: function (e) {
			console.log("Added!");
			$('#comments').modal('hide');
			load_history(ubid);
		}
	});

}

function render_objects(data) {
	$.each(data, function (index, item) {
		if (!known.has(item['ubid'])) {
			var marker = L.marker([item['lat'], item['lon']]).addTo(map);
			var popup = "";
			if (item['amenity']) {
				popup = "<b>" + item['amenity']+ "</b>";
			}
			if (item['name']) {
				popup += "<br/><i>" + item['name']+ "</i>";
			}
			if (item['website']) {
				popup += "<br/><a target='_blank' href='" + item['website'] + "'>link</a>";
			}
			if (item['source']) {
				popup += "<br/><a target='_blank' href='" + item['source'] + "'>link</a>";
			}
			marker.bindPopup(popup);
			known.add(item['ubid']);
		}
	})
}

function request_buildings() {
	var center = map.getBounds().getCenter();
	const code = openLocationCode.encode(center.lat, center.lng, 9);
	const request = {
		"lat": center.lat,
		"lon": center.lng,
		"code": code
	}
	$.ajax({
		url: apiUrl + "/buildings/get",
		type: "POST",
		data: JSON.stringify(request),
		dataType : "json",
		contentType: "application/json; charset=utf-8",
		success: render_buildings
	});
}

function load_history(ubid) {
	const request = {
		"ubid": ubid
	}
	$.ajax({
		url: apiUrl + "/tags/get",
		type: "POST",
		data: JSON.stringify(request),
		dataType : "json",
		contentType: "application/json; charset=utf-8",
		success: render_history
	});
}


function request_objects_nearby() {
	var center = map.getBounds().getCenter();
	console.log(center);
	const request = {
		"lat": center.lat,
		"lon": center.lng
	}
	$.ajax({
		url: apiUrl + "/objects/get",
		type: "POST",
		data: JSON.stringify(request),
		dataType : "json",
		contentType: "application/json; charset=utf-8",
		success: render_objects
	});
}

var map;

var known = new Set();

$(function () {
	console.log("Loaded")
	const ny_lat = 40.722437;
	const ny_lon = -73.997313;
	map = L.map('mapid').setView([ny_lat, ny_lon], 19);

	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
	}).addTo(map);

	L.marker([ny_lat, ny_lon]).addTo(map);

	map.on('moveend', function(e) {
		request_objects_nearby();
		request_buildings();
	});
	request_objects_nearby();
	request_buildings();
})