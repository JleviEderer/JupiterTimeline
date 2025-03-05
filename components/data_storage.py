import os
import logging

# Set up logging
logging.basicConfig(
    filename='app.log',
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_storage')

def get_data_manager():
    """
    Factory function to create the appropriate data manager
    Uses PostgreSQL if available, otherwise falls back to CSV storage
    """
    # Check if DATABASE_URL environment variable is set
    if os.environ.get('DATABASE_URL'):
        try:
            # Try to import and use the database manager
            from components.db_manager import DBManager
            logger.info("Using PostgreSQL database for data storage")
            return DBManager()
        except Exception as e:
            logger.error(f"Error initializing database: {e}. Falling back to CSV storage.")
            # Fall back to CSV storage if there's an error
            from components.data_manager import DataManager
            return DataManager()
    else:
        # Use CSV storage if DATABASE_URL is not set
        logger.info("DATABASE_URL not found. Using CSV storage")
        from components.data_manager import DataManager
        return DataManager()
