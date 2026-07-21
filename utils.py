import os
import sys
import json
import time
import signal
import hashlib
import base64
import random
import tempfile
import logging
import sqlite3
from urllib.request import Request, urlopen
from urllib.error import URLError
from functools import wraps

# --- ANSI RENKLERİ ---
class Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

# --- RAPID TERMINAL PRINTS ---
def log_ok(msg): print(f"{Color.GREEN}[+]{Color.RESET} {msg}")
def log_err(msg): print(f"{Color.RED}[-]{Color.RESET} {msg}", file=sys.stderr)
def log_warn(msg): print(f"{Color.YELLOW}[!]{Color.RESET} {msg}")
def log_info(msg): print(f"{Color.BLUE}[*]{Color.RESET} {msg}")

# --- SYSTEM & PATH ---
def get_path(rel_path):
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_dir, rel_path)

def safe_exit():
    def handler(sig, frame):
        print(f"\n{Color.YELLOW}[!] İşlem kullanıcı tarafından kesildi. Çıkılıyor...{Color.RESET}")
        sys.exit(0)
    signal.signal(signal.SIGINT, handler)

class GracefulLoop:
    def __init__(self):
        self.active = True
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    def stop(self, *args):
        print(f"\n{Color.YELLOW}[!] Durdurma sinyali alındı. Mevcut tur bitince temizce çıkılacak...{Color.RESET}")
        self.active = False

def get_arg(name, default=None):
    try:
        idx = sys.argv.index(name)
        if idx + 1 < len(sys.argv):
            val = sys.argv[idx + 1]
            return int(val) if val.isdigit() else val
    except ValueError:
        pass
    return default

# --- LOGGING ---
def init_log(level="INFO", file_path=None):
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return

    handlers = [logging.StreamHandler(sys.stdout)]
    if file_path:
        full_log_path = get_path(file_path)
        os.makedirs(os.path.dirname(full_log_path), exist_ok=True)
        handlers.append(logging.FileHandler(full_log_path, encoding="utf-8"))

    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S", handlers=handlers)

