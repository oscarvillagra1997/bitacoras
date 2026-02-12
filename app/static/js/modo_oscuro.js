document.addEventListener("DOMContentLoaded", () => {

    const themeButtons = document.querySelectorAll("[data-theme-value]");
    const body = document.body;
    const currentIcon = document.getElementById("current-theme-icon");
    window.sunIcon  = `${window.APP_BASE}/static/icons/brightness-high.svg`;
    window.moonIcon = `${window.APP_BASE}/static/icons/moon-fill.svg`;

    function applyTheme(theme) {
        if (theme === "dark") {
            body.classList.add("dark-mode");
            currentIcon.innerHTML = `<img src="${window.moonIcon}" width="20" height="20">`;
        } 
        else if (theme === "light") {
            body.classList.remove("dark-mode");
            currentIcon.innerHTML = `<img src="${window.sunIcon}" width="20" height="20">`;
        } 
        localStorage.setItem("theme", theme);
    }

    // Inicializar
    const savedTheme = localStorage.getItem("theme") || "auto";
    applyTheme(savedTheme);
    
    // Cambiar tema con click
    themeButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const theme = btn.getAttribute("data-theme-value");
            applyTheme(theme);
        });
    });

});




        