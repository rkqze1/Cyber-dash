import psutil
import datetime
import threading
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Header, Footer, Static, Input

from utils import (
    read_json, save_json, cache_get, cache_set, fetch, 
    log_ok, log_err, log_warn, log_info, get_path, retry,
    GracefulLoop, Timer
)

GOALS_FILE = "goals.json"

# Sözlük / Translation Dictionary
TRANSLATIONS = {
    "tr": {
        "sys_title": "🖥️ SİSTEM DURUMU",
        "cpu": "CPU Kullanımı:",
        "ram": "RAM Kullanımı:",
        "disk": "Disk Kullanımı:",
        "last_update": "Son Güncelleme:",
        "restricted": "Kısıtlı (Android)",
        "market_title": "📈 CANLI PİYASA & KRİPTO",
        "crypto_query": "Sorgu için: !crypto <coin>",
        "loading": "⏳ Yükleniyor...",
        "goals_title": "📝 GÜNLÜK HEDEFLER",
        "no_goals": "Henüz eklenmiş bir hedef yok.",
        "goal_cmds": "Komutlar: !add-daily, !del-daily, !clear-daily",
        "info_title": "⚙️ BİLGİ & ASİSTAN",
        "weather_prompt": "Hava Durumu: !weather <şehir>",
        "pomo_active": "POMODORO:",
        "pomo_inactive": "Pomodoro: Pasif (!pomo <dk>)",
        "pomo_done": "🔔 SÜRE DOLDU! Mola Zamanı!",
        "input_placeholder": "Komut yazın (Örn: !pomo 1, !weather London, !lang en)...",
        "not_found": "bulunamadı",
        "conn_error": "Bağlantı hatası",
    },
    "en": {
        "sys_title": "🖥️ SYSTEM STATUS",
        "cpu": "CPU Usage:",
        "ram": "RAM Usage:",
        "disk": "Disk Usage:",
        "last_update": "Last Update:",
        "restricted": "Restricted (Android)",
        "market_title": "📈 LIVE MARKET & CRYPTO",
        "crypto_query": "Query: !crypto <coin>",
        "loading": "⏳ Loading...",
        "goals_title": "📝 DAILY GOALS",
        "no_goals": "No goals added yet.",
        "goal_cmds": "Commands: !add-daily, !del-daily, !clear-daily",
        "info_title": "⚙️ INFO & ASSISTANT",
        "weather_prompt": "Weather: !weather <city>",
        "pomo_active": "POMODORO:",
        "pomo_inactive": "Pomodoro: Inactive (!pomo <min>)",
        "pomo_done": "🔔 TIME'S UP! Break Time!",
        "input_placeholder": "Type command (e.g. !pomo 1, !weather London, !lang tr)...",
        "not_found": "not found",
        "conn_error": "Connection error",
    }
}

def load_goals():
    """Utils'den read_json kullanarak hedefleri yükle"""
    goals = read_json(GOALS_FILE, fallback=[])
    if goals:
        log_ok(f"{len(goals)} hedef yüklendi")
    return goals

def save_goals(goals):
    """Utils'den save_json kullanarak hedefleri kaydet"""
    if save_json(GOALS_FILE, goals, format_json=True):
        log_ok(f"{len(goals)} hedef kaydedildi")
    else:
        log_err("Hedefler kaydedilemedi")

