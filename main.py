"""영화 데이터 그래프 도감 1 - 시간

KOBIS 일별 박스오피스(1년치, 일별 10위권) 자료를 '시간'의 눈으로 들여다보는 앱입니다.
그래프는 구역(섹션)별로 하나씩 계속 늘려 갑니다.

화면 디자인은 '영화 박스오피스' 앱과 같은 결을 씁니다.
 - 흰 바탕 위에서 색 덩어리가 천천히 떠다니고, 그 위에 반투명 유리판을 얹습니다.
 - 유리판에는 코드로 직접 그린 대리석 결과 어긋난 네모 조각(글리치)이 옅게 깔립니다.
 - 구분선 가운데에는 고딕 건축의 사엽 문양을 둡니다.
"""

import html
import math
import random

import pandas as pd
import plotly.express as px
import streamlit as st

# ────────────────────────────────────────────────────────────────
# 1. 기본 설정값
# ────────────────────────────────────────────────────────────────

# 1년치 일별 박스오피스 10위권 기록이 담긴 CSV 주소입니다.
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

st.set_page_config(page_title="영화 데이터 그래프 도감 1 - 시간", layout="wide")


# ────────────────────────────────────────────────────────────────
# 2. 무늬 만들기 — 같은 간격으로 반복되는 무늬는 아무리 옅게 깔아도 '자로 잰 듯한'
#    느낌이 납니다. 그래서 대리석 결처럼, 굵기·간격·길이가 제각각인 선을 코드로
#    직접 그려서 씁니다. 난수를 쓰지만 씨앗(seed)을 고정했기 때문에 새로고침해도
#    항상 똑같은 모양이 나옵니다.
# ────────────────────────────────────────────────────────────────


def _smooth_path(points: list[tuple[float, float]]) -> str:
    """점들을 부드럽게 이어주는 곡선(SVG path) 문자열로 바꿉니다."""
    path = f"M{points[0][0]:.1f} {points[0][1]:.1f}"
    for i in range(len(points) - 1):
        prev_pt = points[i - 1] if i > 0 else points[0]
        cur_pt, next_pt = points[i], points[i + 1]
        after_pt = points[i + 2] if i + 2 < len(points) else points[-1]
        c1 = (cur_pt[0] + (next_pt[0] - prev_pt[0]) / 6, cur_pt[1] + (next_pt[1] - prev_pt[1]) / 6)
        c2 = (next_pt[0] - (after_pt[0] - cur_pt[0]) / 6, next_pt[1] - (after_pt[1] - cur_pt[1]) / 6)
        path += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {next_pt[0]:.1f} {next_pt[1]:.1f}"
    return path


