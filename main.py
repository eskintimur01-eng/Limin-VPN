import asyncio
import base64
import io
import math
import struct
import time
import wave
import flet as ft


# Генератор звуков кнопок и подключения (WAV в base64, без внешних файлов)
def make_tone_base64(freq: float, duration_ms: int, volume: float = 0.25) -> str:
    sample_rate = 22050
    num_samples = int(sample_rate * (duration_ms / 1000.0))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            env = math.sin(math.pi * (i / num_samples))
            sample = int(32767 * volume * env * math.sin(2 * math.pi * freq * i / sample_rate))
            frames.extend(struct.pack("<h", sample))
        wf.writeframes(bytes(frames))
    return base64.b64encode(buf.getvalue()).decode("ascii")


SOUND_CLICK = make_tone_base64(720, 55, 0.22)
SOUND_ON = make_tone_base64(980, 140, 0.28)
SOUND_OFF = make_tone_base64(420, 140, 0.28)


def main(page: ft.Page):
    page.title = "BlueShield VPN"
    page.bgcolor = "#060D1F"
    page.padding = 0
    page.window.width = 410
    page.window.height = 760
    page.theme_mode = ft.ThemeMode.DARK

    state = {
        "connected": False,
        "start_time": 0.0,
        "sound_enabled": True,
        "auto_connect": False,
        "kill_switch": True,
        "selected_server": "Нидерланды #1 (VLESS-Reality)",
        "selected_dns": "Cloudflare (1.1.1.1)",
        "servers": [
            {"name": "Нидерланды #1 (VLESS-Reality)", "ping": "38 мс", "uri": "vless://example-nl-1"},
            {"name": "Германия #2 (WireGuard)", "ping": "44 мс", "uri": "wg://example-de-2"},
            {"name": "Финляндия #3 (AmneziaWG)", "ping": "31 мс", "uri": "awg://example-fi-3"},
            {"name": "США #4 (WARP+ Tunnel)", "ping": "118 мс", "uri": "warp://example-us-4"},
        ],
        "dns_list": [
            "Cloudflare (1.1.1.1)",
            "Google DNS (8.8.8.8)",
            "AdGuard DNS (94.140.14.14)",
            "Quad9 (9.9.9.9)",
        ],
        "logs": [
            "[Система] Интерфейс инициализирован.",
            "[Сеть] Готов к подключению.",
        ],
    }

    audio_player = ft.Audio(src_base64=SOUND_CLICK, autoplay=False)
    page.overlay.append(audio_player)

    def play_sound(sound_b64: str):
        if not state["sound_enabled"]:
            return
        audio_player.src_base64 = sound_b64
        audio_player.update()
        audio_player.play()

    def add_log(msg: str):
        ts = time.strftime("%H:%M:%S")
        state["logs"].append(f"[{ts}] {msg}")
        if len(state["logs"]) > 30:
            state["logs"].pop(0)

    status_text = ft.Text(
        "ОТКЛЮЧЕНО",
        size=18,
        weight=ft.FontWeight.BOLD,
        color="#6EA8FE",
    )

    timer_text = ft.Text(
        "00:00:00",
        size=32,
        weight=ft.FontWeight.W_700,
        color="#E2ECFF",
        font_family="monospace",
    )

    sub_info_text = ft.Text(
        f"Сервер: {state['selected_server']}\nDNS: {state['selected_dns']}",
        size=13,
        color="#8CA8D8",
        text_align=ft.TextAlign.CENTER,
    )

    pulse_ring = ft.Container(
        width=185,
        height=185,
        border_radius=100,
        bgcolor="#1A6BFF22",
        border=ft.border.all(3, "#2D8CFF"),
        scale=1.0,
        opacity=0.0,
        animate_scale=ft.Animation(650, ft.AnimationCurve.EASE_OUT),
        animate_opacity=ft.Animation(650, ft.AnimationCurve.EASE_OUT),
    )

    power_icon = ft.Icon(
        ft.icons.POWER_SETTINGS_NEW_ROUNDED,
        size=84,
        color="#040B1A",
    )

    power_button = ft.Container(
        width=165,
        height=165,
        border_radius=90,
        bgcolor="#1967FF",
        border=ft.border.all(4, "#4DA3FF"),
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=24,
            color="#1967FF88",
        ),
        ink=True,
        ink_color="#99D1FF",
        content=power_icon,
        animate=ft.Animation(250, ft.AnimationCurve.EASE_IN_OUT),
    )

    async def trigger_blue_pulse():
        pulse_ring.scale = 1.0
        pulse_ring.opacity = 0.95
        pulse_ring.update()
        await asyncio.sleep(0.05)
        pulse_ring.scale = 1.38
        pulse_ring.opacity = 0.0
        pulse_ring.update()

    async def toggle_vpn(e):
        state["connected"] = not state["connected"]
        page.run_task(trigger_blue_pulse)

        if state["connected"]:
            play_sound(SOUND_ON)
            state["start_time"] = time.time()
            power_button.bgcolor = "#00A3FF"
            power_button.border = ft.border.all(4, "#8CE0FF")
            power_button.shadow = ft.BoxShadow(
                spread_radius=6,
                blur_radius=36,
                color="#00A3FFCC",
            )
            status_text.value = "ПОДКЛЮЧЕНО"
            status_text.color = "#4CE8FF"
            add_log(f"Подключено к {state['selected_server']}")
            add_log(f"Активный DNS: {state['selected_dns']}")
        else:
            play_sound(SOUND_OFF)
            power_button.bgcolor = "#1967FF"
            power_button.border = ft.border.all(4, "#4DA3FF")
            power_button.shadow = ft.BoxShadow(
                spread_radius=2,
                blur_radius=24,
                color="#1967FF88",
            )
            status_text.value = "ОТКЛЮЧЕНО"
            status_text.color = "#6EA8FE"
            timer_text.value = "00:00:00"
            add_log("VPN отключён пользователем.")

        sub_info_text.value = f"Сервер: {state['selected_server']}\nDNS: {state['selected_dns']}"
        page.update()

    power_button.on_click = toggle_vpn

    async def timer_and_pulse_loop():
        tick = 0
        while True:
            await asyncio.sleep(1)
            if state["connected"]:
                elapsed = int(time.time() - state["start_time"])
                hrs = elapsed // 3600
                mins = (elapsed % 3600) // 60
                secs = elapsed % 60
                timer_text.value = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                timer_text.update()

                tick += 1
                if tick % 2 == 0:
                    page.run_task(trigger_blue_pulse)

    def nav_icon_button(icon_name, tooltip: str, on_click_fn):
        def handle_click(e):
            play_sound(SOUND_CLICK)
            on_click_fn(e)

        return ft.Container(
            width=54,
            height=46,
            border_radius=12,
            ink=True,
            ink_color="#80D4FF",
            alignment=ft.alignment.center,
            tooltip=tooltip,
            on_click=handle_click,
            content=ft.Icon(icon_name, size=28, color="#040B1A"),
        )

    def build_home_view():
        return ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=18,
            controls=[
                status_text,
                timer_text,
                ft.Container(height=8),
                ft.Stack(
                    width=220,
                    height=220,
                    alignment=ft.alignment.center,
                    controls=[pulse_ring, power_button],
                ),
                ft.Container(height=8),
                sub_info_text,
            ],
        )

    def build_servers_dns_view():
        custom_uri_field = ft.TextField(
            label="Вставь ключ (vless://, wg://, ss://)",
            border_color="#2D8CFF",
            focused_border_color="#66C2FF",
            text_size=13,
        )

        def add_custom_server(e):
            play_sound(SOUND_CLICK)
            val = custom_uri_field.value.strip()
            if val:
                short_name = f"Мой сервер #{len(state['servers']) + 1}"
                state["servers"].append({"name": short_name, "ping": "тест", "uri": val})
                state["selected_server"] = short_name
                custom_uri_field.value = ""
                add_log(f"Добавлен пользовательский сервер: {short_name}")
                switch_screen("servers")

        server_tiles = []
        for srv in state["servers"]:
            is_active = srv["name"] == state["selected_server"]

            def select_srv(e, name=srv["name"]):
                play_sound(SOUND_CLICK)
                state["selected_server"] = name
                add_log(f"Выбран сервер: {name}")
                switch_screen("servers")

            server_tiles.append(
                ft.Container(
                    padding=12,
                    border_radius=12,
                    bgcolor="#102247" if is_active else "#0B1733",
                    border=ft.border.all(2 if is_active else 1, "#3399FF" if is_active else "#1D3566"),
                    ink=True,
                    ink_color="#66C2FF",
                    on_click=select_srv,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(srv["name"], size=14, weight=ft.FontWeight.W_600, color="#E2ECFF"),
                            ft.Text(srv["ping"], size=12, color="#4CE8FF"),
                        ],
                    ),
                )
            )

        dns_dropdown = ft.Dropdown(
            label="Текущий DNS",
            value=state["selected_dns"],
            border_color="#2D8CFF",
            options=[ft.dropdown.Option(d) for d in state["dns_list"]],
            on_change=lambda e: (
                play_sound(SOUND_CLICK),
                state.update({"selected_dns": e.control.value}),
                add_log(f"DNS изменён на {e.control.value}"),
            ),
        )

        return ft.ListView(
            expand=True,
            padding=16,
            spacing=10,
            controls=[
                ft.Text("Выбор сервера и DNS", size=20, weight=ft.FontWeight.BOLD, color="#6EA8FE"),
                dns_dropdown,
                ft.Divider(color="#1D3566"),
                ft.Text("Доступные серверы:", size=15, weight=ft.FontWeight.W_600, color="#B8D4FF"),
                *server_tiles,
                ft.Divider(color="#1D3566"),
                custom_uri_field,
                ft.ElevatedButton(
                    "Добавить свой конфиг",
                    bgcolor="#1967FF",
                    color="#FFFFFF",
                    on_click=add_custom_server,
                ),
            ],
        )

    def build_version_connect_view():
        log_lines = [ft.Text(line, size=12, font_family="monospace", color="#9EC5FE") for line in state["logs"]]
        return ft.ListView(
            expand=True,
            padding=16,
            spacing=10,
            controls=[
                ft.Text("Версия и статус коннекта", size=20, weight=ft.FontWeight.BOLD, color="#6EA8FE"),
                ft.Container(
                    padding=14,
                    border_radius=12,
                    bgcolor="#0B1733",
                    border=ft.border.all(1, "#1D3566"),
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            ft.Text("Версия клиента: v1.0.0 BlueShield", color="#E2ECFF"),
                            ft.Text("Ядро туннеля: Xray / WireGuard Core", color="#8CA8D8"),
                            ft.Text(
                                f"Состояние: {'Активно' if state['connected'] else 'Ожидание'}",
                                color="#4CE8FF" if state["connected"] else "#8CA8D8",
                            ),
                        ],
                    ),
                ),
                ft.Text("Журнал подключения:", size=15, weight=ft.FontWeight.W_600, color="#B8D4FF"),
                ft.Container(
                    padding=12,
                    border_radius=12,
                    bgcolor="#081126",
                    border=ft.border.all(1, "#1D3566"),
                    content=ft.Column(spacing=4, controls=log_lines),
                ),
            ],
        )

    def build_settings_view():
        return ft.ListView(
            expand=True,
            padding=16,
            spacing=14,
            controls=[
                ft.Text("Настройки", size=20, weight=ft.FontWeight.BOLD, color="#6EA8FE"),
                ft.Switch(
                    label="Звуки кнопок и подключения",
                    value=state["sound_enabled"],
                    active_color="#2D8CFF",
                    on_change=lambda e: state.update({"sound_enabled": e.control.value}),
                ),
                ft.Switch(
                    label="Автоподключение при запуске",
                    value=state["auto_connect"],
                    active_color="#2D8CFF",
                    on_change=lambda e: (
                        play_sound(SOUND_CLICK),
                        state.update({"auto_connect": e.control.value}),
                    ),
                ),
                ft.Switch(
                    label="Блокировка трафика при обрыве (Kill Switch)",
                    value=state["kill_switch"],
                    active_color="#2D8CFF",
                    on_change=lambda e: (
                        play_sound(SOUND_CLICK),
                        state.update({"kill_switch": e.control.value}),
                    ),
                ),
            ],
        )

    content_area = ft.Container(expand=True, content=build_home_view())

    def switch_screen(screen_name: str):
        if screen_name == "home":
            sub_info_text.value = f"Сервер: {state['selected_server']}\nDNS: {state['selected_dns']}"
            content_area.content = build_home_view()
        elif screen_name == "servers":
            content_area.content = build_servers_dns_view()
        elif screen_name == "version":
            content_area.content = build_version_connect_view()
        elif screen_name == "settings":
            content_area.content = build_settings_view()
        page.update()

    def exit_app(e):
        page.window.close()

    top_bar = ft.Container(
        height=58,
        bgcolor="#1967FF",
        padding=ft.padding.symmetric(horizontal=10),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                nav_icon_button(ft.icons.SETTINGS, "Настройки", lambda e: switch_screen("settings")),
                ft.Text("BLUE VPN", size=16, weight=ft.FontWeight.BOLD, color="#040B1A"),
                nav_icon_button(ft.icons.CLOSE_ROUNDED, "Выход", exit_app),
            ],
        ),
    )

    bottom_bar = ft.Container(
        height=62,
        bgcolor="#1967FF",
        padding=ft.padding.symmetric(horizontal=14),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                nav_icon_button(ft.icons.BUILD_ROUNDED, "Версия и коннект", lambda e: switch_screen("version")),
                nav_icon_button(ft.icons.HOME_ROUNDED, "Главное меню", lambda e: switch_screen("home")),
                nav_icon_button(ft.icons.PUBLIC_ROUNDED, "Серверы и DNS", lambda e: switch_screen("servers")),
            ],
        ),
    )

    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[
                top_bar,
                content_area,
                bottom_bar,
            ],
        )
    )

    page.run_task(timer_and_pulse_loop)


if __name__ == "__main__":
    ft.app(target=main)