from __future__ import annotations
import streamlit as st
from db.cv_store import load_cv


# ── Template builders ─────────────────────────────────────────

def generate_headline(cv: dict) -> list[str]:
    """
    Returns up to 3 headline variants based on CV data.
    LinkedIn headline max: 220 characters.
    """
    name     = cv.get("personal", {}).get("full_name", "Professional")
    skills   = cv.get("skills", [])
    exp      = cv.get("experience", [])
    latest   = exp[0] if exp else {}
    role     = latest.get("role", "")
    company  = latest.get("company", "")

    top_skills = " | ".join(skills[:3]) if skills else "Professional Skills"
    skill_str  = " | ".join(skills[:5]) if skills else ""

    variants: list[str] = []

    if role and company:
        variants.append(f"{role} at {company} | {top_skills}")
    if role:
        variants.append(f"{role} | {top_skills}")
        variants.append(f"Experienced {role} | Helping organisations achieve results through {skills[0] if skills else 'expertise'}")

    if not variants:
        variants.append(f"{name} | {top_skills}")

    return [v[:220] for v in variants]


def generate_about(cv: dict, tone: str = "Professional") -> str:
    """
    Generate a LinkedIn 'About' section from CV data.
    Tone: Professional | Conversational | Achievement-focused
    """
    p        = cv.get("personal", {})
    name     = p.get("full_name", "I")
    summary  = cv.get("profile_summary", "")
    skills   = cv.get("skills", [])
    exp      = cv.get("experience", [])
    edu      = cv.get("education", [])

    # Build experience narrative
    exp_lines: list[str] = []
    for e in exp[:3]:
        r = e.get("role", "")
        c = e.get("company", "")
        ach = e.get("achievements", [])
        desc = e.get("description", "")
        if r and c:
            line = f"As **{r}** at **{c}**"
            if ach:
                line += f", I {ach[0].lower().lstrip('i ') if ach[0] else desc[:80]}"
            exp_lines.append(line)

    # Build education line
    edu_line = ""
    if edu:
        e0 = edu[0]
        q  = e0.get("qualification", "")
        s  = e0.get("subject", "")
        i  = e0.get("institution", "")
        if q and i:
            edu_line = f"I hold a {q}{' in ' + s if s else ''} from {i}."

    # Skill highlights
    skill_str = ", ".join(skills[:8]) if skills else ""

    if tone == "Professional":
        opening = summary if summary else (
            f"I am a results-driven professional with a track record of delivering "
            f"measurable value across complex, fast-moving environments."
        )
        body = "\n\n".join(exp_lines[:2]) if exp_lines else ""
        skills_para = f"\n\nCore competencies: {skill_str}." if skill_str else ""
        closing = (
            "\n\nI am currently open to opportunities where I can apply my expertise "
            "and make a lasting impact. Feel free to connect."
        )

    elif tone == "Conversational":
        opening = summary if summary else (
            f"Hi, I'm {name} — a passionate professional who loves solving "
            f"real problems and building things that matter."
        )
        body = (
            "\n\nI've had the privilege of working across " +
            ", ".join({e.get("company","") for e in exp[:3] if e.get("company")}) +
            " — experiences that have shaped how I think and work."
            if exp else ""
        )
        skills_para = f"\n\nI particularly enjoy working with: {skill_str}." if skill_str else ""
        closing = (
            "\n\nAlways happy to connect with like-minded people — "
            "feel free to reach out!"
        )

    else:  # Achievement-focused
        opening = (
            f"I deliver results. {'— ' + summary[:120] if summary else ''}"
        ).strip()
        body = "\n\n".join(exp_lines[:2]) if exp_lines else ""
        skills_para = f"\n\nTechnical toolkit: {skill_str}." if skill_str else ""
        closing = (
            "\n\nIf you're looking for someone who combines strategic thinking with "
            "hands-on delivery, I'd be glad to connect."
        )

    about = opening
    if body:
        about += "\n\n" + body
    about += skills_para
    if edu_line:
        about += "\n\n" + edu_line
    about += closing

    return about.strip()


