(function () {
    const root = document.documentElement;
    const saved = localStorage.getItem("credlytic-theme");

    if (saved === "dark") {
        root.classList.add("dark-mode");
    }

    window.toggleTheme = function () {
        root.classList.toggle("dark-mode");

        if (root.classList.contains("dark-mode")) {
            localStorage.setItem("credlytic-theme", "dark");
        } else {
            localStorage.setItem("credlytic-theme", "light");
        }
    };
})();
