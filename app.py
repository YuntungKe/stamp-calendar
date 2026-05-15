import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from streamlit_gsheets import GSheetsConnection

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="SW Calendar", layout="wide")
st.title("📅 蘇菲吳的專屬日曆")

# --- 倒數計時器 ---
target_date = datetime(2026, 7, 23).date()
today = datetime.now().date()
days_left = (target_date - today).days

# 顯示倒數計時 (使用 big font 樣式)
st.markdown(f"""
    <div style="background-color: #d9ead3; padding: 20px; border-radius: 10px; border-left: 5px solid #6aa84f; margin-bottom: 25px;">
        <span style="font-size: 1.2rem; color: #262730;">距離 2026/07/23 目標日還有</span>
        <br>
        <span style="font-size: 3rem; font-weight: bold; color: #6aa84f;">{days_left}</span> 
        <span style="font-size: 1.5rem; color: #262730;">天</span>
    </div>
""", unsafe_allow_html=True)

# 取得系統時間
today = (datetime.now()).date()

# --- 月份切換邏輯 ---
month_options = [(2026, 5), (2026, 6), (2026, 7)] # 初始化月份索引

# 預設選中當前月份 (如果在範圍內)
if 'month_idx' not in st.session_state:
    current_idx = 0
    for i, (y, m) in enumerate(month_options):
        if y == today.year and m == today.month:
            current_idx = i
    st.session_state.month_idx = current_idx

# 建立左右切換按鈕
col_prev, col_m, col_next = st.columns([1, 3, 1])

with col_prev:
    if st.button("⬅ 上月") and st.session_state.month_idx > 0:
        st.session_state.month_idx -= 1
        st.rerun()

with col_next:
    if st.button("下月 ⮕") and st.session_state.month_idx < len(month_options) - 1:
        st.session_state.month_idx += 1
        st.rerun()

# 取得目前要顯示的年月份
view_year, view_month = month_options[st.session_state.month_idx]

with col_m:
    st.markdown(f"<h2 style='text-align: center;'>{view_year} 年 {view_month} 月</h2>", unsafe_allow_html=True)

