(() => {
    const products = JSON.parse(document.getElementById("component-data").textContent);
    const productById = new Map(products.map((product) => [String(product.id), product]));
    const cards = [...document.querySelectorAll(".product-card")];
    const preview = document.getElementById("preview-content");
    const search = document.getElementById("product-search");
    const addButton = document.getElementById("add-to-build");
    const currentCount = document.getElementById("build-count");
    const currentTotal = document.getElementById("build-total");
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
            productCard.setAttribute("aria-pressed", String(isSelected));
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

        addButton.disabled = false;
        addButton.classList.remove("is-added");
        addButton.querySelector("span").textContent = "Добавить в сборку";
        document.getElementById("preview-index").textContent = String(cards.indexOf(card) + 1).padStart(2, "0");
        animatePreview();
    }

    for (const card of cards) {
        card.addEventListener("click", () => {
            const product = productById.get(card.dataset.componentId);
            if (product) selectProduct(product, card);
        });
    }

    if (cards.length) selectProduct(productById.get(cards[0].dataset.componentId), cards[0]);

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

    addButton.addEventListener("click", async () => {
        if (!selectedProduct || addButton.disabled) return;
        addButton.disabled = true;
        addButton.querySelector("span").textContent = "Добавляем...";
        try {
            const response = await fetch(`/components/${selectedProduct.id}/add/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")?.value || "",
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            if (!response.ok) throw new Error("Не удалось добавить компонент");
            const result = await response.json();
            currentCount.textContent = String(result.item_count);
            currentTotal.textContent = formatPrice(result.total_price);
            addButton.classList.add("is-added");
            addButton.querySelector("span").textContent = "Добавлено в сборку";
        } catch (error) {
            addButton.querySelector("span").textContent = "Ошибка. Повторить";
        } finally {
            addButton.disabled = false;
        }
    });
})();