class SystemMonitorWidget(Static):
    """CPU, RAM ve Disk kullanımını saniyede bir güncelleyen widget"""
    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_stats)
        log_info("SystemMonitorWidget başlatıldı")

    def update_stats(self) -> None:
        lang = getattr(self.app, "current_lang", "tr")
        t = TRANSLATIONS[lang]

        try:
            cpu_val = f"%{psutil.cpu_percent()}"
        except PermissionError:
            cpu_val = t["restricted"]
        except Exception as e:
            log_err(f"CPU bilgisi alınamadı: {e}")
            cpu_val = "N/A"

        try:
            ram_val = f"%{psutil.virtual_memory().percent}"
        except PermissionError:
            ram_val = t["restricted"]
        except Exception as e:
            log_err(f"RAM bilgisi alınamadı: {e}")
            ram_val = "N/A"

        try:
            disk_val = f"%{psutil.disk_usage('/').percent}"
        except Exception as e:
            log_err(f"Disk bilgisi alınamadı: {e}")
            disk_val = "N/A"
        
        text = f"[bold]{t['sys_title']}[/bold]\n\n"
        text += f"⚡ [cyan]{t['cpu']}[/cyan]  {cpu_val}\n"
        text += f"🧠 [magenta]{t['ram']}[/magenta]  {ram_val}\n"
        text += f"💾 [yellow]{t['disk']}[/yellow] {disk_val}\n\n"
        text += f"[dim]{t['last_update']} {datetime.datetime.now().strftime('%H:%M:%S')}[/dim]"
        self.update(text)

class MarketWidget(Static):
    """Döviz ve Kripto Fiyatları Widget'ı - Utils fetch() kullanır"""
    FRANKFURTER_API = "https://api.frankfurter.app/latest?to=TRY,USD,GBP"
    CACHE_TTL = 3600  # 1 saat cache

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.crypto_symbol = "BTC"
        self.crypto_price = "Yükleniyor..."
        self.fiat_text = "Yükleniyor..."

    def on_mount(self) -> None:
        self.set_interval(60.0, self.fetch_rates)
        self.fetch_rates()
        self.fetch_crypto("btc")
        log_info("MarketWidget başlatıldı")

    @work(thread=True)
    @retry(attempts=3, delay=2, backoff=True, exceptions=(Exception,))
    def fetch_rates(self) -> None:
        """Utils fetch() ile döviz oranlarını çek"""
        log_info("Döviz oranları çekiliyor...")
        
        # Önce cache'den kontrol et
        cached = cache_get("market_rates")
        if cached:
            log_ok("Döviz oranları cache'den alındı")
            self.fiat_text = cached
            self.refresh_display()
            return

        data = fetch(self.FRANKFURTER_API, timeout=5)
        
        if data:
            rates = data.get("rates", {})
            eur_try = rates.get("TRY", 0)
            usd = rates.get("USD", 1)
            gbp = rates.get("GBP", 1)
            
            usd_try = eur_try / usd if usd else 0
            gbp_try = eur_try / gbp if gbp else 0
            
            self.fiat_text = (
                f"💵 [cyan]USD/TRY:[/cyan]  {usd_try:.2f} ₺\n"
                f"💶 [magenta]EUR/TRY:[/magenta]  {eur_try:.2f} ₺\n"
                f"💷 [yellow]GBP/TRY:[/yellow]  {gbp_try:.2f} ₺"
            )
            # Cache'e kaydet
            cache_set("market_rates", self.fiat_text, ttl=self.CACHE_TTL)
            log_ok("Döviz oranları güncellendi")
        else:
            self.fiat_text = "⚠️ N/A"
            log_err("Döviz oranları çekilemedi")
        
        self.refresh_display()

    @work(thread=True)
    @retry(attempts=3, delay=2, backoff=True, exceptions=(Exception,))
    def fetch_crypto(self, symbol: str) -> None:
        """Utils fetch() ile kripto fiyatını çek"""
        log_info(f"Kripto sorgulanıyor: {symbol}")
        
        sym = symbol.upper()
        
        # Önce cache'den kontrol et
        cache_key = f"crypto_{sym}"
        cached = cache_get(cache_key)
        if cached:
            log_ok(f"{sym} cache'den alındı")
            self.crypto_symbol = sym
            self.crypto_price = cached
            self.refresh_display()
            return

        url = f"https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT"
        res = fetch(url, timeout=5)
        
        if res:
            try:
                price = float(res.get("price", 0))
                self.crypto_symbol = sym
                self.crypto_price = f"${price:,.2f}"
                # Cache'e kaydet
                cache_set(cache_key, self.crypto_price, ttl=self.CACHE_TTL)
                log_ok(f"{sym} fiyatı güncellendi: {self.crypto_price}")
            except (ValueError, TypeError) as e:
                self.crypto_price = "Error"
                log_err(f"Kripto fiyatı parse hatası: {e}")
        else:
            self.crypto_price = "Error"
            log_err(f"{sym} fiyatı çekilemedi")
        
        self.refresh_display()

    def refresh_display(self) -> None:
        lang = getattr(self.app, "current_lang", "tr")
        t = TRANSLATIONS[lang]
        
        text = f"[bold]{t['market_title']}[/bold]\n\n"
        text += f"{self.fiat_text}\n"
        text += f"─────────────────────\n"
        text += f"🪙 [yellow]{self.crypto_symbol}/USDT:[/yellow] {self.crypto_price}\n\n"
        text += f"[dim]{t['crypto_query']}[/dim]"
        
        # Thread Güvenli Güncelleme Kontrolü
        if threading.get_ident() == self.app._thread_id:
            self.update(text)
        else:
            self.app.call_from_thread(self.update, text)