# --- CSS 樣式修正 (格線與對齊) ---
st.markdown("""
    <style>
    [data-testid="column"] {
        min-height: 180px !important;
        border: 1px solid #333333;
        padding: 10px !important;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    .stButton > button {
        width: 100% !important;
        padding: 3px 5px !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB_ Google試算表 ---
SQL_SHEET_URL = "https://docs.google.com/spreadsheets/d/1pOls5JZZcEr7-HryojAHG5ZXB0I--1rJEfPUTbo0CLo/edit?usp=sharing"

# --- Google Sheets 連線與資料讀寫 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_all_data():
    try:
        df = conn.read(ttl=0)
        if not df.empty:
            df['Date'] = df['Date'].astype(str) # 強制將 Date 轉為字串，避免比對時型別出錯
        return df.dropna(subset=['Date'])
    except:
        return pd.DataFrame(columns=['Date', 'Stamp', 'Note', "Remark"])

def save_to_gsheets(date_str, stamp=None, note=None, remark=None):
    df = get_all_data()
    
    # 檢查該日期是否已經存在於試算表中
    if date_str in df['Date'].values:
        if stamp:
            df.loc[df['Date'] == date_str, 'Stamp'] = stamp
        if note:
            df.loc[df['Date'] == date_str, 'Note'] = note
        if note:
            df.loc[df['Date'] == date_str, 'Remark'] = note
    else:
        # 如果日期不存在，新增一行
        new_row = pd.DataFrame([{"Date": date_str, "Stamp": stamp, "Note": note, "Remark": remark}])
        df = pd.concat([df, new_row], ignore_index=True)
    
    # 將更新後的 DataFrame 寫回 Google Sheets
    conn.update(data=df)
    
    # 清除 Streamlit 的快取並強制重新整理頁面
    st.cache_data.clear()
    st.rerun()

# 預先抓取資料並轉為字典
raw_df = get_all_data()
data_map = raw_df.set_index('Date').to_dict('index') # 確保 Date 欄位是 index

# --- 3. 功能組件 ---
@st.dialog("寫下今天的日記")
def write_diary(date_str):
    st.write(f"日期：{date_str}")
    existing_note = data_map.get(date_str, {}).get('Note', "")
    note = st.text_area("內容：", value=existing_note if pd.notna(existing_note) else "", placeholder="寫點什麼吧...")
    
    if st.button("儲存紀錄"):
        save_to_gsheets(date_str, note=note)
        st.success("紀錄成功！")

# --- 4. 介面佈局 ---
st.subheader("選擇你的專屬戳章")
stamps = ["⭐", "☕", "✅", "🔥", "🤡"]
selected_stamp = st.radio("今日心情：", stamps, horizontal=True)

st.info(f"今天是：{today}。系統開放蓋章範圍：{today - timedelta(days=2)} 至 {today}")

# 建立日曆表格 (只針對 view_year, view_month)
calendar.setfirstweekday(calendar.SUNDAY)
cal = calendar.monthcalendar(view_year, view_month)

# 星期標題
h_cols = st.columns(7)
for i, day_name in enumerate(["日", "一", "二", "三", "四", "五", "六"]):
    h_cols[i].write(f"**{day_name}**")

# --- 特殊日期設定 ---
special_events = {
    "2026-07-23": {"emoji": "🏁", "color": "rgba(241, 196, 15, 0.2)"},
    "2026-07-10": {"emoji": "🎁", "color": "rgba(46, 204, 113, 0.2)"},
    "2026-07-03": {"emoji": "🎁", "color": "rgba(46, 204, 113, 0.2)"},
    "2026-06-19": {"emoji": "🐲", "color": "rgba(46, 204, 113, 0.2)"},
    "2026-06-05": {"emoji": "🎁", "color": "rgba(46, 204, 113, 0.2)"},
    "2026-05-29": {"emoji": "🛫", "color": "rgba(241, 196, 15, 0.2)"},
}
   
# 日曆格子
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day == 0:
                st.write("") 
            else:
                current_date = datetime(view_year, view_month, day).date()
                date_str = current_date.strftime("%Y-%m-%d")

                # 檢查是否有特殊設定
                event = special_events.get(date_str, {})
                bg_color = event.get("color", "transparent")
                event_emoji = event.get("emoji", "")
                
                # 讀取現有紀錄
                record = data_map.get(date_str, {})
                existing_stamp = record.get('Stamp', "") if pd.notna(record.get('Stamp')) else ""
                existing_note = record.get('Note', "") if pd.notna(record.get('Note')) else ""
                
                # --- 注入背景色 (使用 HTML 容器) ---
                st.markdown(f"""
                    <div style="
                        background-color: {bg_color}; 
                        border-radius: 8px; 
                        padding: 10px; 
                        min-height: 80px;
                        border: {'2px solid #ff4b4b' if event else '1px solid #eeeeee'};
                    ">
                        <div style="font-weight: bold; font-size: 1.1rem; margin-bottom: 5px;">
                            {day} {event_emoji} {existing_stamp}
                        </div>
                """, unsafe_allow_html=True)


                is_open = (today - timedelta(days=2) <= current_date <= today)

                # 顯示
                if existing_note:
                    st.caption(f"📝 {existing_note[:8]}...")
                else:
                    st.caption("　") 

                if is_open:
                    if not existing_stamp:
                        if st.button("蓋章", key=f"s_{date_str}"):
                            save_to_gsheets(date_str, stamp=selected_stamp)
                    
                    if st.button("✍️ 記錄", key=f"n_{date_str}"):
                        write_diary(date_str)
                else:
                    st.write("")

st.divider()
st.success("☁️ 資料已同步至 Cloud")
st.subheader("📖 歷史日記 - 近7天")

# 歷史紀錄 (從 Google Sheets 讀取表格)
if not raw_df.empty:
    # 1. 整理表格：篩選掉空白內容並依照日期倒序排列（最新的在上面）
    history_df = raw_df.dropna(subset=['Note', 'Stamp'], how='all').copy()
    
    # 確保日期格式正確以便排序
    history_df['Date'] = pd.to_datetime(history_df['Date']).dt.date
    history_df = history_df.sort_values(by='Date', ascending=False).head(7)

    # 2. 顯示表格
    st.dataframe(
        history_df[['Date', 'Stamp', 'Note', 'Remark']], 
        column_config={
            "Date": "日期",
            "Stamp": "戳記",
            "Note": "🇺🇸 Sofie 內容",
            "Remark": "🇹🇼 留言"
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("目前尚無歷史紀錄。")

# py -m streamlit run app.py
