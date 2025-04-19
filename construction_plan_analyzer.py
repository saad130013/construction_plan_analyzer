
import streamlit as st
import pandas as pd
import math
import io

st.title("📊 تحليل خطة المقاولات الذكية")

uploaded_file = st.file_uploader("📤 ارفع ملف BOQ (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    df["Labor Days Needed"] = df["Quantity / الكمية"] / df["Productivity (Unit/Day/Worker) / إنتاجية العامل"]
    df["Workers Needed"] = (df["Labor Days Needed"] / df["Duration (days) / المدة"]).apply(lambda x: round(x + 0.5))

    df["Total Material Needed"] = df["Quantity / الكمية"] * df["Material Rate (per unit) / معدل استهلاك المادة لكل وحدة"]

    st.success("✅ تم تحليل الملف بنجاح. النتائج كالتالي:")
    st.dataframe(df[[
        "Work Item / بند العمل", "Quantity / الكمية", "Unit / الوحدة",
        "Labor Type / نوع العمالة", "Duration (days) / المدة",
        "Workers Needed", "Material / المادة المطلوبة", "Total Material Needed"
    ]])

    @st.cache_data
    def convert_df(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        processed_data = output.getvalue()
        return processed_data

    excel = convert_df(df)
    st.download_button(
        label="📥 تحميل الخطة المحللة (Excel)",
        data=excel,
        file_name="Analyzed_Construction_Plan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
