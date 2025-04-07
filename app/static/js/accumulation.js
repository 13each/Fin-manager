document.addEventListener("DOMContentLoaded", function () {
  // Получение данных цели накопления.
  const dataEl = document.getElementById("accumulation-data");

  // Проверка, если цель у пользователя.
  const hasAccumulation = dataEl?.dataset.accumulation === "true";
  // Парсинг значений.
  const finalPercent = parseFloat(dataEl?.dataset.percent || 0);
  const finalAccumulated = parseFloat(dataEl?.dataset.accumulated || 0);
  const total = parseFloat(dataEl?.dataset.total || 0);
  const lang = dataEl?.dataset.lang || "en";
  const goalName = dataEl?.dataset.goalName || "";

  // Анимация роста чисел с нуля.
  function animateValue(element, start, end, duration, formatter) {
    let startTimestamp = null;

    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      element.innerText = formatter(start + progress * (end - start));

      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    };

    window.requestAnimationFrame(step);
  }

  if (hasAccumulation) {
    const progressFillEl = document.getElementById("progressFill");
    const progressPercentageEl = document.getElementById("progressPercentage");
    const goalInfoEl = document.getElementById("goalInfo");

    // Время увеличения значений.
    setTimeout(() => {
      progressFillEl.style.width = finalPercent + "%";
    }, 100);

    // Анимация процентов и накопленной суммы.
    animateValue(progressPercentageEl, 0, finalPercent, 1000, (value) => Math.round(value) + "%");
    animateValue(goalInfoEl, 0, finalAccumulated, 1000, (value) => Math.round(value) + " / " + total);

    // Мотивационные сообщения.
    const motivationalMessages = {
      en: {
        low: [
          "Every journey starts with a single step.",
          "Small beginnings lead to big endings.",
          "Keep going – you're on the path!",
          "You're planting the seeds of success.",
          "The start is always the hardest."
        ],
        mid: [
          "Keep pushing – you're halfway there!",
          "You're making great progress!",
          "The road is long, but you're moving fast.",
          "Momentum is on your side.",
          "You're closer than you think."
        ],
        high: [
          "Just a little more – the finish line is near!",
          "Almost there – don’t give up now!",
          "Final push – you've got this!",
          "Your goal is within reach!",
          "Stay strong – you're almost done!"
        ],
        complete: [
          "Goal achieved – amazing work!",
          "You did it!",
          "Success! Now on to the next one.",
          "Mission accomplished.",
          "Your dedication paid off!"
        ]
      },
      ru: {
        low: [
          "Ты только начинаешь — отличный старт!",
          "Первый шаг уже сделан!",
          "Начало положено, продолжай!",
          "Главное — начать. Ты справился!",
          "Маленькие шаги ведут к большим победам!"
        ],
        mid: [
          "Дорогу осилит идущий!",
          "Уже на полпути – не останавливайся!",
          "Отличный прогресс, так держать!",
          "Ты движешься в правильном направлении!",
          "Цель становится ближе с каждым шагом!"
        ],
        high: [
          "Осталось совсем немного!",
          "Ты почти у цели!",
          "Последний рывок – и ты победил!",
          "В финальной прямой!",
          "Не сдавайся – победа рядом!"
        ],
        complete: [
          "Цель достигнута – поздравляем!",
          "Ты справился – отличная работа!",
          "Невероятный результат – цель достигнута!",
          "Поздравляем с успешным завершением!",
          "Финал достигнут – ты молодец!"
        ]
      }
    };

    // Определение отрезка для мотивационного сообщения.
    let messageCategory = 'low';
    if (finalPercent >= 100) {
      messageCategory = 'complete';
    } else if (finalPercent >= 75) {
      messageCategory = 'high';
    } else if (finalPercent >= 25) {
      messageCategory = 'mid';
    }

    // Отображение случайного сообщения из подходящего отрезка.
    const messages = motivationalMessages[lang][messageCategory];
    const randomIndex = Math.floor(Math.random() * messages.length);
    document.getElementById("motivationalMessage").textContent = messages[randomIndex];
  }

  // Блок добавления суммы.
  const addMoneyBtn = document.getElementById("addMoneyBtn");
  const addMoneyBlock = document.getElementById("addMoneyBlock");
  const cancelMoneyBtn = document.getElementById("cancelMoneyBtn");
  const confirmMoneyBtn = document.getElementById("confirmMoneyBtn");

  // Открытие.
  addMoneyBtn?.addEventListener("click", () => addMoneyBlock?.classList.add("show"));

  // Закрытие.
  cancelMoneyBtn?.addEventListener("click", () => addMoneyBlock?.classList.remove("show"));

  // Отправка суммы на сервер и перезагрузка страницы.
  confirmMoneyBtn?.addEventListener("click", () => {
    const amount = document.getElementById("addMoneyInput").value;
    fetch("/add_money", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: "amount=" + encodeURIComponent(amount)
    })
    .then((res) => res.ok ? location.reload() : Promise.reject())
    .catch(() => alert("Error adding money"));
  });

  // Блок редактирования цели.
  const editGoalBtn = document.getElementById("editGoalBtn");
  const editGoalBlock = document.getElementById("editGoalBlock");
  const cancelGoalBtn = document.getElementById("cancelGoalBtn");
  const confirmGoalBtn = document.getElementById("confirmGoalBtn");
  const deleteGoalBtn = document.getElementById("deleteGoalBtn");
  const editGoalNameInput = document.getElementById("editGoalName");
  const editGoalTotalInput = document.getElementById("editGoalTotal");

  // Открытие.
  editGoalBtn?.addEventListener("click", () => editGoalBlock?.classList.add("show"));

  // Закрытие.
  cancelGoalBtn?.addEventListener("click", () => editGoalBlock?.classList.remove("show"));

  // Отправка новых данных о цели накопления и перезагрузка страницы.
  confirmGoalBtn?.addEventListener("click", () => {
    const newGoalName = editGoalNameInput.value;
    const newTotal = editGoalTotalInput.value;
    const params = new URLSearchParams();
    params.append("new_goal_name", newGoalName);
    params.append("new_total", newTotal);

    fetch("/update_goal", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: params
    })
    .then((res) => res.ok ? location.reload() : Promise.reject())
    .catch(() => alert("Error updating goal"));
  });

  // Блок подтверждения удаления.
  deleteGoalBtn?.addEventListener("click", () => {
    document.getElementById("deleteGoalModal")?.classList.add("active");
  });

  // Отправка запроса удаления.
  document.getElementById("modalGoalYes")?.addEventListener("click", () => {
    fetch("/delete_goal", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      }
    })
    .then((res) => res.ok ? location.reload() : Promise.reject())
    .catch(() => alert("Error deleting goal"));
  });

  // Отмена удаления.
  document.getElementById("modalGoalNo")?.addEventListener("click", () => {
    document.getElementById("deleteGoalModal")?.classList.remove("active");
  });
});
