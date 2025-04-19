import streamlit as st
import pandas as pd
import math
import io
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from bidi.algorithm import get_display

# تهيئة صفحة Streamlit
st.set_page_config(page_title="تحليل خطة المقاولات الذكية", layout="wide")
st.title("📊 تحليل خطة إدارة مشروع المقاولات")

# الأعمدة المطلوبة
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

# قسم المساعدة
with st.expander("🆘 دليل استخدام التطبيق"):
    st.markdown("""
    ### 📝 تعليمات استخدام التطبيق:
    1. قم بإعداد ملف Excel حسب الأعمدة المطلوبة:
        - **Work Item / بند العمل**: اسم بند العمل (مثال: حفر الأساسات)
        - **Productivity / إنتاجية العامل**: يجب أن تكون قيمة موجبة (>0)
    2. تجنب الفراغات أو الرموز الخاصة في أسماء الأعمدة
    3. يمكنك تحميل نموذج ملف Excel من [هذا الرابط](https://example.com)
    """)

# رفع الملف
uploaded_file = st.file_uploader("📤 ارفع ملف Excel", type=["xlsx"])

if uploaded_file:
    try:
        # قراءة الملف مع اختيار الورقة
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names
        selected_sheet = st.selectbox("اختر الورقة", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        # التحقق من الأعمدة المطلوبة
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error("❌ الملف المرفوع لا يحتوي على الأعمدة التالية:")
            for col in missing_cols:
                st.warning(f"- {col}")
            st.stop()
        
        # فحص جودة البيانات
        if (df["Productivity / إنتاجية العامل"] <= 0).any():
            st.error("❌ قيمة الإنتاجية يجب أن تكون أكبر من صفر!")
            st.stop()
        if (df["Duration (days) / المدة"] <= 0).any():
            st.error("❌ مدة العمل يجب أن تكون أكبر من صفر!")
            st.stop()
        
        # العمليات الحسابية
        df["Labor Days Needed"] = df["Quantity / الكمية"] / df["Productivity / إنتاجية العامل"]
        df["Workers Needed"] = (df["Labor Days Needed"] / df["Duration (days) / المدة"]).apply(math.ceil)
        df["Total Labor Cost"] = df["Labor Days Needed"] * df["Labor Cost per Day / تكلفة العامل لليوم"]
        df["Total Material Needed"] = df["Quantity / الكمية"] * df["Material Rate / معدل استهلاك المادة لكل وحدة"]
        df["Total Material Cost"] = df["Total Material Needed"] * df["Material Cost per Unit / تكلفة المادة"]
        df["Total Cost"] = df["Total Labor Cost"] + df["Total Material Cost"]
        
        # حسابات الجدول الزمني
        df["Start Day"] = df["Duration (days) / المدة"].cumsum().shift(fill_value=1)
        df["End Day"] = df["Start Day"] + df["Duration (days) / المدة"] - 1
        
        # إضافة هامش الربح
        profit_margin = st.number_input("هامش الربح (%)", min_value=0.0, value=10.0)
        df["سعر البيع"] = df["Total Cost"] * (1 + profit_margin/100)
        
        # إضافة التواريخ الفعلية
        start_date = st.date_input("تاريخ بدء المشروع")
        df["تاريخ البدء"] = start_date + pd.to_timedelta(df["Start Day"], unit='d')
        df["تاريخ الانتهاء"] = start_date + pd.to_timedelta(df["End Day"], unit='d')
        
        # التعريب
        df["Work Item / بند العمل"] = df["Work Item / بند العمل"].apply(lambda x: get_display(str(x)))
        
        # عرض النتائج
        st.success("✅ تم تحليل الملف بنجاح!")
        
        # التصورات البيانية
        col1, col2 = st.columns(2)
        with col1:
            fig_gantt = px.timeline(
                df,
                x_start="Start Day",
                x_end="End Day",
                y="Work Item / بند العمل",
                title="الجدول الزمني للمشروع"
            )
            st.plotly_chart(fig_gantt, use_container_width=True)
        
        with col2:
            fig_pie = px.pie(
                df,
                names="Work Item / بند العمل",
                values="Total Cost",
                title="توزيع التكاليف"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # تصفية البيانات
        min_cost = st.slider(
            "الحد الأدنى للتكلفة",
            min_value=float(df["Total Cost"].min()),
            max_value=float(df["Total Cost"].max()),
            value=float(df["Total Cost"].min())
        )
        filtered_df = df[df["Total Cost"] >= min_cost]
        
        # اختيار الأعمدة
        selected_columns = st.multiselect(
            "اختر الأعمدة للعرض",
            df.columns,
            default=["Work Item / بند العمل", "Total Cost", "تاريخ البدء", "تاريخ الانتهاء"]
        )
        st.dataframe(filtered_df[selected_columns], height=400)
        
        # تحميل النتائج
        @st.cache_data
        def convert_to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()
        
        @st.cache_data
        def create_pdf_report(df):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.setFont("Helvetica-Bold", 14)
            
            # العنوان
            c.drawString(100, 750, "تقرير مشروع المقاولات")
            
            # الملخص
            c.setFont("Helvetica", 12)
            c.drawString(100, 730, f"إجمالي التكاليف: {df['Total Cost'].sum():,.2f} ريال")
            c.drawString(100, 710, f"تاريخ البدء: {start_date}")
            
            # الجدول
            y_position = 650
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, y_position, "بنود العمل الرئيسية")
            y_position -= 30
            
            c.setFont("Helvetica", 10)
            for index, row in df.iterrows():
                c.drawString(100, y_position, f"{row['Work Item / بند العمل']}: {row['Total Cost']:,.2f} ريال")
                y_position -= 20
                if y_position < 50:
                    c.showPage()
                    y_position = 750
            
            c.save()
            return buffer.getvalue()
        
        # أزرار التحميل
        col_excel, col_pdf = st.columns(2)
        with col_excel:
            excel_data = convert_to_excel(df)
            st.download_button(
                label="📥 تحميل Excel",
                data=excel_data,
                file_name="project_analysis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col_pdf:
            pdf_data = create_pdf_report(df)
            st.download_button(
                label="📥 تحميل PDF",
                data=pdf_data,
                file_name="project_report.pdf",
                mime="application/pdf"
            )
    
    except Exception as e:
        st.error(f"❌ حدث خطأ: {str(e)}")
