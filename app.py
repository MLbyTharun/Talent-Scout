"""
Talent Scout — Streamlit UI for evidence-based technical vetting.

Resume x Job Description x GitHub -> ranked candidate reports.

Run:
    set GITHUB_TOKEN=ghp_xxx       (Windows)
    set GROQ_API_KEY=gsk_xxx       (Windows, resume parsing)
    set GOOGLE_API_KEY=xxx         (Windows, repo evaluation)
    streamlit run app.py
"""

import html
import json
import os
import shutil
import tempfile

import streamlit as st

from batch_runner import run_batch

try:
    from llm_config import JD as SAMPLE_JD
except Exception:
    SAMPLE_JD = ""

MAX_UPLOAD_MB = 10

st.set_page_config(
    page_title="Talent Scout",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# st.html (not st.markdown): raw HTML with no markdown pass, so the CSS
# can't be swallowed by indented-code / HTML-block rules and rendered as
# visible text. Style-only bodies also get auto-dedented + routed out of
# the main layout flow.
st.html(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,600&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --hermes: #F37021;
        --hermes-deep: #D9600F;
        --hermes-soft: #FDEEE3;
        --hermes-line: #F5C9A8;
        --ink: #2B2622;
        --ink-soft: #6E645A;
        --cream: #FBF6EF;
        --cream-2: #F3EADF;
        --paper: #FFFDFA;
        --line: #E8DCCB;
        --gold: #B8923D;
        --gold-bg: #FAF1DC;
        --gold-ink: #8A6A1B;
        --sage: #4F7043;
        --sage-bg: #EAF1E6;
        --terracotta: #A64B3A;
        --terracotta-bg: #F8E9E5;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background: var(--cream);
        color: var(--ink);
        font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { background: transparent; }

    h1, h2, h3, h4,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        color: var(--ink) !important;
        font-weight: 600;
        letter-spacing: 0.01em;
    }
    h1 { font-size: 2.4rem !important; line-height: 1.1; }
    h2 { font-size: 1.75rem !important; }
    h3 { font-size: 1.35rem !important; }

    p, li, label, [data-testid="stWidgetLabel"] {
        color: var(--ink);
    }
    [data-testid="stCaptionContainer"], .stCaption, small {
        color: var(--ink-soft) !important;
    }

    .hero { padding: 4px 0 10px; }
    .hero-kicker {
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.24em;
        text-transform: uppercase;
        color: var(--hermes);
    }
    .hero-title {
        font-family: 'Cormorant Garamond', Georgia, serif;
        font-size: clamp(2.1rem, 4vw, 2.85rem);
        font-weight: 600;
        color: var(--ink);
        line-height: 1.12;
        margin-top: 6px;
    }
    .hero-rule {
        width: 64px;
        height: 2px;
        background: linear-gradient(90deg, var(--hermes), var(--gold));
        margin: 16px 0 12px;
        border-radius: 2px;
    }
    .hero-sub {
        color: var(--ink-soft);
        font-size: 15px;
        line-height: 1.55;
        margin: 0;
        max-width: 640px;
    }

    section[data-testid="stSidebar"] {
        background: var(--cream-2);
        border-right: 1px solid var(--line);
    }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--ink) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: var(--ink-soft) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSuccess"],
    section[data-testid="stSidebar"] [data-testid="stWarning"],
    section[data-testid="stSidebar"] [data-testid="stNotification"] {
        font-size: 13px;
    }

    .stButton > button,
    [data-testid="stBaseButton"],
    [data-testid="stDownloadButton"] > button {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.02em;
        border-radius: 999px !important;
        transition: all 0.15s ease !important;
        min-height: 2.6rem;
    }
    .stButton > button,
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-tertiary"] {
        background: #fff !important;
        color: var(--ink) !important;
        border: 1px solid var(--line) !important;
        box-shadow: none !important;
    }
    .stButton > button:hover,
    [data-testid="stBaseButton-secondary"]:hover {
        border-color: var(--hermes) !important;
        color: var(--hermes-deep) !important;
        background: var(--hermes-soft) !important;
    }
    [data-testid="stBaseButton-primary"],
    .stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #F58220 0%, var(--hermes-deep) 100%) !important;
        color: #fff !important;
        border: none !important;
        box-shadow: 0 2px 10px rgba(243, 112, 33, 0.35) !important;
    }
    [data-testid="stBaseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover {
        color: #fff !important;
        filter: brightness(1.06);
        box-shadow: 0 4px 16px rgba(243, 112, 33, 0.45) !important;
        transform: translateY(-1px);
    }
    [data-testid="stDownloadButton"] > button {
        background: var(--hermes-soft) !important;
        color: var(--hermes-deep) !important;
        border: 1px solid var(--hermes-line) !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: var(--hermes) !important;
        color: #fff !important;
        border-color: var(--hermes) !important;
    }

    .stTextArea textarea,
    .stTextInput input,
    [data-baseweb="input"], [data-baseweb="textarea"] {
        background: #fff !important;
        border: 1px solid var(--line) !important;
        border-radius: 14px !important;
        color: var(--ink) !important;
    }
    .stTextArea textarea:focus,
    .stTextInput input:focus,
    [data-baseweb="textarea"]:focus-within,
    [data-baseweb="input"]:focus-within {
        border-color: var(--hermes) !important;
        box-shadow: 0 0 0 3px rgba(243, 112, 33, 0.15) !important;
    }
    .stTextArea textarea::placeholder,
    .stTextInput input::placeholder {
        color: #A89B8C !important;
    }

    [data-testid="stFileUploader"] {
        background: var(--paper);
        border: 1px dashed #D9C9B3;
        border-radius: 18px;
        padding: 6px;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: transparent;
        border-color: #D9C9B3;
        border-radius: 14px;
    }
    [data-testid="stFileUploaderDropzone"] button {
        border-radius: 999px !important;
        border: 1px solid var(--line) !important;
        background: #fff !important;
        color: var(--ink) !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploaderDropzone"] button:hover {
        border-color: var(--hermes) !important;
        color: var(--hermes-deep) !important;
    }

    [data-testid="stMetric"] {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 18px 22px;
        box-shadow: 0 1px 3px rgba(43, 38, 34, 0.05);
    }
    [data-testid="stMetricLabel"] {
        color: var(--ink-soft) !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 11px !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: var(--hermes-deep) !important;
        font-family: 'Cormorant Garamond', Georgia, serif !important;
        font-size: 2.3rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stExpander"],
    details[data-testid="stExpander"] {
        background: #fff !important;
        border: 1px solid var(--line) !important;
        border-radius: 16px !important;
    }
    [data-testid="stExpander"] summary {
        color: var(--ink) !important;
        font-weight: 600;
    }

    [data-testid="stSuccess"], [data-testid="stInfo"],
    [data-testid="stWarning"], [data-testid="stError"],
    [data-testid="stNotification"] {
        border-radius: 14px !important;
        border: 1px solid var(--line) !important;
        background: #fff !important;
        color: var(--ink) !important;
    }
    [data-testid="stSuccess"] {
        background: var(--sage-bg) !important;
        border-color: #C9DCC0 !important;
        color: var(--sage) !important;
    }
    [data-testid="stWarning"] {
        background: var(--gold-bg) !important;
        border-color: #EAD9AE !important;
        color: var(--gold-ink) !important;
    }
    [data-testid="stError"] {
        background: var(--terracotta-bg) !important;
        border-color: #EFC9C0 !important;
        color: var(--terracotta) !important;
    }
    [data-testid="stSidebar"] [data-testid="stSuccess"],
    [data-testid="stSidebar"] [data-testid="stWarning"],
    [data-testid="stSidebar"] [data-testid="stNotification"] {
        font-size: 13px !important;
        padding: 8px 12px !important;
    }

    [role="progressbar"] > div > div,
    div[data-testid="stProgress"] > div > div > div > div {
        background: linear-gradient(90deg, var(--hermes), #F5A04A) !important;
    }

    [data-baseweb="select"] {
        background: #fff !important;
        border-color: var(--line) !important;
        border-radius: 14px !important;
    }
    [data-baseweb="select"]:focus-within {
        border-color: var(--hermes) !important;
        box-shadow: 0 0 0 3px rgba(243, 112, 33, 0.15) !important;
    }

    [data-testid="stToggle"] [data-baseweb="switch"] > span {
        background-color: #D9C9B3 !important;
    }
    [data-testid="stToggle"] [data-baseweb="switch"]:has(checked) > span,
    [data-testid="stToggle"] input:checked ~ span,
    [data-testid="stToggle"] [data-baseweb="switch"]:has(input:checked) > span {
        background-color: var(--hermes) !important;
    }
    [data-baseweb="slider"] [data-baseweb="thumb"] {
        background: #fff !important;
        border: 2px solid var(--hermes) !important;
        box-shadow: 0 1px 4px rgba(43, 38, 34, 0.25);
    }

    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--line);
    }

    [data-testid="stCode"] pre, .stCodeBlock pre, .stCodeBlock code {
        background: var(--ink) !important;
        color: var(--cream-2) !important;
        border-radius: 12px !important;
        font-size: 13px;
    }

    hr { border-color: var(--line) !important; }
    a { color: var(--hermes-deep); }

    .pill {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 999px;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.03em;
        margin: 1px 2px;
        vertical-align: middle;
    }
    .pill-green { background: var(--sage-bg); color: var(--sage); }
    .pill-amber { background: var(--gold-bg); color: var(--gold-ink); }
    .pill-red { background: var(--terracotta-bg); color: var(--terracotta); }
    .pill-grey { background: #F0EAE2; color: var(--ink-soft); }
    .pill-blue { background: var(--hermes-soft); color: var(--hermes-deep); }

    [data-testid="stSpinner"] { color: var(--hermes-deep) !important; }
    [data-testid="stSpinner"] svg path {
        stroke: var(--hermes) !important;
        fill: var(--hermes) !important;
    }
    </style>
    """
)


# ---- Helpers (display-only; pipeline output is untouched) ----

PILL_COLORS = {"green", "amber", "red", "grey", "blue"}


def pill(text: str, color: str = "grey") -> str:
    """HTML pill — text is escaped; color is allowlisted (never raw input)."""
    if color not in PILL_COLORS:
        color = "grey"
    return f'<span class="pill pill-{color}">{html.escape(str(text))}</span>'


def confidence_pill(conf) -> str:
    c = str(conf or "").lower()
    if c == "high":
        return pill("high confidence", "green")
    if c == "medium":
        return pill("medium confidence", "amber")
    if c == "low":
        return pill("low confidence", "red")
    return pill(str(conf or "n/a"), "grey")


def evidence_score(notes: dict) -> int:
    """Heuristic 0-100 signal score from per-repo confidence levels.

    Display-only ranking aid — not a hiring decision.
    """
    ev = notes.get("github_evidence", []) or []
    ev = [e for e in ev if isinstance(e, dict)]
    if not ev:
        return 0
    weights = {"high": 1.0, "medium": 0.6, "low": 0.25}
    total = sum(weights.get(str(e.get("confidence", "")).lower(), 0.3) for e in ev)
    return round(100 * total / len(ev))


def verdict(score: int, gaps: int) -> tuple[str, str]:
    if score >= 65 and gaps <= 3:
        return "Strong signal", "green"
    if score >= 35:
        return "Mixed signal", "amber"
    return "Weak signal", "red"


def candidate_display_name(result, path_to_name: dict) -> str:
    file_name = path_to_name.get(result.resume_path, result.resume_path)
    return (result.resume_data or {}).get("name") or os.path.basename(file_name)


def _md_text(value) -> str:
    """Escape a value for safe inclusion in exported Markdown/HTML viewing."""
    return html.escape(str(value if value is not None else ""))


def candidate_markdown(name: str, file_name: str, notes: dict, repos: list) -> str:
    lines = [f"# {_md_text(name)}", "", f"_Source file: {_md_text(file_name)}_", ""]
    if notes.get("github_fetch_error"):
        lines += [
            "> ⚠️ GitHub fetch failed — evidence below is resume-only:",
            f"> {notes['github_fetch_error']}",
            "",
        ]
    if notes.get("parse_error"):
        lines += ["## Evaluator output (raw)", "", _md_text(notes.get("raw_output", ""))]
        return "\n".join(lines)
    lines += ["## Resume / JD match", "", _md_text(notes.get("resume_jd_match", "n/a")), ""]
    lines += ["## GitHub evidence", ""]
    for e in notes.get("github_evidence", []) or []:
        if isinstance(e, dict):
            lines.append(
                f"- **{_md_text(e.get('repo', '?'))}** ({_md_text(e.get('confidence', 'n/a'))}): "
                f"{_md_text(e.get('relevance', 'n/a'))}"
            )
        else:
            lines.append(f"- {_md_text(e)}")
    lines += ["", "## Gaps", ""]
    for g in notes.get("gaps", []) or []:
        lines.append(f"- {_md_text(g)}")
    lines += ["", "## Overall notes", "", _md_text(notes.get("overall_notes", "n/a")), ""]
    if repos:
        lines += ["## Repos evaluated", ""]
        for p in repos:
            desc = f" — {_md_text(p.get('description'))}" if p.get("description") else ""
            lines.append(
                f"- [{_md_text(p.get('name', '?'))}]({_md_text(p.get('url', '#'))}) "
                f"★{_md_text(p.get('stars', 0))} · {_md_text(p.get('primary_language', '?'))} · "
                f"updated {_md_text(p.get('days_since_last_push', '?'))}d ago{desc}"
            )
    return "\n".join(lines)


# ---- Sidebar ----
try:
    import crewai  # noqa: F401

    _crew_available = True
except ImportError:
    _crew_available = False

with st.sidebar:
    st.header("⚙️ Settings")
    use_crew = st.toggle(
        "Multi-agent crew evaluation",
        value=_crew_available,
        disabled=not _crew_available,
        help=(
            "On: 3 agents (resume analyst, code reviewer, recruiter) debate each "
            "candidate — slower, deeper. Off: single LLM call — faster, good for "
            "quick iteration."
            if _crew_available
            else "crewai is not installed — using single LLM evaluation. "
            "Install with `pip install crewai` to enable."
        ),
    )
    max_workers = st.slider(
        "Concurrent candidates",
        min_value=1,
        max_value=5,
        value=3,
        help="How many candidates to evaluate in parallel. Keep modest to "
        "respect GitHub/LLM rate limits.",
    )
    st.divider()
    st.subheader("Environment")
    light_key = (
        "GOOGLE_API_KEY"
        if os.environ.get("LLM_PROVIDER", "groq").lower() == "google"
        else "GROQ_API_KEY"
    )
    heavy_key = (
        "GROQ_API_KEY"
        if os.environ.get("LLM_HEAVY_PROVIDER", "google").lower() == "groq"
        else "GOOGLE_API_KEY"
    )
    for var in ("GITHUB_TOKEN", light_key, heavy_key):
        if os.environ.get(var):
            st.success(f"✅ {var}")
        else:
            st.warning(f"⚠️ {var} missing")
    st.divider()
    if st.button("🗑️ Clear results"):
        st.session_state.pop("results", None)
        st.session_state.pop("path_to_name", None)
        st.rerun()

# ---- Header ----
# Same reason as the style block above: st.markdown would turn the indented
# <div> into a code block; st.html injects it verbatim.
st.html(
    """
    <div class="hero">
        <div class="hero-kicker">Talent Scout</div>
        <div class="hero-title">Evidence-based technical vetting</div>
        <div class="hero-rule"></div>
        <p class="hero-sub">
            Every resume claim checked against the job description and the
            candidate's actual GitHub code.
        </p>
    </div>
    """
)

# ---- Inputs ----
jd_col, up_col = st.columns([3, 2])
with jd_col:
    jd_text = st.text_area(
        "Job description",
        height=220,
        placeholder="Paste the job description here...",
        key="jd_text",
    )
    if st.button("📋 Load sample JD") and SAMPLE_JD:
        st.session_state["jd_text"] = SAMPLE_JD
        st.rerun()
with up_col:
    uploaded_files = st.file_uploader(
        "Candidate resumes (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        key="resume_uploader",
        help=f"Up to {MAX_UPLOAD_MB} MB per file.",
    )
    if uploaded_files:
        total_mb = sum(getattr(f, "size", 0) for f in uploaded_files) / (1024 * 1024)
        st.caption(f"📄 {len(uploaded_files)} file(s) · {total_mb:.1f} MB total")

run_clicked = st.button(
    "🚀 Run evaluation", type="primary", disabled=not (jd_text and uploaded_files)
)

# ---- Run ----
if run_clicked:
    tmp_dir = tempfile.mkdtemp(prefix="talent-scout-")
    resume_paths = []
    path_to_name = {}
    upload_failed = False
    for f in uploaded_files:
        declared = getattr(f, "size", None)
        if declared is not None and declared > MAX_UPLOAD_MB * 1024 * 1024:
            st.error(f"'{f.name}' exceeds the {MAX_UPLOAD_MB} MB limit — skipping.")
            upload_failed = True
            continue
        try:
            data = f.read()
        except Exception:
            st.error(
                f"Couldn't read '{f.name}' — the upload likely expired because "
                "the app reloaded after you uploaded it. Please re-upload and "
                "try again without editing code in between."
            )
            upload_failed = True
            continue
        if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
            st.error(f"'{f.name}' exceeds the {MAX_UPLOAD_MB} MB limit — skipping.")
            upload_failed = True
            continue
        safe_name = os.path.basename(f.name) or "resume.pdf"
        path = os.path.join(tmp_dir, safe_name)
        base, ext = os.path.splitext(path)
        i = 1
        while os.path.exists(path):
            i += 1
            path = f"{base}_{i}{ext}"
        with open(path, "wb") as out:
            out.write(data)
        resume_paths.append(path)
        path_to_name[path] = f.name

    if upload_failed and not resume_paths:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        st.stop()

    progress_bar = st.progress(0, text="Starting...")
    status = st.empty()

    def update_progress(done, total):
        if total:
            progress_bar.progress(
                done / total, text=f"Evaluated {done}/{total} candidates"
            )
            status.caption(f"Working… {done}/{total} done")

    with st.spinner("Running evaluations…"):
        try:
            results = run_batch(
                resume_paths=resume_paths,
                jd_text=jd_text,
                use_crew=use_crew,
                max_workers=max_workers,
                progress_callback=update_progress,
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    progress_bar.empty()
    status.empty()
    st.session_state["results"] = results
    st.session_state["path_to_name"] = path_to_name

# ---- Results ----
if "results" in st.session_state:
    results = st.session_state.get("results", [])
    path_to_name = st.session_state.get("path_to_name", {})

    succeeded = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    # Rank by heuristic evidence score (display-only).
    ranked = []
    for r in succeeded:
        notes = r.notes or {}
        score = 0 if notes.get("parse_error") else evidence_score(notes)
        gaps = len(notes.get("gaps", []) or [])
        label, color = verdict(score, gaps)
        ranked.append(
            {
                "result": r,
                "name": candidate_display_name(r, path_to_name),
                "score": score,
                "verdict": label,
                "color": color,
                "repos": len(r.repo_profiles or []),
                "gaps": gaps,
            }
        )
    ranked.sort(key=lambda x: x["score"], reverse=True)

    st.subheader("📊 Shortlist")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Evaluated", len(results))
    m2.metric("Strong signal", sum(1 for x in ranked if x["verdict"] == "Strong signal"))
    m3.metric("Repos checked", sum(x["repos"] for x in ranked))
    m4.metric("Failed", len(failed))

    if ranked:
        st.dataframe(
            [
                {
                    "Candidate": x["name"],
                    "Signal (heuristic)": x["score"],
                    "Verdict": x["verdict"],
                    "Repos": x["repos"],
                    "Gaps": x["gaps"],
                }
                for x in ranked
            ],
            use_container_width=True,
            hide_index=True,
        )

        # Export whole shortlist.
        export_md = "\n\n---\n\n".join(
            candidate_markdown(
                x["name"],
                path_to_name.get(x["result"].resume_path, ""),
                x["result"].notes or {},
                x["result"].repo_profiles or [],
            )
            for x in ranked
        )
        export_json = json.dumps(
            {
                x["name"]: {
                    "signal_heuristic": x["score"],
                    "verdict_heuristic": x["verdict"],
                    "notes": x["result"].notes,
                    "repos": x["result"].repo_profiles,
                }
                for x in ranked
            },
            indent=2,
            default=str,
        )
        dl1, dl2 = st.columns(2)
        dl1.download_button(
            "⬇️ Download report (.md)",
            data=export_md,
            file_name="talent-scout-report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        dl2.download_button(
            "⬇️ Download raw results (.json)",
            data=export_json,
            file_name="talent-scout-results.json",
            mime="application/json",
            use_container_width=True,
        )

        st.subheader("🧑‍💻 Candidate reports")
        choice = st.selectbox(
            "Select candidate",
            options=list(range(len(ranked))),
            format_func=lambda i: f"{ranked[i]['name']} — {ranked[i]['verdict']} ({ranked[i]['score']})",
        )
        item = ranked[choice]
        r = item["result"]
        notes = r.notes or {}
        file_name = path_to_name.get(r.resume_path, r.resume_path)

        st.markdown(
            f"### {html.escape(str(item['name']))} "
            f"{pill(item['verdict'] + ' (heuristic)', item['color'])}",
            unsafe_allow_html=True,
        )
        st.caption(f"📎 {os.path.basename(file_name)} · {item['repos']} repos evaluated")

        if notes.get("github_fetch_error"):
            st.warning(
                "GitHub fetch failed — evaluation used resume/JD only: "
                f"{notes['github_fetch_error']}"
            )

        if notes.get("parse_error"):
            st.warning("Evaluator output wasn't valid JSON — showing raw text.")
            st.text(notes.get("raw_output", ""))
        else:
            st.markdown("**Resume / JD match**")
            st.write(notes.get("resume_jd_match", "n/a"))

            st.markdown("**GitHub evidence**")
            evidence = notes.get("github_evidence", []) or []
            if evidence:
                for e in evidence:
                    if not isinstance(e, dict):
                        st.markdown(f"- {e}")
                        continue
                    st.markdown(
                        f"- `{html.escape(str(e.get('repo', '?')))}` — "
                        f"{html.escape(str(e.get('relevance', 'n/a')))} "
                        f"{confidence_pill(e.get('confidence'))}",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No repo evidence linked to this candidate.")

            gaps = notes.get("gaps", []) or []
            if gaps:
                st.markdown("**Gaps & red flags**")
                for g in gaps:
                    st.markdown(f"- ⚠️ {g}")

            st.markdown("**Overall notes**")
            st.write(notes.get("overall_notes", "n/a"))

        if r.repo_profiles:
            st.markdown("**Repos evaluated**")
            st.dataframe(
                [
                    {
                        "Repo": p.get("name", "?"),
                        "★": p.get("stars", 0),
                        "Language": p.get("primary_language", "?"),
                        "Updated (days ago)": p.get("days_since_last_push", "?"),
                        "Description": (p.get("description") or "")[:100],
                    }
                    for p in r.repo_profiles
                ],
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Other candidates"):
            for x in ranked:
                if x["result"] is not r:
                    st.markdown(
                        f"- **{html.escape(str(x['name']))}** "
                        f"{pill(x['verdict'], x['color'])} "
                        f"signal {x['score']} · {x['repos']} repos · {x['gaps']} gaps",
                        unsafe_allow_html=True,
                    )

    if failed:
        st.subheader("❌ Failed")
        for r in failed:
            name = path_to_name.get(r.resume_path, r.resume_path)
            st.error(f"{os.path.basename(name)}: {r.error}")

# Surface GitHub fetch errors even for "successful" candidates.
if "results" in st.session_state:
    fetch_errors = [
        r
        for r in st.session_state.get("results", [])
        if r.success and r.github_fetch_error
    ]
    if fetch_errors:
        st.caption(
            f"⚠️ GitHub fetch failed for {len(fetch_errors)} candidate(s) — "
            "those evaluations are resume-only."
        )
