import streamlit as st
import pandas as pd
import random
from datetime import date

st.set_page_config(page_title="G検定フラッシュカード", layout="centered")
st.title("📚 G検定フラッシュカード")

file_path = "フラッシュカード.xlsx"
xls = pd.ExcelFile(file_path)

# ─── セッション初期化 ───────────────────────────────────────────
def init_state():
    defaults = {
        "current_index": None,
        "show_answer": False,
        "selected": None,
        "recent_indices": [],          # 短時間に出た問題を記録
        "recent_max": 10,              # 同じ問題を出さない件数ウィンドウ
        "results": [],                 # {question, correct_answer, user_answer, is_correct}
        "finished": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── 学習終了後の結果画面 ─────────────────────────────────────
if st.session_state.finished:
    results = st.session_state.results
    if not results:
        st.info("まだ回答した問題がありません。")
    else:
        total = len(results)
        correct = sum(1 for r in results if r["is_correct"])
        rate = correct / total * 100

        st.subheader(f"📊 本日の学習結果（{date.today()}）")
        col1, col2, col3 = st.columns(3)
        col1.metric("回答数", f"{total} 問")
        col2.metric("正解数", f"{correct} 問")
        col3.metric("正解率", f"{rate:.1f} %")

        st.divider()
        st.subheader("📋 正誤一覧")

        # 正解一覧
        correct_list = [r for r in results if r["is_correct"]]
        wrong_list   = [r for r in results if not r["is_correct"]]

        if correct_list:
            st.markdown("### ✅ 正解した問題")
            for i, r in enumerate(correct_list, 1):
                with st.expander(f"{i}. {r['question'][:60]}…"):
                    st.write(f"**正解：** {r['correct_answer']}")

        if wrong_list:
            st.markdown("### ❌ 間違えた問題")
            for i, r in enumerate(wrong_list, 1):
                with st.expander(f"{i}. {r['question'][:60]}…"):
                    st.write(f"**あなたの回答：** {r['user_answer']}")
                    st.write(f"**正解：** {r['correct_answer']}")

    st.divider()
    if st.button("🔚 閉じる（アプリ終了）", type="primary"):
        st.success("お疲れさまでした！ブラウザのタブを閉じてください。")
        st.stop()
    st.stop()

# ─── 章選択 ───────────────────────────────────────────────────
chapter = st.selectbox("章を選択してください", xls.sheet_names)
df = pd.read_excel(xls, sheet_name=chapter)

for col in ["Choice_A","Choice_B","Choice_C","Choice_D","Correct","Explanation","Pitfall"]:
    if col not in df.columns:
        df[col] = ""

df = df[df["Question"].notna()].reset_index(drop=True)
all_indices = df.index.tolist()

# ─── ボタン行 ─────────────────────────────────────────────────
col_next, col_end = st.columns([3, 1])

with col_next:
    if st.button("▶ 次の問題", type="primary"):
        # 短時間に出た問題を除いた候補から選ぶ
        recent = st.session_state.recent_indices
        candidates = [i for i in all_indices if i not in recent]
        if not candidates:          # 全問出し切った場合はリセット
            candidates = all_indices
            st.session_state.recent_indices = []
        chosen = random.choice(candidates)
        st.session_state.current_index = chosen
        # 履歴に追加してウィンドウサイズを維持
        recent.append(chosen)
        if len(recent) > st.session_state.recent_max:
            recent.pop(0)
        st.session_state.show_answer = False
        st.session_state.selected = None

with col_end:
    if st.button("🏁 学習終了", type="secondary"):
        st.session_state.finished = True
        st.rerun()

# ─── 問題表示 ─────────────────────────────────────────────────
if st.session_state.current_index is not None:
    row = df.loc[st.session_state.current_index]
    st.markdown(f"### ❓ 質問\n{row['Question']}")

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
            index=0 if st.session_state.selected is None
                  else options.index(st.session_state.selected),
        )

        if st.button("✔ 回答する"):
            st.session_state.show_answer = True
            correct_ans = str(row.get("Correct","")).strip().upper()
            is_correct  = st.session_state.selected == correct_ans
            st.session_state.results.append({
                "question":       str(row["Question"]),
                "correct_answer": f"{correct_ans}. {choice_text.get(correct_ans,'')}",
                "user_answer":    f"{st.session_state.selected}. {choice_text.get(st.session_state.selected,'')}",
                "is_correct":     is_correct,
            })

        if st.session_state.show_answer:
            correct_ans = str(row.get("Correct","")).strip().upper()
            last = st.session_state.results[-1] if st.session_state.results else None
            if last and last["question"] == str(row["Question"]):
                if last["is_correct"]:
                    st.success("✅ 正解！")
                else:
                    st.error(f"❌ 不正解（正解：{correct_ans}）")

            if str(row.get("Answer","")).strip():
                st.markdown(f"**答え（要点）:** {row['Answer']}")
            if str(row.get("Explanation","")).strip():
                st.markdown(f"**解説:** {row['Explanation']}")
            if str(row.get("Pitfall","")).strip():
                st.warning(f"⚠ ひっかけポイント\n\n{row['Pitfall']}")

    else:
        if st.button("👁 答えを見る"):
            st.session_state.show_answer = True

        if st.session_state.show_answer:
            ans = str(row.get("Answer",""))
            st.markdown(f"### ✅ 答え\n{ans}")

else:
    st.info("「次の問題」ボタンを押してスタートしましょう！")
