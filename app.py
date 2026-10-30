import os
import shutil
import datetime
import json
import io
import pandas as pd
import streamlit as st
import ollama

# --- SITE CONFIGURATION ---
st.set_page_config(page_title="Autonomous Excel Modifier", layout="wide")
st.title("🤖 Autonomous Excel Modifier Sandbox (Local Offline Mode)")

# Setup safe systemic directory paths
BACKUP_DIR = "excel_backups"
LOG_FILE_PATH = "excel_agent_audit.json"
os.makedirs(BACKUP_DIR, exist_ok=True)

# --- CORE UTILITY FUNCTIONS ---
def generate_transformation_logic(user_prompt: str, df_head_str: str, sheet_name: str) -> tuple:
    """Uses a locally hosted Llama model with strict guidelines to prevent data type execution bugs."""
    system_instruction = (
        f"You are an expert Python data scientist working with a pandas DataFrame named 'df' "
        f"representing the sheet '{sheet_name}'.\n\n"
        f"DataFrame Preview:\n{df_head_str}\n\n"
        "CRITICAL ARCHITECTURAL RULES:\n"
        "1. The 1st row of the Excel sheet has ALREADY been automatically parsed as the DataFrame column headers.\n"
        "2. Do NOT change, rename, overwrite, or mutate the column headers array unless explicitly told. Start processing from row 2 downward.\n"
        "3. CRITICAL TYPE PROTECTION: If the user request requires string transformations (like splitting, stripping, or slicing a cell value), "
        "   you MUST protect your code by casting values to string or applying type safety (e.g., use `.astype(str)` or check if values are null). "
        "   Never call `.split()` directly on non-string columns as numbers/NaN will throw an execution crash error.\n"
        "4. You MUST respond with exactly two distinct sections separated by a unique split tag '|||SPLIT_LOGIC|||'.\n"
        "   - Section 1: An auto-corrected, grammatically pristine human explanation of the prompt's intended change.\n"
        "   - Section 2: Pure, raw executable Python code utilizing 'df' to make the data modification safely.\n"
        "5. Do not use markdown wrappers (like ```python) or extra conversational chatter.\n"
        "6. SECURITY COMPLIANCE RULE: You are STRICTLY forbidden from writing commands that import or use 'os', 'shutil', 'sys', or 'subprocess' modules. "
        "Only generate safe data-science DataFrame operations (like math, text edits, or row sorting) using pandas.\n"
        "7. Your entire response must look exactly like this template layout:\n\n"
        "Auto-corrected prompt: Calculate the net tax at 18% of the Unit Price column and store it in a new column.\n"
        "|||SPLIT_LOGIC|||\n"
        "df['Net Tax'] = df['Unit Price'] * 0.18"
    )
    
    # Run the transaction completely offline via Ollama local runtime
    response = ollama.chat(
        model='llama3.2',
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        options={"temperature": 0.1}
    )
    
    raw_response = response['message']['content'].strip()

    # Parse out the auto-corrected prompt explanation and code blocks
    if "|||SPLIT_LOGIC|||" in raw_response:
        corrected_explanation, python_code = raw_response.split("|||SPLIT_LOGIC|||", 1)
    else:
        corrected_explanation = f"Auto-corrected: Process adjustments for criteria: {user_prompt}"
        python_code = raw_response

    # Clean any formatting noise out of code segments safely
    clean_code = python_code.strip().replace("```python", "").replace("```", "")
    return corrected_explanation.strip(), clean_code.strip()

def append_to_audit_logs(filename: str, original_prompt: str, corrected_prompt: str, python_code: str, backup_path: str):
    """Saves structured telemetry logs capturing raw input, auto-corrected prompts, and code states."""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "original_file": filename,
        "backup_stored_at": backup_path,
        "raw_user_input_prompt": original_prompt,
        "system_auto_corrected_prompt": corrected_prompt,
        "executed_backend_python_logic": python_code
    }
    
    logs = []
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
            
    logs.append(log_entry)
    with open(LOG_FILE_PATH, 'w') as f:
        json.dump(logs, f, indent=4)

# --- APPLICATION UI PIPELINE ---
uploaded_file = st.file_uploader("📥 Upload your target Excel workbook", type=["xlsx", "xls"])

