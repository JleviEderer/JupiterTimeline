import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time as time_module
import copy
import os
import sys
import logging
from components.data_storage import get_data_manager
from components.timeline_viz import TimelineVisualizer
from components.forms import ProjectForm
from utils.helpers import load_css

# Set up logging for Replit environment - stdout only to avoid file permission issues
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('main_app')
logger.warning("Application starting - Replit deployment configuration")

# Health check - modify to match Replit's expectation
def main():
    # Page config must be the first Streamlit command
    st.set_page_config(
        page_title="Company XYZ",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    

  
    # Display deployment debug info if needed
    deployment_debug = False
    if deployment_debug:
        st.write(f"Current working directory: {os.getcwd()}")
        st.write(f"Files in directory: {os.listdir('.')}")
        st.write(f"Query parameters: {st.query_params.to_dict()}")

    # Initialize session state - more robust initialization with error handling
    try:
        if 'data_manager' not in st.session_state:
            st.session_state.data_manager = get_data_manager()
    except Exception as e:
        logger.error(f"Error initializing data manager: {str(e)}")
        st.error(f"Error initializing application data. Please check if data files exist and have correct permissions.")
        st.stop()

    # Try to load custom CSS with error handling
    try:
        load_css()
    except Exception as e:
        logger.warning(f"Could not load custom CSS: {str(e)}")

    # Header
    st.markdown("""
        <div class="header-container">
            <h1>Company XYZ</h1>
            <p class="subtitle">Project Management</p>
        </div>
    """, unsafe_allow_html=True)

    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Critical Path", "Add Project", "Edit Project"])

    with tab1:
        show_dashboard()  # Dashboard overview
    with tab2:
        show_critical_path()  # Project timeline view
    with tab3:
        show_project_form()
    with tab4:
        show_edit_project()

def show_edit_project():
    st.header("Edit Project")
    
    # Add custom styling for the dropdown container
    st.markdown("""
        <style>
        /* Style the container around the "Select Project to Edit" dropdown */
        [data-testid="stVerticalBlock"] > div:has([data-testid="stSelectbox"] label:contains("Select Project to Edit")) {
            background-color: rgba(200, 230, 255, 0.9);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(200, 230, 255, 0.5);
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Add error handling around data access
    try:
        data = st.session_state.data_manager.get_data()
        if data.empty:
            st.info("No projects available to edit.")
            return
    except Exception as e:
        logger.error(f"Error accessing project data: {str(e)}")
        st.error("Could not load project data. Please check your data files.")
        return

    # Create display options combining ID and Name
    project_options = [f"{row['ID']} - {row['Name']}" for _, row in data.iterrows()]
    selected_option = st.selectbox("Select Project to Edit", project_options)

    # Extract the ID from the selected option
    selected_id = selected_option.split(" - ")[0] if selected_option else None

    if selected_id:
        try:
            project_data = st.session_state.data_manager.get_project(selected_id)
        except Exception as e:
            logger.error(f"Error retrieving project {selected_id}: {str(e)}")
            st.error(f"Could not load project details. Please try again.")
            return

        # Add project header and delete button
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader(f"Editing: {project_data['Name']}")

        # Initialize delete confirmation state
        if f"delete_confirm_{selected_id}" not in st.session_state:
            st.session_state[f"delete_confirm_{selected_id}"] = False
        if f"show_delete_confirm_{selected_id}" not in st.session_state:
            st.session_state[f"show_delete_confirm_{selected_id}"] = False

        # Place delete button in the third column
        with col3:
            if st.button("🗑️ Delete Project", key=f"delete_btn_{selected_id}", type="secondary"):
                st.session_state[f"show_delete_confirm_{selected_id}"] = True

        # If delete was clicked, show confirmation
        if st.session_state[f"show_delete_confirm_{selected_id}"]:
            st.warning("Are you sure you want to delete this project? This action cannot be undone.")

            # Confirmation checkbox
            st.session_state[f"delete_confirm_{selected_id}"] = st.checkbox(
                "Yes, I want to delete this project", 
                key=f"confirm_delete_cb_{selected_id}"
            )

            # Confirm delete button
            if st.button(
                "Confirm Delete", 
                key=f"confirm_delete_btn_{selected_id}", 
                disabled=not st.session_state[f"delete_confirm_{selected_id}"],
                type="primary"
            ):
                try:
                    if st.session_state.data_manager.delete_project(selected_id):
                        st.success("Project deleted successfully!")
                        time_module.sleep(1)
                        st.session_state[f"show_delete_confirm_{selected_id}"] = False
                        st.session_state[f"delete_confirm_{selected_id}"] = False
                        st.rerun()
                    else:
                        st.error("Failed to delete project. Please try again.")
                except Exception as e:
                    logger.error(f"Error deleting project {selected_id}: {str(e)}")
                    st.error(f"Error deleting project: {str(e)}")

        # Custom CSS for styling
        st.markdown("""
            <style>
            .overview-container {
                padding: 1.5rem;
                background-color: #f8f9fa;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                border: 1px solid #dee2e6;
            }
            .items-section {
                padding: 2rem;
                background-color: #ffffff;
                border: 2px solid #4CAF50;
                border-radius: 0.5rem;
                margin: 1.5rem 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .edit-table {
                margin-top: 1rem;
            }
            /* Data editor styling */
            .stDataEditor {
                font-family: 'Inter', sans-serif;
            }
            .stDataEditor td[disabled="true"] {
                background-color: #f5f5f5 !important;
                color: #666 !important;
                font-style: italic !important;
            }
            .stDataEditor td:not([disabled="true"]) {
                background-color: rgba(200, 230, 255, 0.2) !important;
            }
            .stDataEditor td:not([disabled="true"]):hover {
                background-color: rgba(200, 230, 255, 0.4) !important;
                border: 1px solid #2196F3 !important;
            }
            .stDataEditor td:not([disabled="true"]):focus-within {
                background-color: rgba(200, 230, 255, 0.4) !important;
                border: 1px solid #4a90e2 !important;
                box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
            }
            .save-success {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                text-align: center;
                animation: fadeOut 5s forwards;
            }
            @keyframes fadeOut {
                0% { opacity: 1; }
                70% { opacity: 1; }
                100% { opacity: 0; }
            }
            .save-button {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
                margin: 20px 0;
                border: none;
                cursor: pointer;
                width: 100%;
                transition: background-color 0.3s;
            }
            .save-button:hover {
                background-color: #0b7dda;
            }
            /* Form input styling for Edit Project section */
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

            /* Style select boxes with more specific targeting */
            .stSelectbox div[data-baseweb="select"] {
                background-color: rgba(200, 230, 255, 0.2) !important;
                border: 1px solid #e6e6e6 !important;
            }

            .stSelectbox div[data-baseweb="select"]:focus-within,
            .stSelectbox div[data-baseweb="select"]:hover {
                background-color: rgba(200, 230, 255, 0.4) !important;
                border: 1px solid #4a90e2 !important;
                box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
            }
            
            /* Ensure the "Select Project to Edit" dropdown has the blue styling */
            #root > [data-testid="stAppViewContainer"] [data-testid="stVerticalBlock"] > [data-testid="stSelectbox"] div[data-baseweb="select"] {
                background-color: rgba(200, 230, 255, 0.2) !important;
                border: 1px solid #e6e6e6 !important;
            }
            
            #root > [data-testid="stAppViewContainer"] [data-testid="stVerticalBlock"] > [data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within,
            #root > [data-testid="stAppViewContainer"] [data-testid="stVerticalBlock"] > [data-testid="stSelectbox"] div[data-baseweb="select"]:hover {
                background-color: rgba(200, 230, 255, 0.4) !important;
                border: 1px solid #4a90e2 !important;
                box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Project Overview Section
        st.subheader("Project Overview")
        overview_cols = st.columns(6)
        with overview_cols[0]:
            st.markdown(f"**ID:** {project_data['ID']}")
        with overview_cols[1]:
            st.markdown(f"**Name:** {project_data['Name']}")
        with overview_cols[2]:
            st.markdown(f"**ISO:** {project_data['ISO']}")
        with overview_cols[3]:
            st.markdown(f"**Voltage:** {int(float(project_data['Voltage']))} kV")
        with overview_cols[4]:
            st.markdown(f"**Duration:** {float(project_data['Duration']):.2f} hr")
        with overview_cols[5]:
            st.markdown(f"**Target COD:** {project_data['Target COD'].strftime('%Y-%m-%d')}")

        # Add spacing
        st.markdown("---")

        # Update Project Overview Expander
        with st.expander("📝 Update Project Overview"):
            with st.form(key=f"project_overview_form_{selected_id}"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Name", value=project_data['Name'])
                    iso = st.text_input("ISO", value=project_data['ISO'])
                    voltage = st.number_input("Voltage (kV)", value=int(float(project_data['Voltage'])), step=1, format="%d")
                with col2:
                    capacity = st.number_input("Capacity (MW)", value=float(project_data['Capacity']), step=0.01, format="%.2f")
                    duration = st.number_input("Duration (hr)", value=float(project_data['Duration']), step=0.01, format="%.2f", min_value=0.00, max_value=None)
                    target_cod = st.date_input("Target COD", value=pd.to_datetime(project_data['Target COD']).date())

                if st.form_submit_button("Update Overview"):
                    try:
                        project_details = {
                            'ID': project_data['ID'],
                            'Name': name,
                            'ISO': iso,
                            'Voltage': voltage,
                            'Capacity': capacity,
                            'Duration': duration,
                            'Target COD': target_cod
                        }
                        st.session_state.data_manager.update_project(project_details['ID'], project_details)
                        st.success("Project overview updated successfully!")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error updating project overview: {str(e)}")
                        st.error(f"Error updating project: {str(e)}")

        # Add spacing
        st.markdown("---")

        # Project Items Management Section
        st.subheader("Project Items Management")

        # Get existing items with error handling
        try:
            items_df = st.session_state.data_manager.get_project_items(project_data['ID'])
        except Exception as e:
            logger.error(f"Error retrieving project items: {str(e)}")
            st.error("Could not load project items. Please try again later.")
            items_df = pd.DataFrame()  # Initialize empty DF in case of error

        # Initialize column configuration
        column_config = {
            "Item ID": st.column_config.TextColumn(
                "Item ID",
                width="small",
                disabled=True,
                help="🔒 Auto-generated ID (not editable)"
            ),
            "Team": st.column_config.SelectboxColumn(
                "Team",
                width="small",
                options=list(st.session_state.data_manager.get_team_colors().keys()),
                required=True,
                help="Team responsible for this item"
            ),
            "Item Name": st.column_config.TextColumn(
                "Item Name", 
                width="medium",
                required=True
            ),
            "Start Date": st.column_config.DateColumn(
                "Start Date", 
                width="small",
                required=True
            ),
            "End Date": st.column_config.DateColumn(
                "End Date", 
                width="small",
                required=True
            ),
            "Months": st.column_config.NumberColumn(
                "Months", 
                disabled=True, 
                width="small", 
                format="%d",
                help="🔒 Auto-calculated (not editable)"
            )
        }

        # Initialize base DataFrame if empty
        if items_df.empty:
            items_df = pd.DataFrame(columns=['Team', 'Item Name', 'Start Date', 'End Date', 'Months', 'Item ID', 'Project ID'])
            items_df['Project ID'] = selected_id  # Initialize with the current project ID

        # Add Item ID if it doesn't exist
        if 'Item ID' not in items_df.columns:
            items_df['Item ID'] = [f"I{i:03d}" for i in range(1, len(items_df) + 1)]

        # Ensure all required columns exist
        display_columns = ['Item ID', 'Team', 'Item Name', 'Start Date', 'End Date', 'Months']
        for col in display_columns:
            if col not in items_df.columns:
                if col == 'Months':
                    items_df[col] = 1
                elif col == 'Team':
                    items_df[col] = 'Development'  # Default team
                else:
                    items_df[col] = ""

        # Calculate months before displaying
        items_df['Months'] = items_df.apply(
            lambda x: max(1, ((pd.to_datetime(x['End Date']) - pd.to_datetime(x['Start Date'])).days // 30) + 1)
            if pd.notna(x['Start Date']) and pd.notna(x['End Date'])
            else 1,
            axis=1
        )

        # Convert Team to string if present
        if 'Team' in items_df.columns:
            items_df['Team'] = items_df['Team'].astype(str)

        # Initialize session state variables for auto-save
        if 'autosave_enabled' not in st.session_state:
            st.session_state.autosave_enabled = True  # Enabled by default
        if 'last_autosave_time' not in st.session_state:
            st.session_state.last_autosave_time = None
        if f"last_edit_data_{selected_id}" not in st.session_state:
            st.session_state[f"last_edit_data_{selected_id}"] = None
        if 'last_save_time' not in st.session_state:
            st.session_state.last_save_time = None
        if f"editor_changed_{selected_id}" not in st.session_state:
            st.session_state[f"editor_changed_{selected_id}"] = False

        # Callback function for data editor changes
        def on_data_change():
            st.session_state[f"editor_changed_{selected_id}"] = True

        # Add autosave section with toggle and save status
        autosave_container = st.container()
        with autosave_container:
            st.markdown("### Project Items Management")

            # Add autosave toggle and last save info in a horizontal layout
            autosave_cols = st.columns([1, 1, 2])

            with autosave_cols[0]:
                st.session_state.autosave_enabled = st.toggle(
                    "Enable Auto-Save", 
                    value=st.session_state.autosave_enabled,
                    help="Automatically save changes every 30 seconds"
                )

            # Last save status display
            with autosave_cols[1]:
                if st.session_state.last_autosave_time:
                    st.caption(f"Last auto-saved: {st.session_state.last_autosave_time.strftime('%H:%M:%S')}")
                elif st.session_state.last_save_time:
                    st.caption(f"Last manually saved: {st.session_state.last_save_time.strftime('%H:%M:%S')}")
                else:
                    st.caption("No saves yet")

        # Display data editor with standard configuration
        try:
            edited_df = st.data_editor(
                items_df[display_columns],
                column_config=column_config,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                disabled=['Item ID', 'Months'],
                key=f"items_editor_{selected_id}",
                on_change=on_data_change
            )

            # Store the edited dataframe in session state whenever it changes
            if st.session_state[f"editor_changed_{selected_id}"]:
                if edited_df is not None:
                    st.session_state[f"last_edit_data_{selected_id}"] = edited_df.copy()
                    st.session_state[f"editor_changed_{selected_id}"] = False
        except Exception as e:
            logger.error(f"Error displaying data editor: {str(e)}")
            st.error("Error displaying data. Please try again or contact support.")
            return

        # Auto-save logic
        autosave_message = st.empty()
        if st.session_state.autosave_enabled:
            current_time = datetime.now()

            # Define autosave interval (30 seconds)
            autosave_interval = 30

            # Check if it's time to autosave
            should_autosave = (
                st.session_state.last_autosave_time is None or 
                (current_time - st.session_state.last_autosave_time).total_seconds() > autosave_interval
            )

            # If it's time to autosave and we have data changes
            if should_autosave and st.session_state.get(f"editor_changed_{selected_id}", False) and edited_df is not None:
                try:
                    autosave_data = edited_df.copy()

                    # Recalculate months
                    autosave_data['Months'] = autosave_data.apply(
                        lambda x: max(1, ((pd.to_datetime(x['End Date'], errors='coerce') - 
                                          pd.to_datetime(x['Start Date'], errors='coerce')).days // 30) + 1)
                        if pd.notna(pd.to_datetime(x['Start Date'], errors='coerce')) and 
                           pd.notna(pd.to_datetime(x['End Date'], errors='coerce'))
                        else 1,
                        axis=1
                    )

                    # Add required columns
                    autosave_data['Project ID'] = selected_id

                    # Ensure Item IDs for new rows
                    if 'Item ID' in autosave_data.columns and autosave_data['Item ID'].isna().any():
                        # Only assign IDs to rows that don't have them
                        for idx, row in autosave_data.iterrows():
                            if pd.isna(row['Item ID']):
                                autosave_data.at[idx, 'Item ID'] = f"I{idx+1:03d}"

                    # Save changes
                    save_result = st.session_state.data_manager.save_project_items(autosave_data)

                    if save_result:
                        st.session_state.last_autosave_time = current_time
                        # Store the successfully saved data
                        st.session_state[f"last_edit_data_{selected_id}"] = autosave_data.copy()
                        # Update the session state flag
                        st.session_state[f"editor_changed_{selected_id}"] = False

                        # Show a toast notification for autosave
                        st.toast(f"Auto-saved at {current_time.strftime('%H:%M:%S')}")
                    else:
                        logger.error("Auto-save failed, but no exception was raised")
                except Exception as e:
                    logger.error(f"Auto-save error: {str(e)}")
                    autosave_message.error("Error during auto-save. Your changes may not be saved.")

            # If we're approaching the autosave time, show countdown (optional enhancement)
            elif st.session_state.last_autosave_time and st.session_state.get(f"editor_changed_{selected_id}", False):
                seconds_since_last_save = (current_time - st.session_state.last_autosave_time).total_seconds()
                seconds_until_save = max(0, autosave_interval - seconds_since_last_save)

                # Only show countdown if we're within 10 seconds of the next autosave
                if seconds_until_save < 10:
                    autosave_message.caption(f"Auto-saving in {int(seconds_until_save)} seconds...")

        # Create placeholder for save success message
        save_message_placeholder = st.empty()

        # Replace the save button with a more prominent one
        save_col1, save_col2, save_col3 = st.columns([1, 2, 1])
        with save_col2:
            save_button = st.button(
                "💾 Save Changes", 
                key=f"save_items_{selected_id}_btn",
                help="Save all changes to the project items immediately",
                use_container_width=True
            )

        if save_button:
            if edited_df is not None:
                # Show a spinner during save operation
                with st.spinner('Saving changes...'):
                    try:
                        # Make a copy to avoid modifying the displayed dataframe
                        save_df = edited_df.copy()

                        # Recalculate months
                        save_df['Months'] = save_df.apply(
                            lambda x: max(1, ((pd.to_datetime(x['End Date'], errors='coerce') - 
                                             pd.to_datetime(x['Start Date'], errors='coerce')).days // 30) + 1)
                            if pd.notna(pd.to_datetime(x['Start Date'], errors='coerce')) and 
                               pd.notna(pd.to_datetime(x['End Date'], errors='coerce'))
                            else 1,
                            axis=1
                        )

                        # Handle date columns carefully
                        for date_col in ['Start Date', 'End Date']:
                            # First ensure we have datetime objects
                            save_df[date_col] = pd.to_datetime(save_df[date_col], errors='coerce')

                            # For any NA values, set defaults
                            if date_col == 'Start Date':
                                save_df[date_col].fillna(pd.Timestamp('2025-01-01'), inplace=True)
                            else:  # End Date
                                save_df[date_col].fillna(pd.Timestamp('2025-02-01'), inplace=True)

                        # Ensure no empty item names or teams
                        if 'Item Name' in save_df.columns:
                            save_df['Item Name'] = save_df['Item Name'].fillna('Untitled Item')
                            save_df.loc[save_df['Item Name'] == '', 'Item Name'] = 'Untitled Item'

                        if 'Team' in save_df.columns:
                            save_df['Team'] = save_df['Team'].fillna('Development')
                            save_df.loc[save_df['Team'] == '', 'Team'] = 'Development'


                        # Add required columns
                        save_df['Project ID'] = selected_id

                        # Ensure Item IDs are assigned correctly
                        if 'Item ID' in save_df.columns:
                            missing_ids = save_df['Item ID'].isna()
                            if missing_ids.any():
                                for idx in save_df[missing_ids].index:
                                    save_df.at[idx, 'Item ID'] = f"I{idx+1:03d}"

                        # Save changes and get success flag
                        save_success = st.session_state.data_manager.save_project_items(save_df)

                        if save_success:
                            # Store last save time in session state
                            st.session_state.last_save_time = datetime.now()
                            # Update the last_edit_data to match what we just saved
                            st.session_state[f"last_edit_data_{selected_id}"] = save_df.copy()
                            # Reset the changed flag
                            st.session_state[f"editor_changed_{selected_id}"] = False

                            # Display success message with animation
                            save_message_placeholder.markdown(
                                f"""<div class="save-success">
                                    ✅ Project items saved successfully at {st.session_state.last_save_time.strftime('%H:%M:%S')}!
                                </div>""", 
                                unsafe_allow_html=True
                            )
                            # Add a short delay to ensure the success message is visible
                            time_module.sleep(0.5)
                        else:
                            st.error("Error saving data. Check the logs for more information.")

                    except Exception as e:
                        logger.error(f"Error saving data: {str(e)}")
                        st.error(f"Error saving data: {str(e)}")

def show_dashboard():
    st.header("Project Dashboard")

    # Display summary statistics and metrics
    col1, col2 = st.columns(2)

    # Add Team Deadlines Chart section to the dashboard
    st.subheader("Team Deadlines Across Projects")

    # Create a container for the chart configuration
    with st.expander("Chart Configuration", expanded=False):
        # Set up filters in columns
        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            st.write("**Filter by ISO**")
            try:
                all_isos = st.session_state.data_manager.get_unique_isos()
                selected_isos = st.multiselect(
                    "",
                    options=all_isos,
                    default=None,
                    placeholder="Select ISO(s) to filter projects",
                    label_visibility="collapsed",
                    key="dashboard_deadlines_iso_filter"
                )
            except Exception as e:
                logger.error(f"Error getting ISO values: {str(e)}")
                st.error("Could not load ISO filter values")
                selected_isos = []

        with filter_col2:
            st.write("**Date Range**")
            use_custom_dates = st.checkbox(
                "Use custom date range", 
                value=True,  # Enabled by default to show the January 2025 date range
                key="dashboard_deadlines_custom_dates"
            )

            if use_custom_dates:
                date_cols = st.columns(2)
                with date_cols[0]:
                    custom_start = st.date_input(
                        "Start Date",
                        value=datetime(2025, 1, 1).date(),  # Set default to January 2025
                        key="dashboard_deadlines_start_date"
                    )

                with date_cols[1]:
                    # Get the maximum end date from projects or default to 1 year from start
                    try:
                        all_items = pd.DataFrame()
                        for project_id in st.session_state.data_manager.get_data()['ID'].unique():
                            project_items = st.session_state.data_manager.get_project_items(project_id)
                            all_items = pd.concat([all_items, project_items], ignore_index=True)

                        if not all_items.empty:
                            max_end_date = pd.to_datetime(all_items['End Date']).max()
                            # Add 3 months buffer to the max date
                            default_end_date = (max_end_date + pd.DateOffset(months=3)).date()
                        else:
                            default_end_date = datetime(2026, 1, 1).date()
                    except Exception as e:
                        logger.error(f"Error calculating end date: {str(e)}")
                        default_end_date = datetime(2026, 1, 1).date()

                    custom_end = st.date_input(
                        "End Date",
                        value=default_end_date,
                        key="dashboard_deadlines_end_date"
                    )
            else:
                custom_start = None
                custom_end = None

        # Add Time Interval control
        st.write("**Time Interval**")
        interval_options = {
            "Auto": {"value": None, "description": "Automatically adjust based on date range"},
            "Monthly": {"value": 1, "description": "Show ticks every month"},
            "Quarterly": {"value": 3, "description": "Show ticks every 3 months"},
            "Semi-Annual": {"value": 6, "description": "Show ticks every 6 months"},
            "Annual": {"value": 12, "description": "Show ticks every 12 months"}
        }

        # Create a column layout to place description below the slider
        slider_col, _ = st.columns([10, 1])

        with slider_col:
            # Use the select_slider with just the option names
            selected_interval = st.select_slider(
                "Select time interval for y-axis ticks",
                options=list(interval_options.keys()),
                value="Auto",
                key="dashboard_deadlines_interval"
            )

            # Show the description of the currently selected option
            st.caption(f"**{selected_interval}**: {interval_options[selected_interval]['description']}")

        # Get the actual value for the visualization
        tick_interval = interval_options[selected_interval]["value"]

        # Chart height option
        st.write("**Chart Height**")
        chart_height = st.slider(
            "Adjust chart height", 
            min_value=400, 
            max_value=800, 
            value=500, 
            step=50,
            key="dashboard_deadlines_height"
        )

    # Get data for chart with error handling
    try:
        project_data = st.session_state.data_manager.get_data()
    except Exception as e:
        logger.error(f"Error getting project data: {str(e)}")
        st.error("Could not load project data for the dashboard.")
        return

    if not project_data.empty:
        # Apply ISO filter if selected
        if selected_isos:
            filtered_data = project_data[project_data['ISO'].isin(selected_isos)]
            if filtered_data.empty:
                st.info("No projects match the selected ISO filter.")
                return
        else:
            filtered_data = project_data

        # Get all items data with error handling
        try:
            all_items = pd.DataFrame()
            for project_id in filtered_data['ID'].unique():
                try:
                    project_items = st.session_state.data_manager.get_project_items(project_id)
                    all_items = pd.concat([all_items, project_items], ignore_index=True)
                except Exception as e:
                    logger.warning(f"Error loading items for project {project_id}: {str(e)}")
                    # Continue with next project

            if all_items.empty and len(filtered_data) > 0:
                st.warning("Could not load project items. Some data may be missing.")
        except Exception as e:
            logger.error(f"Error loading project items: {str(e)}")
            st.error("Could not load project items data.")
            all_items = pd.DataFrame()

        if not all_items.empty:
            # Add refresh and download buttons ABOVE the chart
            refresh_col, _, download_col = st.columns([1, 1, 1])

            with refresh_col:
                if st.button("🔄 Refresh Chart", key="refresh_dashboard_chart", help="Refresh chart data without resetting settings"):
                    # Force a re-fetch of data by rerunning just this part
                    st.rerun()

            with download_col:
                # Create downloadable DataFrame
                download_df = pd.DataFrame()

                for project_id in filtered_data['ID'].unique():
                    project_info = filtered_data[filtered_data['ID'] == project_id].iloc[0]
                    project_items = all_items[all_items['Project ID'] == project_id]

                    for team in project_items['Team'].unique():
                        team_items = project_items[project_items['Team'] == team]
                        if not team_items.empty:
                            try:
                                latest_date = pd.to_datetime(team_items['End Date']).max()

                                # Check if latest_date is NaT before calling strftime
                                deadline_str = "N/A"
                                if pd.notna(latest_date):
                                    deadline_str = latest_date.strftime('%Y-%m-%d')

                                new_row = pd.DataFrame({
                                    'Project ID': [project_id],
                                    'Project Name': [project_info['Name']],
                                    'ISO': [project_info['ISO']],
                                    'Team': [team],
                                    'Deadline': [deadline_str]
                                })
                                download_df = pd.concat([download_df, new_row], ignore_index=True)
                            except Exception as e:
                                logger.error(f"Error processing team {team} for project {project_id}: {str(e)}")
                                # Continue with next team

                st.download_button(
                    label="📥 Download Deadlines Data (CSV)",
                    data=download_df.to_csv(index=False),
                    file_name=f"team_deadlines_data.csv",
                    mime="text/csv",
                    key="download_dashboard_deadlines_csv"
                )

            # Add a divider to separate controls from the chart            
            st.markdown("---")

            try:
                # Create visualization with progress indicator
                with st.spinner("Generating chart..."):
                    visualizer = TimelineVisualizer()

                    # Double-check we have required data before calling visualization
                    if filtered_data.empty:
                        st.info("No project data available to chart. Please add projects first.")
                    elif all_items.empty:
                        st.info("No timeline items available. Please add project items in the Edit Project tab.")
                    else:
                        # Check for required columns in all_items
                        required_cols = ['Project ID', 'Team', 'End Date']
                        missing_cols = [col for col in required_cols if col not in all_items.columns]
                        if missing_cols:
                            st.error(f"Missing required data columns: {', '.join(missing_cols)}")
                            logger.error(f"Missing required columns in timeline data: {missing_cols}")
                        else:
                            # Log data shape before visualization
                            logger.info(f"Creating chart with {len(filtered_data)} projects and {len(all_items)} items")

                            result = visualizer.create_team_deadlines_chart(
                                filtered_data, 
                                all_items,
                                custom_start_date=custom_start,
                                custom_end_date=custom_end,
                                tick_interval=tick_interval  # Pass the tick interval to the chart
                            )

                            # Handle return values (can be just a figure or a tuple with figure, alerts, and warning info)
                            if isinstance(result, tuple) and len(result) >= 2:
                                fig = result[0]
                                alerts = result[1]
                                warning_info = result[2] if len(result) > 2 else None
                            else:
                                fig = result
                                alerts = []
                                warning_info = None

                            # Only proceed if we got a valid figure back
                            if fig is not None:
                                # Update chart height and width
                                fig.update_layout(
                                    height=chart_height,
                                    margin=dict(l=200, r=50, t=100, b=100)  # Increased left margin for project names
                                )

                                # Display chart
                                st.plotly_chart(fig, use_container_width=True)

                                # Display sequence warnings AFTER the chart if they exist
                                if warning_info:
                                    with st.expander("⚠️ Sequencing Warnings", expanded=False):
                                        st.markdown("### Projects with Potential Scheduling Issues")
                                        st.markdown("The following projects have teams with end dates that occur after Construction end date:")

                                        for project_name, teams in warning_info["alert_projects"].items():
                                            st.markdown(f"**{project_name}:**")

                                            # Find detailed warnings for this project
                                            project_warnings = [w for w in warning_info["alert_details"] if w["proj_name"] == project_name]

                                            # Display warnings in a readable format
                                            for warning in project_warnings:
                                                st.markdown(f"- **{warning['team']}** ends **{warning['days_diff']} days** after Construction end date")

                                            st.markdown("---")
                            else:
                                st.warning("No data available to create the chart. Try adding project items first.")
            except Exception as e:
                logger.error(f"Error creating team deadlines chart: {str(e)}")
                st.error("An error occurred while creating the chart. Please check your data.")
        else:
            st.info("No timeline items available for projects.")
    else:
        st.info("No projects available to display.")

def show_critical_path():
    st.header("Project Timeline Overview")

    # Get all projects with error handling
    try:
        data = st.session_state.data_manager.get_data()
    except Exception as e:
        logger.error(f"Error retrieving project data: {str(e)}")
        st.error("Could not load project data. Please try again later.")
        return

    if data.empty:
        st.info("No projects available.")
        return

    # Initialize session state variables
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = None
    if 'selection_expander_state' not in st.session_state:
        st.session_state.selection_expander_state = True

    # Make the Project Selection section collapsible
    with st.expander("Project Selection", expanded=st.session_state.selection_expander_state):
        # Set up filters in the expandable section
        filter_row = st.columns([1, 1])

        with filter_row[0]:
            st.write("Filter by ISO")
            try:
                all_isos = st.session_state.data_manager.get_unique_isos()
                selected_isos = st.multiselect(
                    "",
                    options=all_isos,
                    default=None,
                    placeholder="Select ISO(s) to filter projects",
                    label_visibility="collapsed"
                )
            except Exception as e:
                logger.error(f"Error getting ISO values: {str(e)}")
                st.error("Could not load ISO filter options")
                selected_isos = []

        # Filter projects based on selected ISO(s)
        filtered_data = data.copy()

        # Apply ISO filter if any are selected
        if selected_isos:
            filtered_data = filtered_data[filtered_data['ISO'].isin(selected_isos)]

        # Show count of filtered projects
        if len(filtered_data) == 0:
            st.warning("No projects match your filter criteria. Try adjusting your filters.")
        else:
            st.caption(f"Found {len(filtered_data)} matching project(s)")

        # Create project options from filtered data
        project_options = [f"{row['ID']} - {row['Name']} ({row['ISO']})" for _, row in filtered_data.iterrows()]

        # Project selection section
        st.write("Select a Project to View")

        # Project selection dropdown with built-in search
        current_selection = st.selectbox(
            "",
            options=project_options,
            index=None,
            placeholder="Search or select a project...",
            label_visibility="collapsed",
            key="project_selector"
        )

        # Check if selection has changed
        if current_selection != st.session_state.selected_project:
            st.session_state.selected_project = current_selection
            # Auto-collapse the selection section after a selection is made
            st.session_state.selection_expander_state = False
            # Rerun to apply the collapsed state
            st.rerun()

    # Continue with displaying project timeline if a project is selected
    if st.session_state.selected_project:
        # Extract project ID from the selected option
        project_id = st.session_state.selected_project.split(" - ")[0]
        project_name = st.session_state.selected_project.split(" - ")[1].split(" (")[0]

        # Get project items with error handling
        try:
            items_df = st.session_state.data_manager.get_project_items(project_id)
        except Exception as e:
            logger.error(f"Error retrieving project items for {project_id}: {str(e)}")
            st.error("Could not load project items. Please try again later.")
            items_df = pd.DataFrame()

        if not items_df.empty:
            # Create timeline visualization
            visualizer = TimelineVisualizer()

            # Prepare data for Gantt chart
            plot_data = items_df.copy()
            plot_data['Task'] = plot_data['Item Name']
            plot_data['Start'] = pd.to_datetime(plot_data['Start Date'], errors='coerce')
            plot_data['Finish'] = pd.to_datetime(plot_data['End Date'], errors='coerce')
            plot_data['Duration'] = (plot_data['Finish'] - plot_data['Start']).dt.days.fillna(0)
            plot_data['Team'] = plot_data['Team'].fillna('Unknown')

            # Calculate min and max dates from data for default date range
            min_date = plot_data['Start'].min()
            max_date = plot_data['Finish'].max() + pd.DateOffset(months=6)

            # Add chart configuration options in an expander
            with st.expander("Chart Configuration"):
                st.subheader("Axis Settings")

                # Update to 2 columns
                col1, col2 = st.columns(2)

                with col1:
                    # X-axis date range controls
                    st.write("**X-Axis (Timeline) Range**")
                    use_custom_dates = st.checkbox("Use custom date range", value=False)

                    if use_custom_dates:
                        custom_start = st.date_input(
                            "Start Date", 
                            value=min_date.date() if not pd.isna(min_date) else datetime.now().date(),
                            key="gantt_start_date"
                        )

                        custom_end = st.date_input(
                            "End Date", 
                            value=max_date.date() if not pd.isna(max_date) else (datetime.now() + timedelta(days=180)).date(),
                            key="gantt_end_date"
                        )
                    else:
                        custom_start = None
                        custom_end = None

                    # Time interval controls with improved feedback
                    st.write("**Time Interval**")
                    interval_options = {
                        "Auto": {"value": None, "description": "Automatically adjust based on date range"},
                        "Monthly": {"value": 1, "description": "Show ticks every month"},
                        "Quarterly": {"value": 3, "description": "Show ticks every 3 months"},
                        "Semi-Annual": {"value": 6, "description": "Show ticks every 6 months"},
                        "Annual": {"value": 12, "description": "Show ticks every 12 months"}
                    }

                    # Create a column layout to place description below the slider
                    slider_col, _ = st.columns([10, 1])

                    with slider_col:
                        # Use the select_slider with just the option names
                        selected_interval = st.select_slider(
                            "Select time interval for x-axis ticks",
                            options=list(interval_options.keys()),
                            value="Auto"
                        )

                        # Show the description of the currently selected option
                        st.caption(f"**{selected_interval}**: {interval_options[selected_interval]['description']}")

                    # Get the actual value for the visualization
                    tick_interval = interval_options[selected_interval]["value"]

                with col2:
                    # Y-axis controls
                    st.write("**Y-Axis Settings**")
                    show_task_labels = st.checkbox("Show task labels", value=True)

                # Chart height control within the configuration section
                st.write("**Chart Height**")
                chart_height = st.slider(
                    "Chart Height", 
                    min_value=400, 
                    max_value=800, 
                    value=650,  # Default to 650px as requested
                    step=50,
                    key=f"timeline_chart_height_{project_id}"
                )

                # At the end of the expander, add a divider
                st.markdown("---")

            # Display timeline with settings
            st.subheader(f"Timeline for {project_name} ({project_id})")

            # Add refresh button and height control to the timeline chart
            refresh_col, height_col, download_col = st.columns([1, 1, 1])

            with refresh_col:
                if st.button("🔄 Refresh Chart", key=f"refresh_timeline_{project_id}", help="Refresh chart data without resetting settings"):
                    st.rerun()

            try:
                timeline_fig = visualizer.create_timeline(
                    plot_data,
                    custom_start_date=custom_start,
                    custom_end_date=custom_end,
                    show_task_labels=show_task_labels,
                    tick_interval=tick_interval
                )

                # Apply custom height from slider
                timeline_fig.update_layout(height=chart_height)

                st.plotly_chart(
                    timeline_fig,
                    use_container_width=True
                )

                # Add download button after the chart is displayed
                with download_col:
                    # Prepare CSV data
                    csv_data = items_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Timeline Data (CSV)",
                        data=csv_data,
                        file_name=f"{project_name}_timeline_data.csv",
                        mime="text/csv",
                        key="download_timeline_csv"
                    )
            except Exception as e:
                logger.error(f"Error creating timeline chart: {str(e)}")
                st.error("An error occurred while creating the timeline. Please check your data.")
        else:
            st.info("No timeline items available for this project.")
    else:
        st.info("Please select a project to view its timeline.")

def show_project_form():
    st.header("Add New Project")
    try:
        form = ProjectForm()
        form.render()
    except Exception as e:
        logger.error(f"Error rendering project form: {str(e)}")
        st.error("Could not load the project form. Please try again later.")

def show_team_dependencies():
    st.header("Team Dependencies")

    try:
        visualizer = TimelineVisualizer()
        data = st.session_state.data_manager.get_data()

        if not data.empty:
            try:
                dependency_chart = visualizer.create_dependency_chart(data)
                if dependency_chart:
                    st.plotly_chart(
                        dependency_chart,
                        use_container_width=True
                    )
                else:
                    st.info("No dependency data available to visualize.")
            except Exception as e:
                logger.error(f"Error creating dependency chart: {str(e)}")
                st.error("Error visualizing team dependencies. Please check your data.")
        else:
            st.info("No project data available to show dependencies.")
    except Exception as e:
        logger.error(f"Error loading data for dependencies: {str(e)}")
        st.error("Could not load dependency data.")

def show_export_page():
    st.header("Export Data")

    try:
        data = st.session_state.data_manager.get_data()
        if not data.empty:
            csv = data.to_csv(index=False)
            st.download_button(
                label="Download Project Data (CSV)",
                data=csv,
                file_name=f"project_timeline_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available to export.")
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        st.error("Could not export data. Please try again later.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Log any uncaught exceptions at the top level
        logger.error(f"Unhandled exception in application: {str(e)}")
        st.error("An unexpected error occurred. Please try refreshing the page or contact support.")