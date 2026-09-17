import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="연도별 인구 현황 대시보드",
    page_icon="📊",
    layout="wide"
)

# 데이터 불러오기 및 전처리
@st.cache_data
def load_data():
    df = pd.read_csv('pop_data.csv')
    num_cols = [c for c in df.columns if c != '연도']
    for col in num_cols:
        if df[col].dtype == object:
            df[col] = df[col].str.replace(',', '').astype(int)
    return df, num_cols

df, num_cols = load_data()

st.title("📊 연도별 연령대 인구 구조 변화 대시보드")
st.caption("그래프 위로 마우스를 이동하면 가장 가까운 연도로 연한 세로 실선이 자동으로 고정(스냅)되어 해당 연도의 전체 데이터가 표시됩니다.")

st.markdown("---")

# 상단 인터랙션 컨트롤
cols_top = st.columns([3, 1])
with cols_top[0]:
    selected_categories = st.multiselect(
        "표시할 인구 항목 선택",
        options=num_cols,
        default=num_cols
    )

with cols_top[1]:
    all_years = sorted(df['연도'].unique())
    default_year = all_years[-1]

if not selected_categories:
    st.warning("최소 하나의 항목을 선택해주세요.")
    selected_categories = num_cols

# Plotly 그래프 생성
fig = go.Figure()

colors = {
    '0-19세 (유소년/청소년)': '#3b82f6',
    '20-39세 (청년층)': '#10b981',
    '40-59세 (중장년층)': '#f59e0b',
    '60세 이상 (고령층)': '#ef4444',
    '총인구': '#6b7280'
}

for col in selected_categories:
    color = colors.get(col, None)
    fig.add_trace(go.Scatter(
        x=df['연도'],
        y=df[col],
        mode='lines+markers',
        name=col,
        line=dict(width=3, color=color),
        marker=dict(size=8),
        hovertemplate='%{y:,.0f} 만 명'
    ))

# X축 / Y축 설정
fig.update_layout(
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor="rgba(255, 255, 255, 0.95)",
        font_size=13,
        font_family="Pretendard, Malgun Gothic, sans-serif"
    ),
    xaxis=dict(
        title="연도",
        tickmode='linear',
        dtick=1,
        showspikes=True,         # 세로 가이드선 활성화
        spikemode='across',       # 그래프 전체 세로 축 가로지름
        spikesnap='data',         # 마우스 위치에서 가장 가까운 데이터(연도) 축에 정확히 스냅/고정
        spikedash='solid',        # 실선형 세로선
        spikecolor='rgba(210, 210, 210, 0.5)', # 아주 연하고 희미한 실선 색상
        spikethickness=1.5,
        gridcolor='rgba(240, 240, 240, 0.8)'
    ),
    yaxis=dict(
        title="인구 수 (만 명)",
        gridcolor='rgba(240, 240, 240, 0.8)',
        tickformat=','
    ),
    height=480,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

# Streamlit Plotly 차트 출력
chart_event = st.plotly_chart(
    fig, 
    use_container_width=True, 
    on_select="rerun", 
    selection_mode="points"
)

# 클릭된 연도 추출
clicked_year = None
if chart_event and "selection" in chart_event and chart_event["selection"]["points"]:
    clicked_point = chart_event["selection"]["points"][0]
    clicked_year = clicked_point.get("x")

# 슬라이더로 연도 지정
st.markdown("### 📅 선택 연도 상세 데이터")

selected_year = st.select_slider(
    "조회할 연도를 선택하세요 (그래프의 포인트를 클릭해도 자동 선택됩니다)",
    options=all_years,
    value=clicked_year if clicked_year in all_years else default_year
)

# 선택된 연도 데이터 추출
row_curr = df[df['연도'] == selected_year].iloc[0]

# 이전 연도 데이터 (전년 대비 변화율 계산용)
prev_year = selected_year - 1
row_prev = df[df['연도'] == prev_year].iloc[0] if prev_year in df['연도'].values else None

st.markdown(f"#### 📌 **{selected_year}년** 주요 인구 지표 요약 (단위: 만 명)")

# 주요 지표 메트릭 카드 배치
cols = st.columns(len(num_cols))

for idx, col in enumerate(num_cols):
    val_curr = row_curr[col]
    
    if row_prev is not None:
        val_prev = row_prev[col]
        diff = val_curr - val_prev
        diff_pct = (diff / val_prev) * 100
        delta_str = f"{diff:+,d} 만 명 ({diff_pct:+.1f}%)"
    else:
        delta_str = "기준 연도"

    with cols[idx]:
        st.metric(
            label=col,
            value=f"{val_curr:,} 만 명",
            delta=delta_str
        )

st.markdown("---")

# 하단 정보 정렬: 인구 구성 비중 및 표
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown(f"##### 🍩 {selected_year}년 연령대별 인구 구성비")
    age_cols = [c for c in num_cols if c != '총인구']
    pie_data = pd.DataFrame({
        '연령대': age_cols,
        '인구수': [row_curr[c] for c in age_cols]
    })
    
    fig_pie = px.pie(
        pie_data, 
        values='인구수', 
        names='연령대',
        color='연령대',
        color_discrete_map=colors,
        hole=0.4
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.markdown(f"##### 📋 {selected_year}년 상세 세부 데이터표")
    total_pop = row_curr['총인구'] if '총인구' in row_curr else sum([row_curr[c] for c in age_cols])
    
    details = []
    for c in age_cols:
        pop = row_curr[c]
        share = (pop / total_pop) * 100
        details.append({
            '연령대 그룹': c,
            '인구 수': f"{pop:,} 만 명",
            '전체 대비 비중': f"{share:.1f}%"
        })
    
    if '총인구' in num_cols:
        details.append({
            '연령대 그룹': '총인구',
            '인구 수': f"{row_curr['총인구']:,} 만 명",
            '전체 대비 비중': '100.0%'
        })

    df_details = pd.DataFrame(details)
    st.dataframe(df_details, hide_index=True, use_container_width=True)