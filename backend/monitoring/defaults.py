"""
Default configuration ported from the front-end engine (air-core.js): the
parameter catalogue, the sensor nodes, the city centres and the runtime
settings. Used by the `seed_data` management command.
"""

CITIES = [
    {'name': 'Tiranë', 'name_en': 'Tirana', 'lat': 41.3235, 'lng': 19.8154},
    {'name': 'Elbasan', 'name_en': 'Elbasan', 'lat': 41.1055, 'lng': 20.0917},
    {'name': 'Korçë', 'name_en': 'Korça', 'lat': 40.6186, 'lng': 20.7793},
]

_G_PM = [[0, '#1F8A4C'], [0.25, '#A9C23F'], [0.45, '#F2C230'], [0.65, '#E07E2E'], [0.85, '#B1322F'], [1, '#6D28D9']]

PARAMETERS = [
    {
        'key': 'pm25', 'field': 'pm25', 'label': 'PM2.5', 'long': 'Grimca të imëta PM2.5',
        'unit': 'µg/m³', 'icon': 'mdi:blur', 'dec': 1, 'public': True,
        'description': 'Grimca nën 2.5 µm që depërtojnë thellë në mushkëri dhe kalojnë në gjak.',
        'phys_min': 0, 'phys_max': 1000, 'disp_min': 0, 'disp_max': 60,
        'normal': 15, 'warn': 25, 'crit': 50, 'low_warn': None,
        'gradient': _G_PM, 'color': '#E07E2E', 'radius_m': 4200, 'blur': 0.55, 'opacity': 0.72,
        'note': 'Kufiri ditor i OBSH-së: 15 µg/m³.', 'sort': 0,
    },
    {
        'key': 'pm10', 'field': 'pm10', 'label': 'PM10', 'long': 'Grimca të thëna PM10',
        'unit': 'µg/m³', 'icon': 'mdi:blur-linear', 'dec': 1, 'public': True,
        'description': 'Pluhur nga trafiku, ndërtimet dhe djegia e druve.',
        'phys_min': 0, 'phys_max': 2000, 'disp_min': 0, 'disp_max': 120,
        'normal': 45, 'warn': 75, 'crit': 120, 'low_warn': None,
        'gradient': _G_PM, 'color': '#C2843A', 'radius_m': 4200, 'blur': 0.55, 'opacity': 0.72,
        'note': 'Kufiri ditor i OBSH-së: 45 µg/m³.', 'sort': 1,
    },
    {
        'key': 'tmp', 'field': 'tmp', 'label': 'Temperatura', 'long': 'Temperatura e ajrit',
        'unit': '°C', 'icon': 'mdi:thermometer', 'dec': 1, 'public': True,
        'description': 'Temperatura e ajrit e matur në lartësinë e nyjes.',
        'phys_min': -25, 'phys_max': 60, 'disp_min': 0, 'disp_max': 42,
        'normal': 30, 'warn': 35, 'crit': 40, 'low_warn': 0,
        'gradient': [[0, '#1E3A8A'], [0.2, '#38BDF8'], [0.4, '#34A853'], [0.6, '#F2C230'], [0.8, '#E07E2E'], [1, '#B1322F']],
        'color': '#B1322F', 'radius_m': 9000, 'blur': 0.7, 'opacity': 0.6,
        'note': 'Vlera 0.0 raportohet nga disa nyje si shenjë e sensorit të pavlefshëm.', 'sort': 2,
    },
    {
        'key': 'hum', 'field': 'hum', 'label': 'Lagështia', 'long': 'Lagështia relative',
        'unit': '%', 'icon': 'mdi:water-percent', 'dec': 0, 'public': True,
        'description': 'Lagështia relative - ndikon te qëndrimi pezull i grimcave.',
        'phys_min': 0, 'phys_max': 100, 'disp_min': 0, 'disp_max': 100,
        'normal': 60, 'warn': 80, 'crit': 95, 'low_warn': 20,
        'gradient': [[0, '#C2843A'], [0.25, '#E3C77A'], [0.45, '#34A853'], [0.7, '#38BDF8'], [1, '#1E3A8A']],
        'color': '#4976F4', 'radius_m': 9000, 'blur': 0.7, 'opacity': 0.55,
        'note': 'E thatë nën 30% · komfort 40–60% · e lartë mbi 70%.', 'sort': 3,
    },
    {
        'key': 'snd', 'field': 'snd', 'label': 'Zhurma', 'long': 'Niveli i zhurmës (raw)',
        'unit': '% e shkallës', 'icon': 'mdi:volume-high', 'dec': 0, 'public': True,
        'description': 'Sinjal i papërpunuar nga mikrofoni, i normalizuar në shkallën e sensorit. Nuk është dB.',
        'phys_min': 0, 'phys_max': 100, 'disp_min': 0, 'disp_max': 100,
        'normal': 35, 'warn': 55, 'crit': 75, 'low_warn': None,
        'gradient': [[0, '#1F8A4C'], [0.35, '#F2C230'], [0.65, '#E07E2E'], [1, '#B1322F']],
        'color': '#6D28D9', 'radius_m': 2600, 'blur': 0.5, 'opacity': 0.7,
        'note': 'Konvertim raw→% për nyje; asnjë formulë dB nuk është e validuar.', 'sort': 4,
    },
    {
        'key': 'uv', 'field': 'uv', 'label': 'UV', 'long': 'Rrezatimi UV (raw)',
        'unit': '% e shkallës', 'icon': 'mdi:weather-sunny', 'dec': 0, 'public': True,
        'description': 'Dalje e papërpunuar e fotodiodës UV, e normalizuar në shkallën e sensorit.',
        'phys_min': 0, 'phys_max': 100, 'disp_min': 0, 'disp_max': 100,
        'normal': 40, 'warn': 60, 'crit': 80, 'low_warn': None,
        'gradient': [[0, '#1F8A4C'], [0.3, '#F2C230'], [0.55, '#E07E2E'], [0.8, '#B1322F'], [1, '#6D28D9']],
        'color': '#F79009', 'radius_m': 12000, 'blur': 0.75, 'opacity': 0.6,
        'note': 'Vlera ≥98% tregon sensor të ngopur ose të bllokuar.', 'sort': 5,
    },
    {
        'key': 'pres', 'field': 'pres', 'label': 'Presioni', 'long': 'Presioni atmosferik',
        'unit': 'hPa', 'icon': 'mdi:gauge', 'dec': 1, 'public': False,
        'description': 'Raportohet vetëm nga nyjet Raspberry Pi me sensor BMP.',
        'phys_min': 850, 'phys_max': 1080, 'disp_min': 890, 'disp_max': 1020,
        'normal': 1030, 'warn': 1050, 'crit': 1070, 'low_warn': 900,
        'gradient': [[0, '#38BDF8'], [0.5, '#34A853'], [1, '#E07E2E']],
        'color': '#1F8A4C', 'radius_m': 12000, 'blur': 0.8, 'opacity': 0.5,
        'note': 'Nyjet LoRaWAN nuk e raportojnë këtë fushë (100% null).', 'sort': 6,
    },
    {
        'key': 'rain', 'field': 'rain', 'label': 'Shiu', 'long': 'Sensori i shiut (raw)',
        'unit': 'raw', 'icon': 'mdi:weather-rainy', 'dec': 0, 'public': False,
        'description': 'Dalje analoge e sensorit të shiut. Nuk ka kalibrim mm/h.',
        'phys_min': 0, 'phys_max': 1100, 'disp_min': 0, 'disp_max': 400,
        'normal': 400, 'warn': 600, 'crit': 800, 'low_warn': None,
        'gradient': [[0, '#E3C77A'], [0.5, '#38BDF8'], [1, '#1E3A8A']],
        'color': '#38BDF8', 'radius_m': 12000, 'blur': 0.8, 'opacity': 0.5,
        'note': 'Nuk publikohet - mungon kalibrimi.', 'sort': 7,
    },
]

