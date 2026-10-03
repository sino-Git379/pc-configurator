(() => {
    const socketOptions = ["AM3+", "AM4", "AM5", "FM2+", "LGA1151", "LGA1200", "LGA1700", "LGA1851", "sTR4", "sTRX4", "sTR5"];
    const ramTypeOptions = ["DDR4", "DDR5"];
    const cpuFields = [
        { name: "socket", label: "Сокет", type: "select", options: socketOptions },
        { name: "cores", label: "Количество ядер", type: "number" },
        { name: "tdp", label: "TDP (Вт)", type: "number" },
        { name: "base_clock", label: "Базовая частота (ГГц)", type: "number", step: "0.1" },
        { name: "threads", label: "Количество потоков", type: "number" },
    ];
    const motherboardFields = [
        { name: "socket", label: "Сокет", type: "select", options: socketOptions },
        { name: "supported_ram_types", label: "Тип поддерживаемой памяти", type: "select", options: ramTypeOptions },
        { name: "form_factor", label: "Форм-фактор", type: "text" },
    ];
    const fieldsByCategory = {
        cpu: cpuFields,
        processors: cpuFields,
        gpu: [
            { name: "length_mm", label: "Длина (мм)", type: "number" },
            { name: "vram", label: "Видеопамять (ГБ)", type: "number" },
            { name: "power_draw", label: "Потребление (Вт)", type: "number" },
            { name: "tdp", label: "TDP (Вт)", type: "number" },
        ],
        ram: [
            { name: "memory_type", label: "Тип памяти", type: "select", options: ramTypeOptions },
            { name: "capacity_gb", label: "Объём (ГБ)", type: "number" },
            { name: "speed_mhz", label: "Частота (МГц)", type: "number" },
        ],
        motherboard: motherboardFields,
        motherboards: motherboardFields,
        case: [
            { name: "max_gpu_length_mm", label: "Макс. длина GPU (мм)", type: "number" },
            { name: "max_cooler_height_mm", label: "Макс. высота кулера (мм)", type: "number" },
            { name: "form_factor", label: "Форм-фактор", type: "text" },
        ],
        cooler: [{ name: "height_mm", label: "Высота кулера (мм)", type: "number" }],
        "power-supply": [{ name: "wattage", label: "Мощность (Вт)", type: "number" }],
        "power-supplies": [{ name: "wattage", label: "Мощность (Вт)", type: "number" }],
        "graphics-card": [
            { name: "length_mm", label: "Длина (мм)", type: "number" },
            { name: "vram", label: "Видеопамять (ГБ)", type: "number" },
            { name: "power_draw", label: "Потребление (Вт)", type: "number" },
        ],
        "graphic-cards": [
            { name: "length_mm", label: "Длина (мм)", type: "number" },
            { name: "vram", label: "Видеопамять (ГБ)", type: "number" },
            { name: "power_draw", label: "Потребление (Вт)", type: "number" },
        ],
        mainboard: motherboardFields,
        psu: [{ name: "wattage", label: "Мощность (Вт)", type: "number" }],
        storage: [
            { name: "drive_type", label: "Тип накопителя", type: "select", options: ["M.2 NVMe", "SATA SSD", "HDD"] },
            { name: "capacity_gb", label: "Объём (ГБ)", type: "number" },
        ],
        cases: [
            { name: "max_gpu_length_mm", label: "Макс. длина GPU (мм)", type: "number" },
            { name: "max_cooler_height_mm", label: "Макс. высота кулера (мм)", type: "number" },
            { name: "form_factor", label: "Форм-фактор", type: "text" },
        ],
        cooling: [{ name: "height_mm", label: "Высота кулера (мм)", type: "number" }],
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
            const input = field.type === "select" ? document.createElement("select") : document.createElement("input");
            input.className = "field-control";
            input.id = `spec-${field.name}`;
            input.name = field.name;
            const savedValue = existingSpecs[field.name];
            if (field.type === "select") {
                input.add(new Option("Выберите значение", ""));
                for (const optionValue of field.options) input.add(new Option(optionValue, optionValue));
                if (savedValue && !field.options.includes(savedValue)) {
                    input.add(new Option(savedValue, savedValue));
                }
                input.value = Array.isArray(savedValue) ? savedValue[0] : savedValue ?? "";
            } else {
                input.type = field.type;
                input.min = field.type === "number" ? "0" : "";
                if (field.step) input.step = field.step;
                if (field.placeholder) input.placeholder = field.placeholder;
                input.value = Array.isArray(savedValue) ? savedValue.join(", ") : savedValue ?? "";
            }
            wrapper.append(label, input);
            inputsContainer.append(wrapper);
        }
    }

    category.addEventListener("change", renderSpecFields);
    renderSpecFields();

    form.addEventListener("submit", () => {
        const specs = {};
        for (const input of inputsContainer.querySelectorAll("input, select")) {
            if (!input.value.trim()) continue;
            specs[input.name] = input.type === "number" ? Number(input.value) : input.value.trim();
        }
        if (typeof specs.supported_ram_types === "string") {
            specs.supported_ram_types = specs.supported_ram_types.split(",").map((type) => type.trim()).filter(Boolean);
        }
        specsInput.value = JSON.stringify(specs);
    });
})();