class TodoWidget(Static):
    """JSON Kayıtlı Günlük Hedefler Widget'ı - Utils read_json/save_json kullanır"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.goals = load_goals()

    def on_mount(self) -> None:
        self.render_goals()
        log_info("TodoWidget başlatıldı")

    def add_goal(self, goal_text: str) -> None:
        self.goals.append(goal_text)
        save_goals(self.goals)
        self.render_goals()
        log_info(f"Hedef eklendi: {goal_text}")

    def del_goal(self, index: int) -> None:
        if 1 <= index <= len(self.goals):
            removed = self.goals.pop(index - 1)
            save_goals(self.goals)
            self.render_goals()
            log_ok(f"Hedef silindi: {removed}")
        else:
            log_warn(f"Geçersiz hedef indeksi: {index}")

    def clear_goals(self) -> None:
        count = len(self.goals)
        self.goals.clear()
        save_goals(self.goals)
        self.render_goals()
        log_ok(f"{count} hedef temizlendi")

    def render_goals(self) -> None:
        lang = getattr(self.app, "current_lang", "tr")
        t = TRANSLATIONS[lang]

        content = f"[bold]{t['goals_title']}[/bold]\n\n"
        if not self.goals:
            content += f"[dim]{t['no_goals']}[/dim]\n\n"
        else:
            for i, goal in enumerate(self.goals, 1):
                content += f"[bold cyan]{i}.[/bold cyan] {goal}\n"
            content += "\n"

        content += f"[dim]{t['goal_cmds']}[/dim]"
        self.update(content)

class InfoWidget(Static):
    """Hava Durumu, Pomodoro & Bilgi Widget'ı - Utils fetch() kullanır"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.city_name = "Istanbul"
        self.weather_temp = "N/A"
        self.pomo_seconds = 0
        self.pomo_active = False

    def on_mount(self) -> None:
        self.set_interval(1.0, self.tick_pomo)
        self.fetch_weather("Istanbul")
        log_info("InfoWidget başlatıldı")

    def tick_pomo(self) -> None:
        if self.pomo_active and self.pomo_seconds > 0:
            self.pomo_seconds -= 1
            if self.pomo_seconds == 0:
                self.pomo_active = False
                self.app.bell()
                log_ok("Pomodoro tamamlandı!")
            self.render_widget()

    def start_pomo(self, minutes: int) -> None:
        self.pomo_seconds = minutes * 60
        self.pomo_active = True
        self.render_widget()
        log_ok(f"Pomodoro başlatıldı: {minutes} dakika")

    def stop_pomo(self) -> None:
        self.pomo_active = False
        self.pomo_seconds = 0
        self.render_widget()
        log_warn("Pomodoro durduruldu")

    @work(thread=True)
    @retry(attempts=2, delay=1, backoff=True, exceptions=(Exception,))
    def fetch_weather(self, city: str) -> None:
        """Utils fetch() ile hava durumunu çek"""
        log_info(f"Hava durumu sorgulanıyor: {city}")
        
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_res = fetch(geo_url, timeout=5)
        
        if geo_res:
            results = geo_res.get("results")
            if results:
                lat, lon = results[0]["latitude"], results[0]["longitude"]
                self.city_name = results[0]["name"]
                
                w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                w_res = fetch(w_url, timeout=5)
                
                if w_res:
                    cw = w_res.get("current_weather", {})
                    temp = cw.get("temperature", "N/A")
                    code = cw.get("weathercode", 0)
                    
                    icon = "☀️" if code == 0 else "🌤️" if code in [1, 2, 3] else "🌧️" if code >= 50 else "🌫️"
                    self.weather_temp = f"{icon} {temp}°C"
                    log_ok(f"Hava durumu güncelleştirildi: {self.city_name}")
                else:
                    self.weather_temp = "N/A"
                    log_err("Hava durumu API'si yanıt vermedi")
            else:
                self.weather_temp = "N/A"
                log_warn(f"Şehir bulunamadı: {city}")
        else:
            self.weather_temp = "Err"
            log_err("Geocoding API hatası")
            
        if threading.get_ident() == self.app._thread_id:
            self.render_widget()
        else:
            self.app.call_from_thread(self.render_widget)

    def render_widget(self) -> None:
        lang = getattr(self.app, "current_lang", "tr")
        t = TRANSLATIONS[lang]

        text = f"[bold]{t['info_title']}[/bold]\n\n"
        text += f"🌍 {self.city_name}: {self.weather_temp}\n\n"
        
        if self.pomo_active and self.pomo_seconds > 0:
            mins, secs = divmod(self.pomo_seconds, 60)
            text += f"⏱️ [bold red]{t['pomo_active']}[/bold red] [yellow]{mins:02d}:{secs:02d}[/yellow]\n"
        elif self.pomo_seconds == 0 and not self.pomo_active:
            text += f"⏱️ [dim]{t['pomo_inactive']}[/dim]\n"
        else:
            text += f"🔔 [bold green]{t['pomo_done']}[/bold green]\n"
            
        self.update(text)