if uploaded_file is not None:
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names
    
    col1, col2 = st.columns(2)
    with col1:
        selected_sheet = st.selectbox("🎯 Target Sheet Name", sheet_names)
    
    all_sheets_data = {sheet: excel_file.parse(sheet) for sheet in sheet_names}
    df_active = all_sheets_data[selected_sheet].copy()
    
    st.subheader(f"📊 Preview: Active Sheet [{selected_sheet}]")
    st.caption("💡 Row 1 contains column headers. All mutations begin on data rows from row 2 downward.")
    st.dataframe(df_active.head(5), use_container_width=True)
    
    user_prompt = st.text_area("✍️ Enter your update prompt or complex logic criteria:")
    
    if st.button("🚀 Process & Validate Changes"):
        if not user_prompt.strip():
            st.warning("Please provide a prompt command instruction first.")
        else:
            with st.spinner("Local model processing..."):
                try:
                    df_head_str = df_active.head(3).to_string()
                    corrected_text, python_code = generate_transformation_logic(user_prompt, df_head_str, selected_sheet)
                    
                    st.session_state['corrected_prompt_text'] = corrected_text
                    st.session_state['generated_code'] = python_code
                    st.session_state['original_prompt'] = user_prompt
                    
                    # Sandbox execution preview
                    local_env = {'df': df_active.copy()}
                    exec(python_code, {}, local_env)
                    df_transformed = local_env['df']
                    
                    st.session_state['transformed_df'] = df_transformed
                    st.session_state['all_sheets_updated'] = all_sheets_data.copy()
                    st.session_state['all_sheets_updated'][selected_sheet] = df_transformed
                    
                except Exception as error_msg:
                    st.error(f"❌ Failed to parse code logic. Error details: {str(error_msg)}")
                    
    # Validation Stage & Execution Preview Dashboard
    if 'transformed_df' in st.session_state:
        st.markdown("---")
        st.success(f"✏️ **Agent Auto-Corrected Prompt Intention:** {st.session_state['corrected_prompt_text']}")
        
        st.subheader("🔍 Verification Sandbox View (No files modified yet)")
        c_left, c_right = st.columns(2)
        with c_left:
            st.caption("⏮️ Original Data State")
            st.dataframe(df_active.head(5), use_container_width=True)
        with c_right:
            st.caption("⏭️ Sandboxed Transformation Preview")
            st.dataframe(st.session_state['transformed_df'].head(5), use_container_width=True)
            
        st.info("💡 Review the calculation changes above. If correct, verify and commit using the button below.")
        
        # Final Confirmation Gate
        if st.button("✅ Give Go-Ahead (Commit & Finalize Updates)"):
            try:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name, ext = os.path.splitext(uploaded_file.name)
                backup_filename = f"{base_name}_bak_{timestamp}{ext}"
                backup_full_path = os.path.join(BACKUP_DIR, backup_filename)
                
                with pd.ExcelWriter(backup_full_path, engine='openpyxl') as writer:
                    for sheet, df_sheet in all_sheets_data.items():
                        df_sheet.to_excel(writer, sheet_name=sheet, index=False)
                        
                append_to_audit_logs(
                    filename=uploaded_file.name,
                    original_prompt=st.session_state['original_prompt'],
                    corrected_prompt=st.session_state['corrected_prompt_text'],
                    python_code=st.session_state['generated_code'],
                    backup_path=backup_full_path
                )
                
                output_buffer = io.BytesIO()
                with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                    for sheet, df_sheet in st.session_state['all_sheets_updated'].items():
                        df_sheet.to_excel(writer, sheet_name=sheet, index=False)
                
                st.session_state['final_download_ready'] = output_buffer.getvalue()
                
                st.balloons()
                st.success("🎉 Excel dataset processing complete! Your clean workbook download is ready below.")
                
            except Exception as e:
                st.error(f"Execution Error during commit phase: {str(e)}")

        if 'final_download_ready' in st.session_state:
            st.download_button(
                label="💾 Download Modified Excel File",
                data=st.session_state['final_download_ready'],
                file_name=f"updated_{uploaded_file.name}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