def generate_connection_message(cv: dict, target_role: str = "") -> str:
    """Generate a short LinkedIn connection request message."""
    name   = cv.get("personal", {}).get("full_name", "")
    skills = cv.get("skills", [])
    exp    = cv.get("experience", [])
    role   = exp[0].get("role", "professional") if exp else "professional"

    msg = (
        f"Hi — I'm {name}, a {role} with expertise in "
        f"{', '.join(skills[:2]) if skills else 'my field'}. "
    )
    if target_role:
        msg += f"I'm exploring roles in {target_role} and "
    msg += "would love to connect and learn from your experience."
    return msg[:300]


# ── Main render ───────────────────────────────────────────────

def render_linkedin_generator(user_id: str, flags: dict) -> None:
    st.header("LinkedIn Generator")
    st.caption(
        "Generate professional LinkedIn headlines, an 'About' section, "
        "and connection request messages from your CV."
    )

    cv, msg = load_cv(user_id)
    if not cv:
        st.warning("No CV found. Please build and save your CV first.")
        return

    tab_hl, tab_about, tab_connect = st.tabs(["Headline", "About Section", "Connection Message"])

    # ── Headline tab ──────────────────────────────────────────
    with tab_hl:
        st.subheader("Headline Variants")
        st.caption("LinkedIn allows up to 220 characters. Choose or customise one of these.")
        headlines = generate_headline(cv)
        for i, h in enumerate(headlines, 1):
            st.markdown(
                f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                f'padding:12px 16px;border-radius:6px;margin-bottom:8px;">'
                f'<strong>Option {i}:</strong> {h}</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Use Option {i}", key=f"hl_use_{i}"):
                st.code(h)

        st.subheader("Custom Headline Builder")
        custom_hl = st.text_input(
            "Edit or write your own headline (220 char max)",
            max_chars=220,
            key="hl_custom",
        )
        if custom_hl:
            chars = len(custom_hl)
            colour = "#22c55e" if chars <= 180 else "#f59e0b" if chars <= 210 else "#ef4444"
            st.markdown(
                f'<span style="color:{colour};font-size:0.8em;">{chars}/220 characters</span>',
                unsafe_allow_html=True,
            )

    # ── About tab ─────────────────────────────────────────────
    with tab_about:
        st.subheader("About Section Generator")
        tone = st.radio(
            "Select tone",
            ["Professional", "Conversational", "Achievement-focused"],
            horizontal=True,
            key="linkedin_tone",
        )

        if st.button("Generate About Section", type="primary", key="gen_about"):
            about_text = generate_about(cv, tone)
            st.session_state["generated_about"] = about_text

        if "generated_about" in st.session_state:
            about = st.session_state["generated_about"]
            chars = len(about)
            colour = "#22c55e" if chars <= 2500 else "#ef4444"

            edited = st.text_area(
                "Edit your About section below (LinkedIn max: 2,600 characters)",
                value=about,
                height=320,
                key="about_edit",
            )
            st.markdown(
                f'<span style="color:{colour};font-size:0.8em;">'
                f'{len(edited)}/2,600 characters</span>',
                unsafe_allow_html=True,
            )

            with st.expander("Formatting Tips"):
                st.markdown("""
- **First line is critical** — LinkedIn shows only the first ~265 characters before 'See more'
- Use short paragraphs (2–3 sentences max)
- Include a clear call to action at the end
- Avoid jargon your audience won't recognise
- Emoji used sparingly can increase visibility
                """)

    # ── Connection message tab ────────────────────────────────
    with tab_connect:
        st.subheader("Connection Request Message")
        st.caption("Keep it under 300 characters — LinkedIn limits connection notes.")
        target_role = st.text_input(
            "What type of role are you targeting? (optional)",
            placeholder="e.g. Product Management, Data Science",
            key="connect_target",
        )

        if st.button("Generate Message", type="primary", key="gen_connect"):
            msg_text = generate_connection_message(cv, target_role)
            st.session_state["generated_connect"] = msg_text

        if "generated_connect" in st.session_state:
            edited_msg = st.text_area(
                "Connection note (max 300 chars)",
                value=st.session_state["generated_connect"],
                max_chars=300,
                height=100,
                key="connect_edit",
            )
            chars = len(edited_msg)
            colour = "#22c55e" if chars <= 270 else "#f59e0b"
            st.markdown(
                f'<span style="color:{colour};font-size:0.8em;">{chars}/300 characters</span>',
                unsafe_allow_html=True,
            )
