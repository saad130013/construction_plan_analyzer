# Construction Project Analyzer (Streamlit App)

📊 This Streamlit app allows you to upload a construction BOQ Excel file and automatically generate:
- Labor plan
- Material requirements
- Cost estimation (labor + material)
- Execution schedule

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_project_analyzer_checked.py
```

## Excel File Format Required

The uploaded Excel file must include the following columns (exact names):

- Work Item / بند العمل
- Unit / الوحدة
- Quantity / الكمية
- Duration (days) / المدة
- Labor Type / نوع العمالة
- Productivity / إنتاجية العامل
- Material / المادة المطلوبة
- Material Rate / معدل استهلاك المادة لكل وحدة
- Material Cost per Unit / تكلفة المادة
- Labor Cost per Day / تكلفة العامل لليوم
