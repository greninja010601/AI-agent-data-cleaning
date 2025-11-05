"""
AI Agent Module
Uses LangChain + LangGraph + Google Gemini for intelligent data cleaning
"""

import pandas as pd 
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
import json

load_dotenv()

class AgentState(TypedDict):
    """State that will be passed between nodes"""
    dataframe: Any
    data_summary: str
    quality_issues: List[Dict]
    cleaning_plan: str
    cleaning_actions: List[str]
    cleaned_dataframe: Any
    messages: List[str]
    iteration: int


class DataQualityAgent:
    """AI-powered data quality agent using LangChain and Google Gemini"""
    
    def __init__(self, api_key=None):
        """Initialize the AI agent with Google Gemini"""
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2
        )
        
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("analyze_data", self.analyze_data)
        workflow.add_node("identify_issues", self.identify_issues)
        workflow.add_node("create_plan", self.create_cleaning_plan)
        workflow.add_node("execute_cleaning", self.execute_cleaning)
        workflow.add_node("validate_results", self.validate_results)
        
        workflow.set_entry_point("analyze_data")
        workflow.add_edge("analyze_data", "identify_issues")
        workflow.add_edge("identify_issues", "create_plan")
        workflow.add_edge("create_plan", "execute_cleaning")
        workflow.add_edge("execute_cleaning", "validate_results")
        workflow.add_edge("validate_results", END)
        
        return workflow.compile()
    
    def analyze_data(self, state: AgentState) -> AgentState:
        """Analyze the dataframe and create a summary"""
        df = state["dataframe"]
        
        summary_stats = {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicates": df.duplicated().sum(),
            "sample_data": df.head(5).to_dict()
        }
        
        prompt = f"""
        Analyze this dataset summary and provide insights:
        
        Dataset Shape: {summary_stats['shape']}
        Columns: {summary_stats['columns']}
        Data Types: {summary_stats['dtypes']}
        Missing Values: {summary_stats['missing_values']}
        Duplicate Rows: {summary_stats['duplicates']}
        
        Sample Data:
        {pd.DataFrame(summary_stats['sample_data']).to_string()}
        
        Provide a brief, clear summary of the dataset including:
        1. What type of data this appears to be
        2. Key observations about data quality
        3. Overall assessment
        """
        
        response = self.llm.invoke(prompt)
        data_summary = response.content
        
        state["data_summary"] = data_summary
        state["messages"].append(f"Data Analysis: {data_summary}")
        
        print("\n" + "="*60)
        print("DATA ANALYSIS")
        print("="*60)
        print(data_summary)
        
        return state
    
    def identify_issues(self, state: AgentState) -> AgentState:
        """Identify data quality issues using Gemini"""
        df = state["dataframe"]
        
        issues_data = {
            "missing_values": df.isnull().sum()[df.isnull().sum() > 0].to_dict(),
            "duplicates": int(df.duplicated().sum()),
            "data_types": df.dtypes.astype(str).to_dict(),
            "sample_values": {}
        }
        
        for col in df.columns:
            unique_vals = df[col].dropna().unique()[:10].tolist()
            issues_data["sample_values"][col] = [str(v) for v in unique_vals]
        
        prompt = f"""
        As a data quality expert, identify ALL data quality issues in this dataset:
        
        Missing Values per Column: {issues_data['missing_values']}
        Total Duplicates: {issues_data['duplicates']}
        Data Types: {issues_data['data_types']}
        
        Sample Values by Column:
        {json.dumps(issues_data['sample_values'], indent=2)}
        
        Identify issues such as:
        1. Missing values
        2. Inconsistent formatting (e.g., 'yes', 'Yes', 'YES')
        3. Data type mismatches (e.g., numbers stored as text)
        4. Trailing/leading spaces
        5. Invalid values
        6. Inconsistent naming conventions
        7. Mixed case in categorical data
        
        Return ONLY a valid JSON array. No markdown, no code blocks:
        [
            {{"column": "column_name", "issue": "description", "severity": "high", "suggestion": "how to fix"}}
        ]
        """
        
        response = self.llm.invoke(prompt)
        
        try:
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx != -1 and end_idx > start_idx:
                content = content[start_idx:end_idx]
            
            issues = json.loads(content)
        except Exception as e:
            print(f"⚠ Warning: Could not parse AI response: {e}")
            issues = [{"column": "general", "issue": "Could not parse issues", "severity": "medium", "suggestion": "Review manually"}]
        
        state["quality_issues"] = issues
        state["messages"].append(f"Issues Identified: {len(issues)} issues found")
        
        print("\n" + "="*60)
        print("QUALITY ISSUES IDENTIFIED")
        print("="*60)
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. Column: {issue.get('column', 'N/A')}")
            print(f"   Issue: {issue.get('issue', 'N/A')}")
            print(f"   Severity: {issue.get('severity', 'N/A')}")
        
        return state
    
    def create_cleaning_plan(self, state: AgentState) -> AgentState:
        """Create a cleaning plan based on identified issues"""
        issues = state["quality_issues"]
        
        prompt = f"""
        Based on these data quality issues, create a step-by-step cleaning plan:
        
        Issues:
        {json.dumps(issues, indent=2)}
        
        Create a prioritized action plan with specific steps. For each action, specify:
        1. Priority (1-5, 1 being highest)
        2. Column(s) affected
        3. What operation to perform
        4. Expected outcome
        
        Be specific and actionable. Format as a clear, numbered list.
        """
        
        response = self.llm.invoke(prompt)
        cleaning_plan = response.content
        
        state["cleaning_plan"] = cleaning_plan
        state["messages"].append("Cleaning plan created")
        
        print("\n" + "="*60)
        print("CLEANING PLAN")
        print("="*60)
        print(cleaning_plan)
        
        return state
    
    def execute_cleaning(self, state: AgentState) -> AgentState:
        """Execute the cleaning operations"""
        df = state["dataframe"].copy()
        actions_taken = []
        
        print("\n" + "="*60)
        print("EXECUTING CLEANING OPERATIONS")
        print("="*60)
        
        # 1. Remove duplicates
        initial_rows = len(df)
        df = df.drop_duplicates()
        if len(df) < initial_rows:
            action = f"Removed {initial_rows - len(df)} duplicate rows"
            actions_taken.append(action)
            print(f"✓ {action}")
        
        # 2. Remove whitespace from ALL object columns
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            df[col] = df[col].astype(str).str.strip()
        if len(text_cols) > 0:
            actions_taken.append(f"Removed leading/trailing whitespace from {len(text_cols)} text columns")
            print("✓ Removed whitespace")
        
        # 3. Replace common null strings with NaN
        null_strings = ['None', 'none', 'NONE', 'null', 'NULL', 'nan', 'NaN', '', ' ']
        df = df.replace(null_strings, pd.NA)
        actions_taken.append("Replaced null strings with NaN")
        print("✓ Replaced null strings with NaN")
        
        # DYNAMIC COLUMN CLEANING - Handle different column naming patterns
        column_mapping = {
            'age': ['age', 'Age', 'AGE'],
            'gender': ['gender', 'Gender', 'GENDER'], 
            'department': ['department', 'Department', 'DEPARTMENT'],
            'attendance_percent': ['attendance_percent', 'attendance', 'Attendance', 'Attendance (%)', 'ATTENDANCE', 'Attendance_Percent'],
            'assignments_submitted': ['assignments_submitted', 'assignments', 'Assignments', 'Assignments_Submitted', 'ASSIGNMENTS'],
            'final_exam_score': ['final_exam_score', 'final_score', 'Final_Exam_Score', 'exam_score', 'Final_Score', 'FINAL_SCORE'],
            'graduated': ['graduated', 'Graduated', 'GRADUATED'],
            'gpa': ['gpa', 'GPA', 'Gpa']
        }
        
        # Find which columns actually exist in the dataframe
        actual_columns = {}
        for standard_name, possible_names in column_mapping.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    actual_columns[standard_name] = possible_name
                    break
        
        print(f"🔍 Found columns to clean: {actual_columns}")
        
        # AGE COLUMN
        if 'age' in actual_columns:
            age_col = actual_columns['age']
            # Convert word numbers to digits
            age_mapping = {
                'twenty': '20', 'twentyone': '21', 'twentytwo': '22', 'twentythree': '23',
                'twentyfour': '24', 'twentyfive': '25', 'eighteen': '18', 'nineteen': '19',
                'thirty': '30', 'thirtyone': '31', 'thirtytwo': '32'
            }
            df[age_col] = df[age_col].replace(age_mapping)
            # Convert to numeric
            df[age_col] = pd.to_numeric(df[age_col], errors='coerce')
            median_age = df[age_col].median()
            df[age_col] = df[age_col].fillna(median_age)
            df[age_col] = df[age_col].astype(int)
            actions_taken.append(f"Cleaned '{age_col}' column (filled with median={median_age:.0f})")
            print(f"✓ Fixed {age_col} column (median={median_age:.0f})")
        
        # GENDER COLUMN  
        if 'gender' in actual_columns:
            gender_col = actual_columns['gender']
            gender_mapping = {
                'm': 'Male', 'M': 'Male', 'male': 'Male', 'MALE': 'Male',
                'f': 'Female', 'F': 'Female', 'female': 'Female', 'FEMALE': 'Female',
                'other': 'Other', 'Other': 'Other', 'OTHER': 'Other'
            }
            df[gender_col] = df[gender_col].replace(gender_mapping)
            mode_gender = df[gender_col].mode()
            if len(mode_gender) > 0:
                df[gender_col] = df[gender_col].fillna(mode_gender[0])
                actions_taken.append(f"Standardized '{gender_col}' values (filled with mode='{mode_gender[0]}')")
                print(f"✓ Standardized {gender_col} (mode={mode_gender[0]})")
        
        # DEPARTMENT COLUMN
        if 'department' in actual_columns:
            dept_col = actual_columns['department']
            dept_mapping = {
                'comp sci': 'Computer Science', 'compsci': 'Computer Science', 'cs': 'Computer Science',
                'bio': 'Biology', 'math': 'Mathematics', 'econ': 'Economics',
                'physics': 'Physics', 'chem': 'Chemistry', 'chemistry': 'Chemistry',
                'eng': 'Engineering', 'comp': 'Computer Science', 'biol': 'Biology'
            }
            df[dept_col] = df[dept_col].str.title()
            df[dept_col] = df[dept_col].replace(dept_mapping)
            mode_dept = df[dept_col].mode()
            if len(mode_dept) > 0:
                df[dept_col] = df[dept_col].fillna(mode_dept[0])
                actions_taken.append(f"Standardized '{dept_col}' values (filled with mode='{mode_dept[0]}')")
                print(f"✓ Standardized {dept_col} (mode={mode_dept[0]})")
        
        # ATTENDANCE PERCENT COLUMN
        if 'attendance_percent' in actual_columns:
            attend_col = actual_columns['attendance_percent']
            df[attend_col] = pd.to_numeric(df[attend_col], errors='coerce')
            # Cap at 100% and floor at 0%
            over_100 = (df[attend_col] > 100).sum()
            under_0 = (df[attend_col] < 0).sum()
            df[attend_col] = df[attend_col].clip(upper=100, lower=0)
            median_attendance = df[attend_col].median()
            df[attend_col] = df[attend_col].fillna(median_attendance)
            actions_taken.append(f"Fixed '{attend_col}' (capped {over_100} values at 100, filled with median={median_attendance:.1f})")
            print(f"✓ Fixed {attend_col} (capped at 100, median={median_attendance:.1f})")
        
        # ASSIGNMENTS SUBMITTED COLUMN
        if 'assignments_submitted' in actual_columns:
            assign_col = actual_columns['assignments_submitted']
            assignment_mapping = {
                'ten': '10', 'nine': '9', 'eight': '8', 'seven': '7', 'six': '6', 
                'five': '5', 'four': '4', 'three': '3', 'two': '2', 'one': '1', 'zero': '0',
                'eleven': '11', 'twelve': '12', 'thirteen': '13', 'fourteen': '14', 'fifteen': '15'
            }
            df[assign_col] = df[assign_col].replace(assignment_mapping)
            df[assign_col] = pd.to_numeric(df[assign_col], errors='coerce')
            median_assignments = df[assign_col].median()
            df[assign_col] = df[assign_col].fillna(median_assignments)
            df[assign_col] = df[assign_col].astype(int)
            actions_taken.append(f"Fixed '{assign_col}' (filled with median={median_assignments:.0f})")
            print(f"✓ Fixed {assign_col} (median={median_assignments:.0f})")
        
        # FINAL EXAM SCORE COLUMN
        if 'final_exam_score' in actual_columns:
            score_col = actual_columns['final_exam_score']
            df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
            df[score_col] = df[score_col].clip(lower=0, upper=100)
            median_score = df[score_col].median()
            df[score_col] = df[score_col].fillna(median_score)
            df[score_col] = df[score_col].astype(int)
            actions_taken.append(f"Fixed '{score_col}' (filled with median={median_score:.0f})")
            print(f"✓ Fixed {score_col} (median={median_score:.0f})")
        
        # GRADUATED COLUMN
        if 'graduated' in actual_columns:
            grad_col = actual_columns['graduated']
            grad_mapping = {
                'yes': 'Yes', 'YES': 'Yes', 'y': 'Yes', 'Y': 'Yes',
                'no': 'No', 'NO': 'No', 'n': 'No', 'N': 'No',
                'true': 'Yes', 'false': 'No', 'True': 'Yes', 'False': 'No'
            }
            df[grad_col] = df[grad_col].replace(grad_mapping)
            mode_grad = df[grad_col].mode()
            if len(mode_grad) > 0:
                df[grad_col] = df[grad_col].fillna(mode_grad[0])
                actions_taken.append(f"Standardized '{grad_col}' values (filled with mode='{mode_grad[0]}')")
                print(f"✓ Standardized {grad_col} (mode={mode_grad[0]})")
        
        # GPA COLUMN
        if 'gpa' in actual_columns:
            gpa_col = actual_columns['gpa']
            df[gpa_col] = pd.to_numeric(df[gpa_col], errors='coerce')
            df[gpa_col] = df[gpa_col].clip(lower=0.0, upper=4.0)
            median_gpa = df[gpa_col].median()
            df[gpa_col] = df[gpa_col].fillna(median_gpa)
            actions_taken.append(f"Fixed '{gpa_col}' (capped at 4.0, filled with median={median_gpa:.2f})")
            print(f"✓ Fixed {gpa_col} (capped at 4.0, median={median_gpa:.2f})")
        
        # Handle missing values for any remaining numeric columns
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            if df[col].isnull().sum() > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                actions_taken.append(f"Filled missing values in '{col}' with median={median_val:.2f}")
                print(f"✓ Filled missing values in {col}")
        
        # Handle missing values for categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if df[col].isnull().sum() > 0:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])
                    actions_taken.append(f"Filled missing values in '{col}' with mode='{mode_val[0]}'")
                    print(f"✓ Filled missing values in {col}")
        
        # CRITICAL FIX: Update both cleaned_dataframe AND dataframe in state
        state["cleaned_dataframe"] = df
        state["dataframe"] = df  # Update the main dataframe too!
        state["cleaning_actions"] = actions_taken
        state["messages"].append(f"Executed {len(actions_taken)} cleaning actions")
        
        return state
    
    def validate_results(self, state: AgentState) -> AgentState:
        """Validate the cleaning results"""
        # Use the original state to compare with cleaned data
        original_df = state.get("original_dataframe", state["dataframe"])
        cleaned_df = state["cleaned_dataframe"]
        
        validation_report = {
            "original_shape": original_df.shape,
            "cleaned_shape": cleaned_df.shape,
            "rows_removed": original_df.shape[0] - cleaned_df.shape[0],
            "missing_values_before": original_df.isnull().sum().sum(),
            "missing_values_after": cleaned_df.isnull().sum().sum(),
            "duplicates_before": original_df.duplicated().sum(),
            "duplicates_after": cleaned_df.duplicated().sum()
        }
        
        print("\n" + "="*60)
        print("VALIDATION REPORT")
        print("="*60)
        print(f"Original Shape: {validation_report['original_shape']}")
        print(f"Cleaned Shape: {validation_report['cleaned_shape']}")
        print(f"Rows Removed: {validation_report['rows_removed']}")
        print(f"Missing Values: {validation_report['missing_values_before']} → {validation_report['missing_values_after']}")
        print(f"Duplicates: {validation_report['duplicates_before']} → {validation_report['duplicates_after']}")
        
        state["messages"].append("Validation complete")
        
        return state
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main method to clean data using the AI agent
        
        Args:
            df: pandas.DataFrame to clean
            
        Returns:
            pandas.DataFrame: Cleaned data
        """
        initial_state = {
            "dataframe": df,
            "original_dataframe": df.copy(),  # Keep original for comparison
            "data_summary": "",
            "quality_issues": [],
            "cleaning_plan": "",
            "cleaning_actions": [],
            "cleaned_dataframe": None,
            "messages": [],
            "iteration": 0
        }
        
        print("\n" + "="*60)
        print("AI AGENT DATA CLEANING STARTED (Google Gemini)")
        print("="*60)
        print(f"Initial data shape: {df.shape}")
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            # CRITICAL FIX: Return cleaned_dataframe if available, otherwise the updated dataframe
            cleaned_df = final_state.get("cleaned_dataframe")
            
            if cleaned_df is None:
                print("Warning: No cleaned_dataframe found in final state, checking dataframe...")
                cleaned_df = final_state.get("dataframe")
            
            if cleaned_df is None:
                print("Error: No dataframe found in final state, returning original")
                return df
            
            print(f"Final data shape: {cleaned_df.shape}")
            
            print("\n" + "="*60)
            print("CLEANING ACTIONS SUMMARY")
            print("="*60)
            if final_state.get("cleaning_actions"):
                for i, action in enumerate(final_state["cleaning_actions"], 1):
                    print(f"{i}. {action}")
            else:
                print("No cleaning actions were recorded")
            
            print(f"\nCleaning completed: {df.shape} → {cleaned_df.shape}")
            print("AI AGENT DATA CLEANING COMPLETED ✓")
            print("="*60)
            
            return cleaned_df
            
        except Exception as e:
            print(f"Error during AI cleaning: {e}")
            print("Returning original dataframe due to error")
            return df