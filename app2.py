import streamlit as st
import os
from openai import OpenAI

# 1️⃣ 初始化 OpenAI 客戶端
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("❌ API Key 未設定，請在環境變數或 Streamlit Secrets 中加入 OPENAI_API_KEY")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# 2️⃣ Streamlit 介面
st.set_page_config(page_title="💬 AI 問答 Demo", page_icon="🤖")
st.title("💬 AI 問答 Demo")

# 輸入問題
user_input = st.text_area("請輸入你的問題：", height=150)

# 送出按鈕
if st.button("送出問題"):
    if user_input.strip():
        with st.spinner("AI 正在思考中..."):
            try:
                # 3️⃣ 呼叫 OpenAI Chat Completions API
                response = client.chat.completions.create(
                    model="gpt-5-mini",  # ✅ 改成 gpt-5-mini
                    messages=[
                        {"role": "system", "content": "你是一個有幫助的助理。"},
                        {"role": "user", "content": user_input},
                    ],
                )

                # 取出回答
                answer = response.choices[0].message.content
                st.success("✅ AI 回覆：")
                st.write(answer)

            except Exception as e:
                st.error(f"發生錯誤：{str(e)}")
    else:
        st.warning("請先輸入問題！")

