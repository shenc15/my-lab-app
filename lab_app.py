import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 页面配置 ---
st.set_page_config(page_title="福建实验室管理", layout="wide")

# --- 2. 建立 Google Sheets 连接 ---
# 它会自动去 Secrets 里读取配置，不再需要本地 Excel 文件
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 辅助函数 ---
def get_status(days):
    if days <= 0: return "🔴 已过期"
    if days <= 30: return "🟡 临近到期"
    return "🟢 正常"

# --- 4. 主界面 ---
st.title("🧪 实验室综合管理平台")

tab1, tab2 = st.tabs(["📅 校准提醒", "📦 试剂管理"])

# --- Tab 1: 校准监控模块 ---
with tab1:
    try:
        # 使用英文名 calibration 彻底避免 ASCII 编码报错
        df = conn.read(worksheet="calibration", ttl=0)
        
        # 转换并计算
        df['校准到期时间'] = pd.to_datetime(df['校准到期时间'])
        df['剩余天数'] = (df['校准到期时间'] - datetime.now()).dt.days
        df['状态'] = df['剩余天数'].apply(get_status)

        # 搜索功能
        search = st.text_input("🔍 搜索客户或工程师")
        if search:
            # fillna('') 防止空单元格导致搜索报错
            df = df[df['客户'].fillna('').str.contains(search) | 
                    df['工程师'].fillna('').str.contains(search)]

        st.dataframe(df[['工程师', '客户', '模块', '校准到期时间', '状态']], use_container_width=True)
    except Exception as e:
        st.error(f"❌ 校准数据读取失败。请确认 Sheet 名称已改为 'calibration'。错误详情: {e}")

# --- Tab 2: 试剂库存管理 ---
with tab2:
    st.header("试剂库存登记")
    
    try:
        # 读取英文名 reagents 标签页，不设置缓存(ttl=0)以保证实时性
        reagent_df = conn.read(worksheet="reagents", ttl=0)
        
        # 使用 data_editor 实现手机端点击修改
        # num_rows="dynamic" 允许添加新行（点击表格底部的 + 号）
        edited_df = st.data_editor(
            reagent_df, 
            num_rows="dynamic", 
            use_container_width=True,
            key="reagent_editor"
        )
        
        # 核心：保存按钮，将修改同步回云端
        if st.button("💾 点击此处：保存并同步到云端"):
            try:
                conn.update(worksheet="reagents", data=edited_df)
                st.success("✅ 保存成功！数据已写入 Google 表格，全员同步。")
                st.balloons()
            except Exception as save_error:
                st.error(f"保存失败，请检查 Google 表格权限：{save_error}")
                
    except Exception as e:
        st.error(f"❌ 库存表读取失败。请确认 Sheet 名称已改为 'reagents'。错误详情: {e}")
