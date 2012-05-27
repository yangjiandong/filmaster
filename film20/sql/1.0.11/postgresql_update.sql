/* Conversations, http://jira.filmaster.org/browse/API-29 */
delete from search_queueditem;
alter table search_queueditem add "LANG" character varying(2) NOT NULL;

alter table messages_message add column "conversation_id" integer;
ALTER TABLE "messages_message" ADD CONSTRAINT "conversation_id_refs_id_60c8b216" FOREIGN KEY ("conversation_id") REFERENCES "messages_conversation" ("id") DEFERRABLE INITIALLY DEFERRED;
alter table "core_profile" add column "twitter_user_id" varchar(32);
alter table "core_profile" add column "foursquare_user_id" varchar(16);

#drop index "one_twitter_association_per_profile";
#create unique index "one_twitter_association_per_profile" on "core_profile"("twitter_user_id", "LANG") where "twitter_user_id" is not null;
#drop index "one_foursquare_association_per_profile";
#create unique index "one_foursquare_association_per_profile" on "core_profile"("foursquare_user_id", "LANG") where "foursquare_user_id" is not null;

alter table core_profile add column "mobile_platform" varchar(16);
alter table core_profile add column "mobile_first_login_at" timestamp with time zone;
alter table core_profile add column "mobile_last_login_at" timestamp with time zone;
alter table core_profile add column "mobile_login_cnt" integer NOT NULL default 0;
alter table "notification_noticequeuebatch" add column "priority" integer NOT NULL default 0;
alter table "notification_noticequeuebatch" add column "created_at" timestamp with time zone;

# http://jira.filmaster.org/browse/FLM-570
alter table "useractivity_useractivity" add column "is_sent" boolean NOT NULL default true;

/* 77. add an index for core_person's imdb_code to accept nulls but still be unique*/
ALTER TABLE core_person ALTER column imdb_code DROP NOT NULL;
update core_person set imdb_code = null where imdb_code in (select imdb_code from core_person group by imdb_code having count(*)>1);
CREATE UNIQUE INDEX "one_imdb_code_per_person" on "core_person"("imdb_code") WHERE "imdb_code" IS NOT NULL;
