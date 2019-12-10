const apiUrl = "%%OPENCITY_API_ENDPOINT%%";

const OpenLocationCode = require('open-location-code').OpenLocationCode;
const openLocationCode = new OpenLocationCode();

function render_buildings(data) {
	$("#results").empty();
	$.each(data, function (index, item) {
		let row = $("<tr/>");
		row.append($("<td/>").text(index + 1));
		row.append($("<td/>").text(item['ubid']));
		row.append($("<td/>").text(item['state']));
		row.append($("<td/>").text(item['height']));
		row.append($("<td/>").text(item['area']));
		$("#results").append(row);
	})
}

function request_buildings(e) {
	e.preventDefault();
	const code = openLocationCode.encode(parseFloat($("#lat").val()), parseFloat($("#lon").val()), 9);
	const request = {
		"lat": $("#lat").val(),
		"lon": $("#lon").val(),
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
$(function () {
	console.log("Loaded")
	$("#request-buildings").on('click', request_buildings)
	$("#nyc").on('click', function (e) {
		e.preventDefault();
		$("#lat").val("40.722437");
		$("#lon").val("-73.997313");
	})
})