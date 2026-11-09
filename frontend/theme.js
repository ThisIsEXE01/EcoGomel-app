document.addEventListener('DOMContentLoaded', () => {
  const themeToggleBtn = document.getElementById('theme-toggle');

  // Функция для обновления иконки
  function updateThemeIcon(theme) {
    if (!themeToggleBtn) return;
    if (theme === 'light') {
      themeToggleBtn.innerHTML = '<img src="sun.svg" alt="Светлая тема" class="theme-icon" style="width:20px; height:20px; pointer-events:none;">';
    } else {
      themeToggleBtn.innerHTML = '<img src="moon.svg" alt="Тёмная тема" class="theme-icon" style="width:20px; height:20px; pointer-events:none;">';
    }
  }

  // Устанавливаем иконку при загрузке на основе текущего атрибута HTML
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
  updateThemeIcon(currentTheme);

  // Клик по кнопке переключения
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const activeTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = activeTheme === 'light' ? 'dark' : 'light';

      // Применяем тему к тегу <html>
      document.documentElement.setAttribute('data-theme', newTheme);
      // Сохраняем в постоянную память браузера
      localStorage.setItem('theme', newTheme);
      
      updateThemeIcon(newTheme);
    });
  }
});