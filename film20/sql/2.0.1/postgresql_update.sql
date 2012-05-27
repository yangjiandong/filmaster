ALTER TABLE "externallink_externallink" add "moderation_status" integer NOT NULL DEFAULT 1;
ALTER TABLE "externallink_externallink" add "moderation_status_at" timestamp with time zone;
ALTER TABLE "externallink_externallink" add "moderation_status_by_id" integer;
ALTER TABLE "externallink_externallink" add "rejection_reason" text;

ALTER TABLE "externallink_externallink" ADD CONSTRAINT "moderation_status_by_id_refs_id_cbef06c" FOREIGN KEY ("moderation_status_by_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "externallink_externallink_moderation_status_by_id" ON "externallink_externallink" ( "moderation_status_by_id" );
