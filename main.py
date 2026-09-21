"""영화 데이터 그래프 도감 1 - 시간

KOBIS 일별 박스오피스(1년치, 일별 10위권) 자료를 '시간'의 눈으로 들여다보는 앱입니다.
그래프는 구역(섹션)별로 하나씩 계속 늘려 갑니다.

화면은 흰 바탕 위에서 색 덩어리가 천천히 떠다니고, 그 위에 반투명 유리판을 얹는
방식입니다. 장식은 구분선 가운데의 고딕 사엽 문양 하나로만 둡니다.
"""

import html
import pandas as pd
import plotly.express as px
import streamlit as st

# ────────────────────────────────────────────────────────────────
# 1. 기본 설정값
# ────────────────────────────────────────────────────────────────

# 1년치 일별 박스오피스 10위권 기록이 담긴 CSV 주소입니다.
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

# 이 화면이 쓰는 색 — 청록에서 보라를 거쳐 분홍으로, 마지막에 황동색으로 이어집니다.
# 여러 영화를 한 그래프에 겹쳐 그릴 때 이 순서대로 색을 나눠 줍니다.
PALETTE = ["#3fa9c9", "#7a86d4", "#b07bd0", "#d9739f", "#c9a04a"]

st.set_page_config(page_title="영화 데이터 그래프 도감 1 - 시간", layout="wide")


# ────────────────────────────────────────────────────────────────
# 2. 고딕 장식 — 사엽 문양(quatrefoil)은 반원 잎 네 개가 모인 고딕 건축의 장식입니다.
#    맑고 투명한 느낌을 해치지 않도록 색을 채우지 않고 가는 선으로만 그립니다.
# ────────────────────────────────────────────────────────────────


def build_quatrefoil_svg(color: str, stroke: float = 1.1, opacity: float = 0.75) -> str:
    """사엽 문양을 SVG 문자열로 그립니다."""
    lobe = 11.0  # 안쪽 정사각형의 반변이자 잎의 반지름
    size = lobe * 4 + stroke * 2
    center = size / 2
    path = (
        f"M{center - lobe:.1f} {center - lobe:.1f}"
        f"A{lobe:.1f} {lobe:.1f} 0 0 1 {center + lobe:.1f} {center - lobe:.1f}"
        f"A{lobe:.1f} {lobe:.1f} 0 0 1 {center + lobe:.1f} {center + lobe:.1f}"
        f"A{lobe:.1f} {lobe:.1f} 0 0 1 {center - lobe:.1f} {center + lobe:.1f}"
        f"A{lobe:.1f} {lobe:.1f} 0 0 1 {center - lobe:.1f} {center - lobe:.1f}Z"
    )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size:.0f}' height='{size:.0f}'"
        f" viewBox='0 0 {size:.1f} {size:.1f}'>"
        f"<path d='{path}' fill='none' stroke='{color}' stroke-width='{stroke}'"
        f" stroke-opacity='{opacity}'/></svg>"
    )


def _css_url(svg: str) -> str:
    """SVG 문자열을 CSS에서 배경 그림으로 쓸 수 있는 형태로 감쌉니다."""
    return f'url("data:image/svg+xml;utf8,{svg}")'


# 글꼴을 먼저 불러오고(@import는 스타일시트 맨 앞에 와야 합니다), 문양을 CSS 변수로
# 한 번만 등록해둔 뒤 아래 스타일에서 가져다 씁니다.
st.markdown(
    "<style>"
    "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');"
    f":root{{--quatrefoil:{_css_url(build_quatrefoil_svg('%236fc7dd'))};"
    f"--quatrefoil-brass:{_css_url(build_quatrefoil_svg('%23d9b877', 1.3, 0.95))};"
    "--font:'Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic',system-ui,sans-serif;}"
    "</style>",
    unsafe_allow_html=True,
)