_ALL = ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain']
_ALL_P = ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain', 'pres']

NODES = [
    {
        'node_id': 'ND-01', 'eui': 'A8404172C75D105A', 'join_eui': 'A840410000000101',
        'name': 'Tiranë - 21 Dhjetori', 'city': 'Tiranë', 'place': '21_dhjetori',
        'address': 'Rr. e Kavajës, zona e 21 Dhjetorit', 'lat': 41.3268, 'lng': 19.8072,
        'transport': 'LoRaWAN', 'hw': 'Nyje LoRa (Dragino)', 'tech': 'lorawan',
        'installed_at': '2026-02-22', 'interval_s': 100, 'active': True, 'public': True, 'maintenance': False,
        'scale': {'snd': 1023, 'uv': 1023, 'rain': 1023}, 'sensors': _ALL, 'api_id': 'lora/A8404172C75D105A',
        'notes': 'Nyja me histori më të gjatë. Sensori PM raporton null në ~4.7% të paketave.',
    },
    {
        'node_id': 'ND-02', 'eui': 'A84041DA335D105B', 'join_eui': 'A840410000000101',
        'name': 'Tiranë - Universitet', 'city': 'Tiranë', 'place': 'upt_campus_universitar',
        'address': 'Universiteti Politeknik i Tiranës, Sheshi Nënë Tereza', 'lat': 41.3186, 'lng': 19.8202,
        'transport': 'LoRaWAN', 'hw': 'Nyje LoRa (Dragino)', 'tech': 'lorawan',
        'installed_at': '2026-03-01', 'interval_s': 150, 'active': True, 'public': True, 'maintenance': False,
        'scale': {'snd': 1023, 'uv': 1023, 'rain': 1023}, 'sensors': _ALL, 'api_id': 'lora/A84041DA335D105B',
        'notes': 'Sensori UV raporton mesatarisht 997/1023 - i ngopur.',
    },
    {
        'node_id': 'ND-03', 'eui': 'raspberrypi_korce_1', 'join_eui': None,
        'name': 'Korçë - Shtëpi Qendër', 'city': 'Korçë', 'place': 'korce_qender',
        'address': 'Lagjja 8, Korçë', 'lat': 40.6186, 'lng': 20.7808,
        'transport': 'Wi-Fi / HTTP', 'hw': 'Raspberry Pi + SDS011 + BME280', 'tech': 'rpi_api',
        'installed_at': '2026-04-24', 'interval_s': 102, 'active': True, 'public': True, 'maintenance': False,
        'scale': {'snd': 255, 'uv': 255, 'rain': 255}, 'sensors': _ALL_P, 'api_id': 'rpi/korce_1',
        'notes': 'Zëvendëson nyjen e vjetër. Raporton 0.0 për temp/lagështi kur sensori dështon.',
    },
    {
        'node_id': 'ND-04', 'eui': 'raspberrypi_Korca_Universiteti', 'join_eui': None,
        'name': 'Korçë - Universitet', 'city': 'Korçë', 'place': None,
        'address': 'Universiteti "Fan S. Noli", Bulevardi Rilindasit, Korçë', 'lat': 40.6142, 'lng': 20.7846,
        'transport': 'Wi-Fi / HTTP', 'hw': 'Raspberry Pi + SDS011 + BME280', 'tech': 'rpi_api',
        'installed_at': '2026-04-23', 'interval_s': 180, 'active': True, 'public': True, 'maintenance': False,
        'scale': {'snd': 255, 'uv': 255, 'rain': 255}, 'sensors': _ALL_P, 'api_id': 'rpi/korca_universiteti',
        'notes': 'Presioni ~920 hPa përputhet me lartësinë ~850 m të Korçës.',
    },
    {
        'node_id': 'ND-05', 'eui': 'raspberrypi_elb_nyja2', 'join_eui': None,
        'name': 'Elbasan - Shtëpi Unaza', 'city': 'Elbasan', 'place': None,
        'address': 'Rr. Rinia, Elbasan', 'lat': 41.0984, 'lng': 20.1012,
        'transport': 'Wi-Fi / HTTP', 'hw': 'Raspberry Pi + SDS011', 'tech': 'rpi_api',
        'installed_at': '2026-04-10', 'interval_s': 805, 'active': True, 'public': True, 'maintenance': False,
        'scale': {'snd': 255, 'uv': 255, 'rain': 255}, 'sensors': _ALL, 'api_id': 'rpi/elb_nyja2',
        'notes': 'Interval i gjerë (≈13 min). Lagështia mesatare 11% - sensori dyshohet i dëmtuar.',
    },
    {
        'node_id': 'ND-06', 'eui': 'raspberrypi_elb_universiteti', 'join_eui': None,
        'name': 'Elbasan - Universitet', 'city': 'Elbasan', 'place': None,
        'address': 'Universiteti "Aleksandër Xhuvani", Elbasan', 'lat': 41.1125, 'lng': 20.0822,
        'transport': 'Wi-Fi / HTTP', 'hw': 'Raspberry Pi + SDS011', 'tech': 'rpi_api',
        'installed_at': '2026-04-10', 'interval_s': 362, 'active': True, 'public': True, 'maintenance': False,
        'scale': {'snd': 255, 'uv': 255, 'rain': 255}, 'sensors': _ALL, 'api_id': 'rpi/elb_universiteti',
        'notes': 'Nyja e dytë e Elbasanit, në kampusin universitar.',
    },
]

