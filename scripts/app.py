# app/app.py
"""
Streamlit UI for AI Data Cleaning
Professional, modern interface
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from dotenv import load_dotenv
import io

# Add scripts folder to path
script_dir = os.path.join(os.path.dirname(__file__), '../scripts')
sys.path.insert(0, script_dir)

# Import from scripts
from data_ingestion import DataIngestion
from data_cleaning import DataCleaning
from ai_agent import DataQualityAgent

load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Data Cleaner",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    db_url = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'student_data_db')}"
    st.session_state.ingestion = DataIngestion(db_url=db_url) if os.getenv('DB_PASSWORD') else None
    st.session_state.ai_agent = DataQualityAgent(api_key=os.getenv("GOOGLE_API_KEY")) if os.getenv('GOOGLE_API_KEY') else None
    st.session_state.data = None
    st.session_state.cleaned_data = None
    st.session_state.initialized = True

# Header
st.markdown('<h1 class="main-header">🧹 AI Data Cleaner</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; font-size: 1.2rem;">Clean your data intelligently with AI</p>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚙️ Configuration")

# Data Source Selection
data_source = st.sidebar.selectbox(
    "📂 Select Data Source",
    ["Upload CSV", "Upload Excel", "Database", "API"]
)

df = None

# Load Data Based on Source
if data_source == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Choose CSV file", type=['csv'])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.session_state.data = df
        st.sidebar.success(f"✓ Loaded {len(df)} rows")

elif data_source == "Upload Excel":
    uploaded_file = st.sidebar.file_uploader("Choose Excel file", type=['xlsx', 'xls'])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.session_state.data = df
        st.sidebar.success(f"✓ Loaded {len(df)} rows")

elif data_source == "Database":
    if st.session_state.ingestion:
        table_name = st.sidebar.text_input("Table Name", "student")
        if st.sidebar.button("📥 Load from Database"):
            with st.spinner("Loading from database..."):
                df = st.session_state.ingestion.load_from_database(f"SELECT * FROM {table_name}")
                if df is not None:
                    st.session_state.data = df
                    st.sidebar.success(f"✓ Loaded {len(df)} rows")
                else:
                    st.sidebar.error("Failed to load data from database")
    else:
        st.sidebar.error("⚠️ Database not configured. Check .env file")

elif data_source == "API":
    api_url = st.sidebar.text_input("API URL", placeholder="https://api.example.com/data")
    if st.sidebar.button("🌐 Fetch from API"):
        if st.session_state.ingestion:
            with st.spinner("Fetching from API..."):
                df = st.session_state.ingestion.fetch_from_api(api_url)
                if df is not None:
                    st.session_state.data = df
                    st.sidebar.success(f"✓ Loaded {len(df)} rows")
                else:
                    st.sidebar.error("Failed to fetch data from API")

# Main Content
if st.session_state.data is not None:
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Overview", "🤖 AI Cleaning", "📈 Results", "📉 Analytics"])
    
    with tab1:
        st.header("📊 Original Data Overview")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rows", f"{st.session_state.data.shape[0]:,}")
        with col2:
            st.metric("Total Columns", st.session_state.data.shape[1])
        with col3:
            st.metric("Missing Values", f"{int(st.session_state.data.isnull().sum().sum()):,}")
        with col4:
            st.metric("Duplicates", f"{int(st.session_state.data.duplicated().sum()):,}")
        
        st.subheader("Data Preview")
        st.dataframe(st.session_state.data.head(20), use_container_width=True)
        
        # Data Quality Visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Missing Values by Column")
            missing = st.session_state.data.isnull().sum()
            if missing.sum() > 0:
                # Convert to native Python types
                fig = px.bar(
                    x=missing.index.tolist(),
                    y=missing.values.tolist(),
                    labels={'x': 'Column', 'y': 'Missing Count'},
                    color=missing.values.tolist(),
                    color_continuous_scale='Reds'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ No missing values!")
        
        with col2:
            st.subheader("Data Types Distribution")
            dtype_counts = st.session_state.data.dtypes.value_counts()
            # Convert to native Python types
            fig = px.pie(
                values=dtype_counts.values.tolist(),
                names=[str(x) for x in dtype_counts.index],
                title="Column Data Types"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Info
        with st.expander("📋 Detailed Data Information"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Data Types:**")
                dtype_df = pd.DataFrame({
                    'Column': st.session_state.data.dtypes.index.tolist(),
                    'Type': [str(x) for x in st.session_state.data.dtypes.values]
                })
                st.dataframe(dtype_df, use_container_width=True)
            with col2:
                st.write("**Missing Values:**")
                missing_df = pd.DataFrame({
                    'Column': st.session_state.data.isnull().sum().index.tolist(),
                    'Missing': st.session_state.data.isnull().sum().values.tolist(),
                    'Percentage': (st.session_state.data.isnull().sum() / len(st.session_state.data) * 100).round(2).values.tolist()
                })
                st.dataframe(missing_df, use_container_width=True)
    
    with tab2:
        st.header("🤖 AI-Powered Data Cleaning")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            cleaning_method = st.radio(
                "Choose Cleaning Method",
                ["🤖 AI Agent (Recommended)", "📋 Traditional Rules"],
                help="AI Agent uses machine learning to intelligently clean data"
            )
        
        with col2:
            st.info("**AI Agent** analyzes your data and applies intelligent cleaning strategies automatically.")
        
        if st.button("🚀 Start Cleaning", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                if cleaning_method == "🤖 AI Agent (Recommended)":
                    if not st.session_state.ai_agent:
                        st.error("❌ AI Agent not available. Check GOOGLE_API_KEY in .env file")
                    else:
                        status_text.text("🤖 AI is analyzing your data...")
                        progress_bar.progress(25)
                        
                        st.session_state.cleaned_data = st.session_state.ai_agent.clean_data(
                            st.session_state.data.copy()
                        )
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Cleaning Complete!")
                        st.success("✅ Data cleaned successfully with AI!")
                        st.balloons()
                else:
                    status_text.text("📋 Applying traditional cleaning rules...")
                    progress_bar.progress(25)
                    
                    cleaner = DataCleaning(st.session_state.data.copy())
                    progress_bar.progress(50)
                    
                    cleaner.remove_duplicates()
                    cleaner.remove_whitespace()
                    cleaner.handle_missing_values(strategy='fill_median')
                    
                    progress_bar.progress(75)
                    st.session_state.cleaned_data = cleaner.get_cleaned_data()
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Cleaning Complete!")
                    st.success("✅ Data cleaned successfully!")
                    st.balloons()
            
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Error during cleaning: {str(e)}")
                with st.expander("Error Details"):
                    st.exception(e)
    
    with tab3:
        if st.session_state.cleaned_data is not None:
            st.header("✨ Cleaned Data Results")
            
            # Before/After Comparison
            col1, col2, col3, col4 = st.columns(4)
            
            original_rows = st.session_state.data.shape[0]
            cleaned_rows = st.session_state.cleaned_data.shape[0]
            original_missing = int(st.session_state.data.isnull().sum().sum())
            cleaned_missing = int(st.session_state.cleaned_data.isnull().sum().sum())
            
            with col1:
                st.metric(
                    "Rows", 
                    f"{cleaned_rows:,}",
                    delta=f"{cleaned_rows - original_rows:,}",
                    delta_color="normal"
                )
            with col2:
                st.metric(
                    "Missing Values", 
                    f"{cleaned_missing:,}",
                    delta=f"{cleaned_missing - original_missing:,}",
                    delta_color="inverse"
                )
            with col3:
                if cleaned_rows > 0 and st.session_state.cleaned_data.shape[1] > 0:
                    quality_score = (1 - cleaned_missing / (cleaned_rows * st.session_state.cleaned_data.shape[1])) * 100
                else:
                    quality_score = 0
                st.metric(
                    "Data Quality Score",
                    f"{quality_score:.1f}%"
                )
            with col4:
                duplicates_removed = int(st.session_state.data.duplicated().sum()) - int(st.session_state.cleaned_data.duplicated().sum())
                st.metric(
                    "Duplicates Removed",
                    f"{duplicates_removed:,}"
                )
            
            st.subheader("Cleaned Data Preview")
            st.dataframe(st.session_state.cleaned_data.head(20), use_container_width=True)
            
            # Comparison Chart
            st.subheader("📊 Before vs After Comparison")
            comparison_data = pd.DataFrame({
                'Metric': ['Rows', 'Missing Values', 'Duplicates'],
                'Before': [original_rows, original_missing, int(st.session_state.data.duplicated().sum())],
                'After': [cleaned_rows, cleaned_missing, int(st.session_state.cleaned_data.duplicated().sum())]
            })
            
            fig = go.Figure(data=[
                go.Bar(name='Before', x=comparison_data['Metric'], y=comparison_data['Before'], marker_color='#ff6b6b'),
                go.Bar(name='After', x=comparison_data['Metric'], y=comparison_data['After'], marker_color='#51cf66')
            ])
            fig.update_layout(barmode='group', title="Data Quality Improvement")
            st.plotly_chart(fig, use_container_width=True)
            
            # Download Section
            st.subheader("💾 Download Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv = st.session_state.cleaned_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"cleaned_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                if st.button("💾 Save to Database", use_container_width=True):
                    if st.session_state.ingestion:
                        table_name = f"cleaned_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
                        success = st.session_state.ingestion.save_to_database(
                            st.session_state.cleaned_data, 
                            table_name
                        )
                        if success:
                            st.success(f"✅ Saved to table: {table_name}")
                        else:
                            st.error("❌ Failed to save to database")
                    else:
                        st.error("❌ Database not configured")
            
            with col3:
                try:
                    excel_buffer = io.BytesIO()
                    st.session_state.cleaned_data.to_excel(excel_buffer, index=False, engine='openpyxl')
                    st.download_button(
                        label="📥 Download Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"cleaned_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Excel export error: {str(e)}")
        
        else:
            st.info("👈 Run cleaning in the AI Cleaning tab first")
            st.markdown("""
            ### Next Steps:
            1. Go to the **AI Cleaning** tab
            2. Choose your cleaning method
            3. Click **Start Cleaning**
            4. Return here to see results and download
            """)
    
    with tab4:
        st.header("📉 Data Analytics")
        
        if st.session_state.cleaned_data is not None:
            df_to_analyze = st.session_state.cleaned_data
            st.info("📊 Analyzing cleaned data")
        else:
            df_to_analyze = st.session_state.data
            st.info("📊 Analyzing original data")
        
        # Select columns for analysis
        numeric_cols = df_to_analyze.select_dtypes(include=['float64', 'int64']).columns.tolist()
        categorical_cols = df_to_analyze.select_dtypes(include=['object']).columns.tolist()
        
        if numeric_cols:
            st.subheader("📈 Numeric Columns Analysis")
            selected_numeric = st.selectbox("Select numeric column", numeric_cols)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(
                    df_to_analyze, 
                    x=selected_numeric,
                    title=f"Distribution of {selected_numeric}",
                    nbins=30
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.box(
                    df_to_analyze, 
                    y=selected_numeric,
                    title=f"Box Plot of {selected_numeric}"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Statistics
            with st.expander("📊 Descriptive Statistics"):
                stats = df_to_analyze[selected_numeric].describe()
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Mean", f"{stats['mean']:.2f}")
                with col2:
                    st.metric("Median", f"{stats['50%']:.2f}")
                with col3:
                    st.metric("Std Dev", f"{stats['std']:.2f}")
                with col4:
                    st.metric("Range", f"{stats['max'] - stats['min']:.2f}")
        else:
            st.warning("No numeric columns found in the dataset")
        
        if categorical_cols:
            st.subheader("📊 Categorical Columns Analysis")
            selected_categorical = st.selectbox("Select categorical column", categorical_cols)
            
            value_counts = df_to_analyze[selected_categorical].value_counts()
            
            # Convert to lists for Plotly
            fig = px.bar(
                x=value_counts.index.tolist(),
                y=value_counts.values.tolist(),
                labels={'x': selected_categorical, 'y': 'Count'},
                title=f"Distribution of {selected_categorical}"
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Value counts table
            with st.expander("📋 Value Counts"):
                value_counts_df = pd.DataFrame({
                    'Value': value_counts.index.tolist(),
                    'Count': value_counts.values.tolist(),
                    'Percentage': (value_counts.values / value_counts.sum() * 100).round(2).tolist()
                })
                st.dataframe(value_counts_df, use_container_width=True)
        else:
            st.warning("No categorical columns found in the dataset")
        
        # Correlation Matrix
        if len(numeric_cols) > 1:
            st.subheader("🔗 Correlation Matrix")
            corr_matrix = df_to_analyze[numeric_cols].corr()
            
            fig = px.imshow(
                corr_matrix.values,
                labels=dict(color="Correlation"),
                x=numeric_cols,
                y=numeric_cols,
                color_continuous_scale='RdBu_r',
                aspect="auto"
            )
            fig.update_layout(title="Feature Correlation Heatmap")
            st.plotly_chart(fig, use_container_width=True)
            
            # Find strong correlations
            with st.expander("🔍 Strong Correlations"):
                strong_corr = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        if abs(corr_matrix.iloc[i, j]) > 0.7:
                            strong_corr.append({
                                'Feature 1': corr_matrix.columns[i],
                                'Feature 2': corr_matrix.columns[j],
                                'Correlation': f"{corr_matrix.iloc[i, j]:.3f}"
                            })
                
                if strong_corr:
                    st.dataframe(pd.DataFrame(strong_corr), use_container_width=True)
                else:
                    st.info("No strong correlations (>0.7) found")

else:
    # Welcome Screen
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <h2>👋 Welcome to AI Data Cleaner!</h2>
        <p style="font-size: 1.2rem; color: #666;">
            Upload or select a data source from the sidebar to get started
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 1rem; color: white; text-align: center;">
            <h3>🤖 AI-Powered</h3>
            <p>Let AI analyze and fix data quality issues automatically</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="padding: 2rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 1rem; color: white; text-align: center;">
            <h3>📊 Multiple Sources</h3>
            <p>CSV, Excel, Database, API - we support them all</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="padding: 2rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 1rem; color: white; text-align: center;">
            <h3>📈 Visual Analytics</h3>
            <p>See before/after comparisons and insights</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("""
    ### 🚀 How to Use
    
    1. **📂 Load Data** - Upload a file or connect to a database from the sidebar
    2. **🔍 Review** - Analyze your data quality in the Data Overview tab
    3. **🧹 Clean** - Use AI or traditional methods in the AI Cleaning tab
    4. **💾 Download** - Save your cleaned data in the Results tab
    5. **📊 Analyze** - Explore insights in the Analytics tab
    
    ### 🎯 Features
    
    - **Smart Data Cleaning**: AI automatically detects and fixes issues
    - **Multiple File Formats**: Support for CSV, Excel, and more
    - **Database Integration**: Direct connection to PostgreSQL
    - **Visual Analytics**: Interactive charts and statistics
    - **Export Options**: Download as CSV or Excel
    
    ### 📝 Supported Data Issues
    
    - Missing values
    - Duplicate rows
    - Inconsistent formatting
    - Data type mismatches
    - Outliers
    - Whitespace issues
    - Invalid values
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Made with ❤️ using <strong>Streamlit</strong> | Powered by <strong>Google Gemini AI</strong></p>
    <p style="font-size: 0.9rem;">AI Agentic Data Cleaning System v1.0</p>
</div>
""", unsafe_allow_html=True)