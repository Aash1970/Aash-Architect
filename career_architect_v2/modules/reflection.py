from __future__ import annotations
from datetime import date, datetime
import streamlit as st
from db.client import get_client

MOOD_OPTIONS  = ["Excellent", "Good", "Neutral", "Difficult", "Challenging"]
MOOD_COLOURS  = {
    "Excellent":   "#22c55e",
    "Good":        "#84cc16",
    "Neutral":     "#94a3b8",
    "Difficult":   "#f59e0b",
    "Challenging": "#ef4444",
}
MOOD_EMOJI = {
    "Excellent":   "🌟",
    "Good":        "😊",
    "Neutral":     "😐",
    "Difficult":   "😔",
    "Challenging": "😟",
}

REFLECTION_PROMPTS = [
    "What is one thing you accomplished today that you are proud of?",
    "What obstacle did you face, and how did you navigate it?",
    "What did you learn today — about your work, yourself, or others?",
    "What would you do differently if you could repeat today?",
    "What is one goal you are committing to for tomorrow?",
    "Who did you help today, and how did that feel?",
    "What energised you today? What drained you?",
    "What progress, however small, did you make towards your career goals?",
]


# ── DB helpers ────────────────────────────────────────────────

def _save_reflection(user_id: str, entry_date: date, mood: str,
                     content: str, goals: str) -> tuple[bool, str]:
    try:
        get_client().table("reflections").insert({
            "user_id":    user_id,
            "entry_date": entry_date.isoformat(),
            "mood":       mood,
            "content":    content.strip(),
            "goals":      goals.strip(),
        }).execute()
        return True, "Reflection saved."
    except Exception as exc:
        return False, f"Save failed: {exc}"


def _load_reflections(user_id: str, limit: int = 30) -> list[dict]:
    try:
        result = (
            get_client()
            .table("reflections")
            .select("id, entry_date, mood, content, goals, created_at")
            .eq("user_id", user_id)
            .order("entry_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def _delete_reflection(reflection_id: str) -> bool:
    try:
        get_client().table("reflections").delete().eq("id", reflection_id).execute()
        return True
    except Exception:
        return False


# ── Mood analytics ────────────────────────────────────────────

def _mood_summary(entries: list[dict]) -> dict:
    counts: dict[str, int] = {m: 0 for m in MOOD_OPTIONS}
    for e in entries:
        m = e.get("mood", "Neutral")
        if m in counts:
            counts[m] += 1
    return counts


# ── Main render ───────────────────────────────────────────────

def render_reflection(user_id: str, flags: dict) -> None:
    st.header("Reflection Journal")
    st.caption(
        "Daily reflections build self-awareness, track progress, and create "
        "a record of your professional growth."
    )

    tab_new, tab_history, tab_insights = st.tabs(["New Entry", "History", "Insights"])

    # ── New entry ─────────────────────────────────────────────
    with tab_new:
        st.subheader("Today's Reflection")

        import random
        prompt = random.choice(REFLECTION_PROMPTS)
        st.markdown(
            f'<div style="background:#EEF2FF;border-left:4px solid #6366F1;'
            f'padding:10px 16px;border-radius:4px;margin-bottom:16px;font-style:italic;">'
            f'💭 {prompt}</div>',
            unsafe_allow_html=True,
        )

        with st.form("reflection_form"):
            col_date, col_mood = st.columns(2)
            with col_date:
                entry_date = st.date_input("Date", value=date.today(), key="ref_date")
            with col_mood:
                mood = st.selectbox("How are you feeling?", MOOD_OPTIONS, key="ref_mood")

            content = st.text_area(
                "Reflection",
                height=160,
                placeholder="Write freely — this is private. Reflect on today's experiences, challenges, and wins.",
                key="ref_content",
            )
            goals = st.text_area(
                "Goals & Intentions for Tomorrow",
                height=80,
                placeholder="What will you focus on? What do you commit to?",
                key="ref_goals",
            )

            submitted = st.form_submit_button("Save Reflection", type="primary")

        if submitted:
            if not content.strip():
                st.error("Please write something in your reflection before saving.")
            else:
                ok, msg = _save_reflection(user_id, entry_date, mood, content, goals)
                if ok:
                    st.success(f"{MOOD_EMOJI.get(mood,'✅')} {msg}")
                else:
                    st.error(msg)

    # ── History ───────────────────────────────────────────────
    with tab_history:
        st.subheader("Previous Entries")
        entries = _load_reflections(user_id, limit=30)

        if not entries:
            st.info("No reflections yet. Start journalling today.")
        else:
            for entry in entries:
                mood    = entry.get("mood", "Neutral")
                colour  = MOOD_COLOURS.get(mood, "#94a3b8")
                emoji   = MOOD_EMOJI.get(mood, "")
                d_label = entry.get("entry_date", "")

                with st.expander(f"{emoji} {d_label}  ·  {mood}", expanded=False):
                    st.markdown(
                        f'<div style="background:#F8FAFC;border-left:4px solid {colour};'
                        f'padding:12px;border-radius:4px;margin-bottom:8px;">'
                        f'{entry.get("content","")}</div>',
                        unsafe_allow_html=True,
                    )
                    goals_text = entry.get("goals", "").strip()
                    if goals_text:
                        st.markdown(f"**Goals recorded:** {goals_text}")

                    if st.button("Delete entry", key=f"ref_del_{entry['id']}"):
                        if _delete_reflection(entry["id"]):
                            st.success("Entry deleted.")
                            st.rerun()
                        else:
                            st.error("Could not delete entry.")

    # ── Insights ──────────────────────────────────────────────
    with tab_insights:
        st.subheader("Mood Trends (Last 30 Days)")
        entries = _load_reflections(user_id, limit=30)

        if len(entries) < 3:
            st.info("Keep journalling — insights appear after 3+ entries.")
        else:
            summary = _mood_summary(entries)
            total   = len(entries)

            for mood, count in summary.items():
                if count == 0:
                    continue
                pct    = count / total * 100
                colour = MOOD_COLOURS[mood]
                emoji  = MOOD_EMOJI[mood]
                st.markdown(
                    f"""
                    <div style="margin-bottom:8px;">
                      <div style="display:flex;justify-content:space-between;font-size:0.85em;">
                        <span>{emoji} {mood}</span>
                        <span style="color:{colour};font-weight:700;">{count} ({pct:.0f}%)</span>
                      </div>
                      <div style="background:#E2E8F0;border-radius:4px;height:8px;">
                        <div style="background:{colour};width:{pct}%;height:8px;border-radius:4px;"></div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Streak calculation
            today = date.today()
            dates = sorted(
                {datetime.strptime(e["entry_date"], "%Y-%m-%d").date() for e in entries},
                reverse=True,
            )
            streak = 0
            for i, d in enumerate(dates):
                if (today - d).days == i:
                    streak += 1
                else:
                    break

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Entries", total)
            with col2:
                st.metric("Current Streak", f"{streak} day{'s' if streak != 1 else ''}")

            with st.expander("Why reflection matters"):
                st.markdown("""
Research consistently shows that people who engage in regular structured reflection:
- Retain learning **25–30% more effectively**
- Report higher job satisfaction and resilience
- Are better able to articulate their value in interviews
- Make faster, more confident career decisions

Even five minutes a day compounds into powerful self-knowledge over time.
                """)
