# Plan: Add Webhook Retry Logic with Exponential Backoff

## Context

The webhook delivery system currently fails silently when external services are temporarily unavailable. This leads to lost events and requires manual reprocessing. This plan adds automatic retry logic with exponential backoff, dead-letter queue support, and observability hooks for monitoring retry attempts.

---

## Change 1: Add RetryPolicy configuration

**File:** `src/config/webhooks.ts`

Add a `RetryPolicy` type and default configuration:

```typescript
export interface RetryPolicy {
  maxAttempts: number;
  initialDelayMs: number;
  maxDelayMs: number;
  backoffMultiplier: number;
}

export const DEFAULT_RETRY_POLICY: RetryPolicy = {
  maxAttempts: 5,
  initialDelayMs: 1000,
  maxDelayMs: 60000,
  backoffMultiplier: 2.0,
};
```

---

## Change 2: Implement exponential backoff calculator

**File:** `src/webhooks/retry.py`

Create a new module with the retry logic:

```python
from dataclasses import dataclass
from typing import Optional
import time
import random


@dataclass
class RetryConfig:
    max_attempts: int = 5
    initial_delay_ms: int = 1000
    max_delay_ms: int = 60000
    backoff_multiplier: float = 2.0


def calculate_backoff_delay(attempt: int, config: RetryConfig) -> int:
    """Calculate delay in milliseconds with exponential backoff and jitter."""
    if attempt <= 0:
        return 0
    
    delay = config.initial_delay_ms * (config.backoff_multiplier ** (attempt - 1))
    delay = min(delay, config.max_delay_ms)
    
    # Add jitter: randomize ±20% to prevent thundering herd
    jitter = delay * 0.2 * (2 * random.random() - 1)
    return int(delay + jitter)


def should_retry(attempt: int, status_code: Optional[int], config: RetryConfig) -> bool:
    """Determine if a webhook delivery should be retried."""
    if attempt >= config.max_attempts:
        return False
    
    # Retry on network errors (status_code is None) or 5xx server errors
    if status_code is None or status_code >= 500:
        return True
    
    # Retry on 429 (rate limit)
    if status_code == 429:
        return True
    
    return False
```

**Tests:**

Create `tests/test_retry_logic.py` with:

- Test `calculate_backoff_delay` for attempt 1, 3, 5 (verify exponential growth)
- Test jitter stays within ±20%
- Test max delay cap is enforced
- Test `should_retry` returns True for 500, 502, 503, 429, None
- Test `should_retry` returns False for 200, 400, 401, 404

---

## Change 3: Update WebhookDelivery model with retry tracking

**File:** `src/models/webhook.py`

Add retry-related fields to the `WebhookDelivery` database model:

```python
class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    
    id = Column(String, primary_key=True)
    webhook_id = Column(String, ForeignKey("webhooks.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    target_url = Column(String, nullable=False)
    
    # Existing fields
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    
    # New retry fields
    attempt_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    last_error_message = Column(String, nullable=True)
    last_status_code = Column(Integer, nullable=True)
```

**Migration:** Generate Alembic migration with `alembic revision --autogenerate -m "add retry fields to webhook deliveries"`

---

## Change 4: Implement retry queue processor

**File:** `src/webhooks/processor.ts`

Add a background job that processes retries:

```typescript
import { WebhookDelivery, DeliveryStatus } from '../models/webhook';
import { DEFAULT_RETRY_POLICY, RetryPolicy } from '../config/webhooks';
import { deliverWebhook } from './delivery';
import { logger } from '../utils/logger';

export async function processRetryQueue(
  policy: RetryPolicy = DEFAULT_RETRY_POLICY
): Promise<void> {
  const now = new Date();
  
  // Find deliveries ready for retry
  const pendingRetries = await WebhookDelivery.findAll({
    where: {
      status: DeliveryStatus.PENDING,
      nextRetryAt: { $lte: now },
      attemptCount: { $lt: policy.maxAttempts },
    },
    limit: 100,
  });
  
  logger.info(`Processing ${pendingRetries.length} webhook retries`);
  
  for (const delivery of pendingRetries) {
    try {
      await deliverWebhook(delivery, policy);
    } catch (error) {
      logger.error(`Retry processor error for delivery ${delivery.id}`, error);
    }
  }
}

async function scheduleNextRetry(
  delivery: WebhookDelivery,
  policy: RetryPolicy
): Promise<void> {
  const delayMs = calculateBackoffDelay(delivery.attemptCount + 1, policy);
  const nextRetry = new Date(Date.now() + delayMs);
  
  await delivery.update({
    nextRetryAt: nextRetry,
  });
}
```

---

## Change 5: Wire up retry processor to job scheduler

**File:** `src/jobs/scheduler.ts`

Register the retry processor to run every minute:

```typescript
import { processRetryQueue } from '../webhooks/processor';
import { CronJob } from 'cron';

export function initializeJobScheduler(): void {
  // Existing jobs...
  
  // Webhook retry processor - runs every minute
  const retryJob = new CronJob('* * * * *', async () => {
    await processRetryQueue();
  });
  
  retryJob.start();
  logger.info('Webhook retry processor scheduled');
}
```

---

## Verification

1. Deploy the changes to staging
2. Simulate a webhook failure (point a webhook at a non-existent endpoint)
3. Verify `attempt_count` increments and `next_retry_at` advances exponentially
4. Verify delivery succeeds once the endpoint becomes available
5. Verify deliveries move to dead-letter status after `maxAttempts` is exceeded
6. Run the test suite and confirm all retry logic tests pass
7. Check logs for retry attempts and confirm jitter is applied (delays vary slightly)
