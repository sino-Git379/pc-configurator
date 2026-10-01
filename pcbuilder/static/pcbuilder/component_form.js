(() => {
    const fieldsByCategory = {
        cpu: [
            { name: "socket", label: "Сокет", type: "text" },
            { name: "cores", label: "Количество ядер", type: "number" },
            { name: "tdp", label: "TDP (Вт)", type: "number" },
            { name: "base_clock", label: "Базовая частота (ГГц)", type: "number", step: "0.1" },
            { name: "threads", label: "Количество потоков", type: "number" },
        ],
        gpu: [
            { name: "length_mm", label: "Длина (мм)", type: "number" },
            { name: "vram", label: "Видеопамять (ГБ)", type: "number" },
            { name: "power_draw", label: "Потребление (Вт)", type: "number" },
            { name: "tdp", label: "TDP (Вт)", type: "number" },
        ],
        ram: [
            { name: "memory_type", label: "Тип памяти (DDR4/DDR5)", type: "text" },
            { name: "capacity_gb", label: "Объём (ГБ)", type: "number" },
            { name: "speed_mhz", label: "Частота (МГц)", type: "number" },
        ],
        motherboard: [
            { name: "socket", label: "Сокет", type: "text" },
            { name: "supported_ram_types", label: "Поддерживаемая память", type: "text", placeholder: "DDR4, DDR5" },
            { name: "form_factor", label: "Форм-фактор", type: "text" },
        ],
        case: [
            { name: "max_gpu_length_mm", label: "Макс. длина GPU (мм)", type: "number" },
            { name: "max_cooler_height_mm", label: "Макс. высота кулера (мм)", type: "number" },
            { name: "form_factor", label: "Форм-фактор", type: "text" },
        ],
        cooler: [{ name: "height_mm", label: "Высота кулера (мм)", type: "number" }],
        "power-supply": [{ name: "wattage", label: "Мощность (Вт)", type: "number" }],
        "graphics-card": [
            { name: "length_mm", label: "Длина (мм)", type: "number" },
            { name: "vram", label: "Видеопамять (ГБ)", type: "number" },
            { name: "power_draw", label: "Потребление (Вт)", type: "number" },
        ],
        mainboard: [
            { name: "socket", label: "Сокет", type: "text" },
            { name: "supported_ram_types", label: "Поддерживаемая память", type: "text", placeholder: "DDR4, DDR5" },
            { name: "form_factor", label: "Форм-фактор", type: "text" },
        ],
        psu: [{ name: "wattage", label: "Мощность (Вт)", type: "number" }],
    };

    const form = document.getElementById("component-form");
    const category = document.getElementById("id_category");
    const fieldset = document.getElementById("spec-fields");
    const inputsContainer = document.getElementById("spec-inputs");
    const specsInput = document.getElementById("id_specs_json");
    if (!form || !category || !fieldset || !inputsContainer || !specsInput) return;

    function readExistingSpecs() {
        try {
            return JSON.parse(specsInput.value || "{}");
        } catch {
            return {};
        }
    }

    function renderSpecFields() {
        const existingSpecs = readExistingSpecs();
        const selectedCategory = category.selectedOptions[0]?.dataset.slug || "";
        const fields = fieldsByCategory[selectedCategory] || [];
        inputsContainer.replaceChildren();
        fieldset.hidden = fields.length === 0;

        for (const field of fields) {
            const wrapper = document.createElement("div");
            wrapper.className = "dynamic-field";
            const label = document.createElement("label");
            label.className = "field-label";
            label.htmlFor = `spec-${field.name}`;
            label.textContent = field.label;
            const input = document.createElement("input");
            input.className = "field-control";
            input.id = `spec-${field.name}`;
            input.name = field.name;
            input.type = field.type;
            input.min = field.type === "number" ? "0" : "";
            if (field.step) input.step = field.step;
            if (field.placeholder) input.placeholder = field.placeholder;
            const savedValue = existingSpecs[field.name];
            input.value = Array.isArray(savedValue) ? savedValue.join(", ") : savedValue ?? "";
            wrapper.append(label, input);
            inputsContainer.append(wrapper);
        }
    }

    category.addEventListener("change", renderSpecFields);
    renderSpecFields();

    form.addEventListener("submit", () => {
        const specs = {};
        for (const input of inputsContainer.querySelectorAll("input")) {
            if (!input.value.trim()) continue;
            specs[input.name] = input.type === "number" ? Number(input.value) : input.value.trim();
        }
        if (typeof specs.supported_ram_types === "string") {
            specs.supported_ram_types = specs.supported_ram_types.split(",").map((type) => type.trim()).filter(Boolean);
        }
        specsInput.value = JSON.stringify(specs);
    });
})();