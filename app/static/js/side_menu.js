document.addEventListener('DOMContentLoaded', () => {
  const sideMenu = document.getElementById('sideMenu');
  const sideMenuContainer = document.getElementById('sideMenuContainer');
  const logoutLink = document.getElementById('logoutLink');
  const logoutModal = document.getElementById('logoutModal');
  const logoutYes = document.getElementById('logoutYes');
  const logoutNo = document.getElementById('logoutNo');
  const langSwitch = document.getElementById('langSwitch');

  sideMenu.addEventListener('mouseenter', () => {
    sideMenuContainer.classList.add('active');
  });

  sideMenuContainer.addEventListener('mouseleave', () => {
    sideMenuContainer.classList.remove('active');
  });

  logoutLink.addEventListener('click', (e) => {
    e.preventDefault();
    logoutModal.classList.add('active');
  });

  logoutNo.addEventListener('click', () => {
    logoutModal.classList.remove('active');
  });

  logoutYes.addEventListener('click', () => {
    window.location.href = logoutLink.getAttribute('href');
  });

  langSwitch?.addEventListener('click', (e) => {
    e.preventDefault();
    fetch(langSwitch.getAttribute('href'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    .then(() => window.location.reload())
    .catch(() => alert('Error switching language'));
  });
});
