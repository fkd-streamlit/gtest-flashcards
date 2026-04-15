import streamlit as st
import pandas as pd
import random

# --- 定数 ---
EXCEL_FILE_PATH = 'フラッシュカード.xlsx'
STATE_QUESTIONS = 'questions'
STATE_QUESTION_INDEX = 'question_index'
STATE_SHOW_ANSWER = 'show_answer'
STATE_CHAPTER = 'selected_chapter'
STATE_TOTAL_QUESTIONS = 'total_questions'

# --- 関数の定義 ---
def load_excel_file(file_path):
    """Excelファイルを読み込む"""
    try:
        return pd.ExcelFile(file_path)
    except FileNotFoundError:
        st.error(f"エラー: {file_path} が見つかりません。Q&Aを記載したExcelファイルを同じフォルダに配置してください。")
        return None

def initialize_session_state(df):
    """
    章が変更された場合、またはセッションが初期化されていない場合に、
    問題リストやインデックスをリセットする。
    """
    # st.session_state['current_chapter'] には selectbox の現在の値が自動で入る
    current_selected_chapter = st.session_state['current_chapter_selector']

    if STATE_CHAPTER not in st.session_state or st.session_state[STATE_CHAPTER] != current_selected_chapter:
        # 選択された章を記録
        st.session_state[STATE_CHAPTER] = current_selected_chapter
        # 該当の章のデータフレームを辞書のリストに変換
        questions_list = df.to_dict('records')
        st.session_state[STATE_QUESTIONS] = questions_list
        st.session_state[STATE_TOTAL_QUESTIONS] = len(questions_list)
        # 最初の問題のインデックスをランダムに設定
        if st.session_state[STATE_TOTAL_QUESTIONS] > 0:
            st.session_state[STATE_QUESTION_INDEX] = random.randint(0, st.session_state[STATE_TOTAL_QUESTIONS] - 1)
        else:
            st.session_state[STATE_QUESTION_INDEX] = -1 # 問題がない場合
        # 答えは非表示に
        st.session_state[STATE_SHOW_ANSWER] = False


# --- UIの描画 ---
st.title("📚 G検定フラッシュカード (改良版)")

# Excelファイルの読み込み
xls = load_excel_file(EXCEL_FILE_PATH)

if xls:
    # --- 章の選択 ---
    # `key` を設定することで、st.session_stateから値を取得できる
    selected_chapter = st.selectbox("章を選択してください", xls.sheet_names, key='current_chapter_selector')

    # 選択された章のデータを読み込み
    df = pd.read_excel(xls, sheet_name=selected_chapter).dropna(subset=['Question', 'Answer'])

    # --- セッション状態の管理 ---
    initialize_session_state(df)

    if st.session_state[STATE_QUESTION_INDEX] == -1:
        st.warning("この章には有効な問題がありません。")
    else:
        # --- 現在の問題と解答を取得 ---
        question_data = st.session_state[STATE_QUESTIONS][st.session_state[STATE_QUESTION_INDEX]]
        question = question_data['Question']
        answer = question_data['Answer']
        
        # --- 進捗表示 ---
        progress_text = f"問題 {st.session_state[STATE_QUESTION_INDEX] + 1} / {st.session_state[STATE_TOTAL_QUESTIONS]}"
        st.progress( (st.session_state[STATE_QUESTION_INDEX] + 1) / st.session_state[STATE_TOTAL_QUESTIONS], text=progress_text)

        # --- 問題表示 ---
        st.subheader("問題")
        st.info(question)

        # --- 解答表示 ---
        if st.button('答えを見る'):
            st.session_state[STATE_SHOW_ANSWER] = True

        if st.session_state[STATE_SHOW_ANSWER]:
            st.subheader("解答")
            st.success(answer)
        
        st.divider() # 区切り線

        # --- 次の問題へ ---
        if st.button('次の問題へ'):
            # 新しいランダムなインデックスをセット
            st.session_state[STATE_QUESTION_INDEX] = random.randint(0, st.session_state[STATE_TOTAL_QUESTIONS] - 1)
            # 答えを非表示にリセット
            st.session_state[STATE_SHOW_ANSWER] = False
            # 画面を再描画して次の問題を表示
            st.experimental_rerun()
else:
    st.info("学習を開始するには、`フラッシュカード.xlsx` ファイルを準備してください。")
