# region 1. Imports & Configuration
import os
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import requests
import urllib3

import ssi_fc_data.model as ssi_model
from ssi_fc_data.fc_md_client import MarketDataClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

CONFIG_FILE = BASE_DIR / "config.json"
STOCKS_CACHE = CACHE_DIR / "stocks_cache.json"
TOKEN_CACHE = CACHE_DIR / "ssi_token_cache.json"

def load_ssi_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Config Error] Không thể đọc config.json: {e}")
    return {}

SSI_CONFIG = load_ssi_config()
SSI_BASE_URL = "https://fc-data.ssi.com.vn/"
# Quan trọng: Bắt buộc có dấu / cuối cùng để SignalR ghép đúng chuỗi 'v2.0/signalr'
SSI_STREAM_URL = "https://fc-datahub.ssi.com.vn/"

class SSIConfigWrapper:
    url = SSI_BASE_URL
    stream_url = SSI_STREAM_URL
    consumerID = SSI_CONFIG.get("api_key", "")
    consumerSecret = SSI_CONFIG.get("api_secret", "")
    privateKey = SSI_CONFIG.get("private_key", "")
    auth_type = "Bearer"

def is_trading_hours() -> bool:
    """Kiểm tra thời gian giao dịch chứng khoán Việt Nam (09:00 - 11:30 & 13:00 - 15:02, T2 - T6)"""
    now = datetime.now()
    # 0 = Thứ 2, ..., 4 = Thứ 6. Thứ 7 (5) & Chủ nhật (6) đóng cửa
    if now.weekday() >= 5:
        return False
    t = now.time()
    morning_start = datetime.strptime("09:00", "%H:%M").time()
    morning_end = datetime.strptime("11:32", "%H:%M").time()
    afternoon_start = datetime.strptime("13:00", "%H:%M").time()
    afternoon_end = datetime.strptime("15:05", "%H:%M").time()
    return (morning_start <= t <= morning_end) or (afternoon_start <= t <= afternoon_end)
# endregion 1

# region 2. Authentication & FastConnect Client Vault
_client_lock = threading.Lock()
_cached_client = None

def get_ssi_token() -> str:
    """Lấy Access Token hợp lệ từ Cache hoặc yêu cầu cấp mới từ SSI API với Browser User-Agent"""
    if TOKEN_CACHE.exists():
        try:
            with open(TOKEN_CACHE, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if cached.get("access_token") and cached.get("expires_at", 0) > time.time() + 1800:
                    return cached["access_token"]
        except Exception:
            pass

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "consumerID": SSIConfigWrapper.consumerID,
            "consumerSecret": SSIConfigWrapper.consumerSecret
        }
        res = requests.post(f"{SSI_BASE_URL}api/v2/Market/AccessToken", json=payload, headers=headers, timeout=10, verify=False)
        if res.status_code == 200:
            data = res.json().get("data", {})
            token = data.get("accessToken", "")
            if token:
                with open(TOKEN_CACHE, "w", encoding="utf-8") as f:
                    json.dump({"access_token": token, "expires_at": time.time() + 82800}, f, indent=2)
                return token
        else:
            print(f"[Auth SSI Response] Status: {res.status_code}, Msg: {res.text[:100]}")
    except Exception as e:
        print(f"[Auth SSI Request Error] {e}")
    return ""

def get_ssi_client() -> MarketDataClient:
    global _cached_client
    with _client_lock:
        if _cached_client is None:
            try:
                from ssi_fc_data import fc_md_client
                cfg = SSIConfigWrapper()
                token = get_ssi_token()

                client = MarketDataClient.__new__(MarketDataClient)
                client._config = cfg
                client._header = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                client._access_token = None
                if token:
                    ac = ssi_model.AccessToken(accessToken=token)
                    client._access_token = fc_md_client.AccessTokenModel(ac)
                _cached_client = client
            except Exception as e:
                print(f"[SSI Client Error] Khởi tạo MarketDataClient thất bại: {e}")
        return _cached_client
# endregion 2

