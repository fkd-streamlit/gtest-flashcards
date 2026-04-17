import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="G検定フラッシュカード", layout="centered")
st.title("📚 G検定フラッシュカード")

file_path = "フラッシュカード.xlsx"
xls = pd.ExcelFile(file_path)

chapter = st.selectbox("章を選択してください", xls.sheet_names)
df = pd.read_excel(xls, sheet_name=chapter)

# 4択カラムが無い古いシートにも耐えるために get で取る
for col in ["Choice_A","Choice_B","Choice_C","Choice_D","Correct","Explanation","Pitfall"]:
    if col not in df.columns:
        df[col] = ""

# Question がある行だけを候補にする（1行＝1問運用推奨）
df = df[df["Question"].notna()].copy()

if "current_index" not in st.session_state:
    st.session_state.current_index = None
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "selected" not in st.session_state:
    st.session_state.selected = None

if st.button("次の質問"):
    st.session_state.current_index = random.choice(df.index.tolist())
    st.session_state.show_answer = False
    st.session_state.selected = None

if st.session_state.current_index is not None:
    row = df.loc[st.session_state.current_index]

    st.markdown(f"### ❓ 質問\n{row['Question']}")

    # 4択モード判定：Choice_A が埋まっているか
    is_mcq = str(row.get("Choice_A","")).strip() != ""

    if is_mcq:
        options = ["A", "B", "C", "D"]
        choice_text = {
            "A": row.get("Choice_A",""),
            "B": row.get("Choice_B",""),
            "C": row.get("Choice_C",""),
            "D": row.get("Choice_D",""),
        }

        st.session_state.selected = st.radio(
            "選択肢",
            options,
            format_func=lambda x: f"{x}. {choice_text[x]}",
            index=0 if st.session_state.selected is None else options.index(st.session_state.selected)
        )

        if st.button("回答する"):
            st.session_state.show_answer = True

        if st.session_state.show_answer:
            correct = str(row.get("Correct","")).strip().upper()
            if st.session_state.selected == correct:
                st.success("✅ 正解！")
            else:
                st.error(f"❌ 不正解（正解：{correct}）")

            # 解説表示
            if str(row.get("Answer","")).strip():
                st.markdown(f"**答え（要点）:** {row['Answer']}")
            if str(row.get("Explanation","")).strip():
                st.markdown(f"**解説:** {row['Explanation']}")
            if str(row.get("Pitfall","")).strip():
                st.warning(f"⚠ ひっかけポイント\n\n{row['Pitfall']}")

    else:
        # 従来Q&Aモード
        if st.button("答えを見る"):
            st.session_state.show_answer = True

        if st.session_state.show_answer:
            st.markdown(f"### ✅ 答え\n{row.get('Answer','')}")
