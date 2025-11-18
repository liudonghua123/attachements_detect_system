import psycopg2
from sqlalchemy.orm import Session
from models import Site, Attachment
from config import settings
from datetime import datetime
import requests
import os
from utils import extract_text_from_file, contains_id_card, contains_phone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RemoteDBSync:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.remote_conn = None
        
    def connect_remote_db(self):
        """Connect to remote PostgreSQL database"""
        try:
            self.remote_conn = psycopg2.connect(
                host=settings.REMOTE_DB_HOST,
                port=settings.REMOTE_DB_PORT,
                database=settings.REMOTE_DB_NAME,
                user=settings.REMOTE_DB_USER,
                password=settings.REMOTE_DB_PASSWORD
            )
            logger.info("Connected to remote database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to remote database: {str(e)}")
            raise

    def sync_sites(self):
        """Sync site information from remote database - sync ALL sites"""
        if not self.remote_conn:
            self.connect_remote_db()

        try:
            cursor = self.remote_conn.cursor()

            # Query to get site information - sync ALL sites
            query = """
            SELECT
                f.wbfirmid as owner,
                f.wbaccount as account,
                f.wbname as name,
                f.wbregisterdate as create_date,
                h.wbdomain as domain,
                h.wbstatus as state,
                h.wbaliasdomains as aliasdomains
            FROM wbfirm f
            LEFT JOIN wbvirhost h ON h.owner = f.wbfirmid
            """

            cursor.execute(query)
            results = cursor.fetchall()

            # Update local database
            for row in results:
                owner, account, name, create_date, domain, state, aliasdomains = row

                # Handle NULL values
                domain = domain or ""
                state = state or 0
                aliasdomains = aliasdomains or ""
                create_date = create_date or None

                # Check if site already exists, update if it does, otherwise create new
                existing_site = self.db.query(Site).filter(Site.owner == owner).first()

                if existing_site:
                    existing_site.account = account
                    existing_site.name = name
                    existing_site.domain = domain
                    existing_site.state = state
                    existing_site.alias_domains = aliasdomains
                    existing_site.create_date = create_date
                else:
                    site = Site(
                        owner=owner,
                        account=account,
                        name=name,
                        domain=domain,
                        state=state,
                        alias_domains=aliasdomains,
                        create_date=create_date
                    )
                    self.db.add(site)

            self.db.commit()
            logger.info(f"Synced {len(results)} sites from remote database")

        except Exception as e:
            logger.error(f"Error syncing sites: {str(e)}")
            self.db.rollback()
            raise
        finally:
            cursor.close()

    def sync_attachments(self, site_owner_filter=None):
        """Sync attachment information from remote database"""
        if not self.remote_conn:
            self.connect_remote_db()

        try:
            cursor = self.remote_conn.cursor()

            # Query to get attachment information
            query = """
            SELECT f.owner, f.wbshowname, f.wbfilepath, s.wburlpath, f.wbext, f.wbcreatedate
            FROM wbnewsfile AS f
            LEFT JOIN wbstoragefile s ON s.wbshorturl =
                CASE
                    WHEN f.wbfilepath LIKE '%?%' THEN SUBSTRING(f.wbfilepath, 1, POSITION('?' IN f.wbfilepath) - 1)
                    ELSE f.wbfilepath
                END
            WHERE s.wburlpath is not null
            """

            if site_owner_filter:
                query += f" AND f.owner = '{site_owner_filter}'"

            cursor.execute(query)
            results = cursor.fetchall()

            # Update local database
            for row in results:
                owner, wbshowname, wbfilepath, wburlpath, wbext, wbcreatedate = row

                # Check if attachment already exists
                # Normalize the URL path by adding the base URL prefix if not already present
                full_url_path = wburlpath
                if wburlpath and not wburlpath.startswith(('http://', 'https://')):
                    if settings.ATTACHMENT_DEFAULT_BASE_URL:
                        full_url_path = f"{settings.ATTACHMENT_DEFAULT_BASE_URL}{wburlpath}"
                    else:
                        full_url_path = wburlpath

                existing_attachment = self.db.query(Attachment).filter(
                    Attachment.file_path == wbfilepath,
                    Attachment.url_path == wburlpath  # Use original path for lookup to maintain consistency
                ).first()

                # Only update if there's no existing record or the new record has a newer create_date
                if existing_attachment:
                    # If we have an existing record, only update if the new one is newer
                    if wbcreatedate and (not existing_attachment.create_date or wbcreatedate > existing_attachment.create_date):
                        existing_attachment.show_name = wbshowname
                        existing_attachment.site_id = owner
                        existing_attachment.file_ext = wbext
                        existing_attachment.create_date = wbcreatedate
                        # Update the URL path with the base URL prefix
                        existing_attachment.url_path = full_url_path
                else:
                    # Create new attachment
                    attachment = Attachment(
                        site_id=owner,
                        show_name=wbshowname,
                        file_path=wbfilepath,
                        url_path=full_url_path,  # Use the full URL path with base prefix
                        file_ext=wbext,
                        create_date=wbcreatedate
                    )
                    self.db.add(attachment)

            self.db.commit()
            logger.info(f"Synced {len(results)} attachments from remote database")

        except Exception as e:
            logger.error(f"Error syncing attachments: {str(e)}")
            self.db.rollback()
            raise
        finally:
            cursor.close()

    def sync_all_sites(self):
        """Sync all sites (this is always done as one batch)"""
        self.sync_sites()

    def sync_all_attachments(self):
        """Sync all attachments"""
        self.sync_attachments()

    def sync_attachments_for_site(self, site_owner):
        """Sync attachments for a specific site"""
        self.sync_attachments(site_owner_filter=site_owner)

    def close(self):
        """Close connections"""
        if self.remote_conn:
            self.remote_conn.close()