SETTINGS = {
    'tz': 'Europe/Tirane', 'online_mult': 2, 'delayed_mult': 6, 'validity_min': 180,
    'source': 'dataset', 'rest_base': 'https://api.airmonitor.al/v1',
    'ws_url': 'wss://api.airmonitor.al/v1/stream', 'poll_s': 30, 'replay': True,
    'replay_speed': 75, 'cursor': '2026-05-29 13:00:00',
}

# Node reporting windows for synthetic data generation (wall-clock).
GLOBAL_FIRST = '2026-02-22 00:00:00'
GLOBAL_LAST = '2026-06-30 23:00:00'
NODE_WINDOWS = {
    'ND-01': ('2026-02-22 00:00:00', GLOBAL_LAST, {'pm': 18, 'null_pm': 0.047}),
    'ND-02': ('2026-03-01 00:00:00', GLOBAL_LAST, {'pm': 21, 'uv_stuck': True}),
    'ND-03': ('2026-04-24 00:00:00', GLOBAL_LAST, {'pm': 14, 'pres_base': 920, 'tmp_sentinel': 0.01}),
    'ND-04': ('2026-04-23 00:00:00', GLOBAL_LAST, {'pm': 12, 'pres_base': 920}),
    'ND-05': ('2026-04-10 00:00:00', GLOBAL_LAST, {'pm': 0.36, 'hum_low': 11}),
    'ND-06': ('2026-04-10 00:00:00', GLOBAL_LAST, {'pm': 13, 'pres_base': 1010}),
}
