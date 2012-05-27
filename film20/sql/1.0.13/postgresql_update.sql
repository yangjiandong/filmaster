alter table notification_noticetype alter column "label" type varchar(64);
alter table notification_noticetype alter column "display" type varchar(100);
update notification_noticetype set label='showtimes_near_cinema_check_in' where label='showtimes_cinema_check_in';
update notification_noticetype set label='showtimes_near_cinema_check_in_cancel' where label='showtimes_cinema_check_in_cancel';

-- New field in useractivity to display link to cinema in checkin template
ALTER TABLE "useractivity_useractivity" DROP COLUMN "channel";
ALTER TABLE "useractivity_useractivity" ADD COLUMN "channel_name" varchar(128);
alter table useractivity_useractivity add column "channel_id" integer REFERENCES "showtimes_channel" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "useractivity_useractivity_channel_id" ON "useractivity_useractivity" ("channel_id");

alter table core_profile add column "recommendations_status" integer;
alter table core_profile add column "recommendations_notice_sent" integer;

update core_profile p set recommendations_status=(select recommendations_status from core_usermeta where user_id=p.user_id) where is_primary=true;
update core_profile set recommendations_status = 1 where recommendations_status is null;
update core_profile p set recommendations_notice_sent=(select recommendations_notice_sent from core_usermeta where user_id=p.user_id) where is_primary=true;
update core_profile set recommendations_notice_sent = 1 where recommendations_notice_sent is null;

-- verified_imdb_code for core_person 
alter table core_person add column verified_imdb_code boolean default false;
update notification_noticetype set label='useractivity_check_in' where label='showtimes_check_in';
update notification_noticetype set label='useractivity_check_in_cancel' where label='showtimes_check_in_cancel';

-- rejection reason in moderated items 
ALTER TABLE "add_films_addedfilm" ADD COLUMN "rejection_reason" text;
ALTER TABLE "posters_moderatedphoto" ADD COLUMN "rejection_reason" text;
