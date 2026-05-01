import streamlit as st
import pandas as pd
import random
from datetime import date

# --- ページ設定 ---
st.set_page_config(page_title="G検定フラッシュカード", layout="centered")
st.title("📚 G検定フラッシュカード")

# --- Excelファイル読み込み ---
file_path = "フラッシュカード.xlsx"
sheet_keyword_name = "G検定シラバス_キーワード集"

try:
    xls = pd.ExcelFile(file_path)
except FileNotFoundError:
    st.error(f"エラー: '{file_path}' が見つかりません。同じディレクトリにファイルを配置してください。")
    st.stop()


# ─── セッション状態の初期化 ───────────────────────────────────
def init_state():
    defaults = {
        "current_index": None,
        "show_answer": False,
        "selected_choice": None,
        "recent_indices": [],
        "recent_max": 10,
        "results": [],
        "finished": False,
        "filter_key": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ─── 学習終了後の結果画面 ─────────────────────────────────────
if st.session_state.finished:
    st.header("学習セッション終了")
    results = st.session_state.results

    if "is_correct" not in pd.DataFrame(results).columns:
        st.info("キーワード学習セッションが終了しました。お疲れさまでした！")
        if st.button("もう一度学習する"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.stop()

    if not results:
        st.info("まだ回答した問題がありません。")
    else:
        total = len(results)
        correct = sum(1 for r in results if r["is_correct"])
        rate = correct / total * 100 if total > 0 else 0

        st.subheader(f"📊 本日の学習結果（{date.today()}）")
        col1, col2, col3 = st.columns(3)
        col1.metric("回答数", f"{total} 問")
        col2.metric("正解数", f"{correct} 問")
        col3.metric("正解率", f"{rate:.1f} %")
        st.divider()

        st.subheader("📋 正誤一覧")
        correct_list = [r for r in results if r["is_correct"]]
        wrong_list = [r for r in results if not r["is_correct"]]

        if correct_list:
            st.markdown("### ✅ 正解した問題")
            for i, r in enumerate(correct_list, 1):
                with st.expander(f"{i}. {str(r['question'])[:60]}…"):
                    st.write(f"**正解：** {r['correct_answer']}")

        if wrong_list:
            st.markdown("### ❌ 間違えた問題")
            for i, r in enumerate(wrong_list, 1):
                with st.expander(f"{i}. {str(r['question'])[:60]}…"):
                    st.write(f"**あなたの回答：** {r['user_answer']}")
                    st.write(f"**正解：** {r['correct_answer']}")

    st.divider()
    if st.button("🔚 閉じる（アプリ終了）", type="primary"):
        st.success("お疲れさまでした！ブラウザのタブを閉じてください。")
        st.stop()
    st.stop()


# ─── 章・難易度選択 ──────────────────────────────────────────
sheet_names = xls.sheet_names

if "はじめに" in sheet_names:
    sheet_names.insert(0, sheet_names.pop(sheet_names.index("はじめに")))

chapter = st.selectbox("章を選択してください", sheet_names)

if chapter == "はじめに":
    st.info("学習したい章を上のプルダウンから選択してください。")
    st.markdown("""
---
### 使い方

1. **章の選択**  
   学習したい章をドロップダウンリストから選びます。

2. **難易度の選択**  
   「初級」「中級」「上級」など、シートに含まれる難易度を選びます。

3. **キーワード集**  
   `G検定シラバス_キーワード集` では、以下を表示します。

   - キーワード
   - 意味
   - 初心者向け補足説明
   - 例え話

4. **4択問題**  
   選択肢を選び、「✔ 回答する」ボタンを押すと正誤と解説が表示されます。

5. **学習終了**  
   「🏁 学習終了」ボタンを押すと、そのセッションの結果が表示されます。
---
""")
    st.stop()


# ─── データ読み込み ──────────────────────────────────────────
df_original = pd.read_excel(xls, sheet_name=chapter)
df_original.columns = [str(c).strip() for c in df_original.columns]
df = df_original.copy()


# ─── シート形式の判定と整形 ──────────────────────────────────
is_keyword_sheet = "キーワード" in df.columns and "意味" in df.columns

if is_keyword_sheet:
    rename_map = {
        "キーワード": "Question",
        "意味": "Answer",
        "初心者向け補足説明": "Beginner_Explanation",
        "例え話": "Example",
    }

    df.rename(columns=rename_map, inplace=True)

    # 補足列が存在しない場合でもエラーにしない
    for col in ["Beginner_Explanation", "Example"]:
        if col not in df.columns:
            df[col] = ""

    # 4択問題用のカラムを空で追加
    for col in ["Level", "Choice_A", "Choice_B", "Choice_C", "Choice_D", "Correct", "Explanation", "Pitfall"]:
        if col not in df.columns:
            df[col] = ""

    df["Level"] = "キーワード"

else:
    required_cols = [
        "Level",
        "Question",
        "Choice_A",
        "Correct",
        "Answer",
        "Explanation",
        "Pitfall",
    ]

    for col in required_cols:
        if col not in df.columns:
            st.error(f"エラー: シート '{chapter}' に必須カラム '{col}' がありません。")
            st.stop()

    for col in ["Choice_B", "Choice_C", "Choice_D"]:
        if col not in df.columns:
            df[col] = ""


# ─── 空行除外 ────────────────────────────────────────────────
df = df[df["Question"].notna() & (df["Question"].astype(str).str.strip() != "")].copy()
df["Level"] = df["Level"].astype(str).str.strip()


# ─── 難易度選択 ──────────────────────────────────────────────
level_order = ["初級", "中級", "上級", "キーワード"]
available_levels = [lv for lv in level_order if lv in df["Level"].unique()]

if not available_levels:
    st.warning("この章には出題できる問題がありません。Excelの Level 列などを確認してください。")
    st.stop()

selected_level = st.selectbox("難易度を選択してください", available_levels)
df = df[df["Level"] == selected_level].reset_index(drop=True)

st.caption(f"現在の出題範囲： {chapter} / {selected_level} / 全{len(df)}問")

if df.empty:
    st.warning("この条件に合う問題がありません。")
    st.stop()

all_indices = df.index.tolist()


# ─── フィルター変更時のリセット処理 ──────────────────────────
filter_key = f"{chapter}_{selected_level}"

if st.session_state.get("filter_key") != filter_key:
    st.session_state.filter_key = filter_key
    st.session_state.current_index = None
    st.session_state.show_answer = False
    st.session_state.selected_choice = None
    st.session_state.recent_indices = []


# ─── ボタン行 ────────────────────────────────────────────────
col_next, col_end = st.columns([3, 1])

with col_next:
    if st.button("▶ 次の問題", type="primary"):
        recent = st.session_state.recent_indices
        candidates = [i for i in all_indices if i not in recent]

        if not candidates:
            candidates = all_indices
            st.session_state.recent_indices = []
            st.toast("全問出題しました。もう一周します！")

        chosen = random.choice(candidates)
        st.session_state.current_index = chosen

        recent.append(chosen)
        if len(recent) > st.session_state.recent_max:
            recent.pop(0)

        st.session_state.show_answer = False
        st.session_state.selected_choice = None
        st.rerun()

with col_end:
    if st.button("🏁 学習終了", type="secondary"):
        st.session_state.finished = True
        st.rerun()


# ─── 問題表示 ────────────────────────────────────────────────
if st.session_state.current_index is not None:
    index = st.session_state.current_index

    if index >= len(df):
        st.warning("問題のインデックスが範囲外です。フィルターを変更した可能性があります。「次の問題」を押してください。")
        st.stop()

    row = df.loc[index]

    # --- 4択問題 ---
    is_mcq = str(row.get("Choice_A", "")).strip() != ""

    if is_mcq:
        st.markdown(f"### ❓ 質問\n{row['Question']}")

        options = ["A", "B", "C", "D"]
        choice_text = {
            opt: str(row.get(f"Choice_{opt}", "")).strip()
            for opt in options
        }

        valid_options = [
            opt for opt, text in choice_text.items()
            if text != "" and text.lower() != "nan"
        ]

        if not valid_options:
            st.warning("選択肢が設定されていません。Excelの Choice_A〜Choice_D を確認してください。")
            st.stop()

        selected_index = 0
        if st.session_state.selected_choice in valid_options:
            selected_index = valid_options.index(st.session_state.selected_choice)

        st.session_state.selected_choice = st.radio(
            "選択肢",
            valid_options,
            format_func=lambda x: f"{x}. {choice_text[x]}",
            key=f"radio_{index}",
            index=selected_index,
        )

        if st.button("✔ 回答する"):
            st.session_state.show_answer = True
            correct_ans = str(row.get("Correct", "")).strip().upper()
            is_correct = st.session_state.selected_choice == correct_ans

            st.session_state.results.append({
                "question": str(row["Question"]),
                "correct_answer": f"{correct_ans}. {choice_text.get(correct_ans, '')}",
                "user_answer": f"{st.session_state.selected_choice}. {choice_text.get(st.session_state.selected_choice, '')}",
                "is_correct": is_correct,
            })

            st.rerun()

        if st.session_state.show_answer:
            correct_ans = str(row.get("Correct", "")).strip().upper()
            last_result = st.session_state.results[-1]

            if last_result["is_correct"]:
                st.success(f"✅ 正解！ 正解：{correct_ans}")
            else:
                st.error(f"❌ 不正解... 正解：{correct_ans}")

            st.divider()

            if str(row.get("Answer", "")).strip():
                st.markdown(f"**答え（要点）：** {row['Answer']}")

            if str(row.get("Explanation", "")).strip():
                st.markdown(f"**解説：** {row['Explanation']}")

            if str(row.get("Pitfall", "")).strip():
                st.warning(f"**⚠ ひっかけ・補足：**\n\n{row['Pitfall']}")

    # --- キーワード暗記形式 ---
    else:
        keyword = str(row.get("Question", "")).strip()
        meaning = str(row.get("Answer", "")).strip()
        beginner = str(row.get("Beginner_Explanation", "")).strip()
        example = str(row.get("Example", "")).strip()

        st.markdown("### 💡 キーワード")
        st.markdown(f"## {keyword}")

        if st.button("👁 意味を見る", key=f"btn_kw_{index}"):
            st.session_state.show_answer = True

        if st.session_state.show_answer:
            st.divider()

            if meaning and meaning.lower() != "nan":
                st.markdown("### ✅ 意味")
                st.write(meaning)
            else:
                st.warning("意味が設定されていません。")

            if beginner and beginner.lower() != "nan":
                st.info(f"### 🌱 初心者向け補足説明\n{beginner}")

            if example and example.lower() != "nan":
                st.success(f"### 🧩 例え話\n{example}")

else:
    st.info("「▶ 次の問題」ボタンを押して学習をスタートしましょう！")