# --- SECURITY & CRYPTO ---
def file_sha256(path):
    h = hashlib.sha256()
    full_path = get_path(path)
    if not os.path.exists(full_path):
        return None
    try:
        with open(full_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        sys.stderr.write(f"[-] Hash hesaplama hatası: {e}\n")
        return None

def b64_encode(text):
    if not isinstance(text, str):
        return None
    try:
        return base64.b64encode(text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        sys.stderr.write(f"[-] Base64 encode hatası: {e}\n")
        return None

def b64_decode(encoded_text):
    if not isinstance(encoded_text, str):
        return None
    try:
        return base64.b64decode(encoded_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        sys.stderr.write(f"[-] Base64 decode hatası: {e}\n")
        return None

# --- STORAGE (READ / ATOMIC WRITE / SQLITE CACHE) ---
def read_json(p, fallback=None):
    full_path = get_path(p)
    if not os.path.exists(full_path):
        return fallback if fallback is not None else {}
    try:
        with open(full_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        sys.stderr.write(f"[!] {p} okuma hatası: {e}\n")
        return fallback if fallback is not None else {}

def save_json(p, data, format_json=True):
    full_path = get_path(p)
    try:
        d = os.path.dirname(full_path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            
        indent = 4 if format_json else None
        fd, temp_path = tempfile.mkstemp(dir=d or ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=indent, ensure_ascii=False)
            os.replace(temp_path, full_path)
            return True
        except Exception as write_err:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise write_err
    except Exception as e:
        sys.stderr.write(f"[!] {p} dosyasına güvenli yazma başarısız: {e}\n")
        return False

def cache_set(key, val, ttl=3600, db_name="cache.db"):
    db_path = get_path(db_name)
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, val TEXT, expire_at REAL)"
            )
            expire_at = time.time() + ttl
            serialized = json.dumps(val, ensure_ascii=False)
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, val, expire_at) VALUES (?, ?, ?)",
                (key, serialized, expire_at)
            )
    except Exception as e:
        sys.stderr.write(f"[-] Cache yazma hatası ({key}): {e}\n")

def cache_get(key, default=None, db_name="cache.db"):
    db_path = get_path(db_name)
    if not os.path.exists(db_path):
        return default
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.execute("DELETE FROM cache WHERE expire_at < ?", (time.time(),))
            cursor = conn.execute("SELECT val FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
    except Exception as e:
        sys.stderr.write(f"[-] Cache okuma hatası ({key}): {e}\n")
    return default

# --- CONFIG & ENV ---
def load_env(path=".env"):
    env = {}
    p = get_path(path)
    if not os.path.exists(p):
        return env
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k_clean = k.strip()
                    v_clean = v.strip().strip("'\"")
                    env[k_clean] = v_clean
                    os.environ[k_clean] = v_clean
    except Exception as e:
        sys.stderr.write(f"[!] .env okunurken hata: {e}\n")
    return env

def load_cfg(filename="config.json"):
    cfg = {}
    path = get_path(filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            sys.stderr.write(f"[!] Config okunamadı: {e}\n")
    
    for k, v in os.environ.items():
        if k.startswith("APP_"):
            clean_key = k.replace("APP_", "").lower()
            if v.lower() == "true":
                val = True
            elif v.lower() == "false":
                val = False
            elif v.isdigit():
                val = int(v)
            else:
                val = v
            cfg[clean_key] = val
    return cfg

# --- NETWORK ---
def fetch(url, method="GET", payload=None, headers=None, timeout=10):
    headers = headers or {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Windows/10) Gecko/20100101 Firefox/ezpy"

    data = None
    if payload:
        if isinstance(payload, dict):
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, str):
            data = payload.encode("utf-8")
        else:
            data = payload

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                return raw.decode("utf-8")
    except URLError as err:
        sys.stderr.write(f"[-] Bağlantı hatası ({url}): {err.reason}\n")
        return None
    except Exception as e:
        sys.stderr.write(f"[-] HTTP hatası: {e}\n")
        return None

def send_alert(webhook_url, text, title="HATA"):
    if not webhook_url:
        return False
    payload = {
        "content": f"**[{title}]** {text}" if "discord" in webhook_url else f"*{title}*: {text}"
    }
    res = fetch(webhook_url, method="POST", payload=payload)
    return res is not None

# --- IP SECURITY & FRAUD PROTECTION ---
def check_ip(ip=None):
    # ip-api.com free tier: Dakikada maks 45 istek hakkı vardır. Fazlasında IP'niz banlanır.
    # SSL/HTTPS ücretsiz planda desteklenmediği için HTTP kullanmak zorundayız.
    endpoint = "http://ip-api.com/json/"
    if ip:
        endpoint += ip
        
    url = f"{endpoint}?fields=status,message,country,regionName,city,isp,org,as,proxy,hosting,query"
    
    res = fetch(url, timeout=5)
    if not res:
        log_err("IP bilgisi çekilemedi (Ağ hatası veya Rate Limit engeli).")
        return None
        
    if res.get("status") == "fail":
        log_warn(f"IP-API Hatası: {res.get('message', 'Bilinmeyen hata')}")
        return None
        
    is_proxy = res.get("proxy", False)
    is_hosting = res.get("hosting", False)
    is_suspicious = is_proxy or is_hosting
    
    report = {
        "ip": res.get("query"),
        "country": res.get("country"),
        "city": res.get("city"),
        "isp": res.get("isp"),
        "proxy": is_proxy,
        "hosting": is_hosting,
        "suspicious": is_suspicious,
        "raw": res
    }
    
    if is_suspicious:
        log_warn(
            f"[!] Riskli IP! IP: {report['ip']} | Ülke: {report['country']} | "
            f"Proxy/VPN: {is_proxy} | Hosting/DC: {is_hosting}"
        )
    else:
        log_ok(f"IP Güvenli: {report['ip']} ({report['country']} - {report['city']})")
        
    return report

# --- RETRY & TIMING ---
def retry(attempts=3, delay=1, backoff=True, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == attempts - 1:
                        raise e
                    
                    jitter = current_delay * random.uniform(0.1, 0.3)
                    sleep_time = current_delay + jitter
                    
                    sys.stderr.write(
                        f"{Color.YELLOW}[!] Hata: {e}. "
                        f"{attempt + 1}/{attempts} deneme başarısız. "
                        f"{sleep_time:.2f}sn sonra tekrar denenecek...{Color.RESET}\n"
                    )
                    
                    time.sleep(sleep_time)
                    if backoff:
                        current_delay *= 2
        return wrapper
    return decorator

class Timer:
    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        t1 = time.perf_counter()
        print(f"[*] İşlem süresi: {t1 - self.t0:.4f} saniye")

# --- INTERACTIVE ---
def spin(duration=2, msg="Yükleniyor"):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    try:
        while time.time() < end_time:
            sys.stdout.write(f"\r{Color.BLUE}{frames[i % len(frames)]}{Color.RESET} {msg}...")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write("\r" + " " * (len(msg) + 10) + "\r")
        sys.stdout.flush()
    except KeyboardInterrupt:
        pass