# ────────────────────────────────────────────────────────────────
# 3. 디자인(CSS)
# ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* 배경은 순백을 기본으로 하고, 색이 있는 빛 번짐은 별도의 층(::after)에서
           천천히 움직이게 만들어 화면이 완전히 정지해 보이지 않도록 합니다.
           이 빛 번짐이 있어야 위에 얹은 유리판들이 '무언가를 비치게' 됩니다. */
        html, body, [data-testid="stAppViewContainer"] {
            background: #fdfeff;
            color: #20242b;
        }
        html, body, [data-testid="stAppViewContainer"], .block-container {
            font-family: var(--font);
            -webkit-font-smoothing: antialiased;
        }
        [data-testid="stHeader"] { background: transparent; }
        .block-container { padding-top: 3.2rem; padding-bottom: 4rem; max-width: 1180px; }

        /* 크게 번진 색 덩어리들이 천천히 떠다니는 배경 층 */
        [data-testid="stAppViewContainer"]::after {
            content: "";
            position: fixed;
            inset: -18%;
            pointer-events: none;
            z-index: 0;
            filter: blur(22px);
            background:
                radial-gradient(38% 42% at 10% 8%, rgba(158, 211, 238, 0.42) 0%, transparent 70%),
                radial-gradient(30% 34% at 88% 4%, rgba(245, 220, 178, 0.55) 0%, transparent 72%),
                radial-gradient(36% 42% at 74% 40%, rgba(178, 215, 238, 0.3) 0%, transparent 72%),
                radial-gradient(42% 38% at 18% 70%, rgba(196, 222, 240, 0.32) 0%, transparent 70%),
                radial-gradient(34% 30% at 58% 88%, rgba(230, 221, 240, 0.3) 0%, transparent 72%);
            animation: driftGlow 26s ease-in-out infinite alternate;
        }
        /* 화면 전체에 아주 옅은 종이 질감(노이즈)을 얹어, 색면이 평평해 보이지 않게 합니다. */
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            opacity: 0.045;
            mix-blend-mode: multiply;
            background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
        }
        [data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }

        @keyframes driftGlow {
            0%   { transform: translate(0, 0) scale(1); }
            100% { transform: translate(-2.5%, 2%) scale(1.04); }
        }
        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .fade-in { animation: fadeSlideUp 0.6s ease both; }

        /* 스크롤에 따른 애니메이션 — 아래로 스크롤해서 요소가 화면에 들어올 때
           서서히 떠오르며 나타납니다. 이 기능을 지원하지 않는 브라우저에서는
           페이지가 열리자마자 한 번 나타나는 것으로 자연스럽게 대체됩니다. */
        @keyframes revealUp {
            from { opacity: 0; transform: translateY(26px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .scroll-reveal {
            opacity: 0;
            transform: translateY(26px);
            animation: revealUp 0.6s ease forwards;
            animation-delay: 0.05s;
        }
        @supports (animation-timeline: view()) {
            .scroll-reveal {
                animation: revealUp linear both;
                animation-timeline: view();
                animation-range: entry 0% cover 40%;
            }
        }

        /* 글씨는 유리 느낌에 맞춰 가늘고 넓게. 큰 제목일수록 굵기를 낮추고 자간을
           벌려서, 두껍게 눌러쓴 느낌 대신 가볍고 트인 인상을 줍니다. */
        h1, h2, h3, h4, p, span, div, label { letter-spacing: 0.01em; }

        .app-title {
            font-size: 2.45rem;
            font-weight: 500;
            letter-spacing: 0.005em;
            color: #16202c;
            margin-bottom: 0.3rem;
        }
        .app-subtitle {
            color: #6a7481;
            font-size: 0.86rem;
            font-weight: 300;
            letter-spacing: 0.04em;
            margin-bottom: 1.8rem;
        }

        /* 구분선 — 가운데 표식은 고딕의 사엽 문양으로 둡니다. 황동색은 제목 바로 아래
           첫 구분선 하나에만 쓰고, 나머지는 같은 문양을 하늘색으로 씁니다. */
        .crack-divider {
            position: relative;
            height: 1px;
            margin: 1.4rem 0 2.0rem 0;
            background: linear-gradient(90deg, transparent 0%, #7ad3e370 22%, #a99ae6b0 48%, #e9a3ceb0 68%, transparent 100%);
        }
        .crack-divider::after {
            content: "";
            position: absolute;
            top: -13px;
            left: 50%;
            width: 26px;
            height: 26px;
            transform: translateX(-50%);
            /* 문양 뒤에 부드러운 흰 빛을 깔아, 구분선이 문양을 관통하지 않게 합니다. */
            background:
                var(--quatrefoil) center / 15px 15px no-repeat,
                radial-gradient(closest-side, rgba(253, 254, 255, 0.97) 52%, rgba(253, 254, 255, 0) 100%);
        }
        .crack-divider.hero::after {
            background-image:
                var(--quatrefoil-brass),
                radial-gradient(closest-side, rgba(253, 254, 255, 0.97) 52%, rgba(253, 254, 255, 0) 100%);
        }

        .section-label {
            color: #7b86c4;
            font-size: 0.72rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.22em;
            margin-bottom: 1rem;
        }
        /* 구역 번호 — 제목 왼쪽에 붙는 작은 표식입니다. */
        .section-no {
            display: inline-block;
            min-width: 1.4rem;
            margin-right: 0.55rem;
            padding: 0.05rem 0.4rem;
            font-size: 0.66rem;
            color: #8a6423;
            background: rgba(251, 240, 220, 0.7);
            border: 1px solid rgba(217, 184, 119, 0.7);
            border-radius: 999px;
            letter-spacing: 0.08em;
        }
        .section-heading {
            color: #16202c;
            font-size: 1.4rem;
            font-weight: 500;
            letter-spacing: 0;
            margin-bottom: 0.4rem;
        }
        /* 그래프를 어떻게 보면 되는지 알려주는 한 줄 안내입니다. */
        .section-hint {
            color: #78828f;
            font-size: 0.78rem;
            font-weight: 300;
            letter-spacing: 0.03em;
            margin-bottom: 1.1rem;
        }

        /* 영화 고르는 칸도 유리판으로 맞춥니다. */
        [data-testid="stSelectbox"] label {
            color: #7b86c4 !important;
            font-size: 0.68rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.18em;
        }
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background: linear-gradient(155deg, rgba(255, 255, 255, 0.66) 0%, rgba(238, 240, 252, 0.46) 100%) !important;
            -webkit-backdrop-filter: blur(14px) saturate(125%);
            backdrop-filter: blur(14px) saturate(125%);
            border: 2px solid rgba(255, 255, 255, 0.92) !important;
            border-radius: 0 !important;
            color: #16202c;
            font-family: var(--font);
            letter-spacing: 0.02em;
            box-shadow:
                0 0 0 1px rgba(163, 168, 224, 0.32),
                0 6px 18px rgba(31, 61, 82, 0.07),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
        }

        /* ── 그래프판 ─────────────────────────────────────────────
           플롯리 그래프 자체는 배경을 투명하게 비워 두고, 그 아래에 유리판을 깔아
           그래프가 판 위에 얹힌 것처럼 보이게 합니다. 판의 높이는 그래프 높이에
           맞춰 파이썬 쪽에서 넣어 줍니다. */
        .chart-glass {
            position: relative;
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.58) 0%, rgba(238, 240, 252, 0.4) 100%);
            -webkit-backdrop-filter: blur(14px) saturate(125%);
            backdrop-filter: blur(14px) saturate(125%);
            border: 1px solid rgba(255, 255, 255, 0.85);
            box-shadow:
                0 0 0 1px rgba(163, 168, 224, 0.16),
                0 8px 26px rgba(31, 61, 82, 0.07),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
            /* 오른쪽 아래 모서리를 비스듬히 잘라, 반듯한 네모를 피합니다. */
            clip-path: polygon(0 0, 100% 0, 100% 94%, 97% 100%, 0 100%);
        }
        [data-testid="stPlotlyChart"] { position: relative; z-index: 1; }

        /* 해설 상자 — 유리판이되 왼쪽에 보라색 띠를 둘러 눈에 먼저 들어오게 하고,
           오른쪽 위 모서리는 비스듬히 잘랐습니다. */
        .guide-box {
            position: relative;
            padding: 1.3rem 1.4rem;
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.6) 0%, rgba(236, 238, 251, 0.45) 100%);
            -webkit-backdrop-filter: blur(14px) saturate(125%);
            backdrop-filter: blur(14px) saturate(125%);
            border: 1px solid rgba(255, 255, 255, 0.85);
            border-left: 3px solid rgba(169, 154, 230, 0.85);
            box-shadow:
                0 0 0 1px rgba(163, 168, 224, 0.16),
                0 8px 26px rgba(31, 61, 82, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
            clip-path: polygon(0 0, 96% 0, 100% 14%, 100% 100%, 0 100%);
            color: #24303a;
            line-height: 1.65;
            font-weight: 300;
        }
        .guide-title {
            color: #6f7cc0;
            font-weight: 700;
            margin-bottom: 0.5rem;
            font-size: 1.0rem;
        }

        /* 아직 그래프가 들어오지 않은 구역 — 같은 유리판이되 테두리를 점선으로 두어
           '비어 있는 자리'임을 알립니다. */
        .slot-empty {
            padding: 2.2rem 1.4rem;
            text-align: center;
            color: #8994a1;
            font-size: 0.82rem;
            font-weight: 300;
            letter-spacing: 0.06em;
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.42) 0%, rgba(238, 240, 252, 0.28) 100%);
            -webkit-backdrop-filter: blur(10px) saturate(120%);
            backdrop-filter: blur(10px) saturate(120%);
            border: 1px dashed rgba(163, 168, 224, 0.5);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ────────────────────────────────────────────────────────────────
