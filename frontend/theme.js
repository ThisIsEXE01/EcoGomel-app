document.addEventListener('DOMContentLoaded', () => {
  const themeToggleBtn = document.getElementById('theme-toggle');
  const currentTheme = localStorage.getItem('theme');

  // Установка начальной темы из localstorage или по умолчанию
  if (currentTheme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
    if (themeToggleBtn) themeToggleBtn.innerHTML = '<img src="sun.png" alt="Светлая тема" class="theme-icon">';
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
    
    // ========================================================
    // ИСПРАВЛЕНИЕ БАГА: 
    // Раньше здесь не хватало открывающего тега '<'. 
    // Из-за этого браузер выводил текст 'img src="..."' прямо на экран, 
    // ломая верстку кнопки и иконки.
    // Теперь добавлен символ '<' в начале строки, и иконка отображается корректно.
    // ========================================================
    if (themeToggleBtn) themeToggleBtn.innerHTML = '<img src="moon.png" alt="Тёмная тема" class="theme-icon">';
  }

  // Переключение темы при клике
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      let theme = document.documentElement.getAttribute('data-theme');

      if (theme === 'light') {
        // Переключаем на тёмную
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        themeToggleBtn.innerHTML = '<img src="moon.png" alt="Тёмная тема" class="theme-icon">';
      } else {
        // Переключаем на светлую
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        themeToggleBtn.innerHTML = '<img src="sun.png" alt="Светлая тема" class="theme-icon">';
      }
    });
  }
});
