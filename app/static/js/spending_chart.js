document.addEventListener("DOMContentLoaded", () => {
  // Блок добавления траты.
  const newSpendingBtn = document.getElementById("newSpendingBtn");
  const newSpendingModal = document.getElementById("newSpendingModal");
  const closeModalBtn = document.getElementById("closeModalBtn");

  newSpendingBtn.addEventListener("click", () => newSpendingModal.classList.add("show"));

  closeModalBtn.addEventListener("click", () => newSpendingModal.classList.remove("show"));

  // Выпадающий список категорий для выбора.
  const customSelect = document.getElementById("customSelect");
  const selectedOption = customSelect.querySelector(".selected-option");
  const optionsContainer = customSelect.querySelector(".options-container");
  const hiddenInput = document.getElementById("ns-category");

  // Открытие / закрытие списка при нажатии.
  customSelect.addEventListener("click", (e) => {
    customSelect.classList.toggle("open");
    e.stopPropagation();
  });

  // Вставка текста и закрытие при выборе категории.
  document.querySelectorAll(".option").forEach(option => {
    option.addEventListener("click", (e) => {
      selectedOption.textContent = option.textContent;
      hiddenInput.value = option.dataset.value;
      customSelect.classList.remove("open");
      e.stopPropagation();
    });
  });

  // Закрытие при клике вне списка.
  document.addEventListener("click", (e) => {
    if (!customSelect.contains(e.target)) {
      customSelect.classList.remove("open");
    }
  });

  // Flash-сообщение о добавлении траты.
  const successMessage = document.getElementById("successMessage");
  if (successMessage.classList.contains("show")) {
    setTimeout(() => {
      successMessage.classList.remove("show");
    }, 3000);
  }

  // Диаграмма.
  const categoriesData = window.categoriesData;

  // Отбрасываем категории без лимита.
  const categoryNames = Object.keys(categoriesData).filter(cat => categoriesData[cat].limit > 0);

  // Сортировка категорий.
  const sorted = categoryNames.slice().sort((a, b) => {
    const ratioA = categoriesData[a].spent / categoriesData[a].limit;
    const ratioB = categoriesData[b].spent / categoriesData[b].limit;
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

  // Выбор цвета по имени.
  const color = cat => categoriesData[cat].color || "#000";

  // Подготовка для отрисовки дуг.
  const pie = d3.pie().value(cat => categoriesData[cat].limit).sort(null);
  const arcs = pie(interleave); // Углы дуг.

  // Отрисовка дуг (spent).
  svg.selectAll(".arcSpent")
    .data(arcs)
    .enter()
    .append("path")
    .attr("class", "arcSpent")
    .attr("fill", d => color(d.data))
    .attr("d", d3.arc().innerRadius(0).outerRadius(0)) // Начало с 0 радиусом для анимации.
    .transition()
    .duration(1500)
    .ease(d3.easeCubicInOut)
    .attrTween("d", function(d) {
      // Вычисление % закраски.
      const ratio = Math.min(categoriesData[d.data].spent / categoriesData[d.data].limit, 1);
      const interpolate = d3.interpolate(0, fullRadius * ratio); // Анимация от 0 до нужного радиуса.
      const arc = d3.arc().innerRadius(0).cornerRadius(8); // Генератор дуги.
      return t => arc.outerRadius(interpolate(t))(d); // Плавное увеличение радиуса дуги.
    });

  // Добавление обводки.
  svg.selectAll(".arcOutline")
    .data(arcs)
    .enter()
    .append("path")
    .attr("class", "arcOutline")
    .attr("fill", "none")
    .attr("stroke", "rgba(100,100,100,0.8)")
    .attr("stroke-width", 2.5)
    .attr("stroke-linecap", "round")
    .attr("stroke-linejoin", "round")
    .attr("d", d3.arc().innerRadius(0).outerRadius(fullRadius));

  // Легенда.
  const legendList = d3.select("#legend-list"); // Получение данных для легенды.

  // Создание блоков для категорий.
  const legendItems = legendList.selectAll(".legend-item")
    .data(interleave)
    .enter()
    .append("div")
    .attr("class", "legend-item")
    .style("opacity", 0)
    .style("transform", "translateY(-20px)");

  // Цвет.
  legendItems.append("div")
    .attr("class", "legend-color")
    .style("background-color", d => color(d));

  // Потрачено / Лимит.
  legendItems.append("div")
    .text(d => `${d}: ${categoriesData[d].spent} / ${categoriesData[d].limit}`);

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
