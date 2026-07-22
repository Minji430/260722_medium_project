"""
1페이지 : 메인 페이지
웹페이지 소개 + 사용 방법 안내.
디자인 컨셉: 원고지 / 보고서 / 형광펜 강조 (2페이지와 동일한 톤)
"""

import streamlit as st

st.set_page_config(
    page_title="보고서 근거 만들기",
    page_icon="📄",
    layout="centered",
)

PAPER = "#EFEDE6"
PAPER_CARD = "#FAF9F5"
INK = "#24303D"
INK_SOFT = "#57636E"
HIGHLIGHT = "#FFD400"
TEAL = "#3C6E71"
LINE = "#D8D4C8"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {PAPER};
        font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
        color: {INK};
    }}

    h1, h2, h3 {{
        font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.01em;
        color: {INK} !important;
    }}

    .hl {{
        background: linear-gradient(to bottom, transparent 55%, {HIGHLIGHT} 55%);
        padding: 0 2px;
    }}

    .eyebrow {{
        font-family: 'Consolas', 'D2Coding', monospace;
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {TEAL};
        margin-bottom: 4px;
    }}

    .card {{
        background: {PAPER_CARD};
        border: 1px solid {LINE};
        border-radius: 4px;
        padding: 20px 22px;
        height: 100%;
    }}

    .card h4 {{
        font-family: 'Noto Sans KR', sans-serif;
        font-weight: 700;
        margin: 4px 0 8px;
        font-size: 1.05rem;
        color: {INK};
    }}

    .card p {{
        color: {INK_SOFT};
        font-size: 0.92rem;
        margin: 0;
    }}

    .ms-step {{
        display: flex;
        gap: 18px;
        align-items: flex-start;
        padding: 18px 0;
        border-bottom: 1px solid {LINE};
    }}
    .ms-step:first-child {{ border-top: 1px solid {LINE}; }}
    .ms-step__num {{
        font-family: 'Consolas', 'D2Coding', monospace;
        font-size: 0.8rem;
        color: {INK_SOFT};
        border: 1px solid {LINE};
        border-radius: 4px;
        padding: 3px 8px;
        flex-shrink: 0;
        margin-top: 2px;
    }}
    .ms-step h5 {{
        font-family: 'Noto Sans KR', sans-serif;
        font-weight: 700;
        margin: 0 0 4px;
        font-size: 1rem;
        color: {INK};
    }}
    .ms-step p {{
        margin: 0;
        color: {INK_SOFT};
        font-size: 0.9rem;
    }}

    div.stButton > button, div.stPageLink > a {{
        border: 1.5px solid {INK} !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 히어로
# ============================================================

st.markdown('<p class="eyebrow">국어 · 보고서 쓰기</p>', unsafe_allow_html=True)
st.markdown(
    "# 우리 반 설문 결과,<br>"
    "<span class='hl'>눈에 보이는 근거</span>로 바꿔보세요",
    unsafe_allow_html=True,
)
st.write(
    "구글 시트에 정리된 설문 조사 결과를 붙여넣으면, 보고서에 넣을 수 있는 그래프로 "
    "만들어 드려요. 세 가지 방식으로 그려본 뒤, 내 주장에 가장 잘 어울리는 그래프를 "
    "골라 다운로드하세요."
)

st.write("")
st.page_link(
    "pages/1_그래프로 변환하기.py",
    label="설문 결과 올리러 가기 →",
    icon="📊",
)

st.write("")
st.write("")

# ============================================================
# 무엇을 다루는지
# ============================================================

st.markdown('<p class="eyebrow">지금 버전에서 다루는 것</p>', unsafe_allow_html=True)
st.markdown(
    "### 구글 시트로 만든 <span class='hl'>조사 결과</span>를 다룹니다",
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        """
        <div class="card">
        <p class="eyebrow" style="margin-bottom:2px;">STEP 1</p>
        <h4>데이터 입력</h4>
        <p>구글 시트에서 설문 응답을 복사해서 붙여넣어요. 따로 손볼 필요 없어요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="card">
        <p class="eyebrow" style="margin-bottom:2px;">STEP 2 · 3</p>
        <h4>문항 선택 · 그래프 비교</h4>
        <p>그래프로 만들 문항을 고르고, matplotlib · plotly · seaborn 세 가지를 비교해요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """
        <div class="card">
        <p class="eyebrow" style="margin-bottom:2px;">STEP 4</p>
        <h4>파일로 저장</h4>
        <p>마음에 드는 그래프를 PNG·JPG로 내려받아 보고서에 바로 붙여넣어요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.caption(
    "※ 이번 버전은 설문(조사) 데이터를 대상으로 해요. "
    "관찰·실험 기록을 다루는 기능은 다음 버전에서 다룰 예정이에요."
)

st.write("")
st.write("")

# ============================================================
# 사용 방법
# ============================================================

st.markdown('<p class="eyebrow">사용 방법</p>', unsafe_allow_html=True)
st.markdown("### 네 칸이면 충분해요", unsafe_allow_html=True)

steps = [
    ("01", "설문 결과 데이터 입력하기", "구글 시트에서 응답 표 전체를 복사해서 붙여넣으세요."),
    ("02", "그래프로 만들 문항 고르기", "보고서 주장을 뒷받침할 문항을 하나 골라요."),
    ("03", "세 가지 그래프 비교하기", "matplotlib · plotly · seaborn 탭을 눌러가며 비교해보세요."),
    ("04", "다운로드하기", "고른 그래프를 PNG나 JPG로 저장해 보고서에 붙여넣어요."),
]

steps_html = "".join(
    f"""
    <div class="ms-step">
        <span class="ms-step__num">{num}</span>
        <div>
            <h5>{title}</h5>
            <p>{desc}</p>
        </div>
    </div>
    """
    for num, title, desc in steps
)
st.markdown(steps_html, unsafe_allow_html=True)

st.write("")
st.page_link(
    "pages/1_그래프로 변환하기.py",
    label="지금 시작하기 →",
    icon="📊",
)

st.write("")
st.caption("보고서 근거 만들기 · 국어과 보고서 쓰기 수업 도구")
