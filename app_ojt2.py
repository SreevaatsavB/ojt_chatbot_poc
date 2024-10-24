import streamlit as st
import os
import re
from datetime import datetime
import pandas as pd
import csv

# Initialize session states
if 'show_flowchart' not in st.session_state:
    st.session_state.show_flowchart = False
if 'current_selections' not in st.session_state:
    st.session_state.current_selections = {
        'payor': None,
        'code': None,
        'reason': None
    }
if 'feedback_given' not in st.session_state:
    st.session_state.feedback_given = False

def reset_all_states():
    # Reset all session states to their default values
    st.session_state.show_flowchart = False
    st.session_state.current_selections = {
        'payor': None,
        'code': None,
        'reason': None
    }
    st.session_state.feedback_given = False
    # Reset selectbox values
    if 'payor_select' in st.session_state:
        del st.session_state.payor_select
    if 'code_select' in st.session_state:
        del st.session_state.code_select
    if 'reason_select' in st.session_state:
        del st.session_state.reason_select
    st.rerun()

def get_saved_flowcharts():
    flowchart_dir = 'flowcharts'
    if not os.path.exists(flowchart_dir):
        return []
    
    flowcharts = []
    for filename in os.listdir(flowchart_dir):
        if filename.endswith('.txt'):
            match = re.match(r'(.+)_(.+)_(.+)\.txt', filename)
            if match:
                payor_name, denial_code, denial_reason = match.groups()
                flowcharts.append({
                    'payor_name': payor_name,
                    'denial_code': denial_code,
                    'denial_reason': denial_reason,
                    'filename': filename
                })
    
    return flowcharts

def read_flowchart(filename):
    flowchart_dir = 'flowcharts'
    with open(os.path.join(flowchart_dir, filename), 'r') as file:
        return file.read()

def log_user_selection(payor_name, denial_code, denial_reason):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file = 'user_selections.csv'
    
    # Create file with headers if it doesn't exist
    if not os.path.exists(log_file):
        with open(log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Payor Name', 'Denial Code', 'Denial Reason'])
    
    # Append the new log entry
    with open(log_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, payor_name, denial_code, denial_reason])

def log_feedback(payor_name, denial_code, denial_reason, feedback):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    feedback_file = 'feedback_log.csv'
    
    # Create file with headers if it doesn't exist
    if not os.path.exists(feedback_file):
        with open(feedback_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Payor Name', 'Denial Code', 'Denial Reason', 'Feedback'])
    
    # Append the new feedback entry
    with open(feedback_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, payor_name, denial_code, denial_reason, feedback])

def on_view_flowchart_click():
    st.session_state.show_flowchart = True
    st.session_state.feedback_given = False
    log_user_selection(
        st.session_state.current_selections['payor'],
        st.session_state.current_selections['code'],
        st.session_state.current_selections['reason']
    )

def on_feedback_click(feedback_type):
    if not st.session_state.feedback_given:
        log_feedback(
            st.session_state.current_selections['payor'],
            st.session_state.current_selections['code'],
            st.session_state.current_selections['reason'],
            feedback_type
        )
        st.session_state.feedback_given = True
        return True
    return False

def on_payor_change():
    st.session_state.show_flowchart = False
    st.session_state.feedback_given = False

st.title('Virtual Denial Coach')

flowcharts = get_saved_flowcharts()

if not flowcharts:
    st.write("No saved flowcharts found.")
else:
    # Get unique payor names
    payor_names = sorted(set(f['payor_name'] for f in flowcharts))
    selected_payor = st.selectbox('Select Payor Name', payor_names, 
                                 on_change=on_payor_change,
                                 key='payor_select')
    st.session_state.current_selections['payor'] = selected_payor

    # Filter denial codes for selected payor
    denial_codes = sorted(set(f['denial_code'] for f in flowcharts 
                            if f['payor_name'] == selected_payor))
    selected_denial_code = st.selectbox('Select Denial Code', denial_codes,
                                      on_change=on_payor_change,
                                      key='code_select')
    st.session_state.current_selections['code'] = selected_denial_code

    # Filter denial reasons for selected payor and denial code
    denial_reasons = sorted(set(f['denial_reason'] for f in flowcharts 
                                if f['payor_name'] == selected_payor 
                                and f['denial_code'] == selected_denial_code))
    selected_denial_reason = st.selectbox('Select Reason', denial_reasons,
                                        on_change=on_payor_change,
                                        key='reason_select')
    st.session_state.current_selections['reason'] = selected_denial_reason

    # View Flowchart button
    if st.button('View Checklist', on_click=on_view_flowchart_click):
        pass


    # Show flowchart and feedback section if button was clicked
    if st.session_state.show_flowchart:
        selected_flowchart = next((f for f in flowcharts 
                               if f['payor_name'] == selected_payor 
                               and f['denial_code'] == selected_denial_code
                               and f['denial_reason'] == selected_denial_reason), None)

        if selected_flowchart:
            # Display the flowchart
            flowchart_content = read_flowchart(selected_flowchart['filename'])
            st.markdown("## Checklist")
            st.markdown(flowchart_content)
            
            # Feedback section
            st.markdown("### Was this Checklist helpful?")
            
            # Only show feedback buttons if feedback hasn't been given
            if not st.session_state.feedback_given:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button('👍 Helpful'):
                        if on_feedback_click('helpful'):
                            st.success('Thank you for your feedback!')
                
                with col2:
                    if st.button('👎 Not Helpful'):
                        if on_feedback_click('not helpful'):
                            st.error('Thank you for your feedback! We will work on improving this.')
            else:
                st.info('Thank you for your feedback!')

    # Add Get New Flowchart button at the top
    if st.button('🔄 Get New Checklist', type='primary'):
        reset_all_states()

    # # Add a section to view logs if needed (can be commented out in production)
    # if st.checkbox('Show Logs'):
    #     st.markdown("### User Selection Logs")
    #     if os.path.exists('user_selections.csv'):
    #         selections_df = pd.read_csv('user_selections.csv')
    #         st.dataframe(selections_df)
        
    #     st.markdown("### Feedback Logs")
    #     if os.path.exists('feedback_log.csv'):
    #         feedback_df = pd.read_csv('feedback_log.csv')
    #         st.dataframe(feedback_df)
