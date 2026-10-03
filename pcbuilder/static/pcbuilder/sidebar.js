(() => {
    for (const accordion of document.querySelectorAll("[data-accordion]")) {
        const trigger = accordion.querySelector(".sidebar-accordion-trigger");
        const panel = accordion.querySelector(".sidebar-accordion-panel");
        if (!trigger || !panel) continue;

        if (!panel.hidden) {
            accordion.classList.add("is-open");
            trigger.setAttribute("aria-expanded", "true");
            panel.style.maxHeight = `${panel.scrollHeight}px`;
            panel.style.opacity = "1";
        }

        trigger.addEventListener("click", () => {
            const isOpen = trigger.getAttribute("aria-expanded") === "true";
            if (isOpen) {
                panel.style.maxHeight = `${panel.scrollHeight}px`;
                requestAnimationFrame(() => {
                    panel.style.maxHeight = "0px";
                    panel.style.opacity = "0";
                    panel.addEventListener("transitionend", () => {
                        if (trigger.getAttribute("aria-expanded") === "false") panel.hidden = true;
                    }, { once: true });
                });
                accordion.classList.remove("is-open");
                trigger.setAttribute("aria-expanded", "false");
                return;
            }

            panel.hidden = false;
            panel.style.maxHeight = "0px";
            panel.style.opacity = "0";
            accordion.classList.add("is-open");
            trigger.setAttribute("aria-expanded", "true");
            requestAnimationFrame(() => {
                panel.style.maxHeight = `${panel.scrollHeight}px`;
                panel.style.opacity = "1";
                panel.addEventListener("transitionend", () => {
                    if (trigger.getAttribute("aria-expanded") === "true") {
                        panel.style.maxHeight = `${panel.scrollHeight}px`;
                    }
                }, { once: true });
            });
        });
    }

    for (const buildButton of document.querySelectorAll("[data-select-url]")) {
        buildButton.addEventListener("click", async () => {
            if (buildButton.disabled || buildButton.classList.contains("is-active")) return;
            buildButton.disabled = true;
            try {
                const response = await fetch(buildButton.dataset.selectUrl, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || "Не удалось выбрать сборку.");
                const catalogUrl = new URL(window.location.href);
                catalogUrl.searchParams.set("build", "active");
                window.location.assign(catalogUrl.toString());
            } catch (error) {
                buildButton.disabled = false;
                buildButton.title = error.message;
            }
        });
    }
})();