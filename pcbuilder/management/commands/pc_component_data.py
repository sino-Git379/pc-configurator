def cpu(socket, cores, threads, tdp, base_clock, boost_clock):
    return {
        "socket": socket,
        "cores": cores,
        "threads": threads,
        "tdp": tdp,
        "base_clock_ghz": base_clock,
        "boost_clock_ghz": boost_clock,
    }


def gpu(length, power, vram, bus):
    return {"length_mm": length, "power_draw": power, "vram_gb": vram, "memory_bus_bit": bus}


def motherboard(socket, ram_type, form_factor):
    return {
        "socket": socket,
        "ram_type": ram_type,
        "supported_ram_types": [ram_type],
        "form_factor": form_factor,
    }


def ram(memory_type, capacity, speed, latency, modules):
    return {
        "memory_type": memory_type,
        "capacity_gb": capacity,
        "speed_mhz": speed,
        "cas_latency": latency,
        "modules": modules,
    }


def storage(drive_type, capacity, interface, read_speed, write_speed):
    return {
        "drive_type": drive_type,
        "capacity_gb": capacity,
        "interface": interface,
        "read_speed_mbps": read_speed,
        "write_speed_mbps": write_speed,
    }


def power_supply(power, efficiency, modular):
    return {"power_w": power, "efficiency_rating": efficiency, "modular": modular}


def case(form_factor, gpu_length, cooler_height, radiator, bays):
    return {
        "form_factor": form_factor,
        "max_gpu_length_mm": gpu_length,
        "max_cooler_height_mm": cooler_height,
        "max_radiator_mm": radiator,
        "drive_bays_35": bays,
    }


def cooler(height, tdp, radiator):
    return {"height_mm": height, "tdp_capacity_w": tdp, "radiator_mm": radiator}


