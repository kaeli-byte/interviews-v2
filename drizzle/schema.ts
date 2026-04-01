import {
  boolean,
  doublePrecision,
  index,
  integer,
  jsonb,
  pgTable,
  text,
  timestamp,
  uniqueIndex,
  uuid,
  varchar,
} from "drizzle-orm/pg-core";

export const documents = pgTable("documents", {
  id: uuid("id").primaryKey(),
  userId: uuid("user_id").notNull(),
  kind: varchar("kind", { length: 50 }).notNull(),
  type: varchar("type", { length: 50 }),
  sourceType: varchar("source_type", { length: 50 }),
  filename: varchar("filename", { length: 255 }),
  mimeType: varchar("mime_type", { length: 255 }),
  storagePath: varchar("storage_path", { length: 500 }),
  filePath: varchar("file_path", { length: 500 }),
  sourceUrl: text("source_url"),
  rawText: text("raw_text"),
  content: jsonb("content").$type<Record<string, unknown>>().default({}),
  parseStatus: varchar("parse_status", { length: 50 }).default("pending"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
});

export const profiles = pgTable("profiles", {
  id: uuid("id").primaryKey(),
  documentId: uuid("document_id").references(() => documents.id, { onDelete: "set null" }),
  userId: uuid("user_id").notNull(),
  profileType: varchar("profile_type", { length: 50 }).notNull(),
  name: varchar("name", { length: 255 }),
  headline: text("headline"),
  skills: text("skills"),
  experience: text("experience"),
  company: varchar("company", { length: 255 }),
  role: varchar("role", { length: 255 }),
  requirements: text("requirements"),
  confidenceScore: doublePrecision("confidence_score"),
  structuredJson: jsonb("structured_json").$type<Record<string, unknown>>().default({}),
  summaryText: text("summary_text"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
});

export const agentConfigs = pgTable("agent_configs", {
  id: uuid("id").primaryKey(),
  name: varchar("name", { length: 100 }).notNull(),
  description: text("description"),
  promptTemplate: text("prompt_template").notNull(),
  behaviorSettings: jsonb("behavior_settings").$type<Record<string, unknown>>().default({}),
  rubricDefinition: jsonb("rubric_definition").$type<Record<string, unknown>[]>().default([]),
  version: integer("version").default(1),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow(),
}, (table) => ({
  isActiveCreatedAtIdx: index("agent_configs_is_active_created_at_idx").on(table.isActive, table.createdAt),
}));

export const interviewContexts = pgTable("interview_contexts", {
  id: uuid("id").primaryKey(),
  userId: uuid("user_id").notNull(),
  resumeProfileId: uuid("resume_profile_id").references(() => profiles.id, { onDelete: "set null" }),
  jobProfileId: uuid("job_profile_id").references(() => profiles.id, { onDelete: "set null" }),
  agentId: uuid("agent_id").references(() => agentConfigs.id, { onDelete: "set null" }),
  customInstructions: text("custom_instructions"),
  matchAnalysisJson: jsonb("match_analysis_json").$type<Record<string, unknown>>().default({}),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow(),
}, (table) => ({
  userCreatedAtIdx: index("interview_contexts_user_created_at_idx").on(table.userId, table.createdAt),
  agentIdIdx: index("interview_contexts_agent_id_idx").on(table.agentId),
}));

export const sessions = pgTable("sessions", {
  id: uuid("id").primaryKey(),
  userId: uuid("user_id").notNull(),
  contextId: uuid("context_id").references(() => interviewContexts.id, { onDelete: "set null" }),
  agentId: uuid("agent_id").references(() => agentConfigs.id, { onDelete: "set null" }),
  status: varchar("status", { length: 50 }).default("pending"),
  startedAt: timestamp("started_at", { withTimezone: true }).defaultNow(),
  endedAt: timestamp("ended_at", { withTimezone: true }),
  transcript: jsonb("transcript").$type<Record<string, unknown>[]>().default([]),
  reconnectToken: uuid("reconnect_token").notNull(),
}, (table) => ({
  userStartedAtIdx: index("sessions_user_started_at_idx").on(table.userId, table.startedAt),
  reconnectTokenIdx: uniqueIndex("sessions_reconnect_token_idx").on(table.reconnectToken),
  contextIdIdx: index("sessions_context_id_idx").on(table.contextId),
  agentIdIdx: index("sessions_agent_id_idx").on(table.agentId),
}));

export const debriefs = pgTable("debriefs", {
  id: uuid("id").primaryKey(),
  sessionId: uuid("session_id").references(() => sessions.id, { onDelete: "cascade" }).notNull(),
  userId: uuid("user_id").notNull(),
  scores: jsonb("scores").$type<Record<string, number>>().default({}),
  feedback: text("feedback"),
  evidence: jsonb("evidence").$type<Record<string, unknown>[]>().default([]),
  rubricUsed: jsonb("rubric_used").$type<Record<string, unknown>[]>().default([]),
  generatedAt: timestamp("generated_at", { withTimezone: true }).defaultNow(),
});
