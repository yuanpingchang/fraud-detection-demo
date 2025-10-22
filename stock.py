import streamlit as st
import requests
from datetime import date
import urllib3

# 關閉 SSL 警告（用 verify=False 時必要）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.title("📈 股票資料自動更新工具 (Supabase REST API 版)")

# 從 Streamlit Secrets 讀取 Supabase 設定
SUPABASE_URL = "https://yclrtgavioarnjelftby.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InljbHJ0Z2F2aW9hcm5qZWxmdGJ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjExMDU2OTUsImV4cCI6MjA3NjY4MTY5NX0.JYpL1FnX4DH_-1PsjljZWmlAGTPURIGjigN67jgXr98"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# 按鈕：更新股價資料
if st.button("更新今日股價資料", key="update_stock_data"):
    try:
        st.info("正在下載台股資料（透過 HTTPS 代理）...")
        api_url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

        # ⚠️ 這裡關閉 SSL 驗證，避免 CERT 錯誤
        response = requests.get(api_url, verify=False)
        response.raise_for_status()
        data = response.json()

        st.success(f"✅ 已取得 {len(data)} 筆台股資料")

        # Step 2️⃣：讀取 STOCK_LIST
        st.info("正在讀取 STOCK_LIST ...")
        res = requests.get(f"{SUPABASE_URL}/rest/v1/STOCK_LIST", headers=headers)
        res.raise_for_status()
        stock_list = res.json()
        valid_codes = {item["STOCK_NO"] for item in stock_list}

        st.write(f"已載入 {len(valid_codes)} 支股票代碼")

        # Step 3️⃣：處理每筆資料
        today = str(date.today())
        insert_count = 0
        skip_count = 0

        for item in data:
            code = item.get("Code")
            close_price = item.get("ClosingPrice")

            # 顯示目前處理的股票
            if not code or code not in valid_codes or not close_price or close_price == "--":
                continue

            # 檢查是否已存在該股票的今日資料
            params = {"STOCK_NO": f"eq.{code}"}
            check = requests.get(f"{SUPABASE_URL}/rest/v1/STOCK_LIST", headers=headers, params=params)
            stock_info = check.json()

            # Debug：顯示查詢結果
            st.text(f"🔎 查詢 STOCK_LIST params = {params}, 回傳筆數: {len(stock_info)}")

            # 如果 STOCK_LIST 查不到這支股票，略過
            if not stock_info:
                skip_count += 1
                st.write(f"⏩ {code} 不在 STOCK_LIST，略過")
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

        st.success(f"✅ 新增 {insert_count} 筆資料，略過 {skip_count} 筆（已存在的）")

    except Exception as e:
        st.error(f"❌ 發生錯誤: {e}")
