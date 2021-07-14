function getjump(doc,s,i)
    {
    $.ajax(
        {
        type: 'GET',
        url: "/jump/"+s+"."+i,
        success: function(response)
            {
            // var initialisation block
            var ctx = doc.getElementById('acc-chart').getContext('2d');
            var json = jQuery.parseJSON(response);
            var borders = json.br;

            document.getElementById("jd0").innerHTML = (borders[1]- borders[0]) + " мсек.";
            document.getElementById("jd1").innerHTML = borders[0]/1000 + " - " + borders[1]/1000;

            document.getElementById("rd0").innerHTML = (json.g.reduce((a,b) => a + b, 0) / json.g.length).toFixed(3) + " об/сек";
            document.getElementById("rd1").innerHTML = "max: " + Math.max.apply(null, json.g)  + " об/сек";

            document.getElementById("rсd0").innerHTML = json.rc + " оборотов";

            var Chart_a = new Chart(ctx,
                {
                type: 'line',
                data:
                    {
                    labels: json.t,
                    datasets:
                        [
                            {
                            data: json.a,
                            borderWidth: 2,
                            borderColor: '#7571f9',
                            pointRadius: 0,
                            }
                        ]
                    },
                options:
                    {
                    legend:
                        {
                        display: false
                        },
                    annotation:
                        {
                        drawTime: 'afterDatasetsDraw',
                        annotations:
                            [
                                {
                                    type: "line",
                                    mode: "vertical",
                                    scaleID: "x-axis-0",
                                    value: borders[0],
                                    borderWidth: 2,
                                    borderDash: [2, 2],
                                    borderColor: '#ec0c38',
                                },
                                {
                                    type: "line",
                                    mode: "vertical",
                                    scaleID: "x-axis-0",
                                    value: borders[1],
                                    borderWidth: 2,
                                    borderDash: [2, 2],
                                    borderColor: '#ec0c38',
                                }
                            ]
                        }
                    }
                }
            );

            // var initialisation block
            var ctx = doc.getElementById('gir-chart').getContext('2d');
            var Chart_g = new Chart(ctx,
                {
                type: 'line',
                data:
                    {
                    labels: json.t,
                    datasets:[
                        {
                        data: json.g,
                        borderWidth: 2,
                        borderColor: '#ec0c38',
                        pointRadius: 0,
                        }
                    ]
                },
                options:
                    {
                    legend:
                        {
                        display: false
                        },
                    annotation:
                        {
                        drawTime: 'afterDatasetsDraw',
                        annotations:
                            [
                                {
                                    type: "line",
                                    mode: "vertical",
                                    scaleID: "x-axis-0",
                                    value: borders[0],
                                    borderWidth: 2,
                                    borderDash: [2, 2],
                                    borderColor: '#7571f9',
                                },
                                {
                                    type: "line",
                                    mode: "vertical",
                                    scaleID: "x-axis-0",
                                    value: borders[1],
                                    borderWidth: 2,
                                    borderDash: [2, 2],
                                    borderColor: '#7571f9',
                                }
                            ]
                        }
                    }
                }
            );
            }
        });
    }

