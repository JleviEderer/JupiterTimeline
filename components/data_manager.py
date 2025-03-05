import pandas as pd
from datetime import datetime
import streamlit as st
import logging

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_manager')

class DataManager:
    def __init__(self):
        self.file_path = "data/projects.csv"
        self.items_path = "data/items.csv"
        self.load_data()
        
    def reload_data(self):
        """Force reload data from file system"""
        self.load_data()
        return True

    def load_data(self):
        try:
            self.data = pd.read_csv(self.file_path)
            if 'Target COD' in self.data.columns:
                self.data['Target COD'] = pd.to_datetime(self.data['Target COD'], format='mixed')
        except FileNotFoundError:
            self.data = pd.DataFrame(columns=[
                'ID', 'Name', 'ISO', 'Voltage', 'Capacity', 'Duration', 'Target COD'
            ])
            self.save_data()

    def save_data(self):
        self.data.to_csv(self.file_path, index=False)

    def add_project(self, project_data):
        new_project = pd.DataFrame([project_data])
        self.data = pd.concat([self.data, new_project], ignore_index=True)
        self.save_data()

    def update_project(self, project_id, project_data):
        row_idx = self.data.index[self.data['ID'] == project_id].tolist()[0]
        for column in self.data.columns:
            self.data.at[row_idx, column] = project_data[column]
        self.save_data()

    def delete_project(self, project_id):
        """Delete a project and all its associated items"""
        try:
            # Handle projects.csv
            # Remove the project from the projects DataFrame
            if project_id not in self.data['ID'].values:
                return False

            self.data = self.data[self.data['ID'] != project_id]
            # Save the changes to projects.csv
            self.data.to_csv(self.file_path, index=False)

            # Handle items.csv
            try:
                import os
                if os.path.exists(self.items_path):
                    items_df = pd.read_csv(self.items_path)
                    if 'Project ID' in items_df.columns:
                        # Remove all items associated with this project
                        items_df = items_df[items_df['Project ID'] != project_id]
                        items_df.to_csv(self.items_path, index=False)
            except Exception as e:
                logger.error(f"Error removing project items: {e}")
                # Continue even if items deletion fails

            return True

        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            return False

    def get_data(self):
        return self.data

    def get_project(self, project_id):
        return self.data[self.data['ID'] == project_id].iloc[0]

    def get_project_ids(self):
        return self.data['ID'].tolist()

    def get_unique_isos(self):
        return sorted(self.data['ISO'].unique().tolist())

    def get_unique_voltages(self):
        return sorted(self.data['Voltage'].unique().tolist())

    def filter_data(self, isos=None, voltages=None):
        filtered = self.data.copy()
        if isos:
            filtered = filtered[filtered['ISO'].isin(isos)]
        if voltages:
            filtered = filtered[filtered['Voltage'].isin(voltages)]
        return filtered

    def save_project_items(self, items_df):
        """
        Save project items with enhanced error handling and date format fixing
        """
        try:
            # Log the data we're trying to save
            logger.info(f"Attempting to save {len(items_df)} items")

            # Validate incoming dataframe
            if items_df is None or not isinstance(items_df, pd.DataFrame):
                logger.error(f"Invalid input: items_df is {type(items_df)}")
                return False
                
            if items_df.empty:
                logger.warning("Empty dataframe provided to save_project_items")
                return False
                
            # Make a copy to avoid modifying the original dataframe
            items_df = items_df.copy()
            
            # Debug log the original dataframe
            logger.info(f"Original data has {len(items_df)} rows with columns: {items_df.columns.tolist()}")
            
            # Remove any completely empty rows
            items_df = items_df.dropna(how='all')
            logger.info(f"After removing empty rows: {len(items_df)} rows remain")
                
            # Check for required columns
            required_columns = ['Project ID', 'Item Name', 'Team']
            missing_columns = [col for col in required_columns if col not in items_df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False

            # Test file writing permissions
            try:
                import os
                data_dir = os.path.dirname(self.items_path)
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)
                    logger.info(f"Created directory: {data_dir}")

                with open(os.path.join(data_dir, 'test_write.txt'), 'w') as f:
                    f.write('Test write operation')
                logger.info("File write test successful")
            except Exception as e:
                logger.error(f"File write test failed: {e}")
                raise Exception(f"Cannot write to data directory: {e}")

            # Read existing items to preserve data
            try:
                existing_items = pd.read_csv(self.items_path)
                logger.info(f"Read {len(existing_items)} existing items")
            except FileNotFoundError:
                logger.info("No existing items file found, creating new one")
                existing_items = pd.DataFrame(columns=['Item ID', 'Project ID', 'Item Name', 'Team', 'Start Date', 'End Date', 'Months'])

            # Get the project ID from the new items
            project_id = items_df['Project ID'].iloc[0] if 'Project ID' in items_df.columns and not items_df.empty else None
            
            if not project_id:
                logger.error("No valid Project ID found in the data")
                return False
                
            logger.info(f"Processing items for Project ID: {project_id}")

            # Fill any blank or NaN values in Item Name with placeholders
            if 'Item Name' in items_df.columns:
                items_df['Item Name'] = items_df['Item Name'].fillna('Untitled Item')
                # Replace empty strings with placeholder
                items_df.loc[items_df['Item Name'] == '', 'Item Name'] = 'Untitled Item'
            
            # Ensure Team is filled
            if 'Team' in items_df.columns:
                items_df['Team'] = items_df['Team'].fillna('Development')
                items_df.loc[items_df['Team'] == '', 'Team'] = 'Development'

            # Add Item ID if it doesn't exist or contains NaN values
            if 'Item ID' not in items_df.columns:
                logger.info("Adding Item IDs to new rows")
                items_df['Item ID'] = [f"I{i:03d}" for i in range(1, len(items_df) + 1)]
            else:
                # Fill any missing Item IDs with new ones
                missing_ids_mask = items_df['Item ID'].isna()
                if missing_ids_mask.any():
                    logger.info(f"Adding missing Item IDs to {missing_ids_mask.sum()} rows")
                    for idx in items_df[missing_ids_mask].index:
                        items_df.at[idx, 'Item ID'] = f"I{idx:03d}"

            # Ensure required columns exist in the DataFrame
            required_columns = ['Item ID', 'Project ID', 'Item Name', 'Team', 'Start Date', 'End Date', 'Months']
            for col in required_columns:
                if col not in items_df.columns:
                    items_df[col] = '' if col not in ['Months'] else 1
                    logger.info(f"Added missing column to new data: {col}")

            # Process dates - improved handling for various formats
            for date_col in ['Start Date', 'End Date']:
                # Log original date values for debugging
                logger.info(f"Original {date_col} values: {items_df[date_col].tolist()}")
                
                # First try standard conversion
                try:
                    items_df[date_col] = pd.to_datetime(items_df[date_col], errors='coerce')
                except Exception as e:
                    logger.warning(f"Error in first date conversion for {date_col}: {str(e)}")
                
                # If we have any NaT values after conversion, try more aggressively
                if items_df[date_col].isna().any():
                    logger.info(f"Attempting additional date format conversions for {date_col}")
                    
                    # Try multiple formats for date strings
                    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d', '%m-%d-%Y']
                    
                    # Process each cell individually for problematic dates
                    for idx in items_df[items_df[date_col].isna()].index:
                        original_value = items_df.loc[idx, date_col]
                        if isinstance(original_value, str) and original_value.strip():
                            for fmt in date_formats:
                                try:
                                    parsed_date = datetime.strptime(original_value.strip(), fmt)
                                    items_df.loc[idx, date_col] = parsed_date
                                    logger.info(f"Successfully parsed date '{original_value}' with format {fmt}")
                                    break
                                except ValueError:
                                    continue
                
                # Set default values for missing dates if there's an item name
                mask = (items_df[date_col].isna() | (items_df[date_col] == ''))
                if mask.any():
                    logger.info(f"Setting default dates for {mask.sum()} entries in {date_col}")
                    today = datetime.now().date()
                    if date_col == 'Start Date':
                        default_date = today  # Use today as default start
                        items_df.loc[mask, date_col] = default_date
                        logger.info(f"Set default {date_col} for {mask.sum()} items to {default_date}")
                    else:  # End Date
                        default_date = today + pd.Timedelta(days=60)  # 2 months after today
                        items_df.loc[mask, date_col] = default_date
                        logger.info(f"Set default {date_col} for {mask.sum()} items to {default_date}")

            # Recalculate Months based on valid dates
            items_df['Months'] = items_df.apply(
                lambda x: max(1, ((x['End Date'] - x['Start Date']).days // 30) + 1)
                if pd.notna(x['Start Date']) and pd.notna(x['End Date'])
                else 1,
                axis=1
            )

            # Convert dates to string format for CSV storage
            items_df['Start Date'] = items_df['Start Date'].apply(
                lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else '2025-01-01'
            )
            items_df['End Date'] = items_df['End Date'].apply(
                lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else '2025-02-01'
            )

            # Remove existing items for this project
            existing_items = existing_items[existing_items['Project ID'] != project_id]
            logger.info(f"Removed existing items for project {project_id}")

            # Concatenate with existing items for other projects
            updated_items = pd.concat([existing_items, items_df], ignore_index=True)
            logger.info(f"Combined data now has {len(updated_items)} rows")

            # Ensure we're not saving empty data by mistake
            if updated_items.empty:
                logger.error("Attempted to save empty dataframe")
                return False

            # Before saving, do a final check for required data
            for idx, row in updated_items.iterrows():
                if pd.isna(row.get('Item Name')) or str(row.get('Item Name')).strip() == '':
                    updated_items.at[idx, 'Item Name'] = 'Untitled Item'
                if pd.isna(row.get('Team')) or str(row.get('Team')).strip() == '':
                    updated_items.at[idx, 'Team'] = 'Development'
            
            # Log what we're about to save for debugging
            logger.info(f"Saving data with columns: {updated_items.columns.tolist()}")
            logger.info(f"Data sample (first 5 rows): {updated_items.head().to_dict()}")
            
            # Save the updated DataFrame
            updated_items.to_csv(self.items_path, index=False)
            logger.info(f"Successfully saved {len(updated_items)} items to {self.items_path}")
            
            # Verify the save operation by reading back the file
            try:
                verification = pd.read_csv(self.items_path)
                logger.info(f"Verification: Read back {len(verification)} items")
                if len(verification) != len(updated_items):
                    logger.warning(f"Verification failed: Saved {len(updated_items)} items but read back {len(verification)}")
            except Exception as e:
                logger.error(f"Verification error: {str(e)}")
            
            return True

        except Exception as e:
            logger.error(f"Error in save_project_items: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def get_project_items(self, project_id):
        try:
            items_df = pd.read_csv(self.items_path)

            # Ensure Team column exists and fill missing values with a default
            if 'Team' not in items_df.columns:
                items_df['Team'] = 'Unknown'  # Use 'Unknown' instead of empty string
            else:
                items_df['Team'] = items_df['Team'].fillna('Unknown')

            # Parse dates as pd.Timestamp and log any parsing issues instead of displaying warnings
            items_df['Start Date'] = pd.to_datetime(items_df['Start Date'], errors='coerce')
            items_df['End Date'] = pd.to_datetime(items_df['End Date'], errors='coerce')

            # Log any date parsing issues
            parse_issues = items_df[items_df['Start Date'].isnull() | items_df['End Date'].isnull()]
            if not parse_issues.empty:
                logger.warning(f"Some date values could not be parsed in {len(parse_issues)} items")
                for _, row in parse_issues.iterrows():
                    logger.warning(f"Unparsed item: {row['Item Name']}, Project ID: {project_id}")

            # Calculate Months based on dates
            items_df['Months'] = items_df.apply(
                lambda x: max(1, ((pd.to_datetime(x['End Date']) - pd.to_datetime(x['Start Date'])).days // 30) + 1)
                if pd.notna(x['Start Date']) and pd.notna(x['End Date'])
                else 1,
                axis=1
            )

            # Log long durations instead of displaying warnings
            long_durations = items_df[items_df['Months'] > 360]
            if not long_durations.empty:
                logger.warning(f"Found {len(long_durations)} items with extremely long durations (>30 years)")
                for _, row in long_durations.iterrows():
                    logger.warning(f"Long duration item: {row['Item Name']}, Duration: {row['Months']} months")

            # Filter for the specific project and return
            return items_df[items_df['Project ID'] == project_id]
        except FileNotFoundError:
            return pd.DataFrame(columns=['Item ID', 'Project ID', 'Item Name', 'Team', 'Start Date', 'End Date', 'Months'])

    def get_team_colors(self):
        return {
            'Procurement': '#0D47A1',    # Dark Blue
            'Construction': '#FFD700',   # Gold (was Development)
            'Development': '#9C27B0',    # Purple (was Interconnection)
            'Interconnection': '#00BCD4' # Bright Turquoise (was Development)
        }