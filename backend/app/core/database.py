from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

# Strip unsupported query params and build asyncpg-compatible URL
def _build_db_url(raw_url: str) -> tuple[str, dict]:
    """
    Convert Neon/standard postgres URL to asyncpg-compatible format.
    asyncpg doesn't support sslmode/channel_binding — pass ssl via connect_args.
    """
    from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
    parsed = urlparse(raw_url.replace("postgresql://", "postgresql+asyncpg://"))
    params = parse_qs(parsed.query, keep_blank_values=True)

    # Parameters asyncpg handles via connect_args, not URL
    ssl_mode = (params.pop("sslmode", ["require"])[0])
    params.pop("channel_binding", None)
    params.pop("options", None)

    clean_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=clean_query))

    connect_args = {}
    if ssl_mode in ("require", "verify-ca", "verify-full"):
        import ssl as ssl_lib
        ctx = ssl_lib.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl_lib.CERT_NONE
        connect_args["ssl"] = ctx

    return clean_url, connect_args


_db_url, _connect_args = _build_db_url(settings.DATABASE_URL)

engine = create_async_engine(
    _db_url,
    echo=settings.APP_ENV == "development",
    pool_size=10,
    max_overflow=20,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
