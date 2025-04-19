
import streamlit as st
import pandas as pd
import math
import io

st.set_page_config(page_title="تحليل خطة المقاولات الذكية", layout="wide")
st.title("📊 تحليل خطة إدارة مشروع المقاولات")

required_columns = [
    "Work Item / بند العمل",
    "Unit / الوحدة",
    "Quantity / الكمية",
    "Duration (days) / المدة",
    "Labor Type / نوع العمالة",
    "Productivity / إنتاجية العامل",
    "Material / المادة المطلوبة",
    "Material Rate / معدل استهلاك المادة لكل وحدة",
    "Material Cost per Unit / تكلفة المادة",
    "Labor Cost per Day / تكلفة العامل لليوم"
]

uploaded_file = st.file_uploader("📤 ارفع ملف Excel يحتوي على بيانات BOQ", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error("❌ الملف المرفوع لا يحتوي على الأعمدة التالية:")
            for col in missing_cols:
                st.warning(f"- {col}")
        else:
            df["Labor Days Needed"] = df["Quantity / الكمية"] / df["Productivity / إنتاجية العامل"]
            df["Workers Needed"] = (df["Labor Days Needed"] / df["Duration (days) / المدة"]).apply(math.ceil)
            df["Total Labor Cost"] = df["Labor Days Needed"] * df["Labor Cost per Day / تكلفة العامل لليوم"]
            df["Total Material Needed"] = df["Quantity / الكمية"] * df["Material Rate / معدل استهلاك المادة لكل وحدة"]
            df["Total Material Cost"] = df["Total Material Needed"] * df["Material Cost per Unit / تكلفة المادة"]
            df["Total Cost"] = df["Total Labor Cost"] + df["Total Material Cost"]
            df["Start Day"] = df["Duration (days) / المدة"].cumsum().shift(fill_value=1)
            df["End Day"] = df["Start Day"] + df["Duration (days) / المدة"] - 1

            st.success("✅ تم تحليل الملف بنجاح")

            st.subheader("📋 خطة الجدول الزمني")
            st.dataframe(df[["Work Item / بند العمل", "Start Day", "End Day", "Duration (days) / المدة"]])

            st.subheader("👷 خطة الموارد (العمالة)")
            labor_plan = df.groupby("Labor Type / نوع العمالة").agg({
                "Workers Needed": "sum",
                "Labor Days Needed": "sum",
                "Total Labor Cost": "sum"
            }).reset_index()
            st.dataframe(labor_plan)

            st.subheader("🧱 خطة المشتريات (المواد)")
            procurement_plan = df.groupby("Material / المادة المطلوبة").agg({
                "Total Material Needed": "sum",
                "Total Material Cost": "sum"
            }).reset_index()
            st.dataframe(procurement_plan)

            st.subheader("💰 خطة الميزانية")
            budget_plan = df[["Work Item / بند العمل", "Total Labor Cost", "Total Material Cost", "Total Cost"]]
            st.dataframe(budget_plan)

            @st.cache_data
            def convert_to_excel():
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name="Raw Data", index=False)
                    labor_plan.to_excel(writer, sheet_name="Resource Plan", index=False)
                    procurement_plan.to_excel(writer, sheet_name="Procurement Plan", index=False)
                    budget_plan.to_excel(writer, sheet_name="Budget Plan", index=False)
                    df[["Work Item / بند العمل", "Start Day", "End Day", "Duration (days) / المدة"]].to_excel(writer, sheet_name="Schedule", index=False)
                return output.getvalue()

            excel_data = convert_to_excel()
            st.download_button(
                label="📥 تحميل الخطة الكاملة (Excel)",
                data=excel_data,
                file_name="Complete_Project_Plan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء التحليل: {str(e)}")
