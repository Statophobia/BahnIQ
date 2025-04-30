var data = [
    {
      x: ['giraffes', 'orangutans', 'monkeys'],
      y: [20, 14, 23],
      type: 'bar'
    }
  ];

  var layout = {
    title: {
      text: 'Bahn stats'
    },
    font: {size: 10},
    autosize: true,
    margin: { t: 40, l: 40, r: 40, b: 40 },    
  };

  var config = {
    responsive: true
}
  
  Plotly.newPlot('myDiv', data, layout, config);


  window.onresize = function() {
    Plotly.relayout('myDiv', {
        'xaxis.autorange': true,
        'yaxis.autorange': true
    });
};