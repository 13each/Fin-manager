function sanitizeId(str) {
  return str.replace(/[^a-zA-Z0-9_-]/g, "");
}

document.addEventListener("DOMContentLoaded", function () {
  const chartWrapper = document.getElementById("chart-wrapper");
  const data = JSON.parse(chartWrapper.dataset.chart);
  const bgColors = JSON.parse(chartWrapper.dataset.bgColors);
  const categoryLabels = JSON.parse(chartWrapper.dataset.labels);
  const legendData = JSON.parse(chartWrapper.dataset.legend);

  const viewWidth = 500, viewHeight = 500, offset = 10;
  const centerX = viewWidth / 2 + offset;
  const centerY = viewHeight / 2 + offset;
  const fullRadius = Math.min(viewWidth, viewHeight) / 2;

  const svg = d3.select("#chart")
                .attr("width", viewWidth)
                .attr("height", viewHeight)
                .append("g")
                .attr("transform", `translate(${centerX}, ${centerY})`)
                .style("filter", "url(#dropShadow)");

  let dataset = [];
  for (let i = 0; i < categoryLabels.length; i++) {
    let clampedSpent = data[i * 2];
    let total = data[i * 2] + data[i * 2 + 1];
    dataset.push({
      category: categoryLabels[i],
      diagramSpent: clampedSpent,
      total: total,
      color: bgColors[i * 2]
    });
  }

  const pie = d3.pie().value(d => d.total).sort(null);
  const arcs = pie(dataset);

  svg.selectAll(".arcSpent")
     .data(arcs)
     .enter()
     .append("path")
     .attr("class", "arcSpent")
     .attr("fill", d => d.data.color)
     .attr("d", d3.arc().innerRadius(0).outerRadius(0))
     .transition()
     .duration(1500)
     .ease(d3.easeCubicInOut)
     .attrTween("d", function (d) {
       const fillFraction = d.data.total > 0 ? Math.min(d.data.diagramSpent / d.data.total, 1) : 0;
       const targetRadius = fullRadius * fillFraction;
       const interpolate = d3.interpolate(0, targetRadius);
       const arcGen = d3.arc().innerRadius(0).cornerRadius(8);
       return function (t) {
         return arcGen.outerRadius(interpolate(t))(d);
       };
     });

  svg.selectAll(".arcOutline")
     .data(arcs)
     .enter()
     .append("path")
     .attr("class", "arcOutline")
     .attr("d", d3.arc().innerRadius(0).outerRadius(fullRadius));

  const legendList = d3.select("#legend-list");
  const legendItems = legendList.selectAll(".legend-item")
    .data(legendData)
    .enter()
    .append("div")
    .attr("class", "legend-item")
    .style("margin-bottom", "8px");

  legendItems.append("div")
    .attr("class", "legend-color")
    .style("background-color", d => d.color);

  legendItems.append("div")
    .text(d => `${d.category}: ${d.spent} / ${d.limit}`);

  const toggleBtn = document.getElementById("toggleLegend");
  const legendListContainer = document.getElementById("legend-list");
  let expanded = true;
  toggleBtn.addEventListener("click", function () {
    if (expanded) {
      legendListContainer.style.maxHeight = "0px";
      toggleBtn.textContent = "+";
    } else {
      legendListContainer.style.maxHeight = "240px";
      toggleBtn.textContent = "−";
    }
    expanded = !expanded;
  });
});