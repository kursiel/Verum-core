"""Outbox scaffolding for future Hacienda integration.

Future:
- Persist domain events in same DB transaction.
- Worker (Celery/RQ) polls unpublished events and publishes to broker.
- Mark as published with retry + backoff + idempotency key.
"""

from sqlalchemy.orm import Session

from app.models import OutboxEvent


class OutboxPublisher:
    def __init__(self, db: Session):
        self.db = db

    def enqueue(self, event: OutboxEvent) -> OutboxEvent:
        self.db.add(event)
        self.db.flush()
        return event
