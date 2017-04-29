(function(document, ajax, Chart) {
	"use strict";

	var charts = [],
		timeFormat = "MM/DD/YY h:mm:ss a",
		chartDatasetLabels = {
			power: 'Power',
			temperature: 'Temperature'
		},
		chartYAxesLabels = {
			power: 'On/Off',
			temperature: 'Temperature (F)'
		};

	function KeezerChart(sensorid, description, type, chart) {
		var self = this,
			timespan = 300;

		self.sensorid = sensorid;
		self.description = description;
		self.type = type;
		self.chart = chart;

		self.getData = function() {
			ajax('api/readings', { data: { timespan: timespan, sensorid: self.sensorid }}).then(function (data) {
				var dataset = {};
				dataset.label = chartDatasetLabels[self.type];
				dataset.fill = false;
				dataset.data = data.map(function (d) {
					return {
						x: moment.unix(d.time).format(timeFormat),
						y: d.value
					};
				});
				if (self.type === 'power') {
					dataset.lineTension = 0;
					dataset.fill = true;
				}
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
				var chartElement = document.createElement('canvas'), chart, chartOptions;
				chartElement.id = "chart-" + sensor.sensorid;
				container.appendChild(chartElement);
				chartOptions = {
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
									labelString: chartYAxesLabels[sensor.sensortype]
								}
							}]
						}
					}
				};
				if (sensor.sensortype === 'power') {
					chartOptions.options.scales.yAxes[0].ticks = {
						callback: function(value, index, values) {
							if (value === 0) {
								return 'Off';
							} else if (value === 1) {
								return 'On';
							}
							return value;
						},
						min: 0,
						max: 1,
						stepSize: 1
					};
				}
				chart = new Chart(chartElement.getContext('2d'), chartOptions);
				return new KeezerChart(sensor.sensorid, sensor.description, sensor.sensortype, chart);
			});
			charts.forEach(function (chart) {
				chart.getData();
			});
		});
	});
}(window.document, $.ajax, Chart));
