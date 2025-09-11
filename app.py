import streamlit as st
import openai
import random
import os
from datetime import datetime

openai.api_key = os.getenv("OPENAI_API_KEY")

accounts = ["user001", "user002", "user003", "user004"]
blacklist = ["user999"]

if "transactions" not in st.session_state:
    st.session_state.transactions = []

def ai_check_suspicious(tx):
    prompt = f"""
    你是一個金融詐欺檢測助手。
    請根據以下交易紀錄判斷是否可疑：
    交易時間: {tx['time']}
    來源帳戶: {tx['from']}
    目標帳戶: {tx['to']}
    金額: {tx['amount']}

    請只輸出以下格式：
    可疑: 是/否
    原因: (一句話說明)
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    return response["choices"][0]["message"]["content"]

st.title("💳 AI Fraud Detection Demo (ChatGPT版)")

if st.button("產生新交易"):
    sender = random.choice(accounts)
    receiver = random.choice(accounts + blacklist)
    amount = random.randint(100, 20000)
    tx = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "from": sender,
        "to": receiver,
        "amount": amount,
    }
    result = ai_check_suspicious(tx)
    tx["ai_result"] = result
    st.session_state.transactions.insert(0, tx)

st.subheader("📒 交易紀錄")
st.dataframe(st.session_state.transactions)

