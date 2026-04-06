"""
============================================================
  Learning from Mistakes Attitude & Academic Growth
                    Tracking Scale

  Module      : Fundamentals of Programming, 4BUIS008C
  Web App     : Streamlit (available online for everyone)
  Author      : Sardorjon Istamov
  Student ID  : 00020312
============================================================
"""
import streamlit as st
import json
import csv
import re
import io
from datetime import datetime

# ══════════════════════════════════════════════════════════
#  CONSTANTS  — demonstrates all required variable types
# ══════════════════════════════════════════════════════════
ALLOWED_FILE_FORMATS: tuple = ("json", "csv", "txt")
VALID_MONTHS: frozenset = frozenset(range(1, 13))
QUESTIONS_FILE: str = "questions.json"
MAX_SCORE_PER_QUESTION: int = 4
PASSING_THRESHOLD: float = 39.5
SURVEY_TITLE: str = "Learning from Mistakes Attitude & Academic Growth Tracking Scale"


# ══════════════════════════════════════════════════════════
#  DATA LOADING  — reads questions from questions.json
# ══════════════════════════════════════════════════════════
def load_survey_data() -> tuple:
    """
    Load questions and states from questions.json.
    Uses a WHILE loop with retry logic.
    Falls back to hardcoded data if file is missing.
    Returns (questions: list, states: list, source: str).
    """
    questions: list = []
    states: list = []
    source: str = "hardcoded"

    max_retries: int = 3
    attempt: int = 0

    while attempt < max_retries:
        try:
            with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
                data: dict = json.load(f)
            questions = data["questions"]
            states = data["psychological_states"]
            source = "file"
            break
        except FileNotFoundError:
            source = "hardcoded"
            break
        except (json.JSONDecodeError, KeyError):
            attempt += 1
            if attempt == max_retries:
                source = "hardcoded"

    if source == "hardcoded":
        questions = HARDCODED_QUESTIONS
        states = HARDCODED_STATES

    return questions, states, source


# ══════════════════════════════════════════════════════════
#  INPUT VALIDATION FUNCTIONS
# ══════════════════════════════════════════════════════════
def validate_name_field(value: str) -> tuple:
    """
    Validate a name (surname or given name).
    Uses a FOR loop to inspect each character.
    Allowed: letters, hyphens, apostrophes, spaces.
    Returns (is_valid: bool, error_message: str).
    """
    if not value.strip():
        return False, "This field cannot be empty."

    invalid_chars: set = set()
    for ch in value:
        if not re.match(r"[A-Za-z\-\' ]", ch):
            invalid_chars.add(ch)

    if invalid_chars:
        return False, (
            f"Invalid character(s): {invalid_chars}. "
            "Only letters, hyphens, apostrophes, and spaces allowed."
        )
    return True, ""


def validate_all_personal_fields(fields: dict) -> list:
    """
    Validate all personal info fields using a WHILE loop.
    Returns a list of error messages (empty list = all valid).
    """
    errors: list = []
    field_keys: list = list(fields.keys())
    idx: int = 0

    while idx < len(field_keys):
        key: str = field_keys[idx]
        value: str = fields[key]

        if key in ("surname", "given_name"):
            is_valid: bool
            msg: str
            is_valid, msg = validate_name_field(value)
            if not is_valid:
                label = "Surname" if key == "surname" else "Given name"
                errors.append(f"{label}: {msg}")

        elif key == "student_id":
            if not value.strip():
                errors.append("Student ID: cannot be empty.")
            elif not value.strip().isdigit():
                errors.append("Student ID: must contain digits only.")

        elif key == "date_of_birth":
            dob_valid, dob_msg = validate_date_of_birth(value)
            if not dob_valid:
                errors.append(f"Date of birth: {dob_msg}")

        idx += 1

    return errors


def validate_date_of_birth(raw: str) -> tuple:
    """
    Validate date of birth in DD/MM/YYYY format.
    Uses IF / ELIF / ELSE conditional statements.
    Returns (is_valid: bool, message: str).
    """
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", raw.strip()):
        return False, "Format must be DD/MM/YYYY (e.g. 15/03/2003)."

    parts: list = raw.strip().split("/")
    day: int = int(parts[0])
    month: int = int(parts[1])
    year: int = int(parts[2])

    if month not in VALID_MONTHS:
        return False, "Month must be between 01 and 12."
    elif year < 1900 or year > datetime.now().year:
        return False, f"Year must be between 1900 and {datetime.now().year}."
    else:
        days_in_month: dict = {
            1: 31,
            2: 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28,
            3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
        }
        if day < 1 or day > days_in_month[month]:
            return False, (
                f"Day must be between 01 and {days_in_month[month]} "
                f"for month {month:02d}."
            )

    birth_date = datetime(year, month, day)
    age_days: int = (datetime.now() - birth_date).days
    if age_days < 3650:
        return False, "Date of birth suggests respondent is under 10 years old."

    return True, ""


