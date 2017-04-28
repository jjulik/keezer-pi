(function(document, ajax, Chart) {
	"use strict";

	var charts = [],
		timeFormat = "MM/DD/YY h:mm:ss a";

	function KeezerChart(sensorid, description, chart) {
		var self = this,
			timespan = 300;

		self.sensorid = sensorid;
		self.description = description;
		self.chart = chart;

		self.getData = function() {
			ajax('api/readings', { data: { timespan: timespan, sensorid: self.sensorid }}).then(function (data) {
				var dataset = {};
				dataset.label = "Temperature";
				dataset.data = data.map(function (d) {
					return {
						x: moment.unix(d.time).format(timeFormat),
						y: d.value
					};
				});
				self.chart.data.datasets = [];
				self.chart.data.datasets.push(dataset);
				self.chart.update();
			});
		};

		return self;
	}

	document.addEventListener("DOMContentLoaded", function() {
		ajax('api/sensors').then(function(sensors) {
			var container = document.getElementById('chartContainer');
			charts = sensors.map(function (sensor) {
				var chartElement = document.createElement('canvas'), chart;
				chartElement.id = "chart-" + sensor.sensorid;
				chartElement.width = 400;
				chartElement.height = 400;
				container.appendChild(chartElement);
				chart = new Chart(chartElement.getContext("2d"), {
					type: 'line',
					data: {
						datasets: []
					},
					options: {
						title: {
							display: true,
							text: sensor.description
						},
						scales: {
							xAxes: [{
								type: 'time',
								display: true,
								time: {
									format: timeFormat,
								},
								scaleLabel: {
									display: true,
									labelString: 'Time'
								}
							}],
							yAxes: [{
								display: true,
								scaleLabel: {
									display: true,
									labelString: 'Temperature (F)'
								}
							}]
						}
					}
				});
				return new KeezerChart(sensor.sensorid, sensor.description, chart);
			});
			charts.forEach(function (chart) {
				chart.getData();
			});
		});
	});
}(window.document, $.ajax, Chart));
