-- Remove "one_review_per_user_object" constrain to allow posting more than one shortreview by user
ALTER TABLE core_shortreview DROP CONSTRAINT "one_review_per_user_object";

-- Add null constrain to shortreview reviewed object
ALTER TABLE core_shortreview ALTER "object_id" DROP NOT NULL;

-- Add kind field to shortreview
AlTER TABLE core_shortreview ADD COLUMN "kind" integer NULL;
UPDATE core_shortreview SET kind = 2;
ALTER TABLE core_shortreview ALTER COLUMN "kind" SET NOT NULL;

-- Add featured field to useractivity
alter table useractivity_useractivity add column featured boolean NOT NULL default false;

-- showtimes
alter table "showtimes_tvchannel" add column "country_id" integer REFERENCES "showtimes_country" ("id") not null;
alter table showtimes_channel add column "last_screening_time" timestamp with time zone;
update showtimes_channel c set last_screening_time = (select max(utc_time) from showtimes_screening where channel_id = c.id);

alter table showtimes_screening alter column utc_time set not null;
alter table showtimes_screening drop column date;
alter table showtimes_screening drop column time;

alter table showtimes_channel add column "is_active" boolean NOT NULL default true;
alter table showtimes_channel add column "icon" varchar(100);

alter table showtimes_tvchannel drop column wp_id;
alter table showtimes_tvchannel drop column is_active;
alter table showtimes_tvchannel drop column lang;

alter table showtimes_cinema add column fetcher1_id varchar(128);

update showtimes_cinema c set fetcher1_id = (select fetcher1_id from showtimes_channel where id=channel_ptr_id);

alter table showtimes_screeningcheckin add column "film_id" integer REFERENCES "core_film" ("parent_id") DEFERRABLE INITIALLY DEFERRED;
alter table showtimes_screeningcheckin alter column screening_id drop not null;
update showtimes_screeningcheckin set film_id = (select f.film_id from showtimes_screening s join showtimes_filmonchannel f on s.film_id = f.id where s.id = screening_id);
alter table showtimes_screeningcheckin add column "number_of_comments" integer NOT NULL default 0;

drop index "one_short_review_per_user_film_lang";

alter table useractivity_useractivity add column "person_id" integer REFERENCES "core_person" ("parent_id") DEFERRABLE INITIALLY DEFERRED;

alter table messages_conversation add column "is_replied" boolean NOT NULL default false;

alter table festivals_festival add column "supported" boolean NOT NULL default true;
alter table festivals_festival add column "country_code" varchar(2) default 'PL';
alter table festivals_festival add column "latitude" numeric(10, 6);
alter table festivals_festival add column "longitude" numeric(10, 6);

alter table showtimes_channel add column "is_default" boolean NOT NULL default false;

alter table festivals_festival add column "background_image" varchar(100);
alter table festivals_festival add column "background_image_lowres" varchar(100);
alter table festivals_festival add column "menu_header_image" varchar(100);
alter table festivals_festival add column "menu_header_image_lowres" varchar(100);
alter table festivals_festival add column "menu_icon_image" varchar(100);
alter table festivals_festival add column "menu_icon_image_lowres" varchar(100);
alter table festivals_festival add column "rate_films_image" varchar(100);
alter table festivals_festival add column "rate_films_image_lowres" varchar(100);
alter table festivals_festival add column "suggestions_image" varchar(100);
alter table festivals_festival add column "suggestions_image_lowres" varchar(100);
alter table festivals_festival add column "showtimes_image" varchar(100);
alter table festivals_festival add column "showtimes_image_lowres" varchar(100);
alter table festivals_festival add column "community_image" varchar(100);
alter table festivals_festival add column "community_image_lowres" varchar(100);
alter table festivals_festival add column "stream_image" varchar(100);
alter table festivals_festival add column "stream_image_lowres" varchar(100);

alter table festivals_festival add column "short_name" varchar(20);

alter table core_rating add column "number_of_comments" integer NULL;

-- FLM-1139
update useractivity_useractivity a set username = (select username from auth_user where id = a.user_id) where a.username is null or a.username='';
-- fix activities 
alter table useractivity_useractivity add column slug varchar(512) NULL;
alter table useractivity_useractivity add column subdomain varchar(30) NULL;

alter table core_film add column "hires_image" varchar(256);
alter table core_person add column "hires_image" varchar(256);

-- execute following line if your posters disappeared, do not use on prod!
-- update core_film set hires_image = image;

-- http://jira.filmaster.org/browse/FLM-1172
update useractivity_useractivity set status=4 where user_id in (select id from auth_user where is_active=False) and status=1;

alter table core_person add column tmdb_import_status integer null;

-- One short review per film (for old short reviews)
CREATE UNIQUE INDEX "one_short_review_per_user_film_lang" ON "core_shortreview"(object_id, user_id, "LANG") WHERE kind=2;