# ══════════════════════════════════════════════════════════
#  SCORE CALCULATION & STATE LOOKUP
# ══════════════════════════════════════════════════════════
def calculate_score(answers: dict, questions: list) -> tuple:
    """
    Calculate total score from answers dict.
    Uses FOR loop and range variable type.
    Returns (total_score: int, scores_per_question: list, max_possible: int).
    """
    scores_per_question: list = []
    total: int = 0
    max_possible: int = 0

    for i in range(len(questions)):
        q = questions[i]
        chosen_idx: int = answers.get(i, 0)
        score_val: int = q["options"][chosen_idx]["score"]
        scores_per_question.append(score_val)
        total += score_val
        max_possible += max(opt["score"] for opt in q["options"])

    return total, scores_per_question, max_possible


def get_psychological_state(total_score: int, states: list) -> dict:
    """Look up the psychological state for a given total score."""
    for state in states:
        if state["min"] <= total_score <= state["max"]:
            return state
    return {
        "label": "Unknown",
        "description": "Score out of range.",
        "emoji": "❓",
        "color": "#888888",
    }


# ══════════════════════════════════════════════════════════
#  FILE GENERATION FOR DOWNLOAD  (persistence — LO3)
# ══════════════════════════════════════════════════════════
def generate_json_bytes(result_data: dict) -> bytes:
    """Serialise result data to JSON bytes for download."""
    return json.dumps(result_data, indent=4, ensure_ascii=False).encode("utf-8")


