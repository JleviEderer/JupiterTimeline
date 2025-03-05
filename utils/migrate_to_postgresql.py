import os
import pandas as pd
import logging
import sys
import argparse

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('migration')

def migrate_data(force=False):
    """
    Migrate data from CSV files to PostgreSQL database
    
    Args:
        force (bool): If True, overwrite existing data in database. If False, only migrate if tables are empty.
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    try:
        # Check if DATABASE_URL is set
        if not os.environ.get('DATABASE_URL'):
            logger.error("DATABASE_URL environment variable not set. Cannot migrate to database.")
            return False
            
        logger.info("Starting migration from CSV to PostgreSQL...")
        
        # Import database manager
        try:
            from components.db_manager import DBManager
            db_manager = DBManager()
            logger.info("Database manager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database manager: {e}")
            return False
        
        # Check if projects table has data (if not forcing migration)
        if not force:
            with db_manager.engine.connect() as connection:
                project_count = connection.execute(
                    "SELECT COUNT(*) FROM projects"
                ).scalar()
                
                if project_count > 0:
                    logger.info(f"Database already has {project_count} projects. Use --force to overwrite.")
                    return False
        
        # If forcing migration, clear existing data
        if force:
            logger.info("Forcing migration - clearing existing database data")
            with db_manager.engine.connect() as connection:
                connection.execute("DELETE FROM items")
                connection.execute("DELETE FROM projects")
                connection.commit()
        
        # Read CSV files
        try:
            projects_df = pd.read_csv("data/projects.csv")
            logger.info(f"Read {len(projects_df)} projects from CSV")
            
            try:
                items_df = pd.read_csv("data/items.csv")
                logger.info(f"Read {len(items_df)} items from CSV")
            except FileNotFoundError:
                items_df = pd.DataFrame()
                logger.warning("items.csv not found, creating empty dataframe")
        except FileNotFoundError:
            logger.error("projects.csv not found, cannot migrate")
            return False
        
        # Process projects data
        projects_df = projects_df.rename(columns={"Target COD": "Target_COD"})
        projects_df['Target_COD'] = pd.to_datetime(projects_df['Target_COD'], format='mixed')
        
        # Insert projects into database
        projects_df.to_sql('projects', db_manager.engine, if_exists='append', index=False)
        logger.info(f"Migrated {len(projects_df)} projects to database")
        
        # Process items data if it exists
        if not items_df.empty:
            items_df = items_df.rename(columns={
                "Item ID": "Item_ID",
                "Project ID": "Project_ID",
                "Item Name": "Item_Name",
                "Start Date": "Start_Date",
                "End Date": "End_Date"
            })
            
            # Convert date columns
            items_df['Start_Date'] = pd.to_datetime(items_df['Start_Date'], format='mixed')
            items_df['End_Date'] = pd.to_datetime(items_df['End_Date'], format='mixed')
            
            # Insert items into database
            items_df.to_sql('items', db_manager.engine, if_exists='append', index=False)
            logger.info(f"Migrated {len(items_df)} items to database")
        
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate data from CSV to PostgreSQL")
    parser.add_argument('--force', action='store_true', help='Force migration even if tables have data')
    args = parser.parse_args()
    
    success = migrate_data(force=args.force)
    if success:
        print("Migration completed successfully")
    else:
        print("Migration failed, see migration.log for details")
        sys.exit(1)
