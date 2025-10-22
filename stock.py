import streamlit as st
import requests
import pandas as pd
from datetime import date
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.title("📈 股票資料自動更新工具 (Supabase REST API 版)")

SUPABASE_URL = "https://yclrtgavioarnjelftby.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InljbHJ0Z2F2aW9hcm5qZWxmdGJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjExMDU2OTUsImV4cCI6MjA3NjY4MTY5NX0.JYpL1FnX4DH_-1PsjljZWmlAGTPURIGjigN67jgXr98"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

if st.button("更新今日股價資料"):
    try:
        # Step 1: 取得台股資料（透過代理避免 SSL 問題）
        api_url = "https://corsproxy.io/?https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
        st.info("正在下載台股資料...")
        response = requests.get(api_url, verify=False)
        data = response.json()
        st.success(f"已取得 {len(data)} 筆資料")

        # Step 2: 讀取 STOCK_LIST
        st.info("讀取 STOCK_LIST ...")
        res = requests.get(f"{SUPABASE_URL}/rest/v1/STOCK_LIST", headers=headers)
        stock_list = res.json()
        valid_codes = {item["STOCK_NO"] for item in stock_list}
        st.write(f"已載入 {len(valid_codes)} 支股票代碼")

        # Step 3: 新增符合的資料到 STOCK_DATA
        today = str(date.today())
        insert_count = 0
        skip_count = 0

        for item in data:
            code = item.get("Code")
            close_price = item.get("ClosingPrice")

            if code not in valid_codes or not close_price or close_price == "--":
                continue

            # 檢查是否已存在
            params = {"STOCK_NO": f"eq.{code}", "DATE": f"eq.{today}"}
            check = requests.get(f"{SUPABASE_URL}/rest/v1/STOCK_DATA", headers=headers, params=params)

            if check.json():
                skip_count += 1
                continue

            # 寫入新資料
            payload = {
                "STOCK_NO": code,
                "Price": close_price,
                "DATE": today
            }
            r = requests.post(f"{SUPABASE_URL}/rest/v1/STOCK_DATA", headers=headers, json=payload)
            if r.status_code in [200, 201]:
                insert_count += 1

        st.success(f"✅ 已新增 {insert_count} 筆資料，略過 {skip_count} 筆重複")

    except Exception as e:
        st.error(f"❌ 發生錯誤: {e}")




import streamlit as st
import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date

# ====== 資料庫連線設定 ======
# ⚠️ 建議日後移入 st.secrets 或環境變數
DB_URL = "postgresql+psycopg2://postgres:Ab551111@db.yclrtgavioarnjelftby.supabase.co:5432/postgres"
engine = create_engine(DB_URL)

# ====== Streamlit 介面 ======
st.title("📈 股票資料自動更新工具")

if st.button("更新今日股價資料"):
    try:
        # Step 1: 取得證交所資料
        api_url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
        st.info("正在下載台股資料...")
        response = requests.get(api_url, verify=False)
        data = response.json()
        st.success(f"已取得 {len(data)} 筆資料")

        # Step 2: 取得 STOCK_LIST 中的股票代碼
        st.info("讀取 STOCK_LIST ...")
        stock_list_df = pd.read_sql("SELECT STOCK_NO FROM STOCK_LIST;", engine)
        valid_codes = set(stock_list_df["STOCK_NO"].astype(str).tolist())

        # Step 3: 篩選符合的股票並寫入
        today = date.today()
        insert_count = 0
        skip_count = 0

        with engine.begin() as conn:  # 自動 commit
            for item in data:
                code = item.get("Code")
                close_price = item.get("ClosingPrice")

                # 檢查股票代碼是否存在於 STOCK_LIST
                if code not in valid_codes:
                    continue

                # 避免空值
                if not close_price or close_price == "--":
                    continue

                # 檢查當天是否已存在
                exists = conn.execute(
                    text("""
                        SELECT 1 FROM STOCK_DATA 
                        WHERE STOCK_NO = :code AND DATE = :today
                        LIMIT 1;
                    """),
                    {"code": code, "today": today}
                ).fetchone()

                if exists:
                    skip_count += 1
                    continue  # 若已有資料則跳過

                # 若不存在則插入
                conn.execute(
                    text("""
                        INSERT INTO STOCK_DATA (STOCK_NO, Price, DATE)
                        VALUES (:code, :price, :today);
                    """),
                    {"code": code, "price": close_price, "today": today}
                )
                insert_count += 1

        st.success(f"✅ 已新增 {insert_count} 筆資料到 STOCK_DATA（略過 {skip_count} 筆重複資料）")

    except Exception as e:
        st.error(f"❌ 發生錯誤: {e}")
