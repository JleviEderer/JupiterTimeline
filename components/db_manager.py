import os
import pandas as pd
from datetime import datetime
import logging
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.sql import select, insert, update, delete

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_manager')

class DBManager:
    def __init__(self):
        """Initialize the database connection and create tables if they don't exist"""
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            logger.error("DATABASE_URL environment variable not found")
            raise ValueError("DATABASE_URL environment variable not found")

        # Create database engine
        try:
            self.engine = create_engine(self.db_url)
            self.metadata = MetaData()
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Error creating database engine: {e}")
            raise
        
        # Define tables
        self.define_tables()
        
        # Create tables if they don't exist
        try:
            self.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

        # Initialize data from CSV files if tables are empty
        self.initialize_data_from_csv()

    def define_tables(self):
        """Define the database tables"""
        # Projects table
        self.projects = Table(
            'projects', self.metadata,
            Column('ID', String(20), primary_key=True),
            Column('Name', String(100), nullable=False),
            Column('ISO', String(20), nullable=False),
            Column('Voltage', Float, nullable=False),
            Column('Capacity', Float, nullable=False),
            Column('Duration', Float, nullable=False),
            Column('Target_COD', DateTime, nullable=False)
        )

        # Project Items table
        self.items = Table(
            'items', self.metadata,
            Column('Item_ID', String(20), primary_key=True),
            Column('Project_ID', String(20), ForeignKey('projects.ID'), nullable=False),
            Column('Item_Name', String(100), nullable=False),
            Column('Team', String(50), nullable=False),
            Column('Start_Date', DateTime, nullable=False),
            Column('End_Date', DateTime, nullable=False),
            Column('Months', Integer, nullable=False)
        )

    def initialize_data_from_csv(self):
        """Initialize database with data from CSV files if the tables are empty"""
        try:
            # Check if projects table is empty
            with self.engine.connect() as connection:
                project_count = connection.execute(sa.select(sa.func.count()).select_from(self.projects)).scalar()
                
                if project_count == 0:
                    # Import from CSV
                    try:
                        projects_df = pd.read_csv("data/projects.csv")
                        
                        # Rename Target COD to match column name
                        projects_df = projects_df.rename(columns={"Target COD": "Target_COD"})
                        
                        # Convert to proper data types
                        projects_df['Target_COD'] = pd.to_datetime(projects_df['Target_COD'], format='mixed')
                        
                        # Insert into database
                        projects_df.to_sql('projects', self.engine, if_exists='append', index=False)
                        logger.info(f"Imported {len(projects_df)} projects from CSV")
                    except FileNotFoundError:
                        logger.warning("projects.csv file not found, skipping import")
                    except Exception as e:
                        logger.error(f"Error importing projects from CSV: {e}")
                
                # Check if items table is empty
                item_count = connection.execute(sa.select(sa.func.count()).select_from(self.items)).scalar()
                
                if item_count == 0:
                    # Import from CSV
                    try:
                        items_df = pd.read_csv("data/items.csv")
                        
                        # Rename columns to match database schema
                        items_df = items_df.rename(columns={
                            "Item ID": "Item_ID",
                            "Project ID": "Project_ID",
                            "Start Date": "Start_Date",
                            "End Date": "End_Date"
                        })
                        
                        # Convert to proper data types
                        items_df['Start_Date'] = pd.to_datetime(items_df['Start_Date'], format='mixed')
                        items_df['End_Date'] = pd.to_datetime(items_df['End_Date'], format='mixed')
                        
                        # Insert into database
                        items_df.to_sql('items', self.engine, if_exists='append', index=False)
                        logger.info(f"Imported {len(items_df)} items from CSV")
                    except FileNotFoundError:
                        logger.warning("items.csv file not found, skipping import")
                    except Exception as e:
                        logger.error(f"Error importing items from CSV: {e}")
        
        except Exception as e:
            logger.error(f"Error initializing data from CSV: {e}")

    def reload_data(self):
        """Force reload data - in database context, this is a no-op"""
        return True

    def get_data(self):
        """Get all projects as a DataFrame"""
        try:
            with self.engine.connect() as connection:
                query = sa.select(self.projects)
                result = connection.execute(query)
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                
                # Rename columns to match the original CSV format
                df = df.rename(columns={"Target_COD": "Target COD"})
                
                return df
        except Exception as e:
            logger.error(f"Error getting project data: {e}")
            return pd.DataFrame(columns=['ID', 'Name', 'ISO', 'Voltage', 'Capacity', 'Duration', 'Target COD'])

    def get_project(self, project_id):
        """Get a specific project by ID"""
        try:
            with self.engine.connect() as connection:
                query = sa.select(self.projects).where(self.projects.c.ID == project_id)
                result = connection.execute(query)
                project = result.fetchone()
                
                if project:
                    # Convert to dictionary with keys matching original CSV format
                    project_dict = dict(project)
                    project_dict['Target COD'] = project_dict.pop('Target_COD')
                    return project_dict
                else:
                    logger.warning(f"Project ID {project_id} not found")
                    return None
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None

    def get_project_ids(self):
        """Get list of all project IDs"""
        try:
            with self.engine.connect() as connection:
                query = sa.select(self.projects.c.ID)
                result = connection.execute(query)
                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error getting project IDs: {e}")
            return []

    def get_unique_isos(self):
        """Get list of unique ISO values"""
        try:
            with self.engine.connect() as connection:
                query = sa.select(self.projects.c.ISO).distinct()
                result = connection.execute(query)
                return sorted([row[0] for row in result])
        except Exception as e:
            logger.error(f"Error getting unique ISOs: {e}")
            return []

    def get_unique_voltages(self):
        """Get list of unique voltage values"""
        try:
            with self.engine.connect() as connection:
                query = sa.select(self.projects.c.Voltage).distinct()
                result = connection.execute(query)
                return sorted([row[0] for row in result])
        except Exception as e:
            logger.error(f"Error getting unique voltages: {e}")
            return []

    def filter_data(self, isos=None, voltages=None):
        """Filter projects by ISO and/or voltage"""
        try:
            with self.engine.connect() as connection:
                query = sa.select(self.projects)
                
                # Apply filters
                if isos:
                    query = query.where(self.projects.c.ISO.in_(isos))
                if voltages:
                    query = query.where(self.projects.c.Voltage.in_(voltages))
                
                result = connection.execute(query)
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                
                # Rename columns to match the original CSV format
                df = df.rename(columns={"Target_COD": "Target COD"})
                
                return df
        except Exception as e:
            logger.error(f"Error filtering project data: {e}")
            return pd.DataFrame(columns=['ID', 'Name', 'ISO', 'Voltage', 'Capacity', 'Duration', 'Target COD'])

    def add_project(self, project_data):
        """Add a new project"""
        try:
            # Convert project_data to match database schema
            db_project = project_data.copy()
            if 'Target COD' in db_project:
                db_project['Target_COD'] = db_project.pop('Target COD')
            
            with self.engine.connect() as connection:
                # Insert the new project
                connection.execute(insert(self.projects).values(**db_project))
                connection.commit()
                logger.info(f"Added project {project_data['ID']}")
                return True
        except Exception as e:
            logger.error(f"Error adding project: {e}")
            return False

    def update_project(self, project_id, project_data):
        """Update an existing project"""
        try:
            # Convert project_data to match database schema
            db_project = project_data.copy()
            if 'Target COD' in db_project:
                db_project['Target_COD'] = db_project.pop('Target COD')
            
            with self.engine.connect() as connection:
                # Update the project
                connection.execute(
                    update(self.projects)
                    .where(self.projects.c.ID == project_id)
                    .values(**db_project)
                )
                connection.commit()
                logger.info(f"Updated project {project_id}")
                return True
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return False

    def delete_project(self, project_id):
        """Delete a project and all its associated items"""
        try:
            with self.engine.connect() as connection:
                # First delete all items associated with this project
                connection.execute(
                    delete(self.items)
                    .where(self.items.c.Project_ID == project_id)
                )
                
                # Then delete the project
                connection.execute(
                    delete(self.projects)
                    .where(self.projects.c.ID == project_id)
                )
                
                connection.commit()
                logger.info(f"Deleted project {project_id} and all its items")
                return True
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            return False

    def get_project_items(self, project_id):
        """Get all items for a specific project"""
        try:
            with self.engine.connect() as connection:
                query = sa.select(self.items).where(self.items.c.Project_ID == project_id)
                result = connection.execute(query)
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                
                if df.empty:
                    return pd.DataFrame(columns=['Item ID', 'Project ID', 'Item Name', 'Team', 'Start Date', 'End Date', 'Months'])
                
                # Rename columns to match the original CSV format
                df = df.rename(columns={
                    "Item_ID": "Item ID",
                    "Project_ID": "Project ID",
                    "Item_Name": "Item Name",
                    "Start_Date": "Start Date",
                    "End_Date": "End Date"
                })
                
                return df
        except Exception as e:
            logger.error(f"Error getting items for project {project_id}: {e}")
            return pd.DataFrame(columns=['Item ID', 'Project ID', 'Item Name', 'Team', 'Start Date', 'End Date', 'Months'])

    def save_project_items(self, items_df):
        """Save project items (update existing and add new ones)"""
        try:
            if items_df.empty:
                logger.warning("Empty dataframe provided to save_project_items")
                return False
            
            # Make a copy to avoid modifying the original dataframe
            df = items_df.copy()
            
            # Get project ID (should be the same for all items)
            project_id = df['Project ID'].iloc[0] if 'Project ID' in df.columns and not df.empty else None
            if not project_id:
                logger.error("No valid Project ID found in the data")
                return False
            
            # Ensure no empty item names or teams
            if 'Item Name' in df.columns:
                df['Item Name'] = df['Item Name'].fillna('Untitled Item')
                df.loc[df['Item Name'] == '', 'Item Name'] = 'Untitled Item'
            
            if 'Team' in df.columns:
                df['Team'] = df['Team'].fillna('Development')
                df.loc[df['Team'] == '', 'Team'] = 'Development'
            
            # Process dates
            for date_col in ['Start Date', 'End Date']:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    
                    # Set default values for missing dates
                    mask = df[date_col].isna()
                    if mask.any():
                        today = datetime.now().date()
                        if date_col == 'Start Date':
                            df.loc[mask, date_col] = today
                        else:  # End Date
                            df.loc[mask, date_col] = today + pd.Timedelta(days=60)
            
            # Recalculate Months
            df['Months'] = df.apply(
                lambda x: max(1, ((x['End Date'] - x['Start Date']).days // 30) + 1)
                if pd.notna(x['Start Date']) and pd.notna(x['End Date'])
                else 1,
                axis=1
            )
            
            # Make sure Item ID exists and is valid
            if 'Item ID' not in df.columns or df['Item ID'].isna().any():
                # Generate Item IDs if needed
                if 'Item ID' not in df.columns:
                    df['Item ID'] = [f"I{i:03d}" for i in range(1, len(df) + 1)]
                else:
                    # Fill any missing Item IDs
                    missing_ids = df['Item ID'].isna()
                    if missing_ids.any():
                        for idx in df[missing_ids].index:
                            df.at[idx, 'Item ID'] = f"I{idx+1:03d}"
            
            # Rename columns to match database schema
            db_df = df.rename(columns={
                "Item ID": "Item_ID",
                "Project ID": "Project_ID",
                "Item Name": "Item_Name",
                "Start Date": "Start_Date",
                "End Date": "End_Date"
            })
            
            with self.engine.connect() as connection:
                # Delete existing items for this project
                connection.execute(
                    delete(self.items)
                    .where(self.items.c.Project_ID == project_id)
                )
                
                # Insert new items
                for _, row in db_df.iterrows():
                    values = {
                        'Item_ID': row['Item_ID'],
                        'Project_ID': row['Project_ID'],
                        'Item_Name': row['Item_Name'],
                        'Team': row['Team'],
                        'Start_Date': row['Start_Date'],
                        'End_Date': row['End_Date'],
                        'Months': row['Months']
                    }
                    connection.execute(insert(self.items).values(**values))
                
                connection.commit()
                logger.info(f"Saved {len(db_df)} items for project {project_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error in save_project_items: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def get_team_colors(self):
        """Return team colors for visualization"""
        return {
            'Procurement': '#0D47A1',    # Dark Blue
            'Construction': '#FFD700',   # Gold
            'Development': '#9C27B0',    # Purple
            'Interconnection': '#00BCD4'  # Bright Turquoise
        }
    
    def add_project_item(self, project_id, item_data):
        """Add a single item to a project"""
        try:
            # Get existing items for this project
            items_df = self.get_project_items(project_id)
            
            # Generate a new Item ID
            if items_df.empty:
                new_item_id = f"I001"
            else:
                # Find the highest item ID number and increment
                item_ids = items_df['Item ID'].tolist()
                item_numbers = [int(item_id[1:]) for item_id in item_ids if item_id.startswith('I') and item_id[1:].isdigit()]
                if item_numbers:
                    new_item_number = max(item_numbers) + 1
                else:
                    new_item_number = 1
                new_item_id = f"I{new_item_number:03d}"
            
            # Add required fields to item_data
            item_data['Item ID'] = new_item_id
            item_data['Project ID'] = project_id
            
            # Create a dataframe with the new item
            new_item_df = pd.DataFrame([item_data])
            
            # Combine with existing items
            combined_df = pd.concat([items_df, new_item_df], ignore_index=True)
            
            # Save all items
            return self.save_project_items(combined_df)
            
        except Exception as e:
            logger.error(f"Error adding project item: {e}")
            return False
