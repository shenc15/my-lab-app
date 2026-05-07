import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 页面设置 ---
st.set_page_config(page_title="福建实验室管理", layout="wide")

# --- 2. 建立 Google Sheets 连接 ---
# 注意：确保你已经在 Streamlit Cloud 的 Secrets 中配置了 spreadsheet 链接
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 辅助函数 ---
def get_status(days):
    if days <= 0: return "🔴 已过期"
    if days <= 30: return "🟡 临近到期"
    return "🟢 正常"

# --- 4. 标题 ---
st.title("🧪 实验室综合管理平台")

tab1, tab2 = st.tabs(["📅 校准提醒", "📦 试剂管理"])

# --- Tab 1: 校准监控模块 ---
with tab1:
    try:
        # 从 Google Sheets 的“校准时间统计”工作表读取数据
        # ttl=600 表示缓存10分钟，避免频繁刷新降低速度
        df = conn.read(worksheet="校准时间统计", ttl=600)
        
        # 转换时间并计算状态
        df['校准到期时间'] = pd.to_datetime(df['校准到期时间'])
        df['剩余天数'] = (df['校准到期时间'] - datetime.now()).dt.days
        df['状态'] = df['剩余天数'].apply(get_status)

        # 搜索功能
        search = st.text_input("🔍 搜索客户或工程师")
        if search:
            # 增加 fillna('') 防止因为表格中有空值导致搜索报错
            df = df[df['客户'].fillna('').str.contains(search) | 
                    df['工程师'].fillna('').str.contains(search)]

        st.dataframe(df[['工程师', '客户', '模块', '校准到期时间', '状态']], use_container_width=True)
    except Exception as e:
        st.warning(f"未能从 Google 表格读取校准数据。请检查 Sheet 名称是否为 '校准时间统计'。错误信息: {e}")

# --- Tab 2: 试剂库存管理 (实现持久化保存) ---
with tab2:
    st.header("试剂库存登记")
    
    try:
        # 从 Google Sheets 的“校准试剂库存”工作表读取数据
        # ttl=0 极其重要！确保每次看到的都是云端最新的库存，而不是旧缓存
        reagent_df = conn.read(worksheet="校准试剂库存", ttl=0)
        
        # 使用 data_editor 创建可以直接修改的表格
        # num_rows="dynamic" 允许同事们点击表格底部的 "+" 号添加新行
        edited_df = st.data_editor(
            reagent_df, 
            num_rows="dynamic", 
            use_container_width=True,
            key="reagent_editor"
        )
        
        # 保存按钮：这是解决“刷新消失”的核心
        if st.button("💾 保存并同步库存到云端"):
            # 将修改后的数据写回 Google Sheets
            conn.update(worksheet="校准试剂库存", data=edited_df)
            st.success("✅ 库存已永久保存到云端，同事刷新后也能看到！")
            st.balloons()
            
    except Exception as e:
        st.error(f"无法加载库存表。请确保 Google 表格中有一个 Sheet 叫 '校准试剂库存'。错误: {e}")