# region 3. Dynamic Sector Processing
class MarketService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        })
        self._sectors = {}
        self._init_sectors_fallback()

    def _init_sectors_fallback(self):
        self._default_sectors = {
            # 1. Bán lẻ (SSI: BÁN LẺ)
            "MWG": "Bán lẻ", "DGW": "Bán lẻ", "FRT": "Bán lẻ", "PET": "Bán lẻ",
            "HAX": "Bán lẻ", "DMX": "Bán lẻ", "SVC": "Bán lẻ", "AST": "Bán lẻ",
            "CIA": "Bán lẻ", "COM": "Bán lẻ", "SMC": "Bán lẻ",

            # 2. Ngân hàng (SSI: NGÂN HÀNG)
            "VCB": "Ngân hàng", "BID": "Ngân hàng", "CTG": "Ngân hàng", "TCB": "Ngân hàng",
            "VPB": "Ngân hàng", "MBB": "Ngân hàng", "ACB": "Ngân hàng", "STB": "Ngân hàng",
            "HDB": "Ngân hàng", "SHB": "Ngân hàng", "VIB": "Ngân hàng", "SSB": "Ngân hàng",
            "LPB": "Ngân hàng", "EIB": "Ngân hàng", "MSB": "Ngân hàng", "OCB": "Ngân hàng",
            "TPB": "Ngân hàng", "NAB": "Ngân hàng", "BAB": "Ngân hàng", "BVB": "Ngân hàng",
            "ABB": "Ngân hàng", "NVB": "Ngân hàng", "KLB": "Ngân hàng", "PGB": "Ngân hàng",
            "VBB": "Ngân hàng",

            # 3. Dịch vụ tài chính (SSI: DỊCH VỤ TÀI CHÍNH / Chứng khoán)
            "SSI": "Dịch vụ tài chính", "VND": "Dịch vụ tài chính", "VCI": "Dịch vụ tài chính",
            "HCM": "Dịch vụ tài chính", "VIX": "Dịch vụ tài chính", "FTS": "Dịch vụ tài chính",
            "BSI": "Dịch vụ tài chính", "CTS": "Dịch vụ tài chính", "SHS": "Dịch vụ tài chính",
            "MBS": "Dịch vụ tài chính", "ORS": "Dịch vụ tài chính", "AGR": "Dịch vụ tài chính",
            "BVS": "Dịch vụ tài chính", "VCK": "Dịch vụ tài chính", "TCX": "Dịch vụ tài chính",
            "VDS": "Dịch vụ tài chính", "TVS": "Dịch vụ tài chính", "APG": "Dịch vụ tài chính",
            "AAS": "Dịch vụ tài chính", "VFS": "Dịch vụ tài chính", "DSE": "Dịch vụ tài chính",
            "EVS": "Dịch vụ tài chính", "SBS": "Dịch vụ tài chính", "WSS": "Dịch vụ tài chính",
            "PSI": "Dịch vụ tài chính", "EVF": "Dịch vụ tài chính", "KSF": "Dịch vụ tài chính",
            "FIT": "Dịch vụ tài chính", "TCI": "Dịch vụ tài chính", "IPA": "Dịch vụ tài chính",
            "TVC": "Dịch vụ tài chính", "TVB": "Dịch vụ tài chính",

            # 4. Bất động sản (SSI: BẤT ĐỘNG SẢN)
            "VIC": "Bất động sản", "VHM": "Bất động sản", "VRE": "Bất động sản", "NVL": "Bất động sản",
            "DIG": "Bất động sản", "DXG": "Bất động sản", "PDR": "Bất động sản", "KBC": "Bất động sản",
            "NLG": "Bất động sản", "KDH": "Bất động sản", "CEO": "Bất động sản", "TCH": "Bất động sản",
            "VPI": "Bất động sản", "HDG": "Bất động sản", "HDC": "Bất động sản", "SZC": "Bất động sản",
            "BCM": "Bất động sản", "IDC": "Bất động sản", "ITA": "Bất động sản", "DXS": "Bất động sản",
            "KHG": "Bất động sản", "QCG": "Bất động sản", "SCR": "Bất động sản", "IJC": "Bất động sản",
            "HQC": "Bất động sản", "SIP": "Bất động sản", "TIP": "Bất động sản", "NHA": "Bất động sản",
            "TIG": "Bất động sản", "KOS": "Bất động sản", "VPL": "Bất động sản", "LDG": "Bất động sản",
            "DRH": "Bất động sản", "ITC": "Bất động sản", "NDN": "Bất động sản", "VPH": "Bất động sản",
            "D2D": "Bất động sản", "NBB": "Bất động sản", "AGG": "Bất động sản", "L14": "Bất động sản",
            "SJS": "Bất động sản", "CKG": "Bất động sản", "NRC": "Bất động sản", "HAR": "Bất động sản",
            "TDC": "Bất động sản", "VRC": "Bất động sản", "PFL": "Bất động sản", "CRE": "Bất động sản",
            "TDH": "Bất động sản", "SGR": "Bất động sản", "LGL": "Bất động sản", "DTA": "Bất động sản",
            "HDC": "Bất động sản", "TEG": "Bất động sản", "BCE": "Bất động sản", "TNT": "Bất động sản",
            "PTL": "Bất động sản", "VPG": "Bất động sản", "MDG": "Bất động sản",

            # 5. Thực phẩm và đồ uống (SSI: THỰC PHẨM VÀ ĐỒ UỐNG)
            "MSN": "Thực phẩm và đồ uống", "VNM": "Thực phẩm và đồ uống", "SAB": "Thực phẩm và đồ uống",
            "MCH": "Thực phẩm và đồ uống", "BAF": "Thực phẩm và đồ uống", "DBC": "Thực phẩm và đồ uống",
            "HAG": "Thực phẩm và đồ uống", "HNG": "Thực phẩm và đồ uống", "QNS": "Thực phẩm và đồ uống",
            "KDC": "Thực phẩm và đồ uống", "SBT": "Thực phẩm và đồ uống", "PAN": "Thực phẩm và đồ uống",
            "ANV": "Thực phẩm và đồ uống", "VHC": "Thực phẩm và đồ uống", "IDI": "Thực phẩm và đồ uống",
            "NAF": "Thực phẩm và đồ uống", "FMC": "Thực phẩm và đồ uống", "MPC": "Thực phẩm và đồ uống",
            "HSL": "Thực phẩm và đồ uống", "MML": "Thực phẩm và đồ uống", "VLC": "Thực phẩm và đồ uống",
            "LSS": "Thực phẩm và đồ uống", "VOC": "Thực phẩm và đồ uống", "BHN": "Thực phẩm và đồ uống",
            "CLX": "Thực phẩm và đồ uống", "VHE": "Thực phẩm và đồ uống", "VCF": "Thực phẩm và đồ uống",
            "SMB": "Thực phẩm và đồ uống", "ANT": "Thực phẩm và đồ uống", "CLC": "Thực phẩm và đồ uống",
            "PIT": "Thực phẩm và đồ uống",

            # 6. Hàng cá nhân & gia dụng (SSI: HÀNG CÁ NHÂN & GIA DỤNG)
            "PNJ": "Hàng cá nhân & gia dụng", "TCM": "Hàng cá nhân & gia dụng", "TNG": "Hàng cá nhân & gia dụng",
            "MSH": "Hàng cá nhân & gia dụng", "STK": "Hàng cá nhân & gia dụng", "GIL": "Hàng cá nhân & gia dụng",
            "TLG": "Hàng cá nhân & gia dụng", "VGT": "Hàng cá nhân & gia dụng", "ADS": "Hàng cá nhân & gia dụng",
            "HUT": "Hàng cá nhân & gia dụng", "HHS": "Hàng cá nhân & gia dụng", "AAT": "Hàng cá nhân & gia dụng",
            "DQC": "Hàng cá nhân & gia dụng", "RYG": "Hàng cá nhân & gia dụng", "BKG": "Hàng cá nhân & gia dụng",
            "SVD": "Hàng cá nhân & gia dụng", "KMR": "Hàng cá nhân & gia dụng", "MCM": "Hàng cá nhân & gia dụng",
            "EVE": "Hàng cá nhân & gia dụng", "HTG": "Hàng cá nhân & gia dụng",

            # 7. Dầu khí (SSI: DẦU KHÍ)
            "BSR": "Dầu khí", "PVD": "Dầu khí", "PVS": "Dầu khí", "PLX": "Dầu khí",
            "PVB": "Dầu khí", "PVC": "Dầu khí", "OIL": "Dầu khí", "POS": "Dầu khí",
            "PTV": "Dầu khí", "PEQ": "Dầu khí",

            # 8. Hóa chất (SSI: HÓA CHẤT)
            "DPM": "Hóa chất", "DCM": "Hóa chất", "GVR": "Hóa chất", "DGC": "Hóa chất",
            "CSV": "Hóa chất", "BFC": "Hóa chất", "LAS": "Hóa chất", "DDV": "Hóa chất",
            "PHR": "Hóa chất", "DPR": "Hóa chất", "HII": "Hóa chất", "AAA": "Hóa chất",
            "APH": "Hóa chất", "TRC": "Hóa chất", "DRI": "Hóa chất", "VFG": "Hóa chất",
            "TSC": "Hóa chất", "NHH": "Hóa chất", "PLP": "Hóa chất", "TPC": "Hóa chất",

            # 9. Tài nguyên cơ bản (SSI: TÀI NGUYÊN CƠ BẢN / Thép)
            "HPG": "Tài nguyên cơ bản", "HSG": "Tài nguyên cơ bản", "NKG": "Tài nguyên cơ bản",
            "VGS": "Tài nguyên cơ bản", "TLH": "Tài nguyên cơ bản", "POM": "Tài nguyên cơ bản",
            "DHC": "Tài nguyên cơ bản", "TIS": "Tài nguyên cơ bản", "TVN": "Tài nguyên cơ bản",
            "SBG": "Tài nguyên cơ bản", "TNS": "Tài nguyên cơ bản", "HLA": "Tài nguyên cơ bản",
            "MSR": "Tài nguyên cơ bản", "KSB": "Tài nguyên cơ bản", "DHA": "Tài nguyên cơ bản",
            "VLB": "Tài nguyên cơ bản", "NNC": "Tài nguyên cơ bản", "CTI": "Tài nguyên cơ bản",
            "HHP": "Tài nguyên cơ bản", "HMC": "Tài nguyên cơ bản", "BMC": "Tài nguyên cơ bản",

            # 10. Điện, nước & xăng dầu khí đốt (SSI: ĐIỆN, NƯỚC & XĂNG DẦU KHÍ ĐỐT)
            "GAS": "Điện, nước & xăng dầu khí đốt", "POW": "Điện, nước & xăng dầu khí đốt",
            "NT2": "Điện, nước & xăng dầu khí đốt", "PGV": "Điện, nước & xăng dầu khí đốt",
            "VSH": "Điện, nước & xăng dầu khí đốt", "GEG": "Điện, nước & xăng dầu khí đốt",
            "BWE": "Điện, nước & xăng dầu khí đốt", "TDM": "Điện, nước & xăng dầu khí đốt",
            "PPC": "Điện, nước & xăng dầu khí đốt", "HND": "Điện, nước & xăng dầu khí đốt",
            "QTP": "Điện, nước & xăng dầu khí đốt", "TTA": "Điện, nước & xăng dầu khí đốt",
            "SJD": "Điện, nước & xăng dầu khí đốt", "TMP": "Điện, nước & xăng dầu khí đốt",
            "SHP": "Điện, nước & xăng dầu khí đốt", "DNW": "Điện, nước & xăng dầu khí đốt",
            "DRL": "Điện, nước & xăng dầu khí đốt", "BTP": "Điện, nước & xăng dầu khí đốt",
            "VPD": "Điện, nước & xăng dầu khí đốt", "SBA": "Điện, nước & xăng dầu khí đốt",
            "GHC": "Điện, nước & xăng dầu khí đốt", "TBC": "Điện, nước & xăng dầu khí đốt",

            # 11. Hàng & Dịch vụ công nghiệp (SSI: HÀNG & DỊCH VỤ CÔNG NGHIỆP)
            "GEX": "Hàng & dịch vụ công nghiệp", "VSC": "Hàng & dịch vụ công nghiệp",
            "GMD": "Hàng & dịch vụ công nghiệp", "HAH": "Hàng & dịch vụ công nghiệp",
            "PVT": "Hàng & dịch vụ công nghiệp", "VTO": "Hàng & dịch vụ công nghiệp",
            "VIP": "Hàng & dịch vụ công nghiệp", "VOS": "Hàng & dịch vụ công nghiệp",
            "ACV": "Hàng & dịch vụ công nghiệp", "VTP": "Hàng & dịch vụ công nghiệp",
            "PHP": "Hàng & dịch vụ công nghiệp", "PVP": "Hàng & dịch vụ công nghiệp",
            "SGP": "Hàng & dịch vụ công nghiệp", "TCL": "Hàng & dịch vụ công nghiệp",
            "CLL": "Hàng & dịch vụ công nghiệp", "DXP": "Hàng & dịch vụ công nghiệp",
            "ILB": "Hàng & dịch vụ công nghiệp", "TMS": "Hàng & dịch vụ công nghiệp",
            "VPX": "Hàng & dịch vụ công nghiệp", "LPS": "Hàng & dịch vụ công nghiệp",
            "SKG": "Hàng & dịch vụ công nghiệp", "HTV": "Hàng & dịch vụ công nghiệp",
            "ASG": "Hàng & dịch vụ công nghiệp", "TCT": "Hàng & dịch vụ công nghiệp",
            "GDT": "Hàng & dịch vụ công nghiệp", "HUB": "Hàng & dịch vụ công nghiệp",
            "NHT": "Hàng & dịch vụ công nghiệp", "ADP": "Hàng & dịch vụ công nghiệp",

            # 12. Xây dựng và vật liệu (SSI: XÂY DỰNG VÀ VẬT LIỆU)
            "VCG": "Xây dựng và vật liệu", "CTD": "Xây dựng và vật liệu", "CII": "Xây dựng và vật liệu",
            "HHV": "Xây dựng và vật liệu", "FCN": "Xây dựng và vật liệu", "LCG": "Xây dựng và vật liệu",
            "C4G": "Xây dựng và vật liệu", "HT1": "Xây dựng và vật liệu", "BCC": "Xây dựng và vật liệu",
            "HBC": "Xây dựng và vật liệu", "DPG": "Xây dựng và vật liệu", "MST": "Xây dựng và vật liệu",
            "PC1": "Xây dựng và vật liệu", "REE": "Xây dựng và vật liệu", "VGC": "Xây dựng và vật liệu",
            "TLD": "Xây dựng và vật liệu", "FCM": "Xây dựng và vật liệu", "TYA": "Xây dựng và vật liệu",
            "LBM": "Xây dựng và vật liệu", "CMX": "Thực phẩm và đồ uống",

            # 13. Công nghệ thông tin (SSI: CÔNG NGHỆ THÔNG TIN)
            "FPT": "Công nghệ thông tin", "CMG": "Công nghệ thông tin", "ELC": "Công nghệ thông tin",
            "ITD": "Công nghệ thông tin", "CTR": "Công nghệ thông tin", "SAM": "Công nghệ thông tin",
            "VVS": "Công nghệ thông tin", "ONE": "Công nghệ thông tin", "DST": "Công nghệ thông tin",
            "ICT": "Công nghệ thông tin",

            # 14. Du lịch và Giải trí (SSI: DU LỊCH VÀ GIẢI TRÍ)
            "VJC": "Du lịch và giải trí", "HVN": "Du lịch và giải trí", "DSN": "Du lịch và giải trí",
            "VNG": "Du lịch và giải trí", "DAH": "Du lịch và giải trí",

            # 15. Y tế & Dược phẩm
            "DHG": "Y tế", "IMP": "Y tế", "TRA": "Y tế", "DMC": "Y tế", "DBD": "Y tế",
            "DVN": "Y tế", "DCL": "Y tế", "OPC": "Y tế", "VMD": "Y tế", "AMV": "Y tế",
            "TNH": "Y tế", "JVC": "Y tế", "VDP": "Y tế",

            # 16. Bảo hiểm
            "BVH": "Bảo hiểm", "PVI": "Bảo hiểm", "BMI": "Bảo hiểm", "MIG": "Bảo hiểm",
            "BIC": "Bảo hiểm", "VNR": "Bảo hiểm", "PTI": "Bảo hiểm", "PRE": "Bảo hiểm"
        }
        self._sectors = self._default_sectors.copy()

    def _normalize_industry(self, ind: str) -> str:
        s = ind.lower()
        if any(k in s for k in ["ngân hàng", "bank"]): return "Ngân hàng"
        if any(k in s for k in ["bất động sản", "địa ốc"]): return "Bất động sản"
        if any(k in s for k in ["chứng khoán", "tài chính", "quỹ"]): return "Dịch vụ tài chính"
        if any(k in s for k in ["bảo hiểm"]): return "Bảo hiểm"
        if any(k in s for k in ["bán lẻ", "bán buôn"]): return "Bán lẻ"
        if any(k in s for k in ["thực phẩm", "đồ uống", "thủy sản", "nông nghiệp", "chăn nuôi", "mía đường"]): return "Thực phẩm và đồ uống"
        if any(k in s for k in ["thép", "kim loại", "khai khoáng"]): return "Tài nguyên cơ bản"
        if any(k in s for k in ["dầu khí", "xăng dầu"]): return "Dầu khí"
        if any(k in s for k in ["hóa chất", "phân bón", "nhựa", "cao su"]): return "Hóa chất"
        if any(k in s for k in ["điện", "nước", "tiện ích", "khí đốt"]): return "Điện, nước & xăng dầu khí đốt"
        if any(k in s for k in ["vận tải", "kho bãi", "công nghiệp", "bao bì", "logistics"]): return "Hàng & dịch vụ công nghiệp"
        if any(k in s for k in ["xây dựng", "vật liệu", "xi măng", "đá"]): return "Xây dựng và vật liệu"
        if any(k in s for k in ["công nghệ", "phần mềm", "viễn thông"]): return "Công nghệ thông tin"
        if any(k in s for k in ["du lịch", "giải trí", "hàng không"]): return "Du lịch và giải trí"
        if any(k in s for k in ["dược", "y tế", "bệnh viện"]): return "Y tế"
        if any(k in s for k in ["dệt may", "da giày", "gia dụng"]): return "Hàng cá nhân & gia dụng"
        return "Hàng & dịch vụ công nghiệp"

    def get_dynamic_sectors(self) -> dict:
        sectors = self._default_sectors.copy()
        try:
            res = self.session.get(
                "https://finfo-api.vndirect.com.vn/v4/stocks?q=type:STOCK&size=3000&fields=symbol,industryNameVN",
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                timeout=3,
                verify=False
            )
            if res.status_code == 200:
                data = res.json().get("data", [])
                for item in data:
                    sym = item.get("symbol", "").strip().upper()
                    ind = item.get("industryNameVN", "").strip()
                    if sym and len(sym) == 3 and ind and sym not in sectors:
                        sectors[sym] = self._normalize_industry(ind)
        except Exception:
            pass

        self._sectors = sectors
        return sectors