def generate_csv_bytes(result_data: dict) -> bytes:
    """Serialise result data to CSV bytes for download."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Field", "Value"])
    summary_fields: list = [
        ("Survey",             result_data["survey"]),
        ("Name",               result_data["respondent"]["name"]),
        ("Student ID",         result_data["respondent"]["student_id"]),
        ("Date of Birth",      result_data["respondent"]["date_of_birth"]),
        ("Timestamp",          result_data["timestamp"]),
        ("Total Score",        result_data["total_score"]),
        ("Max Possible",       result_data["max_possible"]),
        ("Percentage",         f"{result_data['percentage']}%"),
        ("Psychological State",result_data["psychological_state"]),
        ("Description",        result_data["description"]),
    ]
    for field, value in summary_fields:
        writer.writerow([field, value])

    writer.writerow([])
    writer.writerow(["Question #", "Question Text", "Chosen Answer", "Score"])
    for entry in result_data["answers"]:
        writer.writerow([
            entry["question_number"],
            entry["question_text"],
            entry["chosen_answer"],
            entry["score"],
        ])

    return output.getvalue().encode("utf-8")


def generate_txt_bytes(result_data: dict) -> bytes:
    """Serialise result data to plain-text bytes for download."""
    lines: list = [
        "=" * 60,
        f"  SURVEY: {result_data['survey']}",
        "=" * 60,
        f"  Name          : {result_data['respondent']['name']}",
        f"  Student ID    : {result_data['respondent']['student_id']}",
        f"  Date of Birth : {result_data['respondent']['date_of_birth']}",
        f"  Completed     : {result_data['timestamp']}",
        f"  Total Score   : {result_data['total_score']} / {result_data['max_possible']} ({result_data['percentage']}%)",
        f"  Result        : {result_data['psychological_state']}",
        "",
        f"  {result_data['description']}",
        "=" * 60,
        "",
        "  QUESTION-BY-QUESTION BREAKDOWN",
        "-" * 60,
    ]
    for entry in result_data["answers"]:
        lines.append(f"  Q{entry['question_number']}. {entry['question_text']}")
        lines.append(f"       Answer : {entry['chosen_answer']}  (Score: {entry['score']})")
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def build_result_data(ss) -> dict:
    """Build the result data dictionary from session state."""
    questions: list = ss["questions"]
    answers: dict = ss["answers"]
    total_score: int = ss["total_score"]
    scores_per_q: list = ss["scores_per_question"]
    max_possible: int = ss["max_possible"]
    percentage: float = round((total_score / max_possible) * 100, 2)
    state: dict = ss["state"]

    answer_details: list = []
    for i in range(len(questions)):             # FOR loop
        q = questions[i]
        chosen_idx: int = answers.get(i, 0)
        answer_details.append({
            "question_number": i + 1,
            "question_text": q["text"],
            "chosen_answer": q["options"][chosen_idx]["text"],
            "score": scores_per_q[i],
        })

    return {
        "survey": SURVEY_TITLE,
        "respondent": {
            "name": f"{ss['given_name']} {ss['surname']}",
            "student_id": ss["student_id"],
            "date_of_birth": ss["date_of_birth"],
        },
        "timestamp": ss["timestamp"],
        "total_score": total_score,
        "max_possible": max_possible,
        "percentage": percentage,
        "psychological_state": state["label"],
        "description": state["description"],
        "answers": answer_details,
    }


# ══════════════════════════════════════════════════════════
#  PAGE RENDERERS
# ══════════════════════════════════════════════════════════
def page_menu(questions: list, states: list, source: str) -> None:
    """Render the main menu / welcome screen."""
    st.markdown(
        """
        <div style='text-align:center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size:2rem;'>📚 Academic Growth Tracking Scale</h1>
            <p style='font-size:1.05rem; color:#888; max-width:650px; margin:auto;'>
                <em>Learning from Mistakes Attitude Survey</em><br>
                Westminster International University in Tashkent
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📝 New Survey")
        st.markdown("Complete the questionnaire to discover your academic growth mindset profile.")
        if st.button("Start New Survey", use_container_width=True, type="primary"):
            st.session_state["page"] = "personal_info"
            st.rerun()

    with col2:
        st.markdown("### 📂 Load Results")
        st.markdown("Upload a previously saved result file (JSON, CSV, or TXT) to view it again.")
        if st.button("Load Existing Results", use_container_width=True):
            st.session_state["page"] = "load_results"
            st.rerun()

    st.divider()
    with st.expander("ℹ️ About this survey"):
        st.markdown(f"""
        **Survey:** {SURVEY_TITLE}

        This survey measures your attitude toward academic mistakes and your ability
        to track and grow from them. It consists of **{len(questions)} questions**,
        each with **5 answer options** scored 0–4.

        Your total score places you in one of **{len(states)} psychological state
        categories**, ranging from *Exceptional Growth Mindset* to *Fixed Mindset Tendency*.

        Questions loaded from: **{source}**
        """)