COMPONENTS = {
    "processors": [
        ("AMD Ryzen 5 5600", 10500, cpu("AM4", 6, 12, 65, 3.5, 4.4)),
        ("AMD Ryzen 5 5600X", 12500, cpu("AM4", 6, 12, 65, 3.7, 4.6)),
        ("AMD Ryzen 7 5700X", 15500, cpu("AM4", 8, 16, 65, 3.4, 4.6)),
        ("AMD Ryzen 7 5800X3D", 29000, cpu("AM4", 8, 16, 105, 3.4, 4.5)),
        ("AMD Ryzen 5 7500F", 14500, cpu("AM5", 6, 12, 65, 3.7, 5.0)),
        ("AMD Ryzen 5 7600", 18500, cpu("AM5", 6, 12, 65, 3.8, 5.1)),
        ("AMD Ryzen 5 7600X", 20500, cpu("AM5", 6, 12, 105, 4.7, 5.3)),
        ("AMD Ryzen 7 7700", 27500, cpu("AM5", 8, 16, 65, 3.8, 5.3)),
        ("AMD Ryzen 7 7800X3D", 39000, cpu("AM5", 8, 16, 120, 4.2, 5.0)),
        ("AMD Ryzen 9 7900", 37500, cpu("AM5", 12, 24, 65, 3.7, 5.4)),
        ("AMD Ryzen 9 7900X", 42000, cpu("AM5", 12, 24, 170, 4.7, 5.6)),
        ("AMD Ryzen 9 7950X", 59000, cpu("AM5", 16, 32, 170, 4.5, 5.7)),
        ("AMD Ryzen 7 9700X", 34500, cpu("AM5", 8, 16, 65, 3.8, 5.5)),
        ("AMD Ryzen 7 9800X3D", 52000, cpu("AM5", 8, 16, 120, 4.7, 5.2)),
        ("Intel Core i5-14600K", 33000, cpu("LGA1700", 14, 20, 125, 3.5, 5.3)),
    ],
    "graphic-cards": [
        ("MSI GeForce RTX 4060 Ventus 2X 8G", 35000, gpu(199, 115, 8, 128)),
        ("ASUS Dual GeForce RTX 4060 Ti 8GB", 47000, gpu(227, 160, 8, 128)),
        ("Gigabyte GeForce RTX 4060 Ti Gaming OC 16G", 57000, gpu(281, 165, 16, 128)),
        ("MSI GeForce RTX 4070 SUPER Ventus 2X", 72000, gpu(242, 220, 12, 192)),
        ("ASUS Dual GeForce RTX 4070 SUPER OC", 78000, gpu(267, 220, 12, 192)),
        ("Gigabyte GeForce RTX 4070 Ti SUPER Gaming OC", 108000, gpu(300, 285, 16, 256)),
        ("MSI GeForce RTX 4080 SUPER Ventus 3X", 128000, gpu(322, 320, 16, 256)),
        ("ASUS TUF Gaming GeForce RTX 4090 OC", 235000, gpu(348, 450, 24, 384)),
        ("MSI GeForce RTX 5060 8G Ventus 2X", 42000, gpu(197, 145, 8, 128)),
        ("Gigabyte GeForce RTX 5060 Ti Gaming OC 16G", 62000, gpu(281, 180, 16, 128)),
        ("ASUS Prime GeForce RTX 5070 OC", 81000, gpu(304, 250, 12, 192)),
        ("MSI GeForce RTX 5070 Ti Gaming Trio OC", 119000, gpu(338, 300, 16, 256)),
        ("Gigabyte GeForce RTX 5080 Gaming OC", 165000, gpu(342, 360, 16, 256)),
        ("MSI GeForce RTX 5090 Suprim SOC", 315000, gpu(359, 575, 32, 512)),
        ("Sapphire Pulse Radeon RX 7800 XT 16GB", 72000, gpu(280, 263, 16, 256)),
    ],
    "motherboards": [
        ("ASUS TUF Gaming B550-PLUS", 14500, motherboard("AM4", "DDR4", "ATX")),
        ("MSI MAG B550 Tomahawk", 15500, motherboard("AM4", "DDR4", "ATX")),
        ("Gigabyte B550 AORUS Elite V2", 13500, motherboard("AM4", "DDR4", "ATX")),
        ("ASRock B550M Pro4", 10500, motherboard("AM4", "DDR4", "Micro-ATX")),
        ("ASUS ROG Strix B550-F Gaming WiFi II", 18500, motherboard("AM4", "DDR4", "ATX")),
        ("ASUS TUF Gaming B650-PLUS WiFi", 23500, motherboard("AM5", "DDR5", "ATX")),
        ("MSI MAG B650 Tomahawk WiFi", 24500, motherboard("AM5", "DDR5", "ATX")),
        ("MSI PRO B650M-A WiFi", 18500, motherboard("AM5", "DDR5", "Micro-ATX")),
        ("Gigabyte B650 AORUS Elite AX", 22500, motherboard("AM5", "DDR5", "ATX")),
        ("ASRock B650M Pro RS WiFi", 17500, motherboard("AM5", "DDR5", "Micro-ATX")),
        ("ASUS ROG Strix X670E-E Gaming WiFi", 49000, motherboard("AM5", "DDR5", "ATX")),
        ("MSI MAG X670E Tomahawk WiFi", 38500, motherboard("AM5", "DDR5", "ATX")),
        ("Gigabyte X870 AORUS Elite WiFi7", 34500, motherboard("AM5", "DDR5", "ATX")),
        ("ASUS ROG Crosshair X870E Hero", 79000, motherboard("AM5", "DDR5", "ATX")),
        ("ASUS ROG Strix Z790-E Gaming WiFi II", 52000, motherboard("LGA1700", "DDR5", "ATX")),
    ],
    "ram": [
        ("Kingston FURY Beast 16GB DDR4-3200 Kit", 4200, ram("DDR4", 16, 3200, 16, 2)),
        ("Kingston FURY Beast 32GB DDR4-3200 Kit", 6900, ram("DDR4", 32, 3200, 16, 2)),
        ("Corsair Vengeance LPX 32GB DDR4-3600 Kit", 7900, ram("DDR4", 32, 3600, 18, 2)),
        ("G.Skill Ripjaws V 32GB DDR4-3600 Kit", 7600, ram("DDR4", 32, 3600, 16, 2)),
        ("Patriot Viper Steel 32GB DDR4-3600 Kit", 7200, ram("DDR4", 32, 3600, 18, 2)),
        ("Kingston FURY Beast 32GB DDR5-5600 Kit", 8500, ram("DDR5", 32, 5600, 36, 2)),
        ("Kingston FURY Beast 32GB DDR5-6000 Kit", 9900, ram("DDR5", 32, 6000, 36, 2)),
        ("G.Skill Flare X5 32GB DDR5-6000 Kit", 11200, ram("DDR5", 32, 6000, 30, 2)),
        ("Corsair Vengeance 32GB DDR5-6000 Kit", 11500, ram("DDR5", 32, 6000, 36, 2)),
        ("G.Skill Trident Z5 Neo RGB 32GB DDR5-6000 Kit", 14500, ram("DDR5", 32, 6000, 30, 2)),
        ("Kingston FURY Beast 64GB DDR5-6000 Kit", 18800, ram("DDR5", 64, 6000, 36, 2)),
        ("Corsair Vengeance 64GB DDR5-6000 Kit", 20500, ram("DDR5", 64, 6000, 32, 2)),
        ("Crucial Pro 32GB DDR5-5600 Kit", 9200, ram("DDR5", 32, 5600, 46, 2)),
        ("TeamGroup T-Force Delta RGB 32GB DDR5-6000 Kit", 13000, ram("DDR5", 32, 6000, 30, 2)),
        ("Patriot Viper Venom 32GB DDR5-6000 Kit", 10100, ram("DDR5", 32, 6000, 36, 2)),
    ],
    "storage": [
        ("Samsung 990 PRO 1TB NVMe", 10500, storage("M.2 NVMe", 1000, "PCIe 4.0 x4", 7450, 6900)),
        ("Samsung 990 PRO 2TB NVMe", 17500, storage("M.2 NVMe", 2000, "PCIe 4.0 x4", 7450, 6900)),
        ("WD_BLACK SN850X 1TB NVMe", 9800, storage("M.2 NVMe", 1000, "PCIe 4.0 x4", 7300, 6300)),
        ("WD_BLACK SN850X 2TB NVMe", 16500, storage("M.2 NVMe", 2000, "PCIe 4.0 x4", 7300, 6600)),
        ("Kingston KC3000 1TB NVMe", 8900, storage("M.2 NVMe", 1000, "PCIe 4.0 x4", 7000, 6000)),
        ("Kingston KC3000 2TB NVMe", 14900, storage("M.2 NVMe", 2000, "PCIe 4.0 x4", 7000, 7000)),
        ("Crucial P3 Plus 1TB NVMe", 6900, storage("M.2 NVMe", 1000, "PCIe 4.0 x4", 5000, 3600)),
        ("Crucial P3 Plus 2TB NVMe", 10900, storage("M.2 NVMe", 2000, "PCIe 4.0 x4", 5000, 4200)),
        ("ADATA XPG GAMMIX S70 Blade 1TB", 8500, storage("M.2 NVMe", 1000, "PCIe 4.0 x4", 7400, 5500)),
        ("Lexar NM790 2TB NVMe", 13900, storage("M.2 NVMe", 2000, "PCIe 4.0 x4", 7400, 6500)),
        ("Samsung 870 EVO 1TB SATA SSD", 9200, storage("SATA SSD", 1000, "SATA III", 560, 530)),
        ("Crucial MX500 1TB SATA SSD", 7900, storage("SATA SSD", 1000, "SATA III", 560, 510)),
        ("Kingston A400 960GB SATA SSD", 5900, storage("SATA SSD", 960, "SATA III", 500, 450)),
        ("Seagate BarraCuda 2TB HDD", 6500, storage("HDD", 2000, "SATA III", 220, 200)),
        ("WD Blue 4TB HDD", 10500, storage("HDD", 4000, "SATA III", 180, 175)),
    ],
    "power-supplies": [
        ("be quiet! System Power 10 550W", 6200, power_supply(550, "80+ Bronze", False)),
        ("DeepCool PK650D 650W", 6500, power_supply(650, "80+ Bronze", False)),
        ("Corsair CX650 650W", 7900, power_supply(650, "80+ Bronze", False)),
        ("MSI MAG A650BN 650W", 6100, power_supply(650, "80+ Bronze", False)),
        ("Cooler Master MWE 650 Bronze V2", 7200, power_supply(650, "80+ Bronze", False)),
        ("be quiet! Pure Power 12 M 750W", 12500, power_supply(750, "80+ Gold", True)),
        ("Corsair RM750e 750W", 11900, power_supply(750, "80+ Gold", True)),
        ("MSI MAG A750GL PCIE5 750W", 10500, power_supply(750, "80+ Gold", True)),
        ("DeepCool PN850M 850W", 11900, power_supply(850, "80+ Gold", True)),
        ("Seasonic Focus GX-850 850W", 15900, power_supply(850, "80+ Gold", True)),
        ("Corsair RM850x 850W", 17800, power_supply(850, "80+ Gold", True)),
        ("be quiet! Straight Power 12 1000W", 24500, power_supply(1000, "80+ Platinum", True)),
        ("ASUS ROG Strix 1000W Gold Aura Edition", 23900, power_supply(1000, "80+ Gold", True)),
        ("MSI MPG A1000G PCIE5 1000W", 18600, power_supply(1000, "80+ Gold", True)),
        ("Corsair RM1200x SHIFT 1200W", 32900, power_supply(1200, "80+ Gold", True)),
    ],
    "cases": [
        ("DeepCool CC560 V2", 6500, case("ATX", 370, 165, 360, 2)),
        ("DeepCool CH560 Digital", 11800, case("ATX", 380, 175, 360, 2)),
        ("Corsair 4000D Airflow", 11500, case("ATX", 360, 170, 360, 2)),
        ("Corsair 5000D Airflow", 16900, case("ATX", 400, 170, 360, 2)),
        ("NZXT H5 Flow 2024", 10900, case("ATX", 365, 165, 360, 2)),
        ("NZXT H7 Flow 2024", 15900, case("ATX", 410, 185, 420, 2)),
        ("Lian Li LANCOOL 216", 13900, case("ATX", 392, 180, 360, 2)),
        ("Lian Li O11 Dynamic EVO RGB", 20900, case("E-ATX", 426, 167, 420, 6)),
        ("Fractal Design North Charcoal", 17900, case("ATX", 355, 170, 360, 2)),
        ("Fractal Design Meshify 2 Compact", 16500, case("ATX", 341, 169, 360, 2)),
        ("Phanteks Eclipse G360A", 9900, case("ATX", 400, 162, 360, 2)),
        ("Montech AIR 903 MAX", 10500, case("ATX", 400, 180, 360, 2)),
        ("ASUS TUF Gaming GT502", 18900, case("E-ATX", 400, 163, 360, 4)),
        ("Cooler Master MasterBox TD500 Mesh V2", 12500, case("ATX", 410, 165, 360, 2)),
        ("Jonsbo D31 Mesh Screen", 11900, case("Micro-ATX", 330, 168, 360, 2)),
    ],
    "cooling": [
        ("DeepCool AK400", 3200, cooler(155, 220, 0)),
        ("DeepCool AK620", 6900, cooler(160, 260, 0)),
        ("Thermalright Peerless Assassin 120 SE", 4900, cooler(155, 265, 0)),
        ("Thermalright Phantom Spirit 120 SE", 5600, cooler(154, 280, 0)),
        ("be quiet! Pure Rock 2", 5200, cooler(155, 150, 0)),
        ("Noctua NH-D15 chromax.black", 14900, cooler(165, 250, 0)),
        ("Noctua NH-U12S redux", 6900, cooler(158, 150, 0)),
        ("ID-COOLING SE-214-XT", 2100, cooler(150, 180, 0)),
        ("Scythe Fuma 3", 8900, cooler(154, 250, 0)),
        ("Arctic Liquid Freezer III 240", 10500, cooler(38, 300, 240)),
        ("Arctic Liquid Freezer III 360", 13900, cooler(38, 350, 360)),
        ("DeepCool LS520 SE 240", 8900, cooler(27, 300, 240)),
        ("DeepCool LS720S Zero Dark 360", 12500, cooler(27, 350, 360)),
        ("NZXT Kraken 240 RGB", 16900, cooler(30, 300, 240)),
        ("Corsair iCUE H150i Elite Capellix XT 360", 25900, cooler(27, 350, 360)),
    ],
}


