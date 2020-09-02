window.chartIOsColors = {
    red: 'rgb(255, 99, 132)',
    orange: 'rgb(255, 159, 64)',
    yellow: 'rgb(255, 205, 86)',
    green: 'rgb(75, 192, 192)',
    blue: 'rgb(54, 162, 235)',
    purple: 'rgb(153, 102, 255)',
    grey: 'rgb(201, 203, 207)'
};

var $ios_config = {
    type: 'pie',
    data: {
        datasets: [{
            data: [0,0,0,0],
            backgroundColor: [
                window.chartIOsColors.grey,
                window.chartIOsColors.green,
                window.chartIOsColors.orange,
                window.chartIOsColors.red,
            ],
            label: 'IO Status'
        }],
        labels: [
            "Untested",
            "Done",
            "Repeat",
            "Removed"
        ]
    },
    options: {
        responsive: true,
        legend: {
            display: true,
            position: 'right'
        },
        tooltips: {
            callbacks: {
                label: function(tooltipItem, data) {
                    var allData = data.datasets[tooltipItem.datasetIndex].data;
                    var tooltipLabel = data.labels[tooltipItem.index];
                    var tooltipData = allData[tooltipItem.index];
                    var total = 0;
                    for (var i in allData) {
                        total += allData[i];
                    }
                    var tooltipPercentage = Math.round((tooltipData / total) * 100);
                    return tooltipLabel + ': ' + tooltipData + ' (' + tooltipPercentage + '%)';
                }
            }
        }
    }
};

function chartIOsData() {
    $.get(pid + '/api/ios/stats/', function (res) {
            $ios_config.data.datasets[0].data = JSON.parse(res)
            window.myPie.update();
        });
    };

function getIOsChart() {
    var ctx = document.getElementById("ios-chart-area").getContext("2d");
    window.myPie = new Chart(ctx, $ios_config);
    chartIOsData();
};