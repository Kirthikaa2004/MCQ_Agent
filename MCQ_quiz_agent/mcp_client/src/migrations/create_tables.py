from src.repositories.database import Database,Base,get_database
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine
from src.repositories.schemas.user_schema import User
from src.utils.helper import logger


db = Database()
async def create_tables(engine:AsyncEngine) -> None:
    """Create all database tables if they don't already exist."""
    
    try:
        async with engine.begin() as conn:
            # run_sync allows you to call synchronous metadata methods 
            # using the underlying synchronous connection
            await conn.run_sync(Base.metadata.create_all)
        await seed_data()
    except Exception as e:
        print(f"Error while running create_tables: {str(e)}")



async def seed_data() -> None:
    """Seed initial menu items into the database if empty."""


    try:

        async with db.get_session() as db_session:
            if db_session is None:
                print("Error: session is None. Check your yield statement.")
                return
    
            query = select(User).where(User.is_active== True)
            
            results = await db_session.execute(query)
            
            existing_users = results.scalars().first()

            if existing_users:
                logger.info("[Migrations] Seed data already exists, skipping.")
                return

        
            user_list = [
                    User(
                        username="alex_dev_99",
                        created_by="signup_module"
                    ),
                    User(
                        username="system_monitor_bot",
                        created_by="infra_setup",
                        updated_by="infra_setup"
                    ),
                    User(
                        username="temp_tester_01",
                        created_by="qa_team"
                    ),
                    User(
                        username="manager_dashboard",
                        created_by="admin_panel"
                    ),
                    User(
                        username="legacy_data_migrator",
                        created_by="migration_script"
                    )
    ]
            
            db_session.add_all(user_list)
            
            await db_session.commit()
            
            logger.info(f"[Migrations] Seeded {len(user_list)} users successfully.")
    except Exception as e:
        await db_session.rollback()
        logger.info(f"[Migrations] Seed failed: {e}")
    finally:

        await db_session.close()
