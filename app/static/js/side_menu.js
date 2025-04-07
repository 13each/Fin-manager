document.addEventListener('DOMContentLoaded', () => {
  const sideMenu = document.getElementById('sideMenu');
  const sideMenuContainer = document.getElementById('sideMenuContainer');
  const logoutLink = document.getElementById('logoutLink');
  const logoutModal = document.getElementById('logoutModal');
  const logoutYes = document.getElementById('logoutYes');
  const logoutNo = document.getElementById('logoutNo');
  const langSwitch = document.getElementById('langSwitch');

  // Открытие меню при наведении.
  sideMenu.addEventListener('mouseenter', () => {
    sideMenuContainer.classList.add('active');
  });

  // Скрытие меню.
  sideMenuContainer.addEventListener('mouseleave', () => {
    sideMenuContainer.classList.remove('active');
  });

  // Блок подтверждения выхода.
  logoutLink.addEventListener('click', (e) => {
    e.preventDefault(); // Предотвращение перехода.
    logoutModal.classList.add('active');
  });

  // Нажатие на "Нет", закрытие блока.
  logoutNo.addEventListener('click', () => {
    logoutModal.classList.remove('active');
  });

  // Нажатие на "Да", выход.
  logoutYes.addEventListener('click', () => {
    window.location.href = logoutLink.getAttribute('href');
  });

  // Смена языка
  langSwitch?.addEventListener('click', (e) => {
    e.preventDefault(); // Предотвращение перехода.
    // Запрос на смену языка.
    fetch(langSwitch.getAttribute('href'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    .then(() => window.location.reload()) // Перезагрузка страницы после смены.
    .catch(() => alert('Error switching language'));
  });
});
