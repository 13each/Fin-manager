document.addEventListener("DOMContentLoaded", function () {
  // Получение данных для диаграммы.
  const chartWrapper = document.getElementById("chart-wrapper");

  // Парсинг значений.
  const data = JSON.parse(chartWrapper.dataset.chart);
  const bgColors = JSON.parse(chartWrapper.dataset.bgColors);
  const categoryLabels = JSON.parse(chartWrapper.dataset.labels);
  const legendData = JSON.parse(chartWrapper.dataset.legend);

  // Настройка размеров и центра диаграммы.
  const viewWidth = 500, viewHeight = 500, offset = 10;
  const centerX = viewWidth / 2 + offset;
  const centerY = viewHeight / 2 + offset;
  const fullRadius = Math.min(viewWidth, viewHeight) / 2;

  // Создание SVG-группы для диаграммы.
  const svg = d3.select("#chart")
                .attr("width", viewWidth)
                .attr("height", viewHeight)
                .append("g")
                .attr("transform", `translate(${centerX}, ${centerY})`) // Центр диаграммы - центр SVG.
                .style("filter", "url(#dropShadow)");

  // Обработка данных каждой категории.
  let dataset = [];
  for (let i = 0; i < categoryLabels.length; i++) {
    let clampedSpent = data[i * 2]; // Потрачено
    let total = data[i * 2] + data[i * 2 + 1]; // Лимит.
    dataset.push({
      category: categoryLabels[i],
      diagramSpent: clampedSpent,
      total: total,
      color: bgColors[i * 2]
    });
  }

  // Сортировка категорий.
  const sorted = dataset.slice().sort((a, b) => {
    const ratioA = a.total > 0 ? a.diagramSpent / a.total : 0;
    const ratioB = b.total > 0 ? b.diagramSpent / b.total : 0;
    return ratioA - ratioB;
  });

  // Сортировка для хорошего внешнего вида (пустые не рядом с пустыми, полные не рядом с полными).
  const interleave = [];
  let l = 0, r = sorted.length - 1;
  while (l <= r) {
    if (l === r) interleave.push(sorted[l]);
    else {
      interleave.push(sorted[l], sorted[r]);
    }
    l++;
    r--;
  }

  // Подготовка для отрисовки дуг.
  const pie = d3.pie().value(d => d.total).sort(null);
  const arcs = pie(dataset); // Углы дуг.

  // Отрисовка дуг (spent).
  svg.selectAll(".arcSpent")
     .data(arcs)
     .enter()
     .append("path")
     .attr("class", "arcSpent")
     .attr("fill", d => d.data.color)
     .attr("d", d3.arc().innerRadius(0).outerRadius(0)) // Начало с 0 радиусом для анимации.
     .transition()
     .duration(1500)
     .ease(d3.easeCubicInOut)
     .attrTween("d", function (d) {
       // Вычисление % закраски.
       const fillFraction = d.data.total > 0 ? Math.min(d.data.diagramSpent / d.data.total, 1) : 0;
       const targetRadius = fullRadius * fillFraction;
       const interpolate = d3.interpolate(0, targetRadius); // Анимация от 0 до нужного радиуса.
       const arcGen = d3.arc().innerRadius(0).cornerRadius(8); // Генератор дуги.
       return function (t) {
           return arcGen.outerRadius(interpolate(t))(d); // Плавное увеличение радиуса дуги.
       };
     });

  // Добавление обводки.
  svg.selectAll(".arcOutline")
     .data(arcs)
     .enter()
     .append("path")
     .attr("class", "arcOutline")
     .attr("d", d3.arc().innerRadius(0).outerRadius(fullRadius));

  // Легенда.
  const legendList = d3.select("#legend-list"); // Получение данных для легенды.

  // Создание блоков для категорий.
const legendItems = legendList.selectAll(".legend-item")
    .data(legendData)
    .enter()
    .append("div")
    .attr("class", "legend-item")
    .style("opacity", 0)
    .style("transform", "translateY(-20px)");

  // Цвет.
  legendItems.append("div")
    .attr("class", "legend-color")
    .style("background-color", d => d.color);

  // Потрачено / Лимит.
  legendItems.append("div")
    .text(d => `${d.category}: ${d.spent} / ${d.limit}`);

  // Анимация появления категорий.
  legendItems.transition()
    .duration(500)
    .delay((_, i) => i * 200)
    .style("opacity", 1)
    .style("transform", "translateY(0px)");

  // Кнопка свернуть / развернуть.
  const toggleBtn = document.getElementById("toggleLegend");
  const legendListContainer = document.getElementById("legend-list");
  let expanded = true;

  toggleBtn.addEventListener("click", () => {
    legendListContainer.style.maxHeight = expanded ? "0px" : "240px";
    toggleBtn.textContent = expanded ? "+" : "−";
    expanded = !expanded;
  });
});