# 4. 화면을 그리는 작은 도구들
# ────────────────────────────────────────────────────────────────


def section_header(number: int, title: str, label: str, hint: str = "") -> None:
    """구역 머리말 — 영문 라벨, 번호가 붙은 제목, (있으면) 한 줄 안내."""
    st.markdown(f'<div class="section-label scroll-reveal">{html.escape(label)}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-heading scroll-reveal">'
        f'<span class="section-no">{number:02d}</span>{html.escape(title)}</div>',
        unsafe_allow_html=True,
    )
    if hint:
        st.markdown(f'<div class="section-hint scroll-reveal">{html.escape(hint)}</div>', unsafe_allow_html=True)


def insight(text: str) -> None:
    """그래프 아래에 붙는 '이 그래프로 알 수 있는 것' 한 문장."""
    st.markdown(
        f'<div class="guide-box scroll-reveal">'
        f'<div class="guide-title">이 그래프로 알 수 있는 것</div>{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def divider(hero: bool = False) -> None:
    """가운데에 고딕 사엽 문양이 놓인 구분선."""
    css_class = "crack-divider hero fade-in" if hero else "crack-divider scroll-reveal"
    st.markdown(f'<div class="{css_class}"></div>', unsafe_allow_html=True)


def style_figure(fig, height: int, show_legend: bool, legend_top: int):
    """플롯리 그래프를 이 화면의 톤에 맞춥니다. 배경은 투명하게 비워 아래에 깔린
    유리판이 그대로 비치게 하고, 눈금선·글꼴·마우스 쪽지 색만 손봅니다."""
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=28, t=legend_top, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Noto Sans KR, sans-serif", size=12, color="#4a5560"),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="rgba(163,168,224,0.5)",
            font=dict(family="Noto Sans KR, sans-serif", size=12, color="#26303c"),
        ),
        showlegend=show_legend,
        # 범례는 그래프 위쪽에 가로로 눕혀 둡니다. 항목을 누르면 그 영화의 선이
        # 켜지고 꺼지며, 두 번 누르면 그 영화만 남습니다(플롯리 기본 동작).
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title_text="",
            font=dict(size=11, color="#4a5560"),
            bgcolor="rgba(0,0,0,0)",
            itemclick="toggle",
            itemdoubleclick="toggleothers",
        ),
    )
    axis_style = dict(
        gridcolor="rgba(140, 146, 196, 0.16)",
        zeroline=False,
        linecolor="rgba(140, 146, 196, 0.3)",
        tickfont=dict(size=11, color="#8994a1"),
        title=None,
    )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)
    return fig


