import streamlit as st
import pandas as pd
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import load_css
from components.data_storage import get_data_manager

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('settings')

def main():
    st.set_page_config(
        page_title="Settings | Project Timeline",
        page_icon="⚙️",
        layout="wide"
    )
    
    load_css()
    
    st.title("⚙️ Settings")
    st.markdown("Configure your project timeline dashboard settings")
    
    # Data Storage Settings
    st.header("Data Storage Settings")
    
    # Check current storage type
    current_storage = "PostgreSQL" if os.environ.get('DATABASE_URL') else "CSV"
    st.info(f"You are currently using **{current_storage}** for data storage.")
    
    # Database settings
    st.subheader("Database Settings")
    
    if current_storage == "PostgreSQL":
        st.success("PostgreSQL database is configured and active.")
        
        # Show database stats
        stats_col1, stats_col2 = st.columns(2)
        
        try:
            # Get database manager
            db_manager = get_data_manager()
            
            # Get count of projects and items
            with db_manager.engine.connect() as conn:
                project_count = conn.execute("SELECT COUNT(*) FROM projects").scalar()
                item_count = conn.execute("SELECT COUNT(*) FROM items").scalar()
                
                stats_col1.metric("Projects in Database", project_count)
                stats_col2.metric("Timeline Items in Database", item_count)
        except Exception as e:
            st.error(f"Error retrieving database statistics: {e}")
            logger.error(f"Error retrieving database statistics: {e}")
    else:
        st.warning(
            "PostgreSQL database is not configured. You are using CSV files for storage. "
            "To enable PostgreSQL, set the DATABASE_URL environment variable."
        )
    
    # Migration Tools
    st.subheader("Data Migration")
    
    if current_storage == "PostgreSQL":
        # Offer CSV to PostgreSQL migration
        st.info("You can migrate data from existing CSV files to the PostgreSQL database.")
        
        migrate_col1, migrate_col2 = st.columns([3, 1])
        
        with migrate_col1:
            force_migration = st.checkbox(
                "Force migration (overwrites existing database data)",
                help="If checked, existing data in the database will be deleted before migration."
            )
            
        with migrate_col2:
            if st.button("Migrate from CSV to Database", use_container_width=True):
                with st.spinner("Migrating data..."):
                    try:
                        from utils.migrate_to_postgresql import migrate_data
                        success = migrate_data(force=force_migration)
                        
                        if success:
                            st.success("Migration completed successfully!")
                        else:
                            st.error(
                                "Migration failed. See migration.log for details. "
                                "If tables already have data, try using the 'Force migration' option."
                            )
                    except Exception as e:
                        st.error(f"Error during migration: {e}")
                        logger.error(f"Error during migration: {e}")
    
    # Export Data
    st.header("Export Data")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        st.subheader("Export Projects")
        
        try:
            data_manager = get_data_manager()
            projects_df = data_manager.get_data()
            
            if not projects_df.empty:
                csv_projects = projects_df.to_csv(index=False)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                st.download_button(
                    label="📥 Download Projects as CSV",
                    data=csv_projects,
                    file_name=f"projects_export_{timestamp}.csv",
                    mime="text/csv",
                    help="Download all projects data as a CSV file",
                    use_container_width=True
                )
            else:
                st.info("No projects available to export.")
        except Exception as e:
            st.error(f"Error exporting projects: {e}")
            logger.error(f"Error exporting projects: {e}")
    
    with export_col2:
        st.subheader("Export All Items")
        
        try:
            data_manager = get_data_manager()
            project_ids = data_manager.get_project_ids()
            
            if project_ids:
                # Collect all items from all projects
                all_items = pd.DataFrame()
                for project_id in project_ids:
                    items = data_manager.get_project_items(project_id)
                    if not items.empty:
                        all_items = pd.concat([all_items, items], ignore_index=True)
                
                if not all_items.empty:
                    csv_items = all_items.to_csv(index=False)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    st.download_button(
                        label="📥 Download All Items as CSV",
                        data=csv_items,
                        file_name=f"items_export_{timestamp}.csv",
                        mime="text/csv",
                        help="Download all project items data as a CSV file",
                        use_container_width=True
                    )
                else:
                    st.info("No items available to export.")
            else:
                st.info("No projects available to export items from.")
        except Exception as e:
            st.error(f"Error exporting items: {e}")
            logger.error(f"Error exporting items: {e}")

    # Database Backup
    if current_storage == "PostgreSQL":
        st.header("Database Backup & Restore")
        st.info(
            "Backing up your PostgreSQL database ensures you don't lose important project data. "
            "You can download a complete backup of all your projects and timeline items."
        )
        
        backup_col1, _ = st.columns([2, 1])
        
        with backup_col1:
            if st.button("📦 Generate Database Backup", use_container_width=True):
                with st.spinner("Generating backup..."):
                    try:
                        # Get data manager
                        data_manager = get_data_manager()
                        
                        # Get all projects and items
                        projects_df = data_manager.get_data()
                        
                        # Create a ZIP file with projects and items
                        import io
                        import zipfile
                        
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            # Add projects
                            zip_file.writestr('projects.csv', projects_df.to_csv(index=False))
                            
                            # Add items for each project
                            all_items = pd.DataFrame()
                            for project_id in projects_df['ID']:
                                items = data_manager.get_project_items(project_id)
                                if not items.empty:
                                    all_items = pd.concat([all_items, items], ignore_index=True)
                            
                            if not all_items.empty:
                                zip_file.writestr('items.csv', all_items.to_csv(index=False))
                        
                        # Reset buffer position
                        zip_buffer.seek(0)
                        
                        # Create download button
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(
                            label="💾 Download Database Backup",
                            data=zip_buffer,
                            file_name=f"timeline_database_backup_{timestamp}.zip",
                            mime="application/zip",
                            help="Download a complete backup of your database",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Error generating backup: {e}")
                        logger.error(f"Error generating backup: {e}")

if __name__ == "__main__":
    main()
