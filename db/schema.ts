import { pgTable, text, timestamp } from 'drizzle-orm/pg-core';

export const states = pgTable('states', {
  username: text('username').primaryKey(),
  state: text('state').notNull(),
  updatedAt: timestamp('updated_at', { mode: 'string' }).defaultNow().notNull(),
});