def show_chart(fig, height: int = 420, show_legend: bool = False, legend_top: int = 28) -> None:
    """유리판을 먼저 깔고 그 위에 그래프를 얹습니다.
    (판은 음수 여백으로 바로 뒤의 그래프를 자기 위로 끌어올립니다.)"""
    st.markdown(
        f'<div class="chart-glass scroll-reveal" style="height:{height}px;margin-bottom:-{height}px"></div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        style_figure(fig, height, show_legend, legend_top),
        use_container_width=True,
        config={"displayModeBar": False},
    )


# ────────────────────────────────────────────────────────────────
# 5. 데이터 불러오기 — 한 번 받아온 자료는 캐시에 두고 다시 씁니다.
# ────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """CSV를 읽어 날짜 열을 진짜 날짜(datetime)로 바꾼 표를 돌려줍니다."""
    # 파일 맨 앞에 눈에 보이지 않는 표시(BOM)가 있어 utf-8-sig로 읽습니다.
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")
    # 20250901처럼 하이픈 없는 여덟 자리 숫자를 날짜로 바꿉니다.
    df["날짜"] = pd.to_datetime(df["날짜"].astype(str), format="%Y%m%d")
    return df.sort_values(["날짜", "순위"]).reset_index(drop=True)


with st.spinner("박스오피스 기록을 불러오는 중입니다..."):
    df = load_data()