CATEGORY_THUMBNAILS = {
    "processors": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/f/fa/HP-HP9000-PARISC-PA7100LC-CPU-Chip-Closeup-Project-HummingBird.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:HP-HP9000-PARISC-PA7100LC-CPU-Chip-Closeup-Project-HummingBird.jpg",
        "credit": "Thomas Schanz / CC BY-SA 4.0",
    },
    "graphic-cards": {
        "url": "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=640&q=80&fit=crop",
        "source_url": "https://unsplash.com/license",
        "credit": "Unsplash",
    },
    "motherboards": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/5/5a/Computer_motherboard_11.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Computer_motherboard_11.jpg",
        "credit": "Kurt Kaiser / CC0",
    },
    "ram": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/6/6c/RAM_Module_%28SDRAM-DDR4%29.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:RAM_Module_(SDRAM-DDR4).jpg",
        "credit": "ElooKoN / CC BY-SA 4.0",
    },
    "storage": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/e/e2/OCZ_Z6300_NVMe_flash_SSD%2C_U.2_%28SFF-8639%29_form-factor.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:OCZ_Z6300_NVMe_flash_SSD,_U.2_(SFF-8639)_form-factor.jpg",
        "credit": "Dmitry Nosachev / CC BY-SA 4.0",
    },
    "power-supplies": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/1/1d/PC_Power_Supply_Unit_PSU_wird_CPU_cooler_air_flow_funnel_IMG_8127.JPG",
        "source_url": "https://commons.wikimedia.org/wiki/File:PC_Power_Supply_Unit_PSU_wird_CPU_cooler_air_flow_funnel_IMG_8127.JPG",
        "credit": "Hans Haase / CC BY-SA 3.0",
    },
    "cases": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Computer_case_-_Full_Tower.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Computer_case_-_Full_Tower.jpg",
        "credit": "Dmitry Makeev / CC BY-SA 4.0",
    },
    "cooling": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/b/bf/CPU-cooler-14_hg.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:CPU-cooler-14_hg.jpg",
        "credit": "Hannes Grobe / CC BY-SA 4.0",
    },
}