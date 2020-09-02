window.chartDevicesColors = {
    red: 'rgb(255, 99, 132)',
    orange: 'rgb(255, 159, 64)',
    yellow: 'rgb(255, 205, 86)',
    green: 'rgb(75, 192, 192)',
    blue: 'rgb(54, 162, 235)',
    purple: 'rgb(153, 102, 255)',
    grey: 'rgb(201, 203, 207)'
};

var $devices_config = {
    type: 'bar',
    data: {
        datasets: [{
            data: [0,0,0,0,0],
            backgroundColor: window.chartDevicesColors.purple,
            label: 'Device Status'
        }],
        labels: [
            "Equipment",
            "Conduit",
            "Wires Pulled",
            "Field",
            "Panel"
        ]
    },
    options: {
        maintainAspectRatio: true,
        responsive: true,
        legend: {
            display: true,
            position: 'bottom'
        },
        scales: {
            yAxes: [{
                display: true,
                ticks: {
                    suggestedMin: 0,    // minimum will be 0, unless there is a lower value.
                    max: 100
                }
            }]
        }
    },

};

function chartDevicesData() {
    $.get(pid + '/api/devices/stats/', function (res) {
            $devices_config.data.datasets[0].data = JSON.parse(res)
            window.myBar.update();
        });
    };

function getDeviceChart() {
    // TODO should pass some config data to this function and override the config
    var ctx = document.getElementById("devices-chart-area").getContext("2d");
    window.myBar = new Chart(ctx, $devices_config);
    chartDevicesData();
};