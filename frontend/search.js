document.addEventListener('DOMContentLoaded', () => {
  // Создаем выпадающий блок один раз прямо в body
  const dropdown = document.createElement('div');
  dropdown.className = 'autocomplete-dropdown';
  dropdown.style.cssText = `
    position: fixed !important;
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    max-height: 280px !important;
    overflow-y: auto !important;
    z-index: 999999 !important;
    display: none;
    box-shadow: 0 10px 25px rgba(0,0,0,0.3) !important;
  `;
  document.body.appendChild(dropdown);

  let currentFocus = -1;
  let abortController = null;
  let activeInput = null;

  function debounce(func, delay = 200) {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), delay);
    };
  }

  function updateDropdownPosition(input) {
    if (!input) return;
    
    // Ищем родительский контейнер .search-bar или .catalog-search, чтобы дропдаун был по ширине всей строки поиска
    const searchBarContainer = input.closest('.search-bar') || input.closest('.catalog-search') || input;
    const rect = searchBarContainer.getBoundingClientRect();
    
    dropdown.style.top = `${rect.bottom + 6}px`;
    dropdown.style.left = `${rect.left}px`;
    dropdown.style.width = `${rect.width}px`;
  }

  async function fetchSuggestions(query, input) {
    if (!query || query.length < 2) {
      dropdown.style.display = 'none';
      currentFocus = -1;
      return;
    }

    if (abortController) {
      abortController.abort();
    }
    abortController = new AbortController();

    activeInput = input;
    updateDropdownPosition(input);
    dropdown.innerHTML = '<div style="padding: 12px 16px; color: var(--text-muted); font-size: 0.85rem;">Поиск...</div>';
    dropdown.style.display = 'block';

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/waste/?search=${encodeURIComponent(query)}`, {
        signal: abortController.signal
      });
      const data = await response.json();
      const list = Array.isArray(data) ? data : (data.results || []);

      if (list.length === 0) {
        dropdown.innerHTML = '<div style="padding: 12px 16px; color: var(--text-muted); font-size: 0.85rem;">Ничего не найдено</div>';
        dropdown.style.display = 'block';
        return;
      }

      const itemsToRender = list.slice(0, 6);
      currentFocus = -1;

      dropdown.innerHTML = itemsToRender.map((item, index) => `
        <a href="waste.html?id=${item.id}" class="autocomplete-item" data-index="${index}" style="
          padding: 12px 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          cursor: pointer;
          color: var(--text-main);
          text-decoration: none;
          font-size: 0.9rem;
          border-bottom: 1px solid var(--border-color);
          background-color: transparent;
        ">
          <span>${item.name}</span>
          <span style="font-size: 0.75rem; color: var(--text-muted); background: var(--bg-card-hover); padding: 2px 8px; border-radius: 4px;">${item.category}</span>
        </a>
      `).join('');

      updateDropdownPosition(input);
      dropdown.style.display = 'block';

      const links = dropdown.querySelectorAll('.autocomplete-item');
      links.forEach((link, idx) => {
        link.addEventListener('mouseenter', () => {
          currentFocus = idx;
          updateActiveItem(links);
        });
        link.addEventListener('mouseleave', () => {
          link.style.backgroundColor = 'transparent';
        });
      });

    } catch (err) {
      if (err.name === 'AbortError') return;
      console.warn('Ошибка автокомплита:', err);
      dropdown.style.display = 'none';
    }
  }

  function updateActiveItem(links) {
    links.forEach((link, idx) => {
      if (idx === currentFocus) {
        link.style.backgroundColor = 'var(--bg-card-hover)';
      } else {
        link.style.backgroundColor = 'transparent';
      }
    });
  }

  const debouncedFetch = debounce((query, input) => {
    fetchSuggestions(query, input);
  }, 200);

  document.addEventListener('input', (e) => {
    if (e.target.matches('input[type="text"], input[type="search"], .search-bar__input, .catalog-search__input')) {
      debouncedFetch(e.target.value.trim(), e.target);
    }
  });

  window.addEventListener('resize', () => {
    if (dropdown.style.display === 'block' && activeInput) updateDropdownPosition(activeInput);
  });
  window.addEventListener('scroll', () => {
    if (dropdown.style.display === 'block' && activeInput) updateDropdownPosition(activeInput);
  });

  document.addEventListener('keydown', (e) => {
    const links = dropdown.querySelectorAll('.autocomplete-item');
    if (!links.length || dropdown.style.display === 'none') return;

    if (e.key === 'ArrowDown') {
      currentFocus++;
      if (currentFocus >= links.length) currentFocus = 0;
      updateActiveItem(links);
      e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      currentFocus--;
      if (currentFocus < 0) currentFocus = links.length - 1;
      updateActiveItem(links);
      e.preventDefault();
    } else if (e.key === 'Enter') {
      if (currentFocus > -1 && links[currentFocus]) {
        e.preventDefault();
        window.location.href = links[currentFocus].href;
      }
    } else if (e.key === 'Escape') {
      dropdown.style.display = 'none';
    }
  });

  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && !e.target.matches('input[type="text"], input[type="search"], .search-bar__input, .catalog-search__input')) {
      dropdown.style.display = 'none';
    }
  });
});