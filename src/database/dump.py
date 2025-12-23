import subprocess
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Optional

from src.config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseDumper:
    """Class for creating and managing database dumps."""

    def __init__(self, dump_dir: str = "dumps"):
        self.dump_dir = Path(dump_dir)
        self.dump_dir.mkdir(exist_ok=True)

    def create_dump(self) -> Optional[Path]:
        """Create a database dump file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_file = self.dump_dir / f"dump_{timestamp}.sql"

        # Extract database connection details from URL
        # URL format: postgresql://user:password@host:port/database
        db_url = str(settings.database_url)

        try:
            # Parse connection details
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "")

            parts = db_url.split("@")
            if len(parts) != 2:
                logger.error("Invalid database URL format")
                return None

            user_pass, host_db = parts
            user, password = user_pass.split(":")
            host_port, database = host_db.split("/")

            if ":" in host_port:
                host, port = host_port.split(":")
            else:
                host = host_port
                port = "5432"

            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = password

            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h",
                host,
                "-p",
                port,
                "-U",
                user,
                "-d",
                database,
                "-f",
                str(dump_file),
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-acl",
            ]

            # Execute dump command
            logger.info(f"Creating database dump: {dump_file}")
            result = subprocess.run(
                cmd, env=env, capture_output=True, text=True, check=True
            )

            if result.returncode == 0:
                file_size = dump_file.stat().st_size / (1024 * 1024)  # MB
                logger.info(
                    f"Dump created successfully: {dump_file} ({file_size:.2f} MB)"
                )
                return dump_file
            else:
                logger.error(f"pg_dump failed: {result.stderr}")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating dump: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating dump: {e}")
            return None

    def cleanup_old_dumps(self):
        """Remove old dump files based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=settings.keep_dumps_days)

        try:
            files_removed = 0
            for dump_file in self.dump_dir.glob("dump_*.sql"):
                # Extract date from filename: dump_YYYYMMDD_HHMMSS.sql
                try:
                    date_str = dump_file.stem.split("_")[1]  # YYYYMMDD
                    file_date = datetime.strptime(date_str, "%Y%m%d")

                    if file_date < cutoff_date:
                        dump_file.unlink()
                        files_removed += 1
                        logger.debug(f"Removed old dump file: {dump_file}")
                except (IndexError, ValueError):
                    # Skip files with invalid names
                    continue

            if files_removed > 0:
                logger.info(f"Removed {files_removed} old dump files")

        except Exception as e:
            logger.error(f"Error cleaning up old dumps: {e}")

    def list_dumps(self) -> list:
        """List all dump files with metadata."""
        dumps = []
        for dump_file in sorted(self.dump_dir.glob("dump_*.sql"), reverse=True):
            try:
                stat = dump_file.stat()
                dumps.append(
                    {
                        "name": dump_file.name,
                        "path": str(dump_file),
                        "size_mb": stat.st_size / (1024 * 1024),
                        "created": datetime.fromtimestamp(stat.st_ctime),
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                    }
                )
            except Exception:
                continue

        return dumps

    def get_latest_dump(self) -> Optional[Path]:
        """Get the most recent dump file."""
        dumps = sorted(
            self.dump_dir.glob("dump_*.sql"), key=os.path.getmtime, reverse=True
        )
        return dumps[0] if dumps else None
