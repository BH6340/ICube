(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  // --- Chart: 优化前后性能对比 ---
  var chartEl = document.getElementById('chart-optimization');
  if (chartEl) {
    var chart = echarts.init(chartEl, null, { renderer: 'svg' });
    chart.setOption({
      animation: false,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        appendToBody: true,
        formatter: function(params) {
          var html = '<div style="font-weight:600;margin-bottom:6px;">' + params[0].name + '</div>';
          params.forEach(function(p) {
            html += '<div style="color:' + p.color + '">' + p.seriesName + ': ' + p.value + ' ms</div>';
          });
          return html;
        }
      },
      legend: {
        data: ['优化前', '优化后'],
        top: 10,
        textStyle: { color: muted, fontSize: 13 },
        itemWidth: 16,
        itemHeight: 12,
        borderRadius: 3
      },
      grid: { left: '8%', right: '5%', bottom: '10%', top: '22%', containLabel: true },
      xAxis: {
        type: 'category',
        data: ['查询耗时\n(ms)', '扫描行数\n(行)', 'SQL 次数\n(次)'],
        axisLine: { lineStyle: { color: rule } },
        axisLabel: { color: muted, fontSize: 12, lineHeight: 16 },
        axisTick: { show: false }
      },
      yAxis: {
        type: 'log',
        axisLine: { show: false },
        axisLabel: { color: muted, fontSize: 11 },
        splitLine: { lineStyle: { color: rule, type: 'dashed' } }
      },
      series: [
        {
          name: '优化前',
          type: 'bar',
          data: [2345, 128456, 21],
          itemStyle: {
            color: accent2,
            borderRadius: [4, 4, 0, 0]
          },
          barWidth: '30%'
        },
        {
          name: '优化后',
          type: 'bar',
          data: [12, 42, 3],
          itemStyle: {
            color: accent,
            borderRadius: [4, 4, 0, 0]
          },
          barWidth: '30%'
        }
      ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
  }
})();
