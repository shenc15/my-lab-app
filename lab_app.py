import streamlit as st
import pandas as pd
from datetime import datetime

# --- 页面设置 ---
st.set_page_config(page_title="福建实验室管理", layout="wide")

# --- 核心数据处理 ---
def get_status(days):
    if days <= 0: return "🔴 已过期"
    if days <= 30: return "🟡 临近到期"
    return "🟢 正常"

# 1. 校准监控模块
st.title("🧪 实验室综合管理平台")

tab1, tab2 = st.tabs(["📅 校准提醒", "📦 试剂管理"])

with tab1:
    try:
        df = pd.read_excel("福建校准时间统计 - 副本.xlsx")
        df['校准到期时间'] = pd.to_datetime(df['校准到期时间'])
        df['剩余天数'] = (df['校准到期时间'] - datetime.now()).dt.days
        df['状态'] = df['剩余天数'].apply(get_status)

        # 手机端常用的搜索功能
        search = st.text_input("🔍 搜索客户或工程师")
        if search:
            df = df[df['客户'].str.contains(search) | df['工程师'].str.contains(search)]

        st.dataframe(df[['工程师', '客户', '模块', '校准到期时间', '状态']], use_container_width=True)
    except:
        st.warning("未找到校准统计文件，请检查文件名。")

with tab2:
    st.header("试剂库存登记")
    # 使用 st.data_editor 创建一个可以直接修改的表格
    # 在手机上点击单元格即可输入
    if 'reagent_data' not in st.session_state:
        st.session_state.reagent_data = pd.DataFrame(
            columns=["试剂名称", "批号", "数量", "有效期"]
        )
    
    edited_df = st.data_editor(st.session_state.reagent_data, num_rows="dynamic", use_container_width=True)
    
    if st.button("保存试剂清单"):
        st.session_state.reagent_data = edited_df
        st.success("库存已保存！")
