import streamlit as st
import plotly.graph_objects as go

from utils.parser import extract_resume_text, clean_text, check_formatting
from utils.matcher import extract_jd_keywords, match_keywords, compute_ats_score
from utils.suggestions import generate_suggestions
from utils.skill_positioning import get_skill_positioning, category_breakdown, CATEGORY_LABELS
from utils.report import build_pdf_report

st.set_page_config(page_title="ATS Resume Checker", page_icon="📄", layout="wide")

# ---------- Custom styling ----------
st.markdown("""
<style>
    .main .block-container {padding-top: 2rem; max-width: 1100px;}
    h1 {font-weight: 800 !important;}
    .hero-subtitle {color: #6b7280; font-size: 1.05rem; margin-top: -0.5rem;}
    .stButton>button {
        border-radius: 8px; font-weight: 600; padding: 0.6rem 1rem;
    }
    div[data-testid="stMetric"] {
        background: #f8f9fb; border: 1px solid #e5e7eb;
        border-radius: 10px; padding: 12px 16px;
    }
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] div {
        color: #1a1a1a !important;
    }
    .kw-pill {
        display: inline-block; padding: 4px 12px; margin: 4px 6px 4px 0;
        border-radius: 999px; font-size: 0.85rem; font-weight: 500;
    }
    .kw-matched {background: #e6f4ea; color: #1e7e34; border: 1px solid #b7e1c0;}
    .kw-missing {background: #fdeceb; color: #c62828; border: 1px solid #f5c6c3;}
    .suggestion-box {
        background: #f8f9fb; border-left: 3px solid #4f46e5;
        border-radius: 6px; padding: 10px 14px; margin-bottom: 10px;
    }
    .lag-box {
        background: #fdeceb; border-left: 3px solid #c62828;
        border-radius: 6px; padding: 8px 14px; margin-bottom: 8px; color: #1a1a1a;
    }
    .fwd-box {
        background: #e6f4ea; border-left: 3px solid #2e7d32;
        border-radius: 6px; padding: 8px 14px; margin-bottom: 8px; color: #1a1a1a;
    }
    .bonus-box {
        background: #eef2ff; border-left: 3px solid #4f46e5;
        border-radius: 6px; padding: 8px 14px; margin-bottom: 8px; color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 📄 ATS Resume Checker")
    st.caption("Free resume-to-JD match analyzer")
    st.markdown("---")
    st.markdown(
        "**How it works**\n\n"
        "1. Upload your resume (PDF/DOCX)\n"
        "2. Paste the job description\n"
        "3. Get your ATS score + missing keywords\n"
        "4. Edit your resume text and re-score instantly\n"
    )
    st.markdown("---")
    st.caption("Built with Streamlit · v1.1")

# ---------- Hero ----------
st.title("ATS Resume Checker")
st.markdown('<p class="hero-subtitle">See exactly how your resume scores against a job description — then edit and re-score instantly.</p>', unsafe_allow_html=True)
st.write("")

# ---------- Session state init ----------
for key in ["jd_keywords", "resume_text", "formatting_result", "score_result", "matched", "missing"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------- Input area ----------
col1, col2 = st.columns(2)
with col1:
    resume_file = st.file_uploader("📎 Upload your resume", type=["pdf", "docx"])
with col2:
    jd_text = st.text_area("📋 Paste the job description", height=180, placeholder="Paste the full JD text here...")

run_button = st.button("🔍 Analyze Resume", type="primary", use_container_width=True)
st.write("")


def render_score_section(score_result, matched, missing):
    st.subheader("Your ATS Score")
    score_col, verdict_col = st.columns([1, 2])

    with score_col:
        gauge_color = ("#2E7D32" if score_result["overall_score"] >= 80 else
                        "#F9A825" if score_result["overall_score"] >= 60 else "#C62828")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score_result["overall_score"],
            number={"suffix": " / 100", "font": {"size": 36}},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": gauge_color, "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 60], "color": "#FDE0DC"},
                    {"range": [60, 80], "color": "#FFF3CD"},
                    {"range": [80, 100], "color": "#D9EAD3"},
                ],
            },
        ))
        fig.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with verdict_col:
        m1, m2 = st.columns(2)
        m1.metric("Keyword Match", f"{score_result['keyword_match_pct']}%")
        m2.metric("Formatting Score", f"{score_result['formatting_score']}/100")
        if score_result["overall_score"] >= 80:
            st.success(score_result["verdict"])
        elif score_result["overall_score"] >= 60:
            st.warning(score_result["verdict"])
        else:
            st.error(score_result["verdict"])

    st.markdown("---")
    st.subheader("Keyword Breakdown")
    bar_fig = go.Figure(data=[
        go.Bar(name="Matched", x=["Keywords"], y=[len(matched)], marker_color="#2E7D32",
               text=[len(matched)], textposition="inside"),
        go.Bar(name="Missing", x=["Keywords"], y=[len(missing)], marker_color="#C62828",
               text=[len(missing)], textposition="inside"),
    ])
    bar_fig.update_layout(
        barmode="stack", height=140, margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True, legend=dict(orientation="h", y=-0.3),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(bar_fig, use_container_width=True)

    mcol, xcol = st.columns(2)
    with mcol:
        st.markdown("**✅ Found in your resume**")
        if matched:
            pills = "".join(f'<span class="kw-pill kw-matched">{kw["term"]}</span>' for kw in sorted(matched, key=lambda x: -x["score"]))
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.write("None found.")
    with xcol:
        st.markdown("**❌ Missing — consider adding these**")
        if missing:
            pills = "".join(f'<span class="kw-pill kw-missing">{kw["term"]}</span>' for kw in sorted(missing, key=lambda x: -x["score"]))
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.write("No major gaps found!")


# ---------- Run initial analysis ----------
if run_button:
    if not resume_file:
        st.error("Please upload a resume file.")
    elif not jd_text or len(jd_text.strip()) < 50:
        st.error("Please paste a job description (at least a few sentences).")
    else:
        with st.spinner("Analyzing your resume..."):
            raw_resume_text = extract_resume_text(resume_file)
            resume_text = clean_text(raw_resume_text)

            formatting_result = check_formatting(raw_resume_text)
            jd_keywords = extract_jd_keywords(jd_text, top_n=30)
            matched, missing = match_keywords(resume_text, jd_keywords)
            score_result = compute_ats_score(matched, missing, formatting_result["formatting_score"])

        st.session_state.jd_keywords = jd_keywords
        st.session_state.resume_text = resume_text
        st.session_state.formatting_result = formatting_result
        st.session_state.score_result = score_result
        st.session_state.matched = matched
        st.session_state.missing = missing

# ---------- Display results if we have them ----------
if st.session_state.score_result:
    # Pre-compute positioning + suggestions once so they're available for
    # both the dashboard sections below and the PDF download button.
    positioning = get_skill_positioning(
        st.session_state.matched, st.session_state.missing,
        st.session_state.resume_text, st.session_state.jd_keywords,
    )
    suggestions = generate_suggestions(st.session_state.missing, max_suggestions=8)

    st.markdown("---")
    render_score_section(st.session_state.score_result, st.session_state.matched, st.session_state.missing)

    # ----- PDF download -----
    pdf_bytes = build_pdf_report(
        st.session_state.score_result, st.session_state.matched, st.session_state.missing,
        positioning, suggestions, st.session_state.formatting_result["issues"],
    )
    st.download_button(
        "📥 Download PDF Report",
        data=pdf_bytes,
        file_name="ats_resume_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("Formatting & Readability Checks")
    if st.session_state.formatting_result["issues"]:
        for issue in st.session_state.formatting_result["issues"]:
            st.warning(issue)
    else:
        st.success("No major formatting issues detected.")

    st.markdown("---")

    # ----- Skill positioning dashboard: lagging vs forward -----
    st.subheader("📊 Skill Positioning")
    st.caption(
        "Lagging = important skills this JD wants that you're missing. "
        "Forward = skills you already bring, including ones the JD didn't "
        "even ask for -- your differentiators for this specific role."
    )

    positioning = get_skill_positioning(
        st.session_state.matched, st.session_state.missing,
        st.session_state.resume_text, st.session_state.jd_keywords,
    )  # already computed above, kept as-is for clarity in this section
    breakdown = category_breakdown(st.session_state.matched, st.session_state.missing)

    if breakdown:
        categories = list(breakdown.keys())
        cat_labels = [CATEGORY_LABELS.get(c, c.title()) for c in categories]
        matched_counts = [breakdown[c]["matched"] for c in categories]
        missing_counts = [-breakdown[c]["missing"] for c in categories]

        div_fig = go.Figure()
        div_fig.add_trace(go.Bar(
            y=cat_labels, x=matched_counts, name="Forward (have it)",
            orientation="h", marker_color="#2E7D32",
        ))
        div_fig.add_trace(go.Bar(
            y=cat_labels, x=missing_counts, name="Lagging (missing)",
            orientation="h", marker_color="#C62828",
        ))
        div_fig.update_layout(
            barmode="relative", height=280,
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", y=-0.2),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(zeroline=True, zerolinewidth=1, zerolinecolor="#999"),
        )
        st.plotly_chart(div_fig, use_container_width=True)

    lag_col, fwd_col, bonus_col = st.columns(3)
    with lag_col:
        st.markdown("**🔴 Lagging — close these gaps**")
        if positioning["lagging"]:
            for kw in positioning["lagging"]:
                st.markdown(f'<div class="lag-box">{kw["term"]}</div>', unsafe_allow_html=True)
        else:
            st.write("No major gaps.")
    with fwd_col:
        st.markdown("**🟢 Forward — you meet these**")
        if positioning["forward_core"]:
            for kw in positioning["forward_core"]:
                st.markdown(f'<div class="fwd-box">{kw["term"]}</div>', unsafe_allow_html=True)
        else:
            st.write("Nothing matched yet.")
    with bonus_col:
        st.markdown("**🔵 Bonus — beyond what was asked**")
        if positioning["bonus"]:
            for kw in positioning["bonus"]:
                st.markdown(f'<div class="bonus-box">{kw["term"]}</div>', unsafe_allow_html=True)
        else:
            st.write("None detected.")

    st.markdown("---")

    # ----- Suggested sentences for missing keywords -----
    st.subheader("✏️ Suggested lines to add")
    st.caption(
        "These are starting-point templates, not finished bullets — edit each "
        "one so it's truthful and specific to what you actually did before "
        "adding it to your resume."
    )
    suggestions = generate_suggestions(st.session_state.missing, max_suggestions=8)
    if suggestions:
        for s in suggestions:
            st.markdown(f'<div class="suggestion-box"><b>{s["term"]}</b><br>{s["suggestion"]}</div>', unsafe_allow_html=True)
    else:
        st.write("No missing keywords to suggest for — nice work.")

    st.markdown("---")

    # ----- Editable resume text + re-score -----
    st.subheader("🔁 Edit your resume text and re-score")
    st.caption(
        "Paste the updated version of your resume text below (add the lines "
        "above wherever they fit) and click Recalculate to see your new score, "
        "without re-uploading the file."
    )
    edited_text = st.text_area(
        "Editable resume text",
        value=st.session_state.resume_text,
        height=300,
        key="edited_resume_text",
    )
    recalc_button = st.button("🔄 Recalculate Score", type="primary")

    if recalc_button:
        with st.spinner("Recalculating..."):
            new_matched, new_missing = match_keywords(edited_text, st.session_state.jd_keywords)
            new_score = compute_ats_score(
                new_matched, new_missing, st.session_state.formatting_result["formatting_score"]
            )
        st.session_state.resume_text = edited_text
        st.session_state.matched = new_matched
        st.session_state.missing = new_missing
        st.session_state.score_result = new_score
        st.success(f"Updated! New score: {new_score['overall_score']} / 100")
        st.rerun()

else:
    st.info("👆 Upload a resume and paste a job description, then click **Analyze Resume**.")
