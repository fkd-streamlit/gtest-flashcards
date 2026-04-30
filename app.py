import streamlit as st
import pandas as pd
import random
import re

# ▼ ページ設定
st.set_page_config(page_title="G検定フラッシュカード", layout="centered")
st.title("📚 G検定フラッシュカード")

# ▼ Excelファイル読み込み
file_path = "フラッシュカード.xlsx"  # 同じフォルダに配置
xls = pd.ExcelFile(file_path)

# ▼ レベル選択（追加）
level_ranges = {
    "初級（ID 001-020）": (1, 20),
    "中級（ID 021-030）": (21, 30),
    "上級（ID 031-041）": (31, 41),
}
level_label = st.selectbox("レベルを選択してください", list(level_ranges.keys()), index=0)
min_id, max_id = level_ranges[level_label]

# ▼ 章選択（既存）
chapter = st.selectbox("章を選択してください", xls.sheet_names)

# ▼ データ読み込み
df = pd.read_excel(xls, sheet_name=chapter)

# ▼ ID列がある場合はフィルタ（追加）
# 想定列名：ID（例："001" や 1 等）
# 列名が異なる場合は、ここを変更してください（例："No" や "id" など）
ID_COL = "ID"

df_filtered = df.copy()

if ID_COL in df_filtered.columns:
    # "001" / "ID001" / " 002 " などを想定して数値化
    def to_int_id(x):
        if pd.isna(x):
            return None
        s = str(x).strip()
        # 数字だけ抽出
        digits = re.sub(r"\D", "", s)
        if digits == "":
            return None
        return int(digits)

    df_filtered["ID_num"] = df_filtered[ID_COL].apply(to_int_id)
    df_filtered = df_filtered[df_filtered["ID_num"].between(min_id, max_id, inclusive="both")].copy()

    # 参考表示（任意）
    st.caption(f"抽出条件: {level_label} / 章: {chapter} / 件数: {len(df_filtered)}")
else:
    st.warning(
        f"Excelに '{ID_COL}' 列が見つからないため、レベルフィルタは無効です。"
        f"（現状は章 '{chapter}' の全問題から出題します）"
    )
    st.caption(f"章: {chapter} / 件数: {len(df_filtered)}")

# ▼ Q/A の取り出し
# dropna()は列ごとに落ちるのでズレる可能性があるため、行単位でNaN除外が安全
if "Question" not in df_filtered.columns or "Answer" not in df_filtered.columns:
    st.error("Excelに 'Question' 列または 'Answer' 列が見つかりません。列名を確認してください。")
    st.stop()

qa_df = df_filtered[["Question", "Answer"]].dropna(how="any")

questions = list(zip(qa_df["Question"].tolist(), qa_df["Answer"].tolist()))

if len(questions) == 0:
    st.error("条件に合う問題がありません。レベルまたは章を変更してください。")
    st.stop()

# ▼ セッション状態管理
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# ▼ 次の質問ボタン
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("次の質問"):
        st.session_state.current_question = random.choice(questions)
        st.session_state.show_answer = False

with col2:
    if st.session_state.current_question and st.button("答えを見る / 隠す"):
        st.session_state.show_answer = not st.session_state.show_answer

# ▼ 質問表示
if st.session_state.current_question:
    q, a = st.session_state.current_question
    st.write(f"**質問:** {q}")
    if st.session_state.show_answer:
        st.success(f"**答え:** {a}")
else:
    st.info("「次の質問」を押すと問題が表示されます。")