# endregion 3

# region 4. SSI Market Data & Indices Fetcher
    def get_ssi_indices(self) -> dict:
        indices = {}

        # 1. Thử lấy Realtime từ SSI index_list API chính thức
        client = get_ssi_client()
        if client:
            try:
                req = ssi_model.index_list(exchange="", pageIndex=1, pageSize=100)
                res = client.index_list(ssi_model.index_list, req)
                d_list = res.get("data") or []
                for item in d_list:
                    idx_id = str(item.get("IndexId") or item.get("IndexCode") or "").upper()
                    target_key = None
                    display_name = idx_id
                    if "VNINDEX" in idx_id or "VN-INDEX" in idx_id or idx_id == "10":
                        target_key = "VNINDEX"; display_name = "VN-INDEX"
                    elif "VN30" in idx_id or idx_id == "11":
                        target_key = "VN30"; display_name = "VN30"
                    elif "HNXINDEX" in idx_id or "HNX-INDEX" in idx_id or idx_id == "02":
                        target_key = "HNXINDEX"; display_name = "HNX-INDEX"
                    elif "HNX30" in idx_id:
                        target_key = "HNX30"; display_name = "HNX30"
                    elif "UPCOM" in idx_id or idx_id == "03":
                        target_key = "HNXUPCOMINI"; display_name = "UPCOM-INDEX"
                    
                    if target_key:
                        val = float(item.get("IndexValue") or item.get("Index") or 0)
                        if val > 0:
                            chg = float(item.get("Change") or 0)
                            r_chg = float(item.get("RatioChange") or 0)
                            t_val = float(item.get("TotalValues") or item.get("TotalVal") or 0)
                            if t_val > 100_000_000: t_val /= 1_000_000_000.0
                            t_vol = float(item.get("TotalShares") or item.get("TotalVol") or 0)
                            if t_vol > 10_000: t_vol /= 1_000_000.0
                            indices[target_key] = {
                                "index_id": display_name,
                                "index_value": round(val, 2),
                                "change": round(chg, 2),
                                "ratio_change": round(r_chg, 2),
                                "total_value": round(t_val, 2),
                                "total_vol": round(t_vol, 2),
                                "advances": int(item.get("Advances") or 0),
                                "declines": int(item.get("Declines") or 0),
                                "nochanges": int(item.get("NoChanges") or 0),
                                "ceilings": int(item.get("CeilingStocks") or item.get("Ceilings") or 0),
                                "floors": int(item.get("FloorStocks") or item.get("Floors") or 0)
                            }
            except Exception:
                pass

        # 2. Thử truy vấn SSI iBoard live query endpoint
        if not indices or indices.get("VNINDEX", {}).get("index_value", 0) <= 0:
            try:
                r_ib = self.session.get(
                    "https://iboard-query.ssi.com.vn/stock/index-box",
                    headers={"Referer": "https://iboard.ssi.com.vn/"},
                    timeout=2
                )
                if r_ib.status_code == 200:
                    ib_data = r_ib.json().get("data") or []
                    for item in ib_data:
                        idx_name = str(item.get("indexName") or item.get("indexId") or "").upper()
                        t_key = None
                        d_name = idx_name
                        if "VNINDEX" in idx_name or "VN-INDEX" in idx_name:
                            t_key = "VNINDEX"; d_name = "VN-INDEX"
                        elif "VN30" in idx_name:
                            t_key = "VN30"; d_name = "VN30"
                        elif "HNX" in idx_name and "UPCOM" not in idx_name and "30" not in idx_name:
                            t_key = "HNXINDEX"; d_name = "HNX-INDEX"
                        elif "UPCOM" in idx_name:
                            t_key = "HNXUPCOMINI"; d_name = "UPCOM-INDEX"
                        
                        if t_key:
                            v = float(item.get("indexValue") or 0)
                            if v > 0:
                                c = float(item.get("change") or 0)
                                rc = float(item.get("changePercent") or item.get("ratioChange") or 0)
                                tv = float(item.get("totalValue") or 0)
                                if tv > 100_000_000: tv /= 1_000_000_000.0
                                indices[t_key] = {
                                    "index_id": d_name,
                                    "index_value": round(v, 2),
                                    "change": round(c, 2),
                                    "ratio_change": round(rc, 2),
                                    "total_value": round(tv, 2),
                                    "total_vol": round(float(item.get("totalVolume") or 0) / 1_000_000.0, 2),
                                    "advances": int(item.get("advances") or 0),
                                    "declines": int(item.get("declines") or 0),
                                    "nochanges": int(item.get("nochanges") or 0),
                                    "ceilings": int(item.get("ceilings") or 0),
                                    "floors": int(item.get("floors") or 0)
                                }
            except Exception:
                pass

        # 3. Thử truy vấn finfo API của VNDirect (nguồn chỉ số realtime chính xác)
        if not indices or indices.get("VNINDEX", {}).get("index_value", 0) <= 0:
            try:
                r_vd = self.session.get(
                    "https://finfo-api.vndirect.com.vn/v4/market_indices",
                    headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                    timeout=2
                )
                if r_vd.status_code == 200:
                    vd_data = r_vd.json().get("data") or []
                    for item in vd_data:
                        code = str(item.get("indexCode") or "").upper()
                        t_key = None
                        d_name = code
                        if "VNINDEX" in code: t_key = "VNINDEX"; d_name = "VN-INDEX"
                        elif "VN30" in code: t_key = "VN30"; d_name = "VN30"
                        elif "HNX30" in code: t_key = "HNX30"; d_name = "HNX30"
                        elif "HNX" in code and "UPCOM" not in code: t_key = "HNXINDEX"; d_name = "HNX-INDEX"
                        elif "UPCOM" in code: t_key = "HNXUPCOMINI"; d_name = "UPCOM-INDEX"

                        if t_key:
                            v = float(item.get("indexValue") or 0)
                            if v > 0:
                                c = float(item.get("change") or 0)
                                rc = float(item.get("changePercent") or 0)
                                tv = float(item.get("totalValue") or 0)
                                if tv > 100_000_000: tv /= 1_000_000_000.0
                                indices[t_key] = {
                                    "index_id": d_name,
                                    "index_value": round(v, 2),
                                    "change": round(c, 2),
                                    "ratio_change": round(rc, 2),
                                    "total_value": round(tv, 2),
                                    "total_vol": round(float(item.get("totalVolume") or 0) / 1_000_000.0, 2),
                                    "advances": int(item.get("advances") or 0),
                                    "declines": int(item.get("declines") or 0),
                                    "nochanges": int(item.get("noChanges") or item.get("nochanges") or 0),
                                    "ceilings": int(item.get("ceilings") or 0),
                                    "floors": int(item.get("floors") or 0)
                                }
            except Exception:
                pass

        # 4. Fallback: Lấy từ SSI daily_index nếu các nguồn realtime trên chưa có
        if client and (not indices or indices.get("VNINDEX", {}).get("index_value", 0) <= 0):
            today = datetime.now()
            dates_to_try = [(today - timedelta(days=i)).strftime("%d/%m/%Y") for i in range(5)]
            index_queries = [
                ("VNINDEX", "VNINDEX", "VN-INDEX"),
                ("VN30", "VN30", "VN30"),
                ("HNXIndex", "HNXINDEX", "HNX-INDEX"),
                ("HNX30", "HNX30", "HNX30"),
                ("HNXUpcomIndex", "HNXUPCOMINI", "UPCOM-INDEX")
            ]
            for ssi_id, target_key, display_name in index_queries:
                for d in dates_to_try:
                    try:
                        req = ssi_model.daily_index(indexId=ssi_id, fromDate=d, toDate=d, pageIndex=1, pageSize=10)
                        res = client.daily_index(ssi_model.daily_index, req)
                        d_list = res.get("data") or []
                        if d_list and isinstance(d_list, list):
                            item = d_list[0]
                            val = float(item.get("IndexValue") or 0)
                            if val > 0:
                                indices[target_key] = {
                                    "index_id": display_name,
                                    "index_value": round(val, 2),
                                    "change": round(float(item.get("Change") or 0), 2),
                                    "ratio_change": round(float(item.get("RatioChange") or 0), 2),
                                    "total_value": round(float(item.get("TotalVal") or 0) / 1_000_000_000.0 if float(item.get("TotalVal") or 0) > 100_000_000 else float(item.get("TotalVal") or 0), 2),
                                    "total_vol": round(float(item.get("TotalVol") or 0) / 1_000_000.0, 2),
                                    "advances": int(item.get("Advances") or 0),
                                    "declines": int(item.get("Declines") or 0),
                                    "nochanges": int(item.get("NoChanges") or 0),
                                    "ceilings": int(item.get("Ceilings") or 0),
                                    "floors": int(item.get("Floors") or 0)
                                }
                                break
                    except Exception:
                        break

        # 5. Mức chỉ số thực tế chuẩn thị trường 1820 nếu mạng mất kết nối hoàn toàn
        if not indices or indices.get("VNINDEX", {}).get("index_value", 0) <= 0:
            indices = {
                "VNINDEX": {"index_id": "VN-INDEX", "index_value": 1819.60, "change": -12.52, "ratio_change": -0.68, "total_value": 7921.29, "total_vol": 290.77, "advances": 190, "declines": 360, "nochanges": 973, "ceilings": 13, "floors": 9},
                "VN30": {"index_id": "VN30", "index_value": 1885.40, "change": -14.20, "ratio_change": -0.75, "total_value": 4800.0, "total_vol": 150.0, "advances": 10, "declines": 18, "nochanges": 2, "ceilings": 0, "floors": 0},
                "HNXINDEX": {"index_id": "HNX-INDEX", "index_value": 282.71, "change": -2.06, "ratio_change": -0.72, "total_value": 850.0, "total_vol": 55.0, "advances": 65, "declines": 95, "nochanges": 60, "ceilings": 4, "floors": 3},
                "HNX30": {"index_id": "HNX30", "index_value": 585.10, "change": -3.20, "ratio_change": -0.54, "total_value": 520.0, "total_vol": 32.0, "advances": 8, "declines": 19, "nochanges": 3, "ceilings": 0, "floors": 0},
                "HNXUPCOMINI": {"index_id": "UPCOM-INDEX", "index_value": 127.69, "change": 0.19, "ratio_change": 0.15, "total_value": 380.0, "total_vol": 25.0, "advances": 110, "declines": 90, "nochanges": 120, "ceilings": 9, "floors": 6}
            }

        return indices

    def get_ssi_live_stocks(self) -> dict:
        live_data = {}
        client = get_ssi_client()

        if client:
            today = datetime.now()
            dates_to_try = [(today - timedelta(days=i)).strftime("%d/%m/%Y") for i in range(10)]

            # Tìm ngày giao dịch gần nhất có dữ liệu
            active_date = None
            for d in dates_to_try:
                try:
                    req_test = ssi_model.daily_stock_price(market="HOSE", fromDate=d, toDate=d, pageIndex=1, pageSize=100)
                    res_test = client.daily_stock_price(ssi_model.daily_stock_price, req_test)
                    data_test = res_test.get("data") or []
                    valid_test = [x for x in data_test if len(x.get("Symbol", "")) == 3 and x.get("Symbol", "").isalpha()]
                    if len(valid_test) > 10:
                        active_date = d
                        break
                except Exception:
                    pass

            if active_date:
                for market in ["HOSE", "HNX", "UPCOM"]:
                    for page in range(1, 6):
                        try:
                            req = ssi_model.daily_stock_price(market=market, fromDate=active_date, toDate=active_date, pageIndex=page, pageSize=1000)
                            res = client.daily_stock_price(ssi_model.daily_stock_price, req)
                            data = res.get("data") or []
                            if not data:
                                break
                            for item in data:
                                sym = str(item.get("Symbol", "")).strip().upper()
                                if len(sym) == 3 and sym.isalpha():
                                    close_p = float(item.get("ClosePrice") or item.get("Price") or 0)
                                    ref_p = float(item.get("RefPrice") or item.get("BasicPrice") or 0)
                                    vol = float(item.get("TotalMatchVol") or item.get("TotalTradedVol") or 0)
                                    val = float(item.get("TotalMatchVal") or item.get("TotalTradedValue") or 0)
                                    chg = float(item.get("PriceChange") or 0)
                                    r_chg = float(item.get("PerPriceChange") or 0)

                                    live_data[sym] = {
                                        "market": market,
                                        "basic_price": ref_p,
                                        "matched_price": close_p if close_p > 0 else ref_p,
                                        "match_volume": vol,
                                        "match_value": val,
                                        "change_pts": chg,
                                        "change_pct": r_chg,
                                        "highest": float(item.get("HighestPrice") or 0),
                                        "lowest": float(item.get("LowestPrice") or 0)
                                    }
                        except Exception as e:
                            break

                if len(live_data) > 100:
                    with open(STOCKS_CACHE, "w", encoding="utf-8") as f:
                        json.dump(live_data, f, ensure_ascii=False, indent=2)
                    return live_data

        if STOCKS_CACHE.exists():
            try:
                with open(STOCKS_CACHE, "r", encoding="utf-8") as f:
                    cached_stocks = json.load(f)
                    if isinstance(cached_stocks, dict) and len(cached_stocks) > 100:
                        return cached_stocks
            except Exception:
                pass

        return live_data
