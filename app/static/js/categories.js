document.addEventListener('DOMContentLoaded', function () {
  // Редактирвоание категории.
  document.querySelectorAll('.edit-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      // Выбор блока, которому принадлежит кнопка.
      const block = btn.closest('.category-block');

      // Получение данных категории.
      const nameCol = block.querySelector('.cat-name');
      const colorDiv = block.querySelector('.cat-color');
      const limitCol = block.querySelector('.cat-limit');

      // Режим редактирования.
      if (btn.dataset.state !== 'editing') {
        // Сохранение текущих значений.
        const currentName = nameCol.textContent.trim();
        const currentColor = colorDiv.dataset.color;
        const currentLimit = limitCol.textContent.trim();

        // Замена полей категории на поля ввода.
        nameCol.innerHTML = `<input type="text" class="edit-name" value="${currentName}" style="width: 100%; text-align: center;">`;
        colorDiv.innerHTML = `<input type="color" class="edit-color" value="${currentColor}" style="width:100%; height:100%; border:none; padding:0;">`;
        limitCol.innerHTML = `<input type="number" class="edit-limit" value="${currentLimit}" style="width: 100%; text-align: center;">`;

        // Смена состояния кнопки на редактирование и смена текста кнопки.
        btn.dataset.state = 'editing';
        btn.textContent = btn.dataset.confirmText;
      } else {
        // Сохранения новых значений.
        const newName = block.querySelector('.edit-name').value;
        const newColor = block.querySelector('.edit-color').value;
        const newLimit = block.querySelector('.edit-limit').value;
        const oldName = block.dataset.category;

        // Подготовка параметров для отправки.
        let params = new URLSearchParams();
        params.append('old_name', oldName);
        params.append('new_name', newName);
        params.append('new_limit', newLimit);
        params.append('new_color', newColor);

        // Запрос на обновление категории.
        fetch(btn.dataset.updateUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded"
          },
          body: params
        })
          .then(response => {
            if (response.ok) {
              // Обновление изображения.
              nameCol.textContent = newName;
              colorDiv.innerHTML = "";
              colorDiv.style.backgroundColor = newColor;
              colorDiv.dataset.color = newColor;
              limitCol.textContent = newLimit;
              btn.textContent = btn.dataset.editText;
              btn.dataset.state = '';
              block.dataset.category = newName;
            } else {
              throw new Error("Ошибка обновления категории");
            }
          })
          .catch(error => {
            alert(error.message);
          });
      }
    });
  });

  // Удаление категории.
  let currentDeleteBlock = null;

  // Сохранение текущего блока, вывод блока с подтверждением удаления.
  document.querySelectorAll('.delete-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      currentDeleteBlock = btn.closest('.category-block');
      document.getElementById('deleteModal').classList.add('active');
    });
  });

  // Если удаление подтверждено.
  document.getElementById('modalYes').addEventListener('click', function () {
    if (currentDeleteBlock) {
      const categoryName = currentDeleteBlock.dataset.category;
      const deleteUrl = document.getElementById('deleteModal').dataset.deleteUrl;

      // Запрос на удаление.
      fetch(deleteUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body: "category_name=" + encodeURIComponent(categoryName)
      })
        .then(response => {
          if (response.ok) {
            // Удаление блока и очистка переменной.
            currentDeleteBlock.remove();
            currentDeleteBlock = null;
          } else {
            throw new Error("Ошибка удаления категории");
          }
        })
        .catch(error => {
          alert(error.message);
        })
        .finally(() => {
          // Закрытие блока подтверждения удаления.
          document.getElementById('deleteModal').classList.remove('active');
        });
    }
  });

  // Отмена удаления.
  document.getElementById('modalNo').addEventListener('click', function () {
    document.getElementById('deleteModal').classList.remove('active');
  });

  // Новая категория.
  const addCategoryTrigger = document.getElementById('addCategoryTrigger');
  const addCategoryForm = document.getElementById('addCategoryForm');
  const confirmAddCat = document.getElementById('confirmAddCat');
  const cancelAddCat = document.getElementById('cancelAddCat');

  // Блок с формой добавления.
  addCategoryTrigger.addEventListener('click', function () {
    addCategoryTrigger.style.display = 'none';
    addCategoryForm.style.display = 'flex';
  });

  // Скрытие блока при отмене.
  cancelAddCat.addEventListener('click', function () {
    addCategoryForm.style.display = 'none';
    addCategoryTrigger.style.display = 'block';
  });

  // Подтверждение добавления.
  confirmAddCat.addEventListener('click', function () {
    const newName = document.getElementById('newCatName').value;
    const newColor = document.getElementById('newCatColor').value;
    const newLimit = document.getElementById('newCatLimit').value;
    const addUrl = confirmAddCat.dataset.addUrl;

    // Подготовка параметров для отправки.
    let formData = new FormData();
    formData.append('name', newName);
    formData.append('limit', newLimit);
    formData.append('color', newColor);

    // Запрос добавления.
    fetch(addUrl, {
      method: "POST",
      body: formData
    })
      .then(response => {
        if (response.ok) {
          // Обновление страницы.
          location.reload();
        } else {
          throw new Error("Ошибка создания категории");
        }
      })
      .catch(error => {
        const errorBox = document.getElementById('addCatError');
        if (errorBox) {
          errorBox.style.display = 'block';
          errorBox.classList.remove('add-cat-error');
          void errorBox.offsetWidth;
          errorBox.classList.add('add-cat-error');
        }
      });
  });
});
