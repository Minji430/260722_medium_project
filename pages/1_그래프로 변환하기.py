"""
2페이지 : 그래프로 변환하기
구글폼 설문(CSV) → 문항 선택 → matplotlib/seaborn/plotly 비교 → 다운로드
4단계 스텝형 화면으로 구성.

핵심 설계 원칙: 학생마다 서로 다른 CSV를 들고 오므로,
CSV의 인코딩·구분자·문항 형태(선택형/복수응답형/숫자형/주관식)가
무엇이든 안전하게 동작하도록 만든다.
"""

import glob
import io
import os
import shutil
import subprocess

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st

# ============================================================
# 페이지 설정 & 디자인 토큰 (index.html과 동일한 컨셉: 원고지 / 보고서 / 형광펜)
# ============================================================

st.set_page_config(
    page_title="그래프로 변환하기 · 보고서 근거 만들기",
    page_icon="📊",
    layout="wide",
)


@st.cache_resource
def setup_korean_font():
    """fonts/ 폴더에 넣어둔 한글 폰트를 등록해서, 그래프에서 한글이 네모(□)로
    깨지지 않도록 한다. 앱 실행 중 한 번만 실행되도록 캐시한다."""
    font_dir = "static"
    font_files = sorted(glob.glob(os.path.join(font_dir, "*.ttf")))

    if not font_files:
        return None  # 폰트 파일이 없으면 시스템 기본 폰트로 대체 (동작은 계속됨)

    # 1) matplotlib / seaborn 용: matplotlib 폰트 매니저에 직접 등록
    for font_path in font_files:
        fm.fontManager.addfont(font_path)

    regular = next((f for f in font_files if "Regular" in f), font_files[0])
    font_name = fm.FontProperties(fname=regular).get_name()
    plt.rcParams["font.family"] = font_name
    plt.rcParams["axes.unicode_minus"] = False  # 마이너스(-) 기호 깨짐 방지

    # 2) plotly(kaleido)로 이미지 다운로드할 때 쓰는 시스템 폰트 캐시에도 등록 시도
    #    (실패해도 matplotlib/seaborn 그래프에는 영향 없음)
    try:
        user_font_dir = os.path.expanduser("~/.local/share/fonts")
        os.makedirs(user_font_dir, exist_ok=True)
        for font_path in font_files:
            shutil.copy(font_path, user_font_dir)
        subprocess.run(["fc-cache", "-f"], capture_output=True, timeout=15)
    except Exception:
        pass

    return font_name


KOREAN_FONT_NAME = setup_korean_font()

PAPER = "#EFEDE6"
PAPER_CARD = "#FAF9F5"
INK = "#24303D"
INK_SOFT = "#57636E"
HIGHLIGHT = "#FFD400"
TEAL = "#3C6E71"
CORAL = "#E85D4C"
LINE = "#D8D4C8"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {PAPER};
        font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
        color: {INK};
    }}

    h1, h2, h3, .step-title {{
        font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.01em;
        color: {INK} !important;
    }}

    .hl {{
        background: linear-gradient(to bottom, transparent 55%, {HIGHLIGHT} 55%);
        padding: 0 2px;
    }}

    .card {{
        background: {PAPER_CARD};
        border: 1px solid {LINE};
        border-radius: 4px;
        padding: 22px 26px;
    }}

    .step-rail {{
        display: flex;
        gap: 8px;
        margin-bottom: 8px;
    }}
    .step-chip {{
        flex: 1;
        text-align: center;
        padding: 10px 6px;
        border: 1.5px solid {LINE};
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
        color: {INK_SOFT};
        background: {PAPER_CARD};
    }}
    .step-chip.done {{
        border-color: {TEAL};
        color: {TEAL};
    }}
    .step-chip.current {{
        border-color: {INK};
        background: {HIGHLIGHT};
        color: {INK};
        font-weight: 700;
    }}

    .badge {{
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        padding: 3px 9px;
        border-radius: 3px;
        border: 1px solid {TEAL};
        color: {TEAL};
        margin-bottom: 8px;
    }}

    .eyebrow {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {TEAL};
    }}

    div.stButton > button {{
        border: 1.5px solid {INK};
        border-radius: 4px;
        font-weight: 600;
        padding: 0.5rem 1.4rem;
    }}
    div.stButton > button[kind="primary"] {{
        background: {INK};
        color: {PAPER};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 데이터 처리 유틸 — "어떤 CSV가 와도" 견디기 위한 함수들
# ============================================================

ENCODING_CANDIDATES = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]


def read_csv_robust(uploaded_file):
    """인코딩과 구분자를 자동으로 추정해서 CSV를 읽는다.
    성공하면 (DataFrame, None), 실패하면 (None, 에러메시지)를 반환."""
    last_error = None
    for enc in ENCODING_CANDIDATES:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=enc, sep=None, engine="python")
            if df.shape[1] >= 1:
                # 빈 행/열 제거
                df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
                return df, None
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue
    return None, last_error