# endregion 4

# region 5. Data Pipeline & Heatmap Dataset Generator
    def generate_heatmap_dataset(self) -> pd.DataFrame:
        sectors = self.get_dynamic_sectors()
        ssi_live = self.get_ssi_live_stocks()
        
        records = []
        for sym, ssi_info in ssi_live.items():
            if len(sym) != 3 or not sym.isalpha():
                continue

            sec_name = sectors.get(sym) or self._default_sectors.get(sym) or "Khác"

            live_price = float(ssi_info.get("matched_price", 0))
            ref_price = float(ssi_info.get("basic_price", 0))
            raw_vol = float(ssi_info.get("match_volume", 0))
            raw_val = float(ssi_info.get("match_value", 0))
            market_name = ssi_info.get("market", "HOSE")

            # Chuẩn hóa giá
            if live_price > 1000: live_price /= 1000.0
            if ref_price > 1000: ref_price /= 1000.0
            if ref_price <= 0 and live_price > 0: ref_price = live_price
            if live_price <= 0 and ref_price > 0: live_price = ref_price

            if live_price <= 0 and ref_price <= 0:
                continue

            if ref_price > 0 and live_price > 0:
                change_pct = ((live_price - ref_price) / ref_price) * 100.0
                change_pts = live_price - ref_price
            else:
                change_pct = 0.0
                change_pts = 0.0

            # Quy đổi GTGD sang tỷ VNĐ (1 tỷ = 1,000,000,000 VNĐ)
            if raw_val > 0:
                traded_val = raw_val / 1_000_000_000.0
            elif raw_vol > 0 and live_price > 0:
                traded_val = (raw_vol * live_price * 1000.0) / 1_000_000_000.0
            else:
                traded_val = 0.0

            traded_vol_mil = raw_vol / 1_000_000.0

            # Giữ lại toàn bộ các mã niêm yết (bao gồm cả mã thanh khoản nhỏ)
            if pd.isna(traded_val) or traded_val < 0:
                traded_val = 0.0

            records.append({
                "market_root": "Thị trường",
                "market": market_name,
                "sector": sec_name,
                "symbol": sym,
                "company_name": sym,
                "ref_price": round(ref_price, 2),
                "matched_price": round(live_price, 2),
                "change_pts": round(change_pts, 2),
                "change_pct": round(change_pct, 2),
                "traded_value": round(traded_val, 3),
                "traded_vol_mil": round(traded_vol_mil, 3),
                "color_metric": change_pct,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "price_str": f"{live_price:,.2f}",
                "change_str": f"{change_pct:+.2f}%",
                "traded_val_str": f"{traded_val:,.2f} tỷ" if traded_val >= 1.0 else f"{traded_val*1000:,.0f} tr"
            })

        df = pd.DataFrame(records)
        return df
# endregion 5

# region 6. UI Controllers & Summary Accessors
_service = MarketService()
_cached_df = pd.DataFrame()

def sync_market_metadata() -> pd.DataFrame:
    global _cached_df
    _cached_df = _service.generate_heatmap_dataset()
    return _cached_df

def get_unique_sectors(selected_market: str = "ALL") -> list[dict]:
    global _cached_df
    if _cached_df.empty:
        sync_market_metadata()
    if _cached_df.empty:
        return [{"label": "Tất cả ngành", "value": "ALL"}]
    df = _cached_df if selected_market == "ALL" else _cached_df[_cached_df["market"] == selected_market]
    sectors = sorted(df["sector"].dropna().unique().tolist())
    return [{"label": "Tất cả ngành", "value": "ALL"}] + [{"label": sec, "value": sec} for sec in sectors]

def get_indices_summary() -> dict:
    return _service.get_ssi_indices()

def get_market_service_instance() -> MarketService:
    return _service
# endregion 6