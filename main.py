"""영화 데이터 그래프 도감 1 - 시간

KOBIS 일별 박스오피스(1년치, 일별 10위권) 데이터를 시간 흐름으로 살펴보는 앱.
그래프는 섹션 단위로 계속 추가해 나간다.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"


@st.cache_data
def load_data() -> pd.DataFrame:
    """CSV를 읽어 날짜 열을 진짜 날짜(datetime)로 바꾼 데이터프레임을 돌려준다."""
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")
    df["날짜"] = pd.to_datetime(df["날짜"].astype(str), format="%Y%m%d")
    return df.sort_values(["날짜", "순위"]).reset_index(drop=True)


def insight(text: str) -> None:
    """그래프 아래에 넣는 '이 그래프로 알 수 있는 것' 한 문장."""
    st.info(f"**이 그래프로 알 수 있는 것** · {text}")


st.set_page_config(page_title="영화 데이터 그래프 도감 1 - 시간", layout="wide")
st.title("영화 데이터 그래프 도감 1 - 시간")

df = load_data()

with st.expander("데이터 살펴보기", expanded=False):
    st.write(
        f"기간: {df['날짜'].min():%Y-%m-%d} ~ {df['날짜'].max():%Y-%m-%d} "
        f"({df['날짜'].nunique()}일) · 행 {len(df):,}개 · 영화 {df['영화명'].nunique():,}편"
    )
    st.dataframe(df.head(20), use_container_width=True)


# ─────────────────────────────────────────────────────────────
# 그래프 1. 영화 한 편의 날짜별 일관객 변화
# ─────────────────────────────────────────────────────────────
st.header("1. 영화 한 편의 일관객 변화")

movies = sorted(df["영화명"].dropna().unique())
selected = st.selectbox("영화를 고르세요", movies)

one = df[df["영화명"] == selected].sort_values("날짜")

fig1 = px.line(
    one,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"{selected} · 날짜별 일관객",
    labels={"날짜": "날짜", "일관객": "일별 관객 수(명)"},
)
fig1.update_traces(
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>관객수: %{y:,}명<extra></extra>"
)
fig1.update_layout(hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

insight(
    f"'{selected}'의 관객이 언제 가장 많았고, 개봉 이후 어떤 속도로 줄어드는지 알 수 있다."
)


# ─────────────────────────────────────────────────────────────
# 그래프 2. (추가 예정)
# ─────────────────────────────────────────────────────────────
st.header("2. (다음 그래프 자리)")
st.caption("여기에 다음 그래프를 추가한다.")
# insight("...")
