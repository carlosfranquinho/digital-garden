function switchTheme() {
  const currentStyle = currentTheme()
  if (currentStyle === 'light') {
    setTheme('dark')
    setIconTheme('dark')
  } else {
    setTheme('light')
    setIconTheme('light')
  }

  // Atualiza a imagem da borboleta depois da mudança de tema
  setTimeout(() => {
    const butterfly = document.getElementById('theme-butterfly');
    if (butterfly) {
      const isDark = document.documentElement.getAttribute('data-color-mode') === 'dark';
      butterfly.src = isDark ? '/images/borboleta-dia.png' : '/images/borboleta-noite.png';
    }
  }, 100);
}


function setTheme(style) {
  document.querySelectorAll('.isInitialToggle').forEach(elem => {
    elem.classList.remove('isInitialToggle');
  });
  document.documentElement.setAttribute('data-color-mode', style);
  localStorage.setItem('data-color-mode', style);
}

function setIconTheme(theme) {
  const twitterIconElement = document.getElementById('twitter-icon');
  const githubIconElement = document.getElementById('github-icon');

  if (twitterIconElement) {
    twitterIconElement.setAttribute("fill", theme === 'light' ? "black" : "white");
  }

  if (githubIconElement) {
    if (theme === 'light') {
      githubIconElement.removeAttribute('color');
      githubIconElement.removeAttribute('class');
    } else {
      githubIconElement.setAttribute('class', 'octicon');
      githubIconElement.setAttribute('color', '#f0f6fc');
    }
  }
}

function currentTheme() {
  const localStyle = localStorage.getItem('data-color-mode');
  const systemStyle = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  return localStyle || systemStyle;
}

function updateButterfly(theme) {
  const butterfly = document.getElementById('theme-butterfly');
  if (butterfly) {
    butterfly.src = theme === 'dark'
      ? '/images/borboleta-dia.png'
      : '/images/borboleta-noite.png';
  }
}

// Aplica tema e borboleta ao carregar
(() => {
  const theme = currentTheme();
  setTheme(theme);
  updateButterfly(theme);
})();
