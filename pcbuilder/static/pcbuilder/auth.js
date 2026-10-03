(() => {
    const dialog = document.getElementById("auth-modal");
    if (!dialog) return;

    const message = document.getElementById("auth-message");
    const tabs = [...document.querySelectorAll("[data-auth-tab]")];
    const panels = [...document.querySelectorAll("[data-auth-panel]")];

    for (const button of document.querySelectorAll("[data-open-auth]")) {
        button.addEventListener("click", () => {
            dialog.dataset.checkoutPending = "false";
            message.textContent = "";
            dialog.showModal();
        });
    }

    for (const tab of tabs) {
        tab.addEventListener("click", () => {
            const selectedTab = tab.dataset.authTab;
            for (const candidate of tabs) {
                const active = candidate === tab;
                candidate.classList.toggle("is-active", active);
                candidate.setAttribute("aria-selected", String(active));
            }
            for (const panel of panels) panel.hidden = panel.dataset.authPanel !== selectedTab;
            message.textContent = "";
        });
    }

    document.getElementById("auth-close").addEventListener("click", () => {
        dialog.dataset.checkoutPending = "false";
        dialog.close();
    });
    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) {
            dialog.dataset.checkoutPending = "false";
            dialog.close();
        }
    });

    for (const form of panels) {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const submit = form.querySelector(".auth-submit");
            submit.disabled = true;
            message.textContent = "Проверяем данные...";
            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new URLSearchParams(new FormData(form)),
                    headers: {
                        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });
                const result = await response.json();
                if (!response.ok || !result.success) {
                    const errors = result.errors || ["Не удалось выполнить запрос."];
                    const errorList = Array.isArray(errors) ? errors : Object.values(errors).flat();
                    throw new Error(errorList.join(" "));
                }

                message.textContent = `Вход выполнен: ${result.username}`;
                const checkoutPending = dialog.dataset.checkoutPending === "true";
                dialog.close();
                if (checkoutPending) {
                    window.location.assign("/checkout/");
                } else {
                    window.location.reload();
                }
            } catch (error) {
                message.textContent = error.message;
            } finally {
                submit.disabled = false;
            }
        });
    }

    if (new URLSearchParams(window.location.search).get("auth") === "required") {
        dialog.dataset.checkoutPending = "true";
        dialog.showModal();
    }
})();