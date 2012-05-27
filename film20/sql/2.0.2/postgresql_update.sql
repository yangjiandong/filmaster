alter table "festivals_festival" add column "hashtag" varchar(50);
CREATE TABLE "festivals_festival_theaters" (
        "id" serial NOT NULL PRIMARY KEY,
        "festival_id" integer NOT NULL,
        "channel_id" integer NOT NULL REFERENCES "showtimes_channel" ("id") DEFERRABLE INITIALLY DEFERRED,
        UNIQUE ("festival_id", "channel_id")
);
ALTER TABLE "festivals_festival_theaters" ADD CONSTRAINT "festival_id_refs_parent_id_34f77343" FOREIGN KEY ("festival_id") REFERENCES "festivals_festival" ("parent_id") DEFERRABLE INITIALLY DEFERRED;

-- few missing indexes

CREATE INDEX "core_userratingtimerange_user_id" ON "core_userratingtimerange" ("user_id");
CREATE INDEX "useractivity_useractivity_person_id" ON "useractivity_useractivity" ("person_id");
CREATE INDEX "useractivity_useractivity_checkin_id" ON "useractivity_useractivity" ("checkin_id");

CREATE INDEX "showtimes_tvchannel_country_id" ON "showtimes_tvchannel" ("country_id");
CREATE INDEX "showtimes_screeningcheckin_film_id" ON "showtimes_screeningcheckin" ("film_id");

-- http://jira.filmaster.org/browse/FLM-1462
ALTER TABLE core_shortreview ALTER review_text TYPE character varying(1000);

alter table showtimes_screening add column "info" varchar(64);

alter table festivals_festival add column "event_image" varchar(100);
