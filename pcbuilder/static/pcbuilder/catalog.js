(() => {
    const products = JSON.parse(document.getElementById("component-data").textContent);
    const productById = new Map(products.map((product) => [String(product.id), product]));
    const cards = [...document.querySelectorAll(".product-card")];
    const preview = document.getElementById("preview-content");
    const search = document.getElementById("product-search");
    const currentCount = document.getElementById("build-count");
    const currentTotal = document.getElementById("build-total");
    const sortForm = document.getElementById("sort-form");
    const sortSelect = document.getElementById("sort-select");
    const cartOpen = document.getElementById("cart-open");
    const cartDialog = document.getElementById("cart-modal");
    const cartItems = document.getElementById("cart-items");
    const cartSaveBuild = document.getElementById("cart-save-build");
    const cartCheckout = document.getElementById("cart-checkout");
    const checkoutDialog = document.getElementById("checkout-modal");
    const checkoutForm = document.getElementById("checkout-form");
    const authDialog = document.getElementById("auth-modal");
    let selectedProduct = null;

    const labels = {
        socket: "Socket",
        cores: "Cores",
        threads: "Threads",
        base_clock: "Base Clock",
        boost_clock: "Boost Clock",
        turbo_clock: "Turbo Clock",
        tdp: "TDP",
        memory_type: "Memory Type",
        supported_ram_types: "Supported Memory",
        length_mm: "Length",
        max_gpu_length_mm: "Max GPU Length",
        height_mm: "Height",
        max_cooler_height_mm: "Max Cooler Height",
        power_draw: "Power Draw",
        wattage: "Power",
        vram: "Video Memory",
        form_factor: "Form Factor",
    };

    function displayLabel(key) {
        return labels[key] || key.replace(/([a-z])([A-Z])/g, "$1 $2").replaceAll("_", " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase());
    }

    function formatPrice(value) {
        return `${Number(value).toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₽`;
    }

    function animatePreview() {
        preview.classList.remove("is-changing");
        void preview.offsetWidth;
        preview.classList.add("is-changing");
    }

    function selectProduct(product, card) {
        selectedProduct = product;
        for (const productCard of cards) {
            const isSelected = productCard === card;
            productCard.classList.toggle("is-selected", isSelected);
            productCard.querySelector(".product-select").setAttribute("aria-pressed", String(isSelected));
        }

        document.getElementById("preview-category").textContent = product.category.toUpperCase();
        document.getElementById("preview-name").textContent = product.name;
        document.getElementById("preview-price").textContent = formatPrice(product.price);
        const imageStage = document.getElementById("preview-image-stage");
        imageStage.replaceChildren();

        if (product.thumbnail) {
            const image = document.createElement("img");
            image.className = "preview-image";
            image.src = product.thumbnail;
            image.alt = product.name;
            imageStage.append(image);
        } else {
            const placeholder = document.createElement("div");
            placeholder.className = "preview-placeholder";
            const initials = document.createElement("span");
            initials.textContent = product.category.slice(0, 2).toUpperCase();
            placeholder.append(initials, document.createElement("i"));
            imageStage.append(placeholder);
        }
        const imageCredit = document.getElementById("preview-image-credit");
        const imageSource = document.getElementById("preview-image-source");
        imageCredit.hidden = !product.thumbnail_source_url;
        document.getElementById("preview-image-credit-text").textContent = product.thumbnail_credit || "";
        if (product.thumbnail_source_url) imageSource.href = product.thumbnail_source_url;

        const specList = document.getElementById("spec-list");
        specList.replaceChildren();
        const specs = Object.entries(product.specs || {});
        if (specs.length === 0) {
            const empty = document.createElement("p");
            empty.className = "spec-empty";
            empty.textContent = "Характеристики не указаны";
            specList.append(empty);
        } else {
            specs.forEach(([key, value], index) => {
                const row = document.createElement("div");
                row.className = "spec-row";
                row.style.animationDelay = `${Math.min(index * 35, 210)}ms`;
                const term = document.createElement("dt");
                term.textContent = displayLabel(key);
                const description = document.createElement("dd");
                description.textContent = Array.isArray(value) ? value.join(", ") : String(value);
                row.append(term, description);
                specList.append(row);
            });
        }

        document.getElementById("preview-index").textContent = String(cards.indexOf(card) + 1).padStart(2, "0");
        animatePreview();
    }

    async function addComponentToBuild(product, triggerButton) {
        if (!product || triggerButton.disabled) return;
        const label = triggerButton.querySelector("span");
        const originalLabel = triggerButton.dataset.defaultLabel || label.textContent;
        triggerButton.dataset.defaultLabel = originalLabel;
        triggerButton.disabled = true;
        label.textContent = "Добавляем...";
        try {
            const response = await fetch(`/components/${product.id}/add/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "Не удалось добавить компонент");
            updateBuildSummary(result);
            triggerButton.classList.add("is-added");
            label.textContent = "Добавлено";
        } catch (error) {
            label.textContent = "Ошибка. Повторить";
        } finally {
            triggerButton.disabled = false;
            window.setTimeout(() => {
                if (!label.isConnected) return;
                if (["Добавлено", "Ошибка. Повторить"].includes(label.textContent)) label.textContent = originalLabel;
                triggerButton.classList.remove("is-added");
            }, 1600);
        }
    }

    function updateBuildSummary(result) {
        if (currentCount) currentCount.textContent = String(result.item_count);
        if (currentTotal) currentTotal.textContent = formatPrice(result.total_price);
        document.getElementById("cart-item-count").textContent = String(result.item_count);
        document.getElementById("cart-total").textContent = formatPrice(result.total_price);
        document.getElementById("cart-empty").hidden = result.items.length !== 0;
        cartItems.replaceChildren();
        for (const item of result.items) {
            const row = document.createElement("li");
            row.className = "cart-item";
            row.dataset.componentId = item.id;
            const info = document.createElement("div");
            info.className = "cart-item-info";
            const category = document.createElement("span");
            category.className = "cart-item-category";
            category.textContent = item.category;
            const name = document.createElement("strong");
            name.textContent = item.name;
            const description = document.createElement("small");
            description.textContent = `${item.quantity} × ${formatPrice(item.price)}`;
            info.append(category, name, description);
            const lineTotal = document.createElement("b");
            lineTotal.className = "cart-line-total";
            lineTotal.textContent = formatPrice(item.line_total);
            const remove = document.createElement("button");
            remove.className = "cart-remove";
            remove.type = "button";
            remove.dataset.removeId = item.id;
            remove.setAttribute("aria-label", `Удалить ${item.name}`);
            remove.textContent = "×";
            row.append(info, lineTotal, remove);
            cartItems.append(row);
        }
        cartItems.hidden = result.items.length === 0;
        renderCompatibility(result.compatibility);
        cartSaveBuild.disabled = result.item_count === 0;
        cartCheckout.disabled = result.item_count === 0;

        const activeComponentIds = new Set(result.items.map((item) => String(item.id)));
        for (const card of cards) {
            const isInBuild = activeComponentIds.has(card.dataset.componentId);
            card.classList.toggle("is-in-build", isInBuild);
            card.querySelector(".in-build-badge").hidden = !isInBuild;
        }
    }

    function renderCompatibility(result) {
        const panel = document.getElementById("cart-compatibility");
        panel.replaceChildren();
        const status = document.createElement("p");
        status.className = `compatibility-state ${result.is_valid ? "is-valid" : "is-invalid"}`;
        const indicator = document.createElement("i");
        const message = document.createElement("span");
        message.textContent = result.is_valid ? "Конфигурация совместима" : "Обнаружена несовместимость";
        status.append(indicator, message);
        panel.append(status);

        for (const [className, messages] of [
            ["compatibility-errors", result.errors || []],
            ["compatibility-warnings", result.warnings || []],
        ]) {
            if (!messages.length) continue;
            const list = document.createElement("ul");
            list.className = className;
            for (const text of messages) {
                const item = document.createElement("li");
                item.textContent = text;
                list.append(item);
            }
            panel.append(list);
        }
    }

    for (const card of cards) {
        card.querySelector(".product-select").addEventListener("click", () => {
            const product = productById.get(card.dataset.componentId);
            if (product) selectProduct(product, card);
        });
        card.querySelector(".card-add").addEventListener("click", (event) => {
            event.stopPropagation();
            const product = productById.get(card.dataset.componentId);
            if (!product) return;
            selectProduct(product, card);
            addComponentToBuild(product, event.currentTarget);
        });
    }

    if (cards.length) selectProduct(productById.get(cards[0].dataset.componentId), cards[0]);

    sortSelect?.addEventListener("change", () => sortForm?.requestSubmit());

    search?.addEventListener("input", () => {
        const query = search.value.trim().toLocaleLowerCase("ru");
        let visibleCount = 0;
        for (const card of cards) {
            const product = productById.get(card.dataset.componentId);
            const visible = `${product.name} ${product.category}`.toLocaleLowerCase("ru").includes(query);
            card.hidden = !visible;
            if (visible) visibleCount += 1;
        }
        document.getElementById("visible-count").textContent = String(visibleCount);
        document.getElementById("empty-search").hidden = visibleCount !== 0;
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
            event.preventDefault();
            search?.focus();
        }
    });

    document.getElementById("cart-close").addEventListener("click", () => cartDialog.close());
    document.getElementById("checkout-close").addEventListener("click", () => checkoutDialog.close());
    cartOpen.addEventListener("click", () => cartDialog.showModal());
    cartDialog.addEventListener("click", (event) => {
        if (event.target === cartDialog) cartDialog.close();
    });

    cartItems.addEventListener("click", async (event) => {
        const removeButton = event.target.closest("[data-remove-id]");
        if (!removeButton) return;
        removeButton.disabled = true;
        try {
            const response = await fetch(`/cart/components/${removeButton.dataset.removeId}/remove/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "Не удалось удалить товар.");
            updateBuildSummary(result);
        } catch (error) {
            removeButton.disabled = false;
            removeButton.title = error.message;
        }
    });

    cartCheckout.addEventListener("click", () => {
        cartDialog.close();
        if (cartCheckout.dataset.authenticated === "true") {
            checkoutDialog.showModal();
        } else {
            authDialog.dataset.checkoutPending = "true";
            authDialog.showModal();
        }
    });

    cartSaveBuild.addEventListener("click", async () => {
        if (cartSaveBuild.disabled) return;
        if (cartSaveBuild.dataset.authenticated !== "true") {
            cartDialog.close();
            authDialog.dataset.checkoutPending = "false";
            authDialog.showModal();
            return;
        }

        const label = cartSaveBuild.querySelector("span");
        cartSaveBuild.disabled = true;
        label.textContent = "Сохраняем...";
        try {
            const response = await fetch("/builds/save/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            const result = await response.json();
            if (!response.ok || !result.success) throw new Error((result.errors || ["Не удалось сохранить сборку."]).join(" "));
            label.textContent = "Сборка сохранена";
            window.setTimeout(() => window.location.reload(), 500);
        } catch (error) {
            label.textContent = error.message;
            cartSaveBuild.disabled = false;
        }
    });

    checkoutForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const submit = checkoutForm.querySelector("[type=submit]");
        const errorBox = document.getElementById("checkout-error");
        errorBox.hidden = true;
        submit.disabled = true;
        try {
            const response = await fetch(checkoutForm.action, {
                method: "POST",
                body: new URLSearchParams(new FormData(checkoutForm)),
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            const result = await response.json();
            if (!response.ok || !result.success) {
                const errors = result.errors || ["Не удалось оформить заказ."];
                const messages = Array.isArray(errors)
                    ? errors
                    : Object.values(errors).flatMap((entries) => entries.map((entry) => entry.message || entry));
                throw new Error(messages.join(" "));
            }

            updateBuildSummary({
                item_count: 0,
                total_price: "0.00",
                items: [],
                compatibility: { is_valid: true, errors: [], warnings: [] },
            });
            checkoutDialog.close();
            document.getElementById("order-success-message").textContent = result.message;
            document.getElementById("order-success-modal").showModal();
        } catch (error) {
            errorBox.textContent = error.message;
            errorBox.hidden = false;
        } finally {
            submit.disabled = false;
        }
    });

    const successDialog = document.getElementById("order-success-modal");
    const closeSuccess = () => {
        successDialog.close();
        window.location.reload();
    };
    document.getElementById("order-success-close").addEventListener("click", closeSuccess);
    document.getElementById("order-success-continue").addEventListener("click", closeSuccess);

    if (new URLSearchParams(window.location.search).get("checkout") === "1") {
        checkoutDialog.showModal();
    }
})();