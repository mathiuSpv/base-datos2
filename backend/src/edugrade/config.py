from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    app_name: str

    mongo_host: str
    mongo_port: int
    mongo_user: str
    mongo_password: str
    mongo_db: str
    
    neo4j_host: str
    neo4j_port: int
    neo4j_user: str
    neo4j_password: str

    cassandra_hosts: list[str]
    cassandra_port: int
    cassandra_keyspace: str

    redis_host: str
    redis_port: int
    redis_db: int

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}/admin"
            f"?authSource=admin&directConnection=true"
        )

    @property
    def neo4j_uri(self) -> str:
        return f"bolt://{self.neo4j_host}:{self.neo4j_port}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

settings = Settings()