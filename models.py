from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from sqlalchemy import Index

from config import settings


Base = declarative_base()


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, index=True)  # wbfirmid
    account = Column(String)  # wbaccount
    name = Column(String)  # wbname
    domain = Column(String, index=True)  # wbdomain
    state = Column(Integer)  # wbstatus
    alias_domains = Column(Text)  # wbaliasdomains
    create_date = Column(DateTime)  # wbregisterdate


class Attachment(Base):
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, index=True)  # owner from remote
    show_name = Column(String)  # wbshowname
    file_path = Column(String)  # wbfilepath
    url_path = Column(String)  # wburlpath
    file_ext = Column(String)  # wbext
    create_date = Column(DateTime)  # wbcreatedate
    
    # Additional fields for content extraction
    text_content = Column(Text, default="")  # Extracted text from documents
    ocr_content = Column(Text, default="")  # OCR extracted text from images
    llm_content = Column(Text, default="")  # LLM extracted content from complex images
    has_id_card = Column(Boolean, default=False)  # Whether contains ID card numbers
    has_phone = Column(Boolean, default=False)  # Whether contains phone numbers
    
    # Manual verification fields
    manual_verified_sensitive = Column(Boolean, default=False)  # Whether manually verified to contain sensitive info
    verification_notes = Column(Text, default="")  # Notes for manual verification


def get_database_url():
    """Generate database URL based on configuration"""
    if settings.LOCAL_DB_TYPE == "sqlite":
        return f"sqlite:///{settings.LOCAL_DB_PATH}"
    elif settings.LOCAL_DB_TYPE == "postgresql":
        return f"postgresql://{settings.LOCAL_DB_USER}:{settings.LOCAL_DB_PASSWORD}@{settings.LOCAL_DB_HOST}:{settings.LOCAL_DB_PORT}/{settings.LOCAL_DB_NAME}"
    elif settings.LOCAL_DB_TYPE == "mysql":
        return f"mysql+pymysql://{settings.LOCAL_DB_USER}:{settings.LOCAL_DB_PASSWORD}@{settings.LOCAL_DB_HOST}:{settings.LOCAL_DB_PORT}/{settings.LOCAL_DB_NAME}"
    else:
        raise ValueError(f"Unsupported database type: {settings.LOCAL_DB_TYPE}")


# Create local database engine
engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create indices for better performance
Index('idx_site_owner', Site.owner)
Index('idx_site_domain', Site.domain)
Index('idx_attachment_site_id', Attachment.site_id)
Index('idx_attachment_file_ext', Attachment.file_ext)
Index('idx_attachment_has_id_card', Attachment.has_id_card)
Index('idx_attachment_has_phone', Attachment.has_phone)