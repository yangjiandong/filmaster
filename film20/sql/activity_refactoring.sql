/* rename rated_objects_html to content */
ALTER TABLE "useractivity_useractivity" RENAME COLUMN "rated_objects_html" TO content;

/* remove unused table "useractivity_useractivity_rated_objects" */
DROP TABLE "useractivity_useractivity_rated_objects";

/* remove unused fields */
ALTER TABLE "useractivity_useractivity" DROP COLUMN "rate_type";
ALTER TABLE "useractivity_useractivity" DROP COLUMN "rated_objects_count";
ALTER TABLE "useractivity_useractivity" DROP COLUMN "person_id";
ALTER TABLE "useractivity_useractivity" DROP COLUMN "number_of_ratings";

/* new columns */
ALTER TABLE "useractivity_useractivity" ADD COLUMN title character varying(200);
ALTER TABLE "useractivity_useractivity" ADD COLUMN film_title text;
ALTER TABLE "useractivity_useractivity" ADD COLUMN film_permalink text;
ALTER TABLE "useractivity_useractivity" ADD COLUMN url character varying(200);
ALTER TABLE "useractivity_useractivity" ADD COLUMN url_kind integer;
ALTER TABLE "useractivity_useractivity" ADD COLUMN video_thumb character varying(50);
ALTER TABLE "useractivity_useractivity" ADD COLUMN username character varying(30);
ALTER TABLE "useractivity_useractivity" ADD COLUMN spoilers boolean DEFAULT FALSE;
ALTER TABLE "useractivity_useractivity" ADD COLUMN is_first_post boolean DEFAULT FALSE;
ALTER TABLE "useractivity_useractivity" ADD COLUMN number_of_comments integer DEFAULT 0;

/* populate number_of_comments with data from core_object */
update useractivity_useractivity set number_of_comments = (select number_of_comments from core_object where core_object.id=useractivity_useractivity.object_id) WHERE useractivity_useractivity.object_id in (select distinct id from core_object);
/* add status to useractivity */
alter table useractivity_useractivity add column status integer;
/* add permalink to useractivity */
alter table useractivity_useractivity add column permalink character varying(512);
/* add not null constrain to permalink */
/* add indexes to django_content_type TODO: talk with borys about it */
CREATE INDEX "django_content_type_app_label" ON "django_content_type" ("app_label");
CREATE INDEX "django_content_type_model" ON "django_content_type" ("model");

/* checkin activity */
alter table useractivity_useractivity add column checkin_id integer REFERENCES "showtimes_screeningcheckin" ("id") DEFERRABLE INITIALLY DEFERRED;
alter table useractivity_useractivity add column channel varchar(128);
alter table useractivity_useractivity add column checkin_date timestamp with time zone;

update useractivity_useractivity ua set username = (select auth_user.username from useractivity_useractivity u join auth_user on user_id = auth_user.id and ua.id=u.id);

delete from useractivity_useractivity where link_id in (select link_id from useractivity_useractivity where link_id is not null group by link_id having count(id)>1);
delete from useractivity_useractivity where post_id in (select post_id from useractivity_useractivity where post_id is not null group by post_id having count(id)>1);
delete from useractivity_useractivity where short_review_id in (select short_review_id from useractivity_useractivity where short_review_id is not null group by short_review_id having count(id)>1);
delete from useractivity_useractivity where comment_id in (select comment_id from useractivity_useractivity where comment_id is not null group by comment_id having count(id)>1);
delete from useractivity_useractivity where checkin_id in (select checkin_id from useractivity_useractivity where checkin_id is not null group by checkin_id having count(id)>1);

CREATE UNIQUE INDEX "one_activity_per_link" on "useractivity_useractivity"("link_id") WHERE "link_id" IS NOT NULL;
CREATE UNIQUE INDEX "one_activity_per_post" on "useractivity_useractivity"("post_id") WHERE "post_id" IS NOT NULL;
CREATE UNIQUE INDEX "one_activity_per_short_review" on "useractivity_useractivity"("short_review_id") WHERE "short_review_id" IS NOT NULL;
CREATE UNIQUE INDEX "one_activity_per_comment" on "useractivity_useractivity"("comment_id") WHERE "comment_id" IS NOT NULL;
CREATE UNIQUE INDEX "one_activity_per_checkin" on "useractivity_useractivity"("checkin_id") WHERE "checkin_id" IS NOT NULL;
 