def parse_pasted_data(text: str):
    """구글 시트에서 복사해 붙여넣은 표 형태의 텍스트를 DataFrame으로 변환.
    구글 시트/엑셀에서 복사하면 보통 탭(Tab)으로 열이 구분되어 붙여넣기 된다."""
    text = text.strip("\n").strip()
    if not text:
        return None, "붙여넣은 내용이 없어요."

    try:
        df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    except Exception:
        try:
            df = pd.read_csv(io.StringIO(text), sep="\t")
        except Exception as e:  # noqa: BLE001
            return None, str(e)

    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")

    if df.shape[1] < 1 or df.empty:
        return None, "표 형태의 데이터를 찾지 못했어요. 머리글(문항)을 포함해서 복사했는지 확인해주세요."

    return df, None


def remove_private_identifier_columns(df: pd.DataFrame):
    """개인정보로 간주되는 식별자 열을 제거한다."""
    private_names = {"학생id", "studentid", "student_id", "student-id"}
    dropped_columns = []
    kept_columns = []

    for col in df.columns:
        normalized = str(col).strip().lower().replace(" ", "").replace("_", "")
        if normalized in private_names or normalized.endswith("studentid"):
            dropped_columns.append(col)
        else:
            kept_columns.append(col)

    if dropped_columns:
        df = df.loc[:, kept_columns]

    return df, dropped_columns


def load_sample_dataframe():
    """제공된 샘플 CSV를 읽어 세션 상태에 저장하고, 바로 2단계로 진입할 수 있게 한다."""
    sample_path = os.path.join("data", "smartphone_survey_simulated_data.csv")
    if not os.path.exists(sample_path):
        st.error("샘플 데이터 파일을 찾을 수 없어요. data 폴더를 확인해주세요.")
        return False

    try:
        df = pd.read_csv(sample_path)
    except Exception as e:  # noqa: BLE001
        st.error(f"샘플 데이터를 읽는 데 문제가 생겼어요: {e}")
        return False

    first_col = df.columns[0]
    if is_timestamp_column(df[first_col], first_col):
        question_df = df.drop(columns=[first_col])
    else:
        question_df = df

    question_df, dropped_private_columns = remove_private_identifier_columns(question_df)
    if question_df.shape[1] == 0:
        st.error("샘플 데이터에서 문항으로 쓸 열이 없어요.")
        return False

    st.session_state.df = question_df
    st.session_state.question_col = question_df.columns[0]
    st.session_state.question_col_type = classify_column(question_df[st.session_state.question_col])
    st.session_state.final_style = "matplotlib"
    st.session_state.step = 2
    st.session_state.max_step_reached = max(st.session_state.max_step_reached, 2)
    st.success("샘플 데이터로 바로 체험해볼 수 있게 준비됐어요. 이제 ②~④ 단계를 이어서 확인해보세요.")
    st.rerun()
    return True


def is_timestamp_column(series: pd.Series, name: str) -> bool:
    """열 이름에 '타임스탬프'가 없어도, 실제 값이 날짜/시간이면 타임스탬프로 판단."""
    name_str = str(name)
    if any(k in name_str for k in ["타임스탬프", "Timestamp", "timestamp"]):
        return True
    sample = series.dropna().head(30)
    if sample.empty:
        return False
    parsed = pd.to_datetime(sample, errors="coerce")
    return parsed.notna().mean() > 0.9


def classify_column(series: pd.Series) -> str:
    """문항 유형 분류: categorical / numeric / multi_select / high_cardinality_text"""
    non_null = series.dropna()
    if non_null.empty:
        return "empty"

    numeric_converted = pd.to_numeric(non_null, errors="coerce")
    numeric_ratio = numeric_converted.notna().mean()
    if numeric_ratio > 0.9:
        if numeric_converted.nunique() > 12:
            return "numeric"
        return "categorical"

    comma_ratio = non_null.astype(str).str.contains(",").mean()
    if comma_ratio > 0.3:
        return "multi_select"

    if non_null.nunique() <= 15:
        return "categorical"

    return "high_cardinality_text"


TYPE_LABELS = {
    "categorical": "선택형 문항",
    "numeric": "숫자형 문항",
    "multi_select": "복수 응답형 문항",
    "high_cardinality_text": "응답이 다양한 문항 (주관식 등)",
    "empty": "응답이 없는 문항",
}


def get_chart_data(series: pd.Series, col_type: str):
    """문항 유형에 맞게 (라벨 목록, 값 목록, 안내 문구)를 만든다."""
    s = series.dropna()
    note = None

    if col_type == "multi_select":
        tokens = s.astype(str).str.split(",").explode().str.strip()
        tokens = tokens[tokens != ""]
        counts = tokens.value_counts()
        note = "여러 개를 고를 수 있는 문항이에요. 한 학생의 응답이 여러 항목에 함께 반영돼요."

    elif col_type == "numeric":
        numeric_s = pd.to_numeric(s, errors="coerce").dropna()
        bin_count = max(2, min(6, numeric_s.nunique()))
        binned = pd.cut(numeric_s, bins=bin_count)
        counts = binned.value_counts().sort_index()
        counts.index = counts.index.astype(str)
        note = "숫자로 된 응답이라 비슷한 값끼리 구간으로 묶어서 보여드려요."

    elif col_type == "high_cardinality_text":
        vc = s.value_counts()
        top = vc.nlargest(9)
        rest_sum = vc.sum() - top.sum()
        if rest_sum > 0:
            top = pd.concat([top, pd.Series({"기타": rest_sum})])
        counts = top
        note = "응답 종류가 많은 문항이라 상위 응답 위주로 보여드리고, 나머지는 '기타'로 묶었어요."

    else:  # categorical / empty
        counts = s.value_counts()

    labels = counts.index.astype(str).tolist()
    values = counts.values.tolist()
    return labels, values, note


# ============================================================
# 상태 초기화
# ============================================================

if "step" not in st.session_state:
    st.session_state.step = 1
if "max_step_reached" not in st.session_state:
    st.session_state.max_step_reached = 1
if "df" not in st.session_state:
    st.session_state.df = None
if "question_col" not in st.session_state:
    st.session_state.question_col = None
if "final_style" not in st.session_state:
    st.session_state.final_style = "matplotlib"

STEP_LABELS = {
    1: "① 파일 올리기",
    2: "② 문항 고르기",
    3: "③ 그래프 비교",
    4: "④ 다운로드",
}


def go_to(step: int):
    st.session_state.step = step


def next_step():
    st.session_state.step += 1
    st.session_state.max_step_reached = max(
        st.session_state.max_step_reached, st.session_state.step
    )


def prev_step():
    st.session_state.step -= 1


# ============================================================
# 상단 타이틀 & 진행 단계
# ============================================================

st.markdown('<p class="eyebrow">STEP BY STEP</p>', unsafe_allow_html=True)
if KOREAN_FONT_NAME is None:
    st.caption(
        "⚠️ static 폴더에서 한글 폰트를 찾지 못했어요. 그래프의 한글이 깨져 보일 수 있어요."
    )
st.markdown("## 설문 결과를 <span class='hl'>그래프</span>로 만들어요", unsafe_allow_html=True)