# ────────────────────────────────────────────────────────────────
# 6. 화면 상단 — 제목
# ────────────────────────────────────────────────────────────────
st.markdown('<div class="app-title fade-in">영화 데이터 그래프 도감 1 · 시간</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle fade-in" style="animation-delay:0.06s">'
    f"일별 박스오피스 10위권 기록 · {df['날짜'].min():%Y년 %m월 %d일} ~ {df['날짜'].max():%Y년 %m월 %d일}"
    f" · {df['날짜'].nunique():,}일 · 영화 {df['영화명'].nunique():,}편</div>",
    unsafe_allow_html=True,
)

divider(hero=True)


# ────────────────────────────────────────────────────────────────
# 7. 구역 1 — 영화 한 편의 날짜별 일관객 변화
# ────────────────────────────────────────────────────────────────
section_header(
    1,
    "영화 한 편의 일관객 변화",
    "Daily audience",
    "영화를 고르면 그 영화가 10위권에 있던 날들의 일관객을 선으로 잇습니다. 선 위에 마우스를 올리면 날짜와 관객수가 보입니다.",
)

picker_col, _ = st.columns([1.3, 2])
with picker_col:
    movies = sorted(df["영화명"].dropna().unique())
    # 처음 화면에서는 10위권에 가장 오래 머문 영화를 보여 줍니다.
    # (하루만 기록된 영화가 먼저 뽑히면 선 그래프가 점 하나로 보이기 때문입니다.)
    default_movie = df["영화명"].value_counts().idxmax()
    selected = st.selectbox("영화 고르기", movies, index=movies.index(default_movie))

one = df[df["영화명"] == selected].sort_values("날짜")

