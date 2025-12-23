#!/usr/bin/env python3
"""
Test database connection
"""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.append(str(Path(__file__).parent))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database():
    """Test database connection."""
    max_retries = 5
    retry_delay = 3
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to connect to database...")
            
            from src.database.session import engine
            from sqlalchemy import text
            
            # Try to connect - CORRECT WAY FOR SQLAlchemy 2.0
            with engine.connect() as conn:
                # Використовуйте text() для SQL запитів
                result = conn.execute(text("SELECT version(), current_database(), current_user"))
                row = result.fetchone()
                
                logger.info("✅ Database connection successful!")
                logger.info(f"   PostgreSQL Version: {row[0]}")
                logger.info(f"   Database: {row[1]}")
                logger.info(f"   User: {row[2]}")
                
                # Check if tables exist
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result.fetchall()]
                
                if tables:
                    logger.info(f"   Existing tables: {', '.join(tables)}")
                else:
                    logger.info("   No tables found (this is normal for first run)")
                
                return True
                
        except Exception as e:
            logger.warning(f"❌ Database connection failed: {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Max retries reached. Could not connect to database. Error: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    return False

def create_tables_test():
    """Test table creation."""
    try:
        from src.database.session import create_tables
        
        logger.info("Creating database tables...")
        create_tables()
        logger.info("✅ Tables created successfully")
        
        # Verify tables were created
        from src.database.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"📋 Current tables: {', '.join(tables)}")
            
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Database Connection Test")
    logger.info("=" * 50)
    
    # Test connection
    if test_database():
        # Test table creation
        create_tables_test()
        
        logger.info("=" * 50)
        logger.info("✅ All database tests passed!")
        logger.info("=" * 50)
    else:
        logger.error("=" * 50)
        logger.error("❌ Database tests failed!")
        logger.error("=" * 50)
        sys.exit(1)