rail_cols = st.columns(4)
for i, col in enumerate(rail_cols, start=1):
    css_class = "step-chip"
    if i == st.session_state.step:
        css_class += " current"
    elif i < st.session_state.step or i <= st.session_state.max_step_reached:
        css_class += " done"
    with col:
        st.markdown(
            f'<div class="{css_class}">{STEP_LABELS[i]}</div>', unsafe_allow_html=True
        )
        if i <= st.session_state.max_step_reached and i != st.session_state.step:
            if st.button("이동", key=f"jump_{i}", use_container_width=True):
                go_to(i)
                st.rerun()

st.markdown("---")

# ============================================================
# STEP 1 : 파일 올리기
# ============================================================

if st.session_state.step == 1:
    st.markdown("### ① 설문 결과 데이터 입력하기")
    st.write(
        "구글폼 응답이 저장된 **구글 시트**를 열고, 머리글(문항)을 포함해서 표 전체를 "
        "드래그한 뒤 복사(Ctrl+C 또는 ⌘+C)하세요. 그다음 아래 칸에 붙여넣고(Ctrl+V) "
        "**데이터 입력** 버튼을 눌러주세요."
    )

    with st.form("paste_form"):
        pasted_text = st.text_area(
            "여기에 붙여넣기",
            height=220,
            placeholder="타임스탬프\t하루 평균 스마트폰 사용 시간은?\t...\n2026. 7. 10 오전 9:03:11\t2~3시간\t...",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("데이터 입력", type="primary", use_container_width=True)

    if submitted:
        df, error = parse_pasted_data(pasted_text)

        if df is None:
            st.error(error)
        else:
            first_col = df.columns[0]
            if is_timestamp_column(df[first_col], first_col):
                question_df = df.drop(columns=[first_col])
                dropped_msgs = [f"타임스탬프로 보이는 '{first_col}' 열은 제외했어요."]
            else:
                question_df = df
                dropped_msgs = []

            question_df, dropped_private_columns = remove_private_identifier_columns(question_df)
            if dropped_private_columns:
                dropped_msgs.append(
                    f"개인정보로 보이는 열 {', '.join(map(str, dropped_private_columns))}는 제외했어요."
                )

            if question_df.shape[1] == 0:
                st.error("문항으로 쓸 수 있는 열이 없어요. 머리글을 포함해서 다시 복사해주세요.")
            else:
                st.session_state.df = question_df
                st.session_state.question_col = question_df.columns[0]
                st.success(
                    f"입력 완료! **{question_df.shape[1]}개 문항**, "
                    f"**{question_df.shape[0]}명**의 응답을 확인했어요."
                    + (" " + " ".join(dropped_msgs) if dropped_msgs else "")
                )
                st.dataframe(question_df.head(5), use_container_width=True)

    with st.expander("CSV 파일로 가지고 있다면 (선택)"):
        st.write("스프레드시트 대신 CSV 파일이 있다면 이걸로 올려도 돼요.")
        uploaded_file = st.file_uploader("CSV 파일 선택", type=["csv"])
        if uploaded_file is not None:
            df, error = read_csv_robust(uploaded_file)
            if df is None:
                st.error("파일을 읽는 데 문제가 생겼어요. CSV 파일이 맞는지 확인해주세요.")
                st.caption(f"오류 내용: {error}")
            else:
                first_col = df.columns[0]
                if is_timestamp_column(df[first_col], first_col):
                    question_df = df.drop(columns=[first_col])
                else:
                    question_df = df

                question_df, dropped_private_columns = remove_private_identifier_columns(question_df)
                if question_df.shape[1] == 0:
                    st.error("문항으로 쓸 수 있는 열이 없어요.")
                else:
                    st.session_state.df = question_df
                    st.session_state.question_col = question_df.columns[0]
                    if dropped_private_columns:
                        st.success(
                            f"업로드 완료! {question_df.shape[1]}개 문항, "
                            f"{question_df.shape[0]}명의 응답을 확인했어요. "
                            f"개인정보로 보이는 열 {', '.join(map(str, dropped_private_columns))}는 제외했어요."
                        )
                    else:
                        st.success(
                            f"업로드 완료! {question_df.shape[1]}개 문항, "
                            f"{question_df.shape[0]}명의 응답을 확인했어요."
                        )
                    st.dataframe(question_df.head(5), use_container_width=True)

        st.markdown("---")
        st.caption("CSV 형식이 헷갈린다면 예시 파일을 참고하세요.")
        with open("sample_data/sample_survey.csv", "rb") as f:
            st.download_button(
                "예시 CSV 내려받기",
                data=f,
                file_name="sample_survey.csv",
                mime="text/csv",
            )

    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("샘플 데이터 입력해보기", use_container_width=True):
            load_sample_dataframe()
    with c2:
        disabled = st.session_state.df is None
        if st.button("다음 단계 →", type="primary", disabled=disabled, use_container_width=True):
            next_step()
            st.rerun()

# ============================================================
# STEP 2 : 문항 고르기
# ============================================================

elif st.session_state.step == 2:
    st.markdown("### ② 그래프로 만들 문항 고르기")
    st.write("보고서에서 근거로 쓰고 싶은 문항을 하나 골라주세요.")

    df = st.session_state.df

    if df is None:
        st.warning("먼저 ① 단계에서 파일을 올려주세요.")
    else:
        question_col = st.radio(
            "문항 목록",
            options=list(df.columns),
            index=0
            if st.session_state.question_col is None
            else list(df.columns).index(st.session_state.question_col),
            label_visibility="collapsed",
        )
        st.session_state.question_col = question_col

        col_type = classify_column(df[question_col])
        st.session_state.question_col_type = col_type

        st.markdown(f'<span class="badge">{TYPE_LABELS[col_type]}</span>', unsafe_allow_html=True)

        labels, values, note = get_chart_data(df[question_col], col_type)
        if note:
            st.info(note)

        st.markdown("**응답 미리 보기**")
        preview = pd.DataFrame({"응답": labels, "응답 수": values})
        st.dataframe(preview, use_container_width=True)

        if len(labels) == 0:
            st.warning("이 문항에는 그래프로 만들 데이터가 없어요. 다른 문항을 선택해주세요.")

    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("← 이전 단계"):
            prev_step()
            st.rerun()
    with c2:
        next_disabled = df is None or len(labels) == 0 if df is not None else True
        if st.button("다음 단계 →", type="primary", disabled=next_disabled):
            next_step()
            st.rerun()

# ============================================================
# STEP 3 : 그래프 비교 (탭)
# ============================================================

elif st.session_state.step == 3:
    st.markdown("### ③ 세 가지 그래프 비교하기")
    st.write("같은 데이터를 세 가지 방식으로 그려봤어요. 탭을 눌러 비교해보세요.")

    df = st.session_state.df
    question_col = st.session_state.question_col
    col_type = st.session_state.get("question_col_type")

    if df is None or question_col is None:
        st.warning("① , ② 단계를 먼저 완료해주세요.")
    else:
        labels, values, note = get_chart_data(df[question_col], col_type)
        if note:
            st.caption(note)

        tab_mpl, tab_sns, tab_plotly = st.tabs(["matplotlib", "seaborn", "plotly"])

        with tab_mpl:
            fig_mpl, ax = plt.subplots(figsize=(7, 4.3))
            ax.bar(labels, values, color=INK, edgecolor=INK)
            ax.set_title(question_col, fontsize=12)
            ax.set_ylabel("응답 수")
            plt.xticks(rotation=20, ha="right")
            fig_mpl.tight_layout()
            st.pyplot(fig_mpl)
            st.session_state["fig_mpl"] = fig_mpl

        with tab_sns:
            fig_sns, ax2 = plt.subplots(figsize=(7, 4.3))
            sns.barplot(x=labels, y=values, ax=ax2, color=TEAL)
            ax2.set_title(question_col, fontsize=12)
            ax2.set_ylabel("응답 수")
            plt.xticks(rotation=20, ha="right")
            fig_sns.tight_layout()
            st.pyplot(fig_sns)
            st.session_state["fig_sns"] = fig_sns

        with tab_plotly:
            fig_plotly = px.bar(
                x=labels,
                y=values,
                labels={"x": question_col, "y": "응답 수"},
                title=question_col,
                color_discrete_sequence=[CORAL],
            )
            fig_plotly.update_layout(
                plot_bgcolor=PAPER_CARD,
                paper_bgcolor=PAPER_CARD,
                font=dict(family=KOREAN_FONT_NAME or "sans-serif"),
            )
            st.plotly_chart(fig_plotly, use_container_width=True)
            st.session_state["fig_plotly"] = fig_plotly

        st.write("")
        st.markdown("**다운로드할 스타일을 골라주세요**")
        st.session_state.final_style = st.radio(
            "최종 스타일",
            options=["matplotlib", "seaborn", "plotly"],
            index=["matplotlib", "seaborn", "plotly"].index(st.session_state.final_style),
            horizontal=True,
            label_visibility="collapsed",
        )

    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("← 이전 단계"):
            prev_step()
            st.rerun()
    with c2:
        if st.button("다음 단계 →", type="primary"):
            next_step()
            st.rerun()

# ============================================================
# STEP 4 : 다운로드
# ============================================================

elif st.session_state.step == 4:
    st.markdown("### ④ 그래프 저장하기")

    style = st.session_state.final_style
    question_col = st.session_state.question_col

    if style == "matplotlib" and "fig_mpl" in st.session_state:
        st.pyplot(st.session_state["fig_mpl"])
    elif style == "seaborn" and "fig_sns" in st.session_state:
        st.pyplot(st.session_state["fig_sns"])
    elif style == "plotly" and "fig_plotly" in st.session_state:
        st.plotly_chart(st.session_state["fig_plotly"], use_container_width=True)
    else:
        st.warning("③ 단계에서 그래프를 먼저 만들어주세요.")

    st.write("")
    reason = st.text_area(
        "이 그래프는 보고서의 어떤 문장을 뒷받침하나요? (선택)",
        placeholder="예: 우리 반 학생 중 60%가 하루 2시간 이상 스마트폰을 사용한다는 근거로 사용",
        height=80,
    )

    file_format = st.radio("파일 형식", ["PNG", "JPG"], horizontal=True)

    col_dl1, col_dl2 = st.columns(2)

    if style in ("matplotlib", "seaborn"):
        fig = st.session_state.get("fig_mpl" if style == "matplotlib" else "fig_sns")
        if fig is not None:
            buf = io.BytesIO()
            fmt = "png" if file_format == "PNG" else "jpg"
            fig.savefig(buf, format=fmt, dpi=200, bbox_inches="tight")
            buf.seek(0)
            with col_dl1:
                st.download_button(
                    f"{file_format} 파일 다운로드",
                    data=buf,
                    file_name=f"{question_col}_{style}.{fmt}",
                    mime=f"image/{fmt}",
                    type="primary",
                    use_container_width=True,
                )
    elif style == "plotly":
        fig = st.session_state.get("fig_plotly")
        if fig is not None:
            fmt = "png" if file_format == "PNG" else "jpg"
            img_bytes = fig.to_image(format=fmt, scale=2)
            with col_dl1:
                st.download_button(
                    f"{file_format} 파일 다운로드",
                    data=img_bytes,
                    file_name=f"{question_col}_{style}.{fmt}",
                    mime=f"image/{fmt}",
                    type="primary",
                    use_container_width=True,
                )

    with col_dl2:
        if st.button("← 이전 단계로 돌아가 다른 문항 그래프 만들기"):
            go_to(2)
            st.rerun()

    st.write("")
    if st.button("처음부터 새로 하기"):
        for key in [
            "df", "question_col", "question_col_type", "final_style",
            "fig_mpl", "fig_sns", "fig_plotly",
        ]:
            st.session_state.pop(key, None)
        st.session_state.step = 1
        st.session_state.max_step_reached = 1
        st.rerun()