fig1 = px.line(one, x="날짜", y="일관객", markers=True)
fig1.update_traces(
    line=dict(color="#7a86d4", width=2.4, shape="spline", smoothing=0.6),
    marker=dict(size=5, color="#3fa9c9", line=dict(width=1, color="rgba(255,255,255,0.9)")),
    fill="tozeroy",
    fillcolor="rgba(122, 134, 212, 0.10)",
    hovertemplate="관객수: %{y:,}명<extra></extra>",
)
# 날짜는 쪽지 머리말에 한국어로 적고, 눈금도 날짜 형식으로 고정합니다.
# (기록이 하루뿐인 영화에서 눈금이 시:분:초로 쪼개지는 것을 막아 줍니다.)
fig1.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y년 %m월 %d일")
# 세로 제목은 한글이 눕혀져 읽기 어려우므로 두지 않고, 눈금에 단위를 붙입니다.
fig1.update_yaxes(tickformat=",", ticksuffix="명")

show_chart(fig1)

insight(
    f"'{selected}'의 관객이 어느 날 가장 많았고(=개봉 직후인지 주말인지), "
    "그 뒤로 어떤 속도로 줄어드는지를 한눈에 볼 수 있습니다."
)

divider()


# ────────────────────────────────────────────────────────────────
# 8. 구역 2 — 기간 일관객 합계 상위 5편을 한 그래프에 겹쳐 보기
#    영화마다 색을 달리하고, 범례를 눌러 선을 켜고 끌 수 있습니다.
# ────────────────────────────────────────────────────────────────
section_header(
    2,
    "흥행 상위 5편의 일관객 흐름",
    "Top 5 over time",
    "범례를 한 번 누르면 그 영화를 껐다 켤 수 있고, 두 번 누르면 그 영화만 남습니다.",
)

# 이 기간 동안 일관객을 모두 더해, 합계가 가장 큰 다섯 편을 고릅니다.
total_by_movie = df.groupby("영화명")["일관객"].sum().sort_values(ascending=False)
top5_names = list(total_by_movie.head(5).index)
top5 = df[df["영화명"].isin(top5_names)].sort_values(["영화명", "날짜"])

fig2 = px.line(
    top5,
    x="날짜",
    y="일관객",
    color="영화명",
    color_discrete_sequence=PALETTE,
    # 합계가 큰 순서대로 색과 범례 차례를 맞춥니다.
    category_orders={"영화명": top5_names},
)
fig2.update_traces(
    line=dict(width=2.1, shape="spline", smoothing=0.5),
    # 통합 쪽지에서는 줄마다 영화 이름을 직접 적어 줍니다.
    # (이름을 빼면 색 점만 남아 어느 영화인지 알 수 없습니다.)
    hovertemplate="%{fullData.name} · %{y:,}명<extra></extra>",
)
fig2.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y년 %m월 %d일")
fig2.update_yaxes(tickformat=",", ticksuffix="명")

# 범례가 그래프 위에 한 줄 더 들어가므로, 판과 그래프를 조금 더 높게 잡습니다.
show_chart(fig2, height=470, show_legend=True, legend_top=78)

insight(
    "가장 많은 관객을 모은 다섯 편이 각각 언제 정점을 찍었는지, "
    "그리고 흥행 시기가 서로 겹쳤는지 엇갈렸는지를 비교할 수 있습니다."
)

divider()


# ────────────────────────────────────────────────────────────────
# 9. 구역 3 — (다음 그래프 자리)
#    새 그래프를 넣을 때는 위 구역을 그대로 본떠서 이어 붙이면 됩니다.
#      section_header(3, "제목", "English label", "한 줄 안내")
#      fig = px.line(...)  →  show_chart(fig)  →  insight("한 문장")
# ────────────────────────────────────────────────────────────────
section_header(3, "다음 그래프 자리", "Coming next")
st.markdown(
    '<div class="slot-empty scroll-reveal">이 자리에 다음 그래프가 들어옵니다</div>',
    unsafe_allow_html=True,
)
# insight("이 그래프로 알 수 있는 것을 여기에 한 문장으로 적습니다.")