def page_personal_info() -> None:
    """Render the personal information form."""
    st.markdown("## 👤 Personal Information")
    st.markdown("Please fill in your details below. All fields are required.")
    st.progress(0.1, text="Step 1 of 3 — Personal Details")

    with st.form("personal_info_form"):
        col1, col2 = st.columns(2)
        with col1:
            surname = st.text_input(
                "Surname *",
                placeholder="e.g. Smith, O'Connor, Smith-Jones",
                help="Letters, hyphens, apostrophes, and spaces only.",
            )
        with col2:
            given_name = st.text_input(
                "Given Name *",
                placeholder="e.g. Mary Ann",
                help="Letters, hyphens, apostrophes, and spaces only.",
            )

        col3, col4 = st.columns(2)
        with col3:
            dob = st.text_input(
                "Date of Birth *",
                placeholder="DD/MM/YYYY",
                help="Format: DD/MM/YYYY — e.g. 15/03/2003",
            )
        with col4:
            student_id = st.text_input(
                "Student ID *",
                placeholder="e.g. 00020312",
                help="Digits only.",
            )

        submitted = st.form_submit_button(
            "Continue to Survey →",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            fields: dict = {
                "surname": surname,
                "given_name": given_name,
                "date_of_birth": dob,
                "student_id": student_id,
            }
            errors: list = validate_all_personal_fields(fields)

            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                st.session_state["surname"] = surname.strip()
                st.session_state["given_name"] = given_name.strip()
                st.session_state["date_of_birth"] = dob.strip()
                st.session_state["student_id"] = student_id.strip()
                st.session_state["answers"] = {}
                st.session_state["page"] = "survey"
                st.rerun()

    if st.button("← Back to Menu"):
        st.session_state["page"] = "menu"
        st.rerun()


def page_survey(questions: list) -> None:
    """Render the survey questionnaire."""
    st.markdown("## 📋 Survey Questions")
    st.markdown(
        f"*Hello, **{st.session_state.get('given_name', '')} "
        f"{st.session_state.get('surname', '')}**! "
        "Please answer all questions honestly. There are no right or wrong answers.*"
    )
    st.progress(0.5, text="Step 2 of 3 — Answering Questions")
    st.divider()

    answers: dict = st.session_state.get("answers", {})

    with st.form("survey_form"):
        for i in range(len(questions)):         # FOR loop + range variable type
            q = questions[i]
            option_labels: list = [opt["text"] for opt in q["options"]]

            st.markdown(f"**Q{i + 1}.** {q['text']}")
            default_idx: int = answers.get(i, 0)
            chosen = st.radio(
                label=f"q_{i}",
                options=option_labels,
                index=default_idx,
                label_visibility="collapsed",
                key=f"radio_{i}",
            )
            answers[i] = option_labels.index(chosen)
            st.markdown("---")

        submitted = st.form_submit_button(
            "Submit & See Results →",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            unanswered: list = [
                i + 1 for i in range(len(questions)) if i not in answers
            ]
            if unanswered:
                st.error(f"Please answer all questions. Missing: Q{unanswered}")
            else:
                total, scores_per_q, max_possible = calculate_score(answers, questions)
                state_info: dict = get_psychological_state(
                    total, st.session_state["states"]
                )
                st.session_state["answers"] = answers
                st.session_state["total_score"] = total
                st.session_state["scores_per_question"] = scores_per_q
                st.session_state["max_possible"] = max_possible
                st.session_state["state"] = state_info
                st.session_state["timestamp"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                st.session_state["page"] = "results"
                st.rerun()

    if st.button("← Back to Personal Info"):
        st.session_state["page"] = "personal_info"
        st.rerun()


def page_results(questions: list) -> None:
    """Render the results page with download options."""
    total: int = st.session_state["total_score"]
    max_possible: int = st.session_state["max_possible"]
    percentage: float = round((total / max_possible) * 100, 2)
    state: dict = st.session_state["state"]
    scores_per_q: list = st.session_state["scores_per_question"]
    answers: dict = st.session_state["answers"]

    st.progress(1.0, text="Step 3 of 3 — Your Results")
    st.markdown("## 🎯 Your Results")

    # Result card
    st.markdown(
        f"""
        <div style='border-left: 6px solid {state["color"]};
                    border-radius:8px; padding:1.5rem; margin-bottom:1rem;'>
            <h2 style='color:{state["color"]}; margin:0;'>
                {state["emoji"]} {state["label"]}
            </h2>
            <p style='margin:0.5rem 0 0 0; font-size:1rem;'>
                {state["description"]}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Score", f"{total} / {max_possible}")
    col2.metric("Percentage", f"{percentage}%")
    col3.metric(
        "Respondent",
        f"{st.session_state.get('given_name', '')} "
        f"{st.session_state.get('surname', '')}",
    )

    st.divider()

    with st.expander("📊 Score Breakdown by Question", expanded=False):
        chart_data: dict = {
            "Question": [f"Q{i+1}" for i in range(len(scores_per_q))],
            "Score": scores_per_q,
        }
        st.bar_chart(
            data=chart_data, x="Question", y="Score", use_container_width=True
        )

    with st.expander("📝 Detailed Answer Review", expanded=False):
        for i in range(len(questions)):         # FOR loop
            q = questions[i]
            chosen_idx: int = answers.get(i, 0)
            chosen_text: str = q["options"][chosen_idx]["text"]
            sc: int = scores_per_q[i]
            color: str = (
                "#1a7f3c" if sc <= 1 else ("#e0a500" if sc <= 2 else "#c0392b")
            )
            st.markdown(
                f"**Q{i+1}.** {q['text']}  \n"
                f"→ *{chosen_text}* &nbsp; "
                f"<span style='color:{color}; font-weight:bold;'>Score: {sc}</span>",
                unsafe_allow_html=True,
            )

    with st.expander("🧠 All Psychological States", expanded=False):
        for s in st.session_state["states"]:
            marker = " ◀ **You are here**" if s["label"] == state["label"] else ""
            st.markdown(
                f"<span style='color:{s.get('color','#333')};'>"
                f"**{s['emoji']} {s['label']}**</span>"
                f" ({s['min']}–{s['max']} pts){marker}",
                unsafe_allow_html=True,
            )
            st.caption(s["description"])

    st.divider()
    st.markdown("### 💾 Save Your Results")

    result_data: dict = build_result_data(st.session_state)
    ts: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    sid: str = st.session_state.get("student_id", "000000")

    col_j, col_c, col_t = st.columns(3)
    with col_j:
        st.download_button(
            label="⬇ Download JSON",
            data=generate_json_bytes(result_data),
            file_name=f"result_{sid}_{ts}.json",
            mime="application/json",
            use_container_width=True,
            type="primary",
        )
    with col_c:
        st.download_button(
            label="⬇ Download CSV",
            data=generate_csv_bytes(result_data),
            file_name=f"result_{sid}_{ts}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_t:
        st.download_button(
            label="⬇ Download TXT",
            data=generate_txt_bytes(result_data),
            file_name=f"result_{sid}_{ts}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.divider()
    if st.button("🔄 Take Survey Again", use_container_width=True):
        for key in [
            "answers", "total_score", "scores_per_question", "max_possible",
            "state", "timestamp", "surname", "given_name", "date_of_birth", "student_id",
        ]:
            st.session_state.pop(key, None)
        st.session_state["page"] = "menu"
        st.rerun()


def page_load_results() -> None:
    """Render the load/view existing results page."""
    st.markdown("## 📂 Load Existing Results")
    st.markdown("Upload a previously saved result file to view it here.")

    uploaded = st.file_uploader(
        "Choose a result file",
        type=["json", "csv", "txt"],
        help="Files saved by this app — named result_STUDENTID_TIMESTAMP.json/csv/txt",
    )

    if uploaded is not None:
        ext: str = uploaded.name.rsplit(".", 1)[-1].lower()
        content: str = uploaded.read().decode("utf-8")

        st.success(f"✅ File **{uploaded.name}** loaded successfully.")
        st.divider()

        if ext == "json":
            try:
                data: dict = json.loads(content)
                r = data.get("respondent", {})
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Survey Details**")
                    st.write(f"📋 Survey: {data.get('survey', 'N/A')}")
                    st.write(f"📅 Completed: {data.get('timestamp', 'N/A')}")
                with col2:
                    st.markdown("**Respondent**")
                    st.write(f"👤 Name: {r.get('name', 'N/A')}")
                    st.write(f"🆔 Student ID: {r.get('student_id', 'N/A')}")
                    st.write(f"🎂 DOB: {r.get('date_of_birth', 'N/A')}")

                pct: float = data.get("percentage", 0)
                col_a, col_b, col_c = st.columns(3)
                col_a.metric(
                    "Score",
                    f"{data.get('total_score','N/A')} / {data.get('max_possible','N/A')}",
                )
                col_b.metric("Percentage", f"{pct}%")
                col_c.metric("State", data.get("psychological_state", "N/A"))
                st.info(f"📝 {data.get('description', '')}")

                with st.expander("Full Answer Breakdown"):
                    for entry in data.get("answers", []):
                        st.markdown(
                            f"**Q{entry['question_number']}.** {entry['question_text']}  \n"
                            f"→ *{entry['chosen_answer']}* (Score: {entry['score']})"
                        )
            except (json.JSONDecodeError, KeyError) as e:
                st.error(f"Could not parse JSON file: {e}")

        elif ext == "csv":
            st.markdown("**CSV Contents:**")
            lines: list = content.splitlines()
            display_rows: list = []
            for line in lines:
                if line.strip():
                    display_rows.append(line)
            st.code("\n".join(display_rows[:15]))

        elif ext == "txt":
            st.markdown("**Text Contents:**")
            st.code(content[:2000])

    if st.button("← Back to Menu"):
        st.session_state["page"] = "menu"
        st.rerun()


# ══════════════════════════════════════════════════════════
#  HARDCODED FALLBACK DATA
#  (used only if questions.json is missing)
# ══════════════════════════════════════════════════════════
HARDCODED_QUESTIONS: list = [
    {
        "id": 1,
        "text": "When you make an academic mistake, how do you typically feel afterward?",
        "options": [
            {"text": "Motivated to improve immediately", "score": 0},
            {"text": "Slightly discouraged but recover quickly", "score": 1},
            {"text": "Neutral — it happens to everyone", "score": 2},
            {"text": "Discouraged for a while", "score": 3},
            {"text": "Very discouraged and unmotivated", "score": 4},
        ],
    },
    {
        "id": 2,
        "text": "How often do you reflect on the reasons behind your academic errors?",
        "options": [
            {"text": "Always", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 3,
        "text": "When you receive a low grade, what is your first reaction?",
        "options": [
            {"text": "Analyse what went wrong and plan to fix it", "score": 0},
            {"text": "Seek feedback from the teacher", "score": 1},
            {"text": "Accept it and move on", "score": 2},
            {"text": "Feel frustrated and dwell on it", "score": 3},
            {"text": "Give up on the subject", "score": 4},
        ],
    },
    {
        "id": 4,
        "text": "How frequently do you revisit past mistakes to extract lessons from them?",
        "options": [
            {"text": "Always", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 5,
        "text": "Do you believe your academic abilities can be developed through effort?",
        "options": [
            {"text": "Strongly agree", "score": 0},
            {"text": "Agree", "score": 1},
            {"text": "Neutral", "score": 2},
            {"text": "Disagree", "score": 3},
            {"text": "Strongly disagree", "score": 4},
        ],
    },
    {
        "id": 6,
        "text": "How often do you actively seek constructive feedback after making errors?",
        "options": [
            {"text": "Always", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 7,
        "text": "When you struggle with an academic topic, how do you respond?",
        "options": [
            {"text": "Seek extra resources and help immediately", "score": 0},
            {"text": "Ask for help eventually", "score": 1},
            {"text": "Struggle on my own for a long time", "score": 2},
            {"text": "Avoid the topic as much as possible", "score": 3},
            {"text": "Give up on understanding it", "score": 4},
        ],
    },
    {
        "id": 8,
        "text": "How often do you set new academic goals after identifying a personal weakness?",
        "options": [
            {"text": "Always", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 9,
        "text": "How comfortable are you discussing your academic mistakes with classmates or teachers?",
        "options": [
            {"text": "Very comfortable", "score": 0},
            {"text": "Comfortable", "score": 1},
            {"text": "Neutral", "score": 2},
            {"text": "Uncomfortable", "score": 3},
            {"text": "Very uncomfortable", "score": 4},
        ],
    },
    {
        "id": 10,
        "text": "How often do you keep a record tracking your academic progress and improvements?",
        "options": [
            {"text": "Always", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 11,
        "text": "When you fail a test, how quickly do you get back on track?",
        "options": [
            {"text": "Immediately — I start planning my recovery", "score": 0},
            {"text": "Within a day or two", "score": 1},
            {"text": "Within a week", "score": 2},
            {"text": "After several weeks", "score": 3},
            {"text": "I struggle to fully recover", "score": 4},
        ],
    },
    {
        "id": 12,
        "text": "Do you view constructive criticism as an opportunity to grow?",
        "options": [
            {"text": "Always", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 13,
        "text": "How often do you compare your current academic performance to your past performance?",
        "options": [
            {"text": "Always — I track my progress carefully", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 14,
        "text": "When classmates outperform you, how does it make you feel?",
        "options": [
            {"text": "Inspired to work harder", "score": 0},
            {"text": "Slightly motivated", "score": 1},
            {"text": "Neutral", "score": 2},
            {"text": "Discouraged", "score": 3},
            {"text": "Deeply demotivated", "score": 4},
        ],
    },
    {
        "id": 15,
        "text": "How often do you revise your study strategies after poor academic results?",
        "options": [
            {"text": "Always", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 16,
        "text": "How strongly do you believe that mistakes are a natural and essential part of learning?",
        "options": [
            {"text": "Completely — mistakes are necessary", "score": 0},
            {"text": "Mostly", "score": 1},
            {"text": "Somewhat", "score": 2},
            {"text": "Slightly", "score": 3},
            {"text": "Not at all", "score": 4},
        ],
    },
    {
        "id": 17,
        "text": "How often do you try a different approach after failing at an academic task?",
        "options": [
            {"text": "Always", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 18,
        "text": "How do you handle repeated mistakes in the same subject area?",
        "options": [
            {"text": "Develop a targeted improvement plan", "score": 0},
            {"text": "Seek specific guidance from a teacher", "score": 1},
            {"text": "Try harder without changing my approach", "score": 2},
            {"text": "Feel frustrated and lose confidence", "score": 3},
            {"text": "Avoid that subject area entirely", "score": 4},
        ],
    },
    {
        "id": 19,
        "text": "How often do you acknowledge and celebrate your own academic growth over time?",
        "options": [
            {"text": "Always", "score": 0},
            {"text": "Often", "score": 1},
            {"text": "Sometimes", "score": 2},
            {"text": "Rarely", "score": 3},
            {"text": "Never", "score": 4},
        ],
    },
    {
        "id": 20,
        "text": "When given a chance to redo or correct an assignment, how do you approach it?",
        "options": [
            {"text": "I thoroughly analyse errors and resubmit with full effort", "score": 0},
            {"text": "I correct errors and make some improvements", "score": 1},
            {"text": "I make minimal changes just to pass", "score": 2},
            {"text": "I rarely take the opportunity", "score": 3},
            {"text": "I never bother redoing assignments", "score": 4},
        ],
    },
]

HARDCODED_STATES: list = [
    {
        "min": 0, "max": 13,
        "label": "Exceptional Growth Mindset",
        "emoji": "🌟",
        "color": "#1a7f3c",
        "description": (
            "You have an outstanding attitude toward mistakes and excellent academic resilience. "
            "You consistently turn errors into growth opportunities. "
            "No intervention needed — keep inspiring others!"
        ),
    },
    {
        "min": 14, "max": 26,
        "label": "Strong Positive Attitude",
        "emoji": "✅",
        "color": "#2d9e5f",
        "description": (
            "You embrace mistakes as learning opportunities and actively track your academic growth. "
            "Your mindset is healthy and productive. "
            "Continue applying your reflective habits."
        ),
    },
    {
        "min": 27, "max": 39,
        "label": "Good Tracking Ability",
        "emoji": "📈",
        "color": "#5aaa3b",
        "description": (
            "You generally learn from mistakes but could improve consistency in reflection. "
            "Consider keeping a more structured error journal to sustain your growth trajectory."
        ),
    },
    {
        "min": 40, "max": 52,
        "label": "Moderate Growth Orientation",
        "emoji": "⚠️",
        "color": "#e0a500",
        "description": (
            "You sometimes struggle with processing mistakes constructively. "
            "Try reframing errors as data points rather than failures. "
            "Practising self-compassion and structured reflection may help."
        ),
    },
    {
        "min": 53, "max": 65,
        "label": "Low Growth Orientation",
        "emoji": "📉",
        "color": "#e07800",
        "description": (
            "You tend to avoid mistakes rather than learn from them. "
            "Keeping an error journal and seeking regular feedback from teachers "
            "is strongly recommended to build a healthier academic mindset."
        ),
    },
    {
        "min": 66, "max": 80,
        "label": "Fixed Mindset Tendency",
        "emoji": "🔴",
        "color": "#c0392b",
        "description": (
            "Mistakes significantly affect your academic confidence and motivation. "
            "Seeking academic counselling or support resources is recommended. "
            "Remember: every expert was once a beginner who did not give up."
        ),
    },
]


# ══════════════════════════════════════════════════════════
#  MAIN APP ENTRY POINT
# ══════════════════════════════════════════════════════════
def main() -> None:
    """Main Streamlit app — entry point."""
    st.set_page_config(
        page_title="Academic Growth Survey — WIUT",
        page_icon="📚",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    # Global CSS — no hardcoded background so it works in both light and dark mode
    st.markdown("""
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        div[data-testid="stForm"] { border-radius: 12px; padding: 1.5rem; }
        .stRadio > div { gap: 0.3rem; }
        </style>
    """, unsafe_allow_html=True)

    if "questions" not in st.session_state:
        questions, states, source = load_survey_data()
        st.session_state["questions"] = questions
        st.session_state["states"] = states
        st.session_state["source"] = source

    questions: list = st.session_state["questions"]
    states: list = st.session_state["states"]
    source: str = st.session_state["source"]

    if "page" not in st.session_state:
        st.session_state["page"] = "menu"

    page: str = st.session_state["page"]
    if page == "menu":
        page_menu(questions, states, source)
    elif page == "personal_info":
        page_personal_info()
    elif page == "survey":
        page_survey(questions)
    elif page == "results":
        page_results(questions)
    elif page == "load_results":
        page_load_results()
    else:
        st.session_state["page"] = "menu"
        st.rerun()


if __name__ == "__main__":
    main()