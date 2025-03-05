import streamlit as st
from datetime import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta
import time

class ProjectForm:
    def __init__(self, edit_mode=False, project_data=None):
        self.edit_mode = edit_mode
        self.project_data = project_data

    def on_date_change(self):
        """Callback for date changes"""
        start = st.session_state.start_date_input
        end = st.session_state.end_date_input

        if start and end:
            diff = relativedelta(end, start)
            total_months = diff.years * 12 + diff.months

            if diff.days > 0:
                total_months += 1

            st.session_state.months = max(1, total_months)

    def render(self):
        # Add CSS for styling
        st.markdown("""
            <style>
            .submit-button-container {
                display: flex;
                justify-content: center;
                margin-top: 20px;
            }
            .project-success {
                background-color: #4CAF50;
                color: white;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .project-success-header {
                font-size: 20px;
                margin-bottom: 10px;
            }
            .project-success-details {
                font-size: 14px;
                margin-bottom: 5px;
            }
            /* Form field highlighting */
            .form-field-container input, 
            .form-field-container select,
            .form-field-container .stDateInput > div > div > input {
                background-color: rgba(200, 230, 255, 0.2) !important;
                border: 1px solid #dfe1e6 !important;
                border-radius: 4px !important;
                transition: all 0.3s !important;
            }
            .form-field-container input:focus, 
            .form-field-container select:focus,
            .form-field-container .stDateInput > div > div > input:focus {
                background-color: rgba(200, 230, 255, 0.4) !important;
                border: 1px solid #4a90e2 !important;
                box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
            }
            /* Direct styling for Streamlit components */
            .stTextInput > div > div > input, 
            .stNumberInput > div > div > input,
            .stDateInput > div > div > input {
                background-color: rgba(200, 230, 255, 0.2) !important;
                transition: background-color 0.3s, border 0.3s !important;
            }

            .stTextInput > div > div > input:focus, 
            .stNumberInput > div > div > input:focus,
            .stDateInput > div > div > input:focus {
                background-color: rgba(200, 230, 255, 0.4) !important;
                border: 1px solid #4a90e2 !important;
                box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
            }

            /* Style select boxes */
            .stSelectbox div[data-baseweb="select"] {
                background-color: rgba(200, 230, 255, 0.2) !important;
            }

            .stSelectbox div[data-baseweb="select"]:focus-within {
                background-color: rgba(200, 230, 255, 0.4) !important;
                border: 1px solid #4a90e2 !important;
            }
            </style>
        """, unsafe_allow_html=True)

        if self.edit_mode:
            # Project Details Form
            with st.form("project_details_form"):
                with st.container():
                    st.markdown('<div class="form-field-container">', unsafe_allow_html=True)
                    project_id = st.text_input(
                        "ID",
                        value=self.project_data['ID'],
                        disabled=True
                    )
                    name = st.text_input(
                        "Name",
                        value=self.project_data['Name']
                    )

                    iso = st.text_input(
                        "ISO",
                        value=self.project_data['ISO']
                    )
                    voltage = st.number_input(
                        "Voltage (kV)",
                        value=float(self.project_data['Voltage']),
                        step=0.1
                    )
                    capacity = st.number_input(
                        "Capacity (MW)",
                        value=float(self.project_data['Capacity']),
                        step=0.1
                    )
                    duration = st.number_input(
                        "Duration (hr)",
                        value=float(self.project_data['Duration']),
                        step=0.1
                    )
                    target_cod = st.date_input(
                        "Target COD",
                        value=pd.to_datetime(self.project_data['Target COD']).date()
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

                # Create columns for better button placement
                _, button_col, _ = st.columns([1, 2, 1])
                with button_col:
                    project_submitted = st.form_submit_button("Update Project", use_container_width=True)

                if project_submitted:
                    if all([project_id, name, iso, voltage, capacity, duration, target_cod]):
                        project_details = {
                            'ID': project_id,
                            'Name': name,
                            'ISO': iso,
                            'Voltage': voltage,
                            'Capacity': capacity,
                            'Duration': duration,
                            'Target COD': target_cod
                        }
                        st.session_state.data_manager.update_project(project_details['ID'], project_details)
                        st.success("Project updated successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all project fields.")

            # Items Management
            st.subheader("Project Items")
            items_df = st.session_state.data_manager.get_project_items(self.project_data['ID'])

            if not items_df.empty:
                st.dataframe(items_df[['Item Name', 'Start Date', 'End Date', 'Months']])

            # Initialize months in session state
            if 'months' not in st.session_state:
                st.session_state.months = 1

            # Create a container for better spacing
            with st.container():
                st.markdown("### Add New Item")
                st.markdown("---")

                # Date selection section
                st.markdown("#### Timeline Details")
                date_cols = st.columns([1, 1])

                with date_cols[0]:
                    start_date = st.date_input(
                        "Start Date",
                        value=datetime.now().date(),
                        key='start_date_input'
                    )

                with date_cols[1]:
                    end_date = st.date_input(
                        "End Date",
                        value=datetime.now().date(),
                        key='end_date_input'
                    )

                # Calculate months
                if start_date and end_date:
                    diff = relativedelta(end_date, start_date)
                    total_months = diff.years * 12 + diff.months
                    if diff.days > 0:
                        total_months += 1
                    months = max(1, total_months)
                    # Debug check for Months consistency
                    if months > 120:
                        st.warning(f"Long duration detected ({months} months). This is allowed but may affect visualization.")
                else:
                    months = 1

                st.markdown("#### Duration")
                st.number_input(
                    "Number of Months",
                    value=months,
                    min_value=1,
                    disabled=True,
                    help="Automatically calculated based on start and end dates"
                )

                # Form for item details
                st.markdown("#### Item Details")
                with st.form("add_item_form"):
                    with st.container():
                        st.markdown('<div class="form-field-container">', unsafe_allow_html=True)
                        item_name = st.text_input("Item Name", placeholder="Enter item name")
                        team = st.selectbox("Team", options=['Procurement', 'Construction', 'Development', 'Interconnection'], index=0)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown("")  # Add some spacing
                    submitted = st.form_submit_button("Add Item")

                if submitted:
                    if all([item_name, start_date, end_date]):
                        # Calculate months on submission
                        diff = relativedelta(end_date, start_date)
                        total_months = diff.years * 12 + diff.months
                        if diff.days > 0:
                            total_months += 1
                        months = max(1, total_months)

                        item_data = {
                            'Item Name': item_name,
                            'Start Date': start_date.strftime('%Y-%m-%d'),  # Convert to string
                            'End Date': end_date.strftime('%Y-%m-%d'),      # Convert to string
                            'Months': months,
                            'Team': team  # Explicitly include Team
                        }
                        st.session_state.data_manager.add_project_item(self.project_data['ID'], item_data)
                        st.success("Item added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all item fields.")

        else:
            # Create placeholder for success message outside the form
            success_placeholder = st.empty()

            with st.form("project_form"):
                with st.container():
                    st.markdown('<div class="form-field-container">', unsafe_allow_html=True)
                    project_id = st.text_input(
                        "ID",
                        value=self.project_data['ID'] if self.project_data is not None else "",
                        disabled=self.edit_mode
                    )

                    name = st.text_input(
                        "Name",
                        value=self.project_data['Name'] if self.project_data is not None else ""
                    )

                    iso = st.text_input(
                        "ISO",
                        value=self.project_data['ISO'] if self.project_data is not None else ""
                    )

                    voltage = st.number_input(
                        "Voltage (kV)",
                        value=float(self.project_data['Voltage']) if self.project_data is not None else 0.0,
                        step=0.1
                    )

                    capacity = st.number_input(
                        "Capacity (MW)",
                        value=float(self.project_data['Capacity']) if self.project_data is not None else 0.0,
                        step=0.1
                    )

                    duration = st.number_input(
                        "Duration (hr)",
                        value=float(self.project_data['Duration']) if self.project_data is not None else 0.0,
                        step=0.1
                    )

                    target_cod = st.date_input(
                        "Target COD",
                        value=pd.to_datetime(self.project_data['Target COD']).date() if self.project_data is not None else datetime.now().date()
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

                # Add a divider before submit
                st.markdown("---")

                # Create columns for better button placement
                _, button_col, _ = st.columns([1, 2, 1])
                with button_col:
                    submitted = st.form_submit_button("📋 Submit Project", use_container_width=True)

            if submitted:
                if all([project_id, name, iso, voltage, capacity, duration, target_cod]):
                    project_data = {
                        'ID': project_id,
                        'Name': name,
                        'ISO': iso,
                        'Voltage': voltage,
                        'Capacity': capacity,
                        'Duration': duration,
                        'Target COD': target_cod
                    }

                    # Show spinner during save
                    with st.spinner("Saving project..."):
                        time.sleep(0.5)  # Short delay for better UX

                        if self.edit_mode:
                            st.session_state.data_manager.update_project(project_id, project_data)
                            action = "updated"
                        else:
                            st.session_state.data_manager.add_project(project_data)
                            action = "added"

                        # Show detailed success message
                        success_placeholder.markdown(f"""
                            <div class="project-success">
                                <div class="project-success-header">✅ Project successfully {action}!</div>
                                <div class="project-success-details"><b>ID:</b> {project_id}</div>
                                <div class="project-success-details"><b>Name:</b> {name}</div>
                                <div class="project-success-details"><b>Target COD:</b> {target_cod.strftime('%Y-%m-%d')}</div>
                                <div class="project-success-details"><b>ISO:</b> {iso} | <b>Voltage:</b> {voltage} kV | <b>Capacity:</b> {capacity} MW</div>
                            </div>
                        """, unsafe_allow_html=True)

                        # Automatically refresh the page after a short delay
                        time.sleep(1.5)
                        st.rerun()  # This will clear all form fields
                else:
                    st.error("Please fill in all required fields.")