class CyberDash(App):
    """Ana Terminal Uygulaması - Utils kütüphanesi entegrasyonu"""
    TITLE = "CYBER-DASH v2.5"
    SUB_TITLE = "Multi-Language TUI Dashboard"
    
    current_lang = "tr"  # Varsayılan dil: Türkçe

    CSS = """
    Screen { background: #0d1117; }
    Header { background: #161b22; color: #3fb950; }
    Footer { background: #161b22; color: #8b949e; }
    Grid { layout: grid; grid-size: 2 2; grid-gutter: 1 2; padding: 1; }
    .box { border: heavy #238636; background: #161b22; color: #c9d1d9; height: 100%; padding: 1; }
    Input { dock: bottom; margin: 0 1 1 1; border: heavy #238636; background: #161b22; color: #3fb950; }

    /* Dracula Tema */
    Screen.theme-dracula { background: #282a36; }
    Screen.theme-dracula Header { background: #44475a; color: #ff79c6; }
    Screen.theme-dracula Footer { background: #44475a; color: #f8f8f2; }
    Screen.theme-dracula .box { border: heavy #bd93f9; background: #44475a; color: #f8f8f2; }
    Screen.theme-dracula Input { border: heavy #ff79c6; background: #44475a; color: #ff79c6; }

    /* Nord Tema */
    Screen.theme-nord { background: #2e3440; }
    Screen.theme-nord Header { background: #3b4252; color: #88c0d0; }
    Screen.theme-nord Footer { background: #3b4252; color: #d8dee9; }
    Screen.theme-nord .box { border: heavy #88c0d0; background: #3b4252; color: #d8dee9; }
    Screen.theme-nord Input { border: heavy #88c0d0; background: #3b4252; color: #88c0d0; }

    /* Cyberpunk Tema */
    Screen.theme-cyberpunk { background: #000b1e; }
    Screen.theme-cyberpunk Header { background: #001535; color: #ff0055; }
    Screen.theme-cyberpunk Footer { background: #001535; color: #00f0ff; }
    Screen.theme-cyberpunk .box { border: heavy #00f0ff; background: #001535; color: #ffffff; }
    Screen.theme-cyberpunk Input { border: heavy #ff0055; background: #001535; color: #00f0ff; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Grid(
            SystemMonitorWidget(classes="box", id="sys-widget"),
            MarketWidget(classes="box", id="market-widget"),
            TodoWidget(classes="box", id="todo-widget"),
            InfoWidget(classes="box", id="info-widget"),
        )
        yield Input(
            placeholder=TRANSLATIONS[self.current_lang]["input_placeholder"], 
            id="cmd-input"
        )
        yield Footer()

    def on_mount(self) -> None:
        """App başlayınca log yazdır"""
        log_ok("CyberDash başlatıldı")

    def refresh_all_widgets(self) -> None:
        """Dil değiştiğinde tüm ekranı güvenli şekilde günceller"""
        self.query_one("#sys-widget", SystemMonitorWidget).update_stats()
        self.query_one("#market-widget", MarketWidget).refresh_display()
        self.query_one("#todo-widget", TodoWidget).render_goals()
        self.query_one("#info-widget", InfoWidget).render_widget()
        
        input_widget = self.query_one("#cmd-input", Input)
        input_widget.placeholder = TRANSLATIONS[self.current_lang]["input_placeholder"]
        log_ok(f"Dil değiştirildi: {self.current_lang}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        cmd_text = event.value.strip()
        event.input.value = ""
        
        if not cmd_text:
            return

        log_info(f"Komut: {cmd_text}")
        
        todo_widget = self.query_one("#todo-widget", TodoWidget)
        market_widget = self.query_one("#market-widget", MarketWidget)
        info_widget = self.query_one("#info-widget", InfoWidget)

        # Dil Değiştirme
        if cmd_text.startswith("!lang"):
            lang_code = cmd_text[len("!lang"):].strip().lower()
            if lang_code in TRANSLATIONS:
                self.current_lang = lang_code
                self.refresh_all_widgets()
            else:
                log_warn(f"Geçersiz dil: {lang_code}")

        # Hedef Komutları
        elif cmd_text.startswith("!add-daily"):
            goal = cmd_text[len("!add-daily"):].strip()
            if goal:
                todo_widget.add_goal(goal)
            else:
                log_warn("Hedef metni boş")
        
        elif cmd_text.startswith("!del-daily"):
            try:
                idx = int(cmd_text[len("!del-daily"):].strip())
                todo_widget.del_goal(idx)
            except ValueError:
                log_err("Geçersiz indeks")
        
        elif cmd_text == "!clear-daily":
            todo_widget.clear_goals()

        # Hava Durumu
        elif cmd_text.startswith("!weather"):
            city = cmd_text[len("!weather"):].strip()
            if city:
                info_widget.fetch_weather(city)
            else:
                log_warn("Şehir adı boş")

        # Kripto
        elif cmd_text.startswith("!crypto"):
            coin = cmd_text[len("!crypto"):].strip()
            if coin:
                market_widget.fetch_crypto(coin)
            else:
                log_warn("Kripto adı boş")

        # Pomodoro
        elif cmd_text.startswith("!pomo"):
            param = cmd_text[len("!pomo"):].strip()
            if param == "stop":
                info_widget.stop_pomo()
            elif param.isdigit():
                info_widget.start_pomo(int(param))
            else:
                log_warn("Geçersiz pomodoro parametresi")

        # Tema Değiştirici
        elif cmd_text.startswith("!theme"):
            theme_name = cmd_text[len("!theme"):].strip().lower()
            self.screen.remove_class("theme-dracula", "theme-nord", "theme-cyberpunk")
            if theme_name in ["dracula", "nord", "cyberpunk"]:
                self.screen.add_class(f"theme-{theme_name}")
                log_ok(f"Tema değiştirildi: {theme_name}")
            else:
                log_warn(f"Geçersiz tema: {theme_name}")

if __name__ == "__main__":
    log_ok("Uygulama başlıyor...")
    graceful = GracefulLoop()
    try:
        app = CyberDash()
        app.run()
    except KeyboardInterrupt:
        log_warn("Uygulama kullanıcı tarafından durduruldu")
    except Exception as e:
        log_err(f"Beklenmeyen hata: {e}")
