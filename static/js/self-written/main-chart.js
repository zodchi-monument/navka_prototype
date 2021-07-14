function get_trend(doc, s, i)
    {
    $.ajax(
        {
        type: 'GET',
        url: "/trend/"+s,
        success: function(response)
            {
            // var initialisation block
            var ctx = doc.getElementById('main-chart').getContext('2d');
            var json = jQuery.parseJSON(response);

            var cascades = json.cascades.x.map((x, i) => { return {x: x, y: json.cascades.y[i]}; });
            var raw = json.raw.x.map((x, i) => { return {x: x, y: json.raw.y[i]}; });
            var jmp = json.jmp_points.x.map((x, i) => { return {x: x, y: json.jmp_points.y[i]}; });

            var selected = []
            if (jmp.length>0)
                {
                 selected = [jmp[i]]
                }

            var my1Chart = new Chart(ctx,
                {
                type: 'line',
                data:
                    {
                    labels: json.labels,
                    datasets:
                        [
                            {
                            data: raw,
                            borderWidth: 2,
                            pointRadius: 0,
                            pointHitRadius: 0,
                            },
                            {
                            borderColor: '#7571f9',
                            data: cascades,
                            fill: true,
                            borderWidth: 1,
                            pointRadius: 0,
                            pointHitRadius: 0,
                            },
                            {
                            type: 'scatter',
                            borderColor: '#ec0c38',
                            showLine: false,
                            pointRadius: 4,
                            hoverRadius: 4,
                            data: jmp,
                            },
                            {
                            type: 'scatter',
                            borderColor: '#ec0c38',
                            backgroundColor: '#ec0c38',
                            showLine: false,
                            pointRadius: 4,
                            hoverRadius: 4,
                            data: selected
                            }
                        ]
                    },
                options:
                    {
                    legend:
                        {
                        display: false
                        },
                    hover:
                        {
                        mode: null,
                        intersect: false
                        },
                    animation: {
                        duration: 0
                        },
                    elements: {
                        line: {
                            tension: 0
                            }
                        }
                    }
                });
            }
        });
    }
