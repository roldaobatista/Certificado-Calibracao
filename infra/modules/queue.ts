/**
 * Abstract queue interface for async outbox pattern.
 * Production requires SQS, RabbitMQ, Azure Service Bus, or similar.
 */

export interface QueueMessage {
  id: string;
  type: string;
  payload: unknown;
  metadata?: Record<string, string>;
  timestamp: Date;
}

export interface QueueEnqueueInput {
  type: string;
  payload: unknown;
  metadata?: Record<string, string>;
  delayMs?: number;
}

export interface QueueProvider {
  enqueue(input: QueueEnqueueInput): Promise<QueueMessage>;
  dequeue(batchSize?: number): Promise<QueueMessage[]>;
  acknowledge(messageId: string): Promise<void>;
  retry(messageId: string, delayMs?: number): Promise<void>;
  deadLetter(messageId: string, reason: string): Promise<void>;
}

// Stub implementation for development.
// Uses in-memory array — all messages are lost on restart.
export function createDevQueueProvider(): QueueProvider {
  const messages: QueueMessage[] = [];
  const inFlight = new Map<string, QueueMessage>();
  const deadLetterQueue: Array<{ message: QueueMessage; reason: string }> = [];

  return {
    async enqueue(input) {
      const message: QueueMessage = {
        id: `dev-msg-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        type: input.type,
        payload: input.payload,
        metadata: input.metadata ?? {},
        timestamp: new Date(Date.now() + (input.delayMs ?? 0)),
      };
      messages.push(message);
      return message;
    },
    async dequeue(batchSize = 1) {
      const now = new Date();
      const batch: QueueMessage[] = [];
      for (let i = 0; i < messages.length && batch.length < batchSize; ) {
        if (messages[i].timestamp <= now) {
          const [msg] = messages.splice(i, 1);
          inFlight.set(msg.id, msg);
          batch.push(msg);
        } else {
          i++;
        }
      }
      return batch;
    },
    async acknowledge(messageId) {
      inFlight.delete(messageId);
    },
    async retry(messageId, delayMs = 5000) {
      const msg = inFlight.get(messageId);
      if (!msg) return;
      inFlight.delete(messageId);
      messages.push({ ...msg, timestamp: new Date(Date.now() + delayMs) });
    },
    async deadLetter(messageId, reason) {
      const msg = inFlight.get(messageId);
      if (msg) {
        inFlight.delete(messageId);
        deadLetterQueue.push({ message: msg, reason });
      }
    },
  };
}
