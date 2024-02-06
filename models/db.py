import os

import requests
from sqlalchemy import URL, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DOWNLOAD_CERT_URL = "https://storage.yandexcloud.net/cloud-certs/CA.pem"
CERT_PATH = "~/.postgresql/root.crt"


def _download_db_cert():
    file_path = os.path.expanduser(CERT_PATH)
    directory = os.path.dirname(file_path)

    if not os.path.exists(directory):
        os.makedirs(directory)

    if os.path.exists(file_path):
        return

    cert = requests.get(DOWNLOAD_CERT_URL).text
    with open(file_path, "w") as file:
        file.write(cert)


_download_db_cert()


db_url = URL.create(
    "postgresql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(port) if isinstance((port := os.getenv("DB_PORT")), str) else None,
    database=os.getenv("DB_NAME"),
    query={"sslmode": "verify-full"},
)


Session = sessionmaker(bind=create_engine(db_url, pool_pre_ping=True))
SessionMaker = Session


_naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    metadata = MetaData(naming_convention=_naming_convention)
