import streamlit as st
import os
import random
from datetime import datetime
from openai import OpenAI

# 1️⃣ 初始化 OpenAI client
client = OpenAI()

# 2️⃣ 模擬帳號
accounts = ["user001", "user002", "user003", "user004"]
blacklist = ["user999"]

# 3️⃣ 初始化交易紀錄
if "transactions" not in st.session_state:
    st.session_state.transactions = []

# 4️⃣ 函數：AI 判斷可疑交易
def ai_check_suspicious(tx):
    prompt = f"""
你是一個金融詐欺檢測助手。
請判斷以下交易是否可疑，並說明原因：
交易時間: {tx['time']}
來源帳戶: {tx['from']}
目標帳戶: {tx['to']}
金額: {tx['amount']}

請只回覆：
可疑: 是/否
原因: (一句話)
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",  # ✅ 使用現有模型
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=60  # ✅ 改用 max_completion_tokens
        )
        result = response.choices[0].message.content.strip()
    except Exception as e:
        result = f"Error: {str(e)}"
    return result

# 5️⃣ 函數：Rule-based 判斷
def rule_check_suspicious(tx):
    if tx['amount'] > 100000:
        return "是", "單筆交易金額超過 100,000"
    return "否", ""

# 6️⃣ Streamlit UI
st.title("💳 AI + Rule Fraud Detection Demo")
st.write("模擬交易紀錄，AI 與規則判斷可疑交易")

# 7️⃣ 輸入金額
input_amount = st.text_input("輸入交易金額 (留空則隨機生成)")

# 8️⃣ 按鈕：產生新交易
if st.button("產生新交易"):
    sender = random.choice(accounts)
    receiver = random.choice(accounts + blacklist)
    
    try:
        if input_amount.strip() != "":
            amount = int(input_amount)
        else:
            amount = random.randint(100, 200000)
    except ValueError:
        st.error("❌ 請輸入正確的數字金額")
        amount = random.randint(100, 200000)
    
    tx = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "from": sender,
        "to": receiver,
        "amount": amount,
    }

    # Rule 判斷
    rule_flag, rule_reason = rule_check_suspicious(tx)
    tx["rule_result"] = f"可疑: {rule_flag} | 原因: {rule_reason}" if rule_flag=="是" else "否"

    # AI 判斷
    tx["ai_result"] = ai_check_suspicious(tx)

    st.session_state.transactions.insert(0, tx)

# 9️⃣ 顯示交易紀錄
st.subheader("📒 交易紀錄")
st.dataframe(st.session_state.transactions)

# 🔟 顯示可疑提醒（Rule + AI）
st.subheader("⚠️ 可疑帳號提醒")
has_suspicious = False
for tx in st.session_state.transactions:
    suspicious_texts = []
    if "是" in tx.get("rule_result",""):
        suspicious_texts.append(f"規則判斷: {tx['rule_result']}")
    if "是" in tx.get("ai_result",""):
        suspicious_texts.append(f"AI判斷: {tx['ai_result']}")
    if suspicious_texts:
        st.warning(f"{tx['time']} | {tx['from']} -> {tx['to']} 金額 {tx['amount']} | " + " ; ".join(suspicious_texts))
        has_suspicious = True

if not has_suspicious:
    st.success("目前無可疑交易 ✅")
