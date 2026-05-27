from sqlalchemy import inspect, text


def ensure_dev_schema(engine) -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "media_sources" not in table_names:
        return

    source_existing = {column["name"] for column in inspector.get_columns("media_sources")}
    source_additions = {
        "channel": "VARCHAR",
        "thumbnail": "VARCHAR",
        "status": "VARCHAR NOT NULL DEFAULT 'ready'",
        "transcript_status": "VARCHAR NOT NULL DEFAULT 'completed'",
        "chunks_count": "INTEGER NOT NULL DEFAULT 0",
        "error_message": "TEXT",
    }

    with engine.begin() as connection:
        for column, ddl in source_additions.items():
            if column not in source_existing:
                connection.execute(text(f"ALTER TABLE media_sources ADD COLUMN {column} {ddl}"))

        if "processing_jobs" in table_names:
            job_existing = {column["name"] for column in inspector.get_columns("processing_jobs")}
            job_additions = {
                "job_id": "VARCHAR",
                "source_type": "VARCHAR",
                "progress": "INTEGER NOT NULL DEFAULT 0",
                "input_value": "TEXT",
                "title": "VARCHAR",
                "thumbnail_url": "VARCHAR",
                "duration": "FLOAT",
                "channel": "VARCHAR",
                "chunks_count": "INTEGER NOT NULL DEFAULT 0",
            }
            for column, ddl in job_additions.items():
                if column not in job_existing:
                    connection.execute(text(f"ALTER TABLE processing_jobs ADD COLUMN {column} {ddl}"))
