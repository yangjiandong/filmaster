alter table "core_profile" add column "timezone_id" varchar(40);
alter table "showtimes_town" add column "timezone_id" varchar(40);
alter table "showtimes_channel" add column "timezone_id" varchar(40);
alter table "showtimes_screening" add column "utc_time" timestamp with time zone;
update core_profile set metacritic_name='' where metacritic_name is null;
-- FLM-726
CREATE UNIQUE INDEX "unique_verified_email" ON "emailconfirmation_emailaddress"("email") WHERE verified='t';
update core_profile set metacritic_name='' where metacritic_name is null;
alter table "showtimes_filmonchannel" add column "source" varchar(32) NOT NULL default '';
ALTER TABLE "useractivity_useractivity" ALTER COLUMN "url" TYPE character varying(2048);

delete from core_profile where is_primary=false;
alter table core_profile drop constraint one_profile_per_user_per_lang;
select user_id, id from core_profile where user_id in (select user_id from core_profile group by user_id having count(user_id)>1) order by user_id, id;
ALTER TABLE "core_profile" ADD CONSTRAINT "one_profile_per_user" UNIQUE ("user_id");

ALTER TABLE core_userratingtimerange DROP constraint core_userratingtimerange_user_id_key;
ALTER TABLE core_userratingtimerange ADD CONSTRAINT one_timerange_per_user_lang UNIQUE ("user_id", "LANG");