def _wander(rng, start, end, segments, amplitude, drift):
    """시작점에서 끝점까지, 옆으로 조금씩 흔들리며 흘러가는 점들을 만듭니다."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length  # 진행 방향에 수직인 방향
    points, offset = [], 0.0
    for i in range(segments + 1):
        t = i / segments
        taper = (4 * t * (1 - t)) ** 0.6  # 양 끝으로 갈수록 흔들림이 잦아듭니다.
        offset = max(-amplitude, min(amplitude, offset + rng.uniform(-drift, drift)))
        wobble = offset * taper + rng.uniform(-amplitude * 0.12, amplitude * 0.12)
        points.append((start[0] + dx * t + nx * wobble, start[1] + dy * t + ny * wobble))
    return points


def build_vein_svg() -> str:
    """대리석 결 — 길게 흐르는 주 맥 몇 가닥과, 거기에 붙지 않은 짧은 실금들."""
    rng = random.Random(20260917)
    width, height = 600, 380
    parts = []

    # 서로 나란하지 않도록 각도를 크게 다르게 둔 주 맥 세 가닥.
    for start, end, stroke in (
        ((-40, 300), (660, 60), 1.5),
        ((-30, 120), (640, 330), 1.1),
        ((120, -30), (430, 410), 0.9),
    ):
        parts.append((_smooth_path(_wander(rng, start, end, 9, 58, 26)), stroke, 0.14))
        # 주 맥 옆에 잔 맥을 붙이되, 시작·끝을 어긋내어 평행선이 되지 않게 합니다.
        for _ in range(rng.randint(1, 3)):
            head = rng.uniform(0.05, 0.4)
            tail = rng.uniform(0.55, 0.95)
            branch_start = (
                start[0] + (end[0] - start[0]) * head + rng.uniform(-40, 40),
                start[1] + (end[1] - start[1]) * head + rng.uniform(-40, 40),
            )
            branch_end = (
                start[0] + (end[0] - start[0]) * tail + rng.uniform(-70, 70),
                start[1] + (end[1] - start[1]) * tail + rng.uniform(-70, 70),
            )
            parts.append(
                (
                    _smooth_path(_wander(rng, branch_start, branch_end, 7, 34, 18)),
                    rng.uniform(0.4, 0.8),
                    rng.uniform(0.05, 0.1),
                )
            )

    # 아무 데도 닿지 않는 짧은 실금 — 화면이 고르게 덮이지 않도록 한쪽으로 몰아둡니다.
    for _ in range(5):
        head = (rng.uniform(-20, 420), rng.uniform(-20, 400))
        tail = (head[0] + rng.uniform(80, 260), head[1] + rng.uniform(-150, 150))
        parts.append(
            (_smooth_path(_wander(rng, head, tail, 6, 26, 14)), rng.uniform(0.35, 0.6), rng.uniform(0.04, 0.08))
        )

    # 결마다 청록·보라·분홍을 돌려 써서, 빛이 갈라진 것처럼 보이게 합니다.
    hues = ("%2358bcd6", "%238f86d8", "%23d283bd")
    body = "".join(
        f"<path d='{d}' fill='none' stroke='{hues[i % len(hues)]}' stroke-width='{w:.2f}'"
        f" stroke-opacity='{o:.3f}' stroke-linecap='round'/>"
        for i, (d, w, o) in enumerate(parts)
    )
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>{body}</svg>"


# ── 고딕 장식 ──────────────────────────────────────────────────────
# 뾰족한 아치와 사엽 문양은 고딕 건축의 대표적인 형태입니다. 지금의 맑고 투명한
# 느낌을 해치지 않도록, 색을 채우지 않고 가는 선으로만 그려서 아주 옅게 깝니다.


def build_quatrefoil_svg(color: str, stroke: float = 1.1, opacity: float = 0.75) -> str:
    """사엽 문양(quatrefoil) — 반원 잎 네 개가 모인 고딕 장식."""
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


# ── 글리치 ────────────────────────────────────────────────────────
# 아주 드문드문 어긋난 네모 조각을 섞어, 판이 매끈하기만 하지 않도록 합니다.


def build_glitch_svg() -> str:
    """어긋난 네모 조각 — 청록과 분홍을 살짝 비껴 겹쳐 색이 번진 것처럼 보이게 합니다."""
    rng = random.Random(404)
    width, height = 600, 380
    parts = []
    for _ in range(14):
        x, y = rng.uniform(-20, width), rng.uniform(-10, height)
        w, h = rng.uniform(10, 74), rng.uniform(1.5, 7)
        offset = rng.uniform(1.5, 4)
        parts.append(
            f"<rect x='{x:.0f}' y='{y:.0f}' width='{w:.0f}' height='{h:.1f}'"
            f" fill='%2360d6ea' fill-opacity='{rng.uniform(0.05, 0.13):.2f}'/>"
            f"<rect x='{x + offset:.0f}' y='{y + offset * 0.5:.0f}' width='{w:.0f}' height='{h:.1f}'"
            f" fill='%23ef8fd0' fill-opacity='{rng.uniform(0.04, 0.11):.2f}'/>"
        )
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>{''.join(parts)}</svg>"


def _css_url(svg: str) -> str:
    """SVG 문자열을 CSS에서 배경 그림으로 쓸 수 있는 형태로 감쌉니다."""
    return f'url("data:image/svg+xml;utf8,{svg}")'


# 글꼴을 먼저 불러오고(@import는 스타일시트 맨 앞에 와야 합니다), 만든 결을
# CSS 변수로 한 번만 등록해둔 뒤 아래 스타일에서 가져다 씁니다.
st.markdown(
    "<style>"
    "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');"
    f":root{{--vein:{_css_url(build_vein_svg())};"
    f"--glitch:{_css_url(build_glitch_svg())};"
    f"--quatrefoil:{_css_url(build_quatrefoil_svg('%236fc7dd'))};"
    f"--quatrefoil-brass:{_css_url(build_quatrefoil_svg('%23d9b877', 1.3, 0.95))};"
    "--font:'Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic',system-ui,sans-serif;}"
    "</style>",
    unsafe_allow_html=True,
)


# ────────────────────────────────────────────────────────────────
# 3. 디자인(CSS) — 흔한 사각형 카드 대신, 모서리가 잘려 있거나 결이 비치는
#    비대칭 유리판을 씁니다. 배경과 판이 또렷이 분리되지 않도록 은은한 색으로만
#    구분합니다.
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
        html, body, [data-testid="stAppViewContainer"], .block-container, .peek-table {
            font-family: var(--font);
            -webkit-font-smoothing: antialiased;
        }
        [data-testid="stHeader"] { background: transparent; }
        .block-container { padding-top: 3.2rem; padding-bottom: 4rem; max-width: 1180px; }

        /* 크게 번진 색 덩어리들이 천천히 떠다니는 배경 층 — 유리판 뒤에서 흐릿하게
           비쳐 보이는 것이 이 층입니다. */
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
           서서히 떠오르며 나타납니다. 이 기능(scroll-driven animation)을 지원하지
           않는 브라우저에서는 페이지가 열리자마자 한 번 나타나는 것으로 자연스럽게
           대체됩니다. */
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

        /* 구분선은 하늘색 하나만 씁니다. */
        .crack-divider {
            position: relative;
            height: 1px;
            margin: 1.4rem 0 2.0rem 0;
            background: linear-gradient(90deg, transparent 0%, #7ad3e370 22%, #a99ae6b0 48%, #e9a3ceb0 68%, transparent 100%);
        }
        /* 구분선 가운데 표식은 고딕의 사엽 문양으로 둡니다. 황동색은 제목 바로 아래
           첫 구분선 하나에만 쓰고, 나머지는 같은 문양을 하늘색으로 씁니다. */
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
            margin-bottom: 1.1rem;
        }

        /* 영화 고르는 칸도 카드와 같은 유리판으로 맞춥니다. */
        [data-testid="stSelectbox"] label,
        [data-testid="stExpander"] summary p {
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

        /* 지표 카드 — 반투명 유리판처럼 보이도록 배경을 살짝만 채우고, 뒤에 깔린
           색을 흐리게 비쳐 보이게(backdrop-filter) 만들었습니다. 대리석 결은 한 장을
           카드마다 다른 위치에서 잘라 쓰되, 배율은 비슷하게 맞춰 카드별로 결의
           밀도가 들쭉날쭉하지 않게 했습니다. */
        /* 카드가 커질 자리를 미리 잡아 두는 빈 칸입니다. 마우스를 올려 카드가 자라도
           아래 내용이 밀려 내려가지 않습니다. */
        .kpi-slot { min-height: 178px; }
        .kpi-card {
            position: relative;
            min-height: 118px;
            padding: 1.3rem 1.3rem 1.1rem 1.3rem;
            /* 결 위에 어긋난 네모 조각(글리치)을 아주 드문드문 얹습니다. */
            background-image: var(--glitch), var(--vein), linear-gradient(155deg, rgba(255, 255, 255, 0.62) 0%, rgba(238, 240, 252, 0.42) 100%);
            background-repeat: no-repeat, no-repeat, no-repeat;
            -webkit-backdrop-filter: blur(14px) saturate(125%);
            backdrop-filter: blur(14px) saturate(125%);
            border: 2px solid rgba(255, 255, 255, 0.92);
            box-shadow:
                0 0 0 1px rgba(163, 168, 224, 0.32),
                0 8px 26px rgba(31, 61, 82, 0.09),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
            overflow: hidden;
            transition:
                transform 0.25s ease,
                box-shadow 0.25s ease,
                min-height 0.3s ease,
                padding 0.3s ease;
        }
        /* 마우스가 올라간 카드 한 장만 커집니다. */
        .kpi-card:hover {
            transform: translateY(-3px);
            min-height: 168px;
            padding: 1.7rem 1.5rem 1.4rem 1.5rem;
            box-shadow:
                0 0 0 1px rgba(163, 168, 224, 0.45),
                0 16px 34px rgba(31, 61, 82, 0.13),
                inset 0 1px 0 rgba(255, 255, 255, 0.95);
        }
        .kpi-card:hover .kpi-value { font-size: 2.6rem; }
        /* 마우스를 올리면 유리 위로 빛이 한 번 스칩니다. */
        .kpi-card::after {
            content: "";
            position: absolute;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            background: linear-gradient(115deg, transparent 36%, rgba(255, 255, 255, 0.5) 50%, transparent 64%);
            transform: translateX(-130%);
            transition: transform 0.75s cubic-bezier(0.2, 0.7, 0.3, 1);
        }
        .kpi-card:hover::after { transform: translateX(130%); }
        /* 평소에는 숨어 있다가, 마우스를 올리면 이 숫자가 무엇인지 알려줍니다. */
        .kpi-hint {
            position: relative;
            z-index: 1;
            margin-top: 0.6rem;
            font-size: 0.7rem;
            font-weight: 300;
            letter-spacing: 0.02em;
            color: #7b8794;
            opacity: 0;
            transform: translateY(4px);
            transition: opacity 0.25s ease, transform 0.25s ease;
        }
        .kpi-card:hover .kpi-hint { opacity: 1; transform: translateY(0); }
        .kpi-card.card-hero {
            clip-path: polygon(0 0, 100% 0, 100% 100%, 6% 100%, 0 90%);
            background-size: 150% 190%, 205% 250%, auto;
            background-position: 18% 30%, 12% 88%, 0 0;
        }
        .kpi-card.card-2 {
            clip-path: polygon(0 9%, 90% 0, 100% 0, 100% 100%, 0 100%);
            background-size: 175% 210%, 195% 265%, auto;
            background-position: 74% 72%, 68% 6%, 0 0;
        }
        /* 3번 카드는 결이 한 점으로 모이는 부분을 피해, 선들이 서로 떨어져 흐르는
           구간을 오른쪽에서 잘라 씁니다. */
        .kpi-card.card-3 {
            clip-path: polygon(0 0, 100% 0, 100% 82%, 90% 100%, 0 100%);
            background-size: 160% 200%, 230% 210%, auto;
            background-position: 36% 84%, 88% 16%, 0 0;
        }
        .kpi-label, .kpi-value, .kpi-unit { position: relative; z-index: 1; }
        .kpi-label {
            color: #6a7481;
            font-size: 0.7rem;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            margin-bottom: 0.7rem;
        }
        .kpi-value {
            color: #16202c;
            font-size: 2rem;
            font-weight: 500;
            letter-spacing: -0.01em;
            font-variant-numeric: tabular-nums;
            transition: font-size 0.3s ease;
        }
        .kpi-unit {
            font-size: 0.85rem;
            color: #78828f;
            font-weight: 300;
            margin-left: 0.35rem;
            letter-spacing: 0.02em;
        }

        .movie-headline {
            display: inline-block;
            color: #16202c;
            font-size: 1.5rem;
            font-weight: 600;
            letter-spacing: 0em;
            margin-bottom: 0.2rem;
            margin-right: 0.6rem;
        }
        /* 화면에서 황동색이 등장하는 두 지점 중 하나 — 영화 이름 옆의 작은 표식입니다. */
        .rank-badge {
            display: inline-block;
            padding: 0.16rem 0.62rem;
            font-size: 0.66rem;
            font-weight: 500;
            letter-spacing: 0.12em;
            color: #8a6423;
            background: rgba(251, 240, 220, 0.75);
            border: 1px solid rgba(217, 184, 119, 0.75);
            border-radius: 999px;
            vertical-align: middle;
        }
        .movie-meta {
            color: #78828f;
            font-size: 0.78rem;
            font-weight: 300;
            letter-spacing: 0.04em;
            margin-bottom: 1.3rem;
        }

        /* ── 그래프판 ─────────────────────────────────────────────
           플롯리 그래프 자체는 배경을 투명하게 비워 두고, 그 아래에 카드와 같은
           유리판을 깔아 그래프가 판 위에 얹힌 것처럼 보이게 합니다. */
        .chart-glass {
            position: relative;
            margin-bottom: -420px;  /* 바로 아래에 오는 그래프를 이 판 위로 끌어올립니다. */
            height: 420px;
            background-image: var(--vein), linear-gradient(160deg, rgba(255, 255, 255, 0.58) 0%, rgba(238, 240, 252, 0.4) 100%);
            background-repeat: no-repeat, no-repeat;
            background-size: 210% 240%, auto;
            background-position: 62% 24%, 0 0;
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

        /* 안내·해설 상자 — 카드와 같은 유리판이되, 왼쪽에 보라색 띠를 둘러
           눈에 먼저 들어오게 합니다. 오른쪽 위 모서리는 비스듬히 잘랐습니다. */
        .guide-box {
            position: relative;
            padding: 1.3rem 1.4rem;
            /* 카드와 같은 대리석 결을, 또 다른 위치에서 잘라 깔았습니다. */
            background-image: var(--vein), linear-gradient(160deg, rgba(255, 255, 255, 0.6) 0%, rgba(236, 238, 251, 0.45) 100%);
            background-repeat: no-repeat, no-repeat;
            background-size: 200% 260%, auto;
            background-position: 82% 62%, 0 0;
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

        /* 원자료 미리보기 표 — 캔버스로 그려지는 기본 표 대신 직접 만든 표를 써서,
           배경/글자색이 항상 이 화면의 밝은 톤을 그대로 따르도록 했습니다. */
        .peek-wrap {
            position: relative;
            overflow-x: auto;
            padding: 0.6rem 0.9rem 0.3rem 0.9rem;
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.58) 0%, rgba(238, 240, 252, 0.38) 100%);
            -webkit-backdrop-filter: blur(14px) saturate(125%);
            backdrop-filter: blur(14px) saturate(125%);
            border: 1px solid rgba(255, 255, 255, 0.85);
            box-shadow:
                0 0 0 1px rgba(163, 168, 224, 0.16),
                0 8px 26px rgba(31, 61, 82, 0.07),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
            clip-path: polygon(0 0, 100% 0, 100% 96%, 97% 100%, 0 100%);
        }
        .peek-table { position: relative; z-index: 1; width: 100%; border-collapse: collapse; font-size: 0.86rem; }
        /* 칸과 칸 사이에도 아주 연한 세로선을 하나씩 — 그래프의 눈금선과 같은 결로,
           숫자를 읽을 때 열이 눈으로 구분되게 해줍니다. */
        .peek-table th + th,
        .peek-table td + td { border-left: 1px solid rgba(150, 154, 200, 0.12); }
        .peek-table thead th {
            text-align: left;
            color: #667380;
            font-size: 0.67rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-weight: 500;
            padding: 0.55rem 0.95rem 0.75rem 0.95rem;
            border-bottom: 1px solid rgba(150, 150, 210, 0.26);
        }
        .peek-table thead th.num { text-align: right; }
        .peek-table tbody td {
            padding: 0.72rem 0.95rem;
            color: #26303c;
            font-weight: 300;
            border-bottom: 1px solid rgba(150, 154, 200, 0.13);
            transition: color 0.2s ease;
        }
        .peek-table tbody tr:last-child td { border-bottom: none; }
        .peek-table tbody td.num { text-align: right; font-variant-numeric: tabular-nums; }
        .peek-table tbody tr { transition: background-color 0.2s ease; }
        .peek-table tbody tr:hover { background-color: rgba(255, 255, 255, 0.62); }
        .peek-table tbody tr:hover td { color: #16202c; }
        /* 마우스를 올린 줄의 왼쪽에 가는 띠가 위아래로 펴집니다. */
        .peek-table tbody td:first-child { position: relative; }
        .peek-table tbody td:first-child::before {
            content: "";
            position: absolute;
            left: 0;
            top: 5px;
            bottom: 5px;
            width: 2px;
            background: linear-gradient(180deg, #7ad3e3 0%, #a99ae6 55%, #e9a3ce 100%);
            transform: scaleY(0);
            transition: transform 0.2s ease;
        }
        .peek-table tbody tr:hover td:first-child::before { transform: scaleY(1); }

        /* 접었다 펴는 칸(expander)도 유리판으로 맞춥니다. */
        [data-testid="stExpander"] details {
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.5) 0%, rgba(238, 240, 252, 0.32) 100%);
            -webkit-backdrop-filter: blur(12px) saturate(120%);
            backdrop-filter: blur(12px) saturate(120%);
            border: 1px solid rgba(255, 255, 255, 0.85) !important;
            border-radius: 0 !important;
            box-shadow: 0 0 0 1px rgba(163, 168, 224, 0.16);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ────────────────────────────────────────────────────────────────
# 4. 화면을 그리는 작은 도구들
# ────────────────────────────────────────────────────────────────
# 이 화면이 쓰는 세 가지 색 — 청록에서 보라를 거쳐 분홍으로 이어집니다.
ACCENT_CYAN = "#58bcd6"
ACCENT_VIOLET = "#8f86d8"
ACCENT_PINK = "#d283bd"


def section_header(number: int, title: str, label: str) -> None:
    """구역 머리말 — 작은 영문 라벨과 번호가 붙은 제목을 함께 그립니다."""
    st.markdown(f'<div class="section-label scroll-reveal">{html.escape(label)}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-heading scroll-reveal">'
        f'<span class="section-no">{number:02d}</span>{html.escape(title)}</div>',
        unsafe_allow_html=True,
    )


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


def kpi_cards(specs: list[tuple[str, int, str, str]]) -> None:
    """지표 카드 세 장. 너비를 일부러 다르게 두어(1.3 : 1 : 1) 똑같은 네모가
    반복되는 느낌을 없애고, 왼쪽 카드가 '대표 카드'가 되도록 했습니다."""
    columns = st.columns([1.3, 1, 1])
    for col, card_class, (label, value, unit, hint) in zip(columns, ("card-hero", "card-2", "card-3"), specs):
        with col:
            # (문자열을 한 줄로 이어 붙여야 합니다 — 빈 줄이 섞이면 스트림릿의 마크다운
            # 파서가 이어지는 내용을 코드 블록으로 오인해 HTML 태그가 그대로 보입니다.)
            st.markdown(
                f'<div class="kpi-slot scroll-reveal">'
                f'<div class="kpi-card {card_class}">'
                f'<div class="kpi-label">{html.escape(label)}</div>'
                f'<div class="kpi-value">{value:,}<span class="kpi-unit">{html.escape(unit)}</span></div>'
                f'<div class="kpi-hint">{html.escape(hint)}</div>'
                f"</div></div>",
                unsafe_allow_html=True,
            )


def style_figure(fig):
    """플롯리 그래프를 이 화면의 톤에 맞춥니다. 배경은 투명하게 비워 아래에 깔린
    유리판이 그대로 비치게 하고, 눈금선·글꼴·마우스 쪽지 색만 손봅니다."""
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=28, t=28, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Noto Sans KR, sans-serif", size=12, color="#4a5560"),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="rgba(163,168,224,0.5)",
            font=dict(family="Noto Sans KR, sans-serif", size=12, color="#26303c"),
        ),
        showlegend=False,
    )
    axis_style = dict(
        gridcolor="rgba(140, 146, 196, 0.16)",
        zeroline=False,
        linecolor="rgba(140, 146, 196, 0.3)",
        tickfont=dict(size=11, color="#8994a1"),
        title_font=dict(size=11, color="#7b86c4"),
    )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)
    return fig


def show_chart(fig) -> None:
    """유리판을 먼저 깔고 그 위에 그래프를 얹습니다."""
    st.markdown('<div class="chart-glass scroll-reveal"></div>', unsafe_allow_html=True)
    st.plotly_chart(style_figure(fig), use_container_width=True, config={"displayModeBar": False})


def peek_table_html(table_df: pd.DataFrame) -> str:
    """미리보기 표를 직접 스타일을 입힌 HTML 표로 바꿉니다."""
    numeric_columns = {"순위", "일관객", "누적관객", "스크린수", "상영횟수"}
    header = "".join(
        f'<th class="{"num" if col in numeric_columns else ""}">{html.escape(str(col))}</th>'
        for col in table_df.columns
    )
    body = []
    for row in table_df.itertuples(index=False):
        cells = []
        for col, value in zip(table_df.columns, row):
            if col in numeric_columns:
                cells.append(f'<td class="num">{value:,}</td>')
            else:
                cells.append(f"<td>{html.escape(str(value))}</td>")
        body.append(f"<tr>{''.join(cells)}</tr>")
    return (
        '<div class="peek-wrap"><table class="peek-table">'
        f"<thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
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
section_header(1, "영화 한 편의 일관객 변화", "Daily audience")

picker_col, _ = st.columns([1.3, 2])
with picker_col:
    movies = sorted(df["영화명"].dropna().unique())
    # 처음 화면에서는 10위권에 가장 오래 머문 영화를 보여 줍니다.
    # (하루만 기록된 영화가 먼저 뽑히면 선 그래프가 점 하나로 보이기 때문입니다.)
    default_movie = df["영화명"].value_counts().idxmax()
    selected = st.selectbox("영화 고르기", movies, index=movies.index(default_movie))

one = df[df["영화명"] == selected].sort_values("날짜")

# 고른 영화의 이름과 기간을 카드 위에 먼저 적어 둡니다.
best_day = one.loc[one["일관객"].idxmax()]
st.markdown(
    f'<div class="scroll-reveal" style="margin-top:1.2rem">'
    f'<span class="movie-headline">{html.escape(selected)}</span>'
    f'<span class="rank-badge">최고 {int(one["순위"].min())}위</span></div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="movie-meta scroll-reveal">'
    f'10위권 기록 · {one["날짜"].min():%Y-%m-%d} ~ {one["날짜"].max():%Y-%m-%d}</div>',
    unsafe_allow_html=True,
)

kpi_cards(
    [
        ("최다 일관객", int(one["일관객"].max()), "명", f"가장 많았던 날은 {best_day['날짜']:%Y년 %m월 %d일}입니다"),
        ("누적 관객", int(one["누적관객"].max()), "명", "이 기간에 기록된 누적 관객의 최댓값"),
        ("10위권에 머문 날", int(one["날짜"].nunique()), "일", "이 영화가 일별 10위 안에 든 날의 수"),
    ]
)

# 날짜별 일관객 변화를 선으로 잇습니다. 마우스를 올리면 그날의 날짜와 관객수가 보입니다.
fig1 = px.line(
    one,
    x="날짜",
    y="일관객",
    markers=True,
)
fig1.update_traces(
    line=dict(color=ACCENT_VIOLET, width=2.4, shape="spline", smoothing=0.6),
    marker=dict(size=5, color=ACCENT_CYAN, line=dict(width=1, color="rgba(255,255,255,0.9)")),
    fill="tozeroy",
    fillcolor="rgba(143, 134, 216, 0.10)",
    hovertemplate="관객수: %{y:,}명<extra></extra>",
)
# 날짜는 쪽지 머리말에 한국어로 적고, 눈금도 날짜 형식으로 고정합니다.
# (기록이 하루뿐인 영화에서 눈금이 시:분:초로 쪼개지는 것을 막아 줍니다.)
fig1.update_xaxes(tickformat="%Y-%m-%d", hoverformat="%Y년 %m월 %d일", title=None)
# 세로 제목은 한글이 눕혀져 읽기 어려우므로 두지 않고, 눈금에 단위를 붙입니다.
fig1.update_yaxes(tickformat=",", ticksuffix="명", title=None)
show_chart(fig1)

insight(
    f"'{selected}'의 관객이 어느 날 가장 많았고(=개봉 직후인지 주말인지), "
    "그 뒤로 어떤 속도로 줄어드는지를 한눈에 볼 수 있습니다."
)

with st.expander("이 영화의 원자료 보기"):
    st.markdown(peek_table_html(one.assign(날짜=one["날짜"].dt.strftime("%Y-%m-%d"))), unsafe_allow_html=True)

divider()


# ────────────────────────────────────────────────────────────────
# 8. 구역 2 — (다음 그래프 자리)
#    새 그래프를 넣을 때는 이 구역을 그대로 본떠서 아래에 이어 붙이면 됩니다.
#      section_header(2, "제목", "English label")
#      fig = px.line(...)  →  show_chart(fig)  →  insight("한 문장")
# ────────────────────────────────────────────────────────────────
section_header(2, "다음 그래프 자리", "Coming next")
st.markdown(
    '<div class="slot-empty scroll-reveal">이 자리에 다음 그래프가 들어옵니다</div>',
    unsafe_allow_html=True,
)
# insight("이 그래프로 알 수 있는 것을 여기에 한 문장으로 적습니다.")
