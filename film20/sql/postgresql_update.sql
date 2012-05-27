/*1. Numeric */
ALTER TABLE core_rating DROP COLUMN normalized;
ALTER TABLE core_rating DROP COLUMN guess_rating_alg1;
ALTER TABLE core_rating DROP COLUMN guess_rating_alg2;

ALTER TABLE core_rating ADD COLUMN normalized numeric(6, 4) NULL;
ALTER TABLE core_rating ADD COLUMN guess_rating_alg1 numeric(6, 4) NULL;
ALTER TABLE core_rating ADD COLUMN guess_rating_alg2 numeric(6, 4) NULL;


/*2. Column length */
alter table core_filmlocalized alter column description type character varying(500);


/*3. Short review refactoring */
alter table core_shortreview add column "created_at" timestamp with time zone NOT NULL default now();
alter table core_shortreview add column "updated_at" timestamp with time zone NOT NULL default now();
update core_shortreview r set created_at = coalesce((select coalesce(last_rated, now()) from core_rating where id=r.rating_id), now());
update core_shortreview r set updated_at = coalesce((select coalesce(last_rated, now()) from core_rating where id=r.rating_id), now());

/*4. Film comparator - common films  */
ALTER TABLE core_ratingcomparator ADD COLUMN common_films integer NULL;

/* 5. Person ID */
ALTER TABLE useractivity_useractivity ADD COLUMN "person_id" integer NULL REFERENCES "core_person" ("parent_id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "useractivity_useractivity_person_id" ON "useractivity_useractivity" ("person_id");

/* 6. Longer description */
alter table core_filmlocalized alter column "description" TYPE character varying(1500) ;

/* 7. Character - lang */
ALTER TABLE core_character ADD "LANG" character varying(2) not null DEFAULT 'en';
INSERT INTO core_character(person_id, film_id, importance, character, "LANG") SELECT person_id, film_id, importance, character, 'pl' FROM core_character WHERE "LANG"='en';

/* 8. Descriptions in filmlocalized */
ALTER TABLE "core_filmlocalized" ADD "fetched_description" varchar(5000) NULL;
ALTER TABLE "core_filmlocalized" ADD "fetched_description_url" varchar(100) NULL;
ALTER TABLE "core_filmlocalized" ADD "fetched_description_url_text" varchar(100) NULL;
ALTER TABLE "core_filmlocalized" ADD "fetched_description_type" integer NULL;

/* 9. Generic forum title and description */
ALTER TABLE forum_forum ADD COLUMN "description" text NULL;
ALTER TABLE forum_forum ADD COLUMN "title" varchar(128) NULL;

/*10. Obsluga obrazkow */
ALTER TABLE "core_person" ADD COLUMN "image" varchar(100) NULL;
ALTER TABLE "core_film" ADD COLUMN "image" varchar(100) NULL;

ALTER TABLE "core_person" ALTER COLUMN "imdb_code" TYPE varchar(128);

/*11. Obsluga rezysera */
ALTER TABLE "core_person" ADD COLUMN "writer_popularity_month" integer DEFAULT 0 NOT NULL;
ALTER TABLE "core_person" ADD COLUMN "writer_popularity" integer DEFAULT 0 NOT NULL;
ALTER TABLE "core_person" ADD COLUMN "is_writer" boolean DEFAULT FALSE NOT NULL;

ALTER TABLE "core_personlog" ADD COLUMN "is_writer" boolean DEFAULT FALSE NOT NULL;
ALTER TABLE "core_personlog" ADD COLUMN "writer_popularity_month" integer DEFAULT 0 NOT NULL;
ALTER TABLE "core_personlog" ADD COLUMN "writer_popularity" integer DEFAULT 0 NOT NULL;

CREATE TABLE "core_film_writers" (
    "id" serial NOT NULL PRIMARY KEY,
    "film_id" integer NOT NULL REFERENCES "core_film" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    "person_id" integer NOT NULL REFERENCES "core_person" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("film_id", "person_id")
)
;

/*12. Zmiana typu danych dla imdb_code*/
ALTER TABLE "core_person" ALTER COLUMN "imdb_code" TYPE varchar(128);
ALTER TABLE "core_film" ALTER COLUMN "imdb_code" TYPE varchar(128);

/*13. Dodanie kraju produkcji filmu */
ALTER TABLE "core_film" ADD COLUMN "production_country_list" varchar(256) NULL;
CREATE TABLE "core_country" ("id" serial NOT NULL PRIMARY KEY, "country" varchar(128) NULL);
CREATE TABLE "core_film_production_country" (
    "id" serial NOT NULL PRIMARY KEY,
    "film_id" integer NOT NULL REFERENCES "core_film" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    "country_id" integer NOT NULL REFERENCES "core_country" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("film_id", "country_id")
)
;

/*14. Dodanie pola  is_published  do notek */
ALTER TABLE blog_post ADD COLUMN "is_published" boolean DEFAULT false NOT NULL;
/*15. DĹ‚uĹĽsze opisy dla fetched_description */
ALTER TABLE "core_filmlocalized" ALTER COLUMN "fetched_description_url" TYPE character varying(200);
ALTER TABLE "core_filmlocalized" ALTER COLUMN "fetched_description_url_text" TYPE character varying(200);

/*16. Rating Comparator refactoring: FLM-563 */
ALTER TABLE "core_ratingcomparator" ADD COLUMN "sum_difference" integer DEFAULT 0 NOT NULL;
alter table "core_ratingcomparator" add column "created_at" timestamp with time zone NOT NULL default now();
alter table "core_ratingcomparator" add column "updated_at" timestamp with time zone NOT NULL default now();
alter table "core_ratingcomparator" add column "previous_save_date" timestamp with time zone NULL;
UPDATE "core_ratingcomparator" SET sum_difference = -1;
CREATE INDEX "core_ratingcomparator_updated_at" on "core_ratingcomparator"("updated_at");

/* 17. Oskary - altery */
ALTER TABLE "core_rating" DROP CONSTRAINT "one_rating_per_film" ;
ALTER TABLE "core_rating" ADD CONSTRAINT "one_rating_per_film" UNIQUE
("parent_id" , "user_id", "type", "actor_id");
ALTER TABLE event_nominated ADD COLUMN oscar_type INTEGER;

/* 18. Normalizowanie tytulow filmow */
ALTER TABLE "core_filmlocalized" add column "title_normalized" character varying(128);
CREATE INDEX core_filmlocalized_title_normalized ON core_filmlocalized USING btree (title_normalized);
ALTER TABLE "core_film" add column "title_normalized" varchar(128);
CREATE INDEX core_film_title_normalized ON core_film USING btree (title_normalized);

CREATE TABLE core_searchkey
(
  id serial NOT NULL,
  object_id integer NOT NULL,
  object_localized_id integer,
  key_normalized character varying(128),
  key_root character varying(128),
  key_letters character varying(128) NOT NULL,
  text_length integer NOT NULL,
  CONSTRAINT core_searchkey_pkey PRIMARY KEY (id),
  CONSTRAINT core_searchkey_object_id_fkey FOREIGN KEY (object_id)
      REFERENCES core_object (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT core_searchkey_object_localized_id_fkey FOREIGN KEY (object_localized_id)
      REFERENCES core_objectlocalized (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED
)
WITH (OIDS=FALSE);
ALTER TABLE core_searchkey OWNER TO film20;

-- Index: core_searchkey_object_id

-- DROP INDEX core_searchkey_object_id;

CREATE INDEX core_searchkey_object_id
  ON core_searchkey
  USING btree
  (object_id);

-- Index: core_searchkey_object_localized_id

-- DROP INDEX core_searchkey_object_localized_id;

CREATE INDEX core_searchkey_object_localized_id
  ON core_searchkey
  USING btree
  (object_localized_id);

CREATE INDEX core_searchkey_key_normalized
  ON core_searchkey
  USING btree
  (key_normalized);

CREATE INDEX core_searchkey_key_root
  ON core_searchkey
  USING btree
  (key_root);  
  
CREATE INDEX core_searchkey_key_letters
  ON core_searchkey
  USING btree
  (key_letters);  

/* 19 last updated - for ratings */
ALTER TABLE core_rating ADD COLUMN last_displayed timestamp with time zone NULL;

/* 20. number of ratings for recommendations */
ALTER TABLE core_rating ADD COLUMN number_of_ratings integer NULL;

/* 21 dla rekomendacji */
alter table core_ratingcomparator add column score_to_recom numeric(4,2)  null;
update core_ratingcomparator set score_to_recom = 5 - (score / 0.5);

/* 22 Wyszukiwarka osob oraz lepsze indeksy + personlocalized */

DROP INDEX core_film_title_normalized;
DROP INDEX core_filmlocalized_title_normalized;
CREATE INDEX core_filmlocalized_title_normalized ON core_filmlocalized USING btree (title_normalized varchar_pattern_ops);
CREATE INDEX core_film_title_normalized ON core_film USING btree (title_normalized varchar_pattern_ops);

DROP INDEX core_searchkey_key_normalized;
DROP INDEX core_searchkey_key_root;
DROP INDEX core_searchkey_key_letteres;

CREATE INDEX core_searchkey_key_normalized ON core_searchkey USING btree (key_normalized varchar_pattern_ops);
CREATE INDEX core_searchkey_key_root ON core_searchkey USING btree (key_root varchar_pattern_ops);    
CREATE INDEX core_searchkey_key_letters ON core_searchkey USING btree (key_letters varchar_pattern_ops);  


CREATE TABLE core_personlocalized
(
  object_localized_id integer NOT NULL,
  person_id integer NOT NULL,
  "name" character varying(50) NOT NULL,
  surname character varying(50) NOT NULL,
  CONSTRAINT core_personlocalized_pkey PRIMARY KEY (object_localized_id),
  CONSTRAINT core_personlocalized_object_localized_id_fkey FOREIGN KEY (object_localized_id)
      REFERENCES core_objectlocalized (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT core_personlocalized_person_id_fkey FOREIGN KEY (person_id)
      REFERENCES core_person (parent_id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED
)
WITH (OIDS=FALSE);
ALTER TABLE core_personlocalized OWNER TO film20;

CREATE INDEX core_personlocalized_person_id ON core_personlocalized USING btree (person_id);
CREATE INDEX core_personlocalized_surname_name ON core_personlocalized USING btree(surname, "name");
CREATE INDEX core_personlocalized_surname_name_upper ON core_personlocalized USING btree(upper(surname::text), upper("name"::text));
CREATE INDEX core_personlocalized_surname_name_ilike ON core_personlocalized USING btree(upper(surname::text), upper("name"::text) varchar_pattern_ops);

/* 23. Oznaczenie SPOILER przed tytulem notki */
ALTER TABLE blog_post ADD COLUMN "spoilers" boolean DEFAULT false NOT NULL;

/* 24. Wagi tagow */
ALTER TABLE tagging_tag ADD COLUMN "weight" numeric(4,2);

/* 25. LANG dla notek */
ALTER TABLE blog_post ADD "LANG" character varying(2) not null DEFAULT 'pl';

/* 26. Lokalizacja forum */
ALTER TABLE threadedcomments_threadedcomment ADD "LANG" character varying(2) not null DEFAULT 'pl';
ALTER TABLE threadedcomments_freethreadedcomment ADD "LANG" character varying(2) not null DEFAULT 'pl';
ALTER TABLE forum_thread ADD "LANG" character varying(2) not null DEFAULT 'pl';

/* 27. Notki - poprawna data publikacji */
ALTER TABLE "blog_post" ADD COLUMN "is_public" boolean DEFAULT FALSE NOT NULL;
ALTER TABLE "blog_post" ALTER COLUMN "publish" DROP NOT NULL;

/* 28. Wagi tagow cd. */
ALTER TABLE tagging_tag DROP COLUMN weight;
ALTER TABLE tagging_tag ADD COLUMN "weight" integer;

/* 29. Aliasy tagĂłw */
CREATE TABLE tagging_tagalias
(
  id serial NOT NULL,
  "name" character varying(50) NOT NULL,
  tag_id integer NOT NULL,
  CONSTRAINT tagging_tagalias_pkey PRIMARY KEY (id),
  CONSTRAINT tagging_tagalias_tag_id_fkey FOREIGN KEY (tag_id)
      REFERENCES tagging_tag (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT tagging_tagalias_name_key UNIQUE (name)
)
WITH (OIDS=FALSE);
ALTER TABLE tagging_tagalias OWNER TO film20;

CREATE INDEX tagging_tagalias_tag_id ON tagging_tagalias USING btree (tag_id);
CREATE INDEX tagging_tagalias_name_id ON tagging_tagalias USING btree (upper(name::text));

/* 30. Pole is_closed - na forum */
ALTER TABLE "forum_thread" ADD COLUMN "is_closed" boolean DEFAULT FALSE;
/* 31 LANG w Profile */
ALTER TABLE core_profile ADD "LANG" character varying(2) not null DEFAULT 'pl';
ALTER TABLE core_profile DROP CONSTRAINT core_profile_user_id_key;
-- only one localized profile per user (one in each language)
ALTER TABLE "core_profile" ADD CONSTRAINT "one_profile_per_user_per_lang" UNIQUE ("user_id" , "LANG");
ALTER TABLE "core_profile" ADD COLUMN "is_primary" boolean DEFAULT FALSE NOT NULL;
/* 32 */
ALTER TABLE "core_profile" ALTER COLUMN "is_primary" SET DEFAULT TRUE;

/* 33 Better criticker import */
alter table import_ratings_importratings add column overwrite_rating boolean;
alter table core_film add column criticker_id character  varying(16);
create index core_film_imdb_code on core_film (imdb_code);
create index core_film_criticker_id on core_film (criticker_id);
alter table core_film add column verified_imdb_code boolean default false;

alter table core_filmlocalized alter column "description" TYPE character varying(15000) ;
alter table core_filmlocalized alter column "fetched_description" TYPE character varying(15000) ;

/* 34. Editor moderation for imported movies */
ALTER TABLE "import_films_filmtoimport" ADD COLUMN "status" integer NOT NULL DEFAULT 1;

/* 35. Email constraint hack */
update auth_user set email = '' where id in(1208, 602, 52);
CREATE UNIQUE INDEX "auth_user_email" on "auth_user"("email") WHERE "email"<>'';

/* 36. Short review longer */
ALTER TABLE core_shortreview ALTER COLUMN review_text TYPE character varying(500);

/* 37. Comment is_first_post */
alter table threadedcomments_threadedcomment add column is_first_post boolean DEFAULT FALSE;

/* 38. Object ID in useractivity */
alter table useractivity_useractivity ADD COLUMN "object_id" integer NULL REFERENCES "core_object" ("id") DEFERRABLE INITIALLY DEFERRED;

/* 39. Unique username */
create unique index unique_username_case_insensitive on auth_user (lower(username));

/* 40. Thread inheriting from object */
alter table forum_thread drop constraint forum_thread_pkey;
alter table forum_thread add column "parent_id" integer NULL;
insert into core_object(type, permalink, status, version) (select 7, permalink, 1, 1 from forum_thread);
update forum_thread t1 set parent_id = (select id from core_object where permalink = t1.permalink and type=7 limit 1);
alter table forum_thread alter column "parent_id" SET NOT NULL;

-- START: fix 'polski-tytul': to trzeba z glowa!!!
--select * from forum_thread where parent_id=621292;
--select * from core_object where permalink='polski-tytul';
update forum_thread set parent_id=621387 where id=177; -- nie kopiowac, wziac drugie ID z core_object!!!
-- END

alter table forum_thread add constraint "forum_thread_pkey" PRIMARY KEY(parent_id);
update threadedcomments_threadedcomment c set object_id = (select parent_id from forum_thread where id=c.object_id) where object_id in (select id from forum_thread);

-- update user activity object_ids
update useractivity_useractivity set object_id = post_id  where activity_type=1;
update useractivity_useractivity set object_id = short_review_id  where activity_type=2;
update useractivity_useractivity set object_id = (select object_id from threadedcomments_threadedcomment where id=useractivity_useractivity.comment_id) where activity_type=3;

-- watching
insert into useractivity_watching(object_id, user_id, watching_type, is_observed, is_auto, created_at, updated_at) (select p.parent_id, b.user_id, 1, true, true, now(), now() from blog_post p left join blog_blog b on b.id=p.author_id);
insert into useractivity_watching(object_id, user_id, watching_type, is_observed, is_auto, created_at, updated_at) (select parent_id, user_id, 1, true, true, now(), now() from core_shortreview);
insert into useractivity_watching(object_id, user_id, watching_type, is_observed, is_auto, created_at, updated_at) (select object_id, user_id, 1, true, true, now(), now() from threadedcomments_threadedcomment where is_first_post=true);

/* 41. Core_rating */
CREATE INDEX non_null_rating_for_per_film ON core_rating (parent_id, type) WHERE rating is not null;

/* 42. Optimize useractivity */
CREATE INDEX "useractivity_useractivity_created_at" ON "useractivity_useractivity" ("created_at");

/* 43. ENH9 hack */
ALTER TABLE core_film ADD COLUMN is_enh9 BOOLEAN DEFAULT FALSE;
UPDATE core_film SET is_enh9 = true where parent_id in (select parent_id from core_objectlocalized ol LEFT JOIN tagging_taggeditem tti ON tti.object_id = ol.id LEFT JOIN tagging_tag tt ON tt.id = tti.tag_id WHERE ol."LANG"='pl' AND tti.content_type_id='18' AND tt.name IN ('enh9'));

ALTER TABLE core_ratingcomparator ADD COLUMN score2 decimal;

-- tags
alter table tagging_tag drop constraint tagging_tag_name_key;
ALTER TABLE "tagging_tag" ADD CONSTRAINT "tagging_tag_name_key" UNIQUE ("name" , "LANG");

/* 44. Email field longer */
ALTER TABLE auth_user ALTER COLUMN email TYPE character varying(255);

/* 45. Unique constraint for user and activity in django_digg table */
alter table django_digg_vote add UNIQUE (activity_id, user_id);

/* 46. Logs - longer comments */
alter table core_filmlog alter column comment type character varying(40000);
alter table core_personlog alter column comment type character varying(40000);

/* 47. Event - status */
ALTER TABLE event_event ADD COLUMN event_status integer NULL;
UPDATE event_event SET event_status = 2;
alter table event_event alter column "event_status" SET NOT NULL;

/* 48. Externallink inherits form core_object */
alter table externallink_externallink drop constraint externallink_externallink_pkey;
alter table externallink_externallink add column permalink character varying(128);
alter table externallink_externallink add column "parent_id" integer NULL;
update "externallink_externallink" e1 set "permalink" = (select 'link-' || "externallink_externallink"."id" from "externallink_externallink" where e1.id = id limit 1);
insert into core_object(type, permalink, status, version) (select 8, permalink, 1, 1 from externallink_externallink);
update externallink_externallink e1 set parent_id = (select id from core_object where permalink = e1.permalink and type=8 limit 1);
alter table externallink_externallink alter column "parent_id" SET NOT NULL;
alter table externallink_externallink add constraint "externallink_externallink_pkey" PRIMARY KEY(parent_id);
update useractivity_useractivity a1 set object_id = (select parent_id from externallink_externallink where a1.link_id=externallink_externallink.id and a1.activity_type=5) where a1.activity_type=5;

/* 49. Setting all status to 1 */
update "core_object" set status=1 where status!=1;

/* 50. Creating externalink status */
update "core_object" e1 set "status"=2 where (select is_deleted from "externallink_externallink" where is_deleted=True and e1.id="externallink_externallink"."parent_id" limit 1);

/* 51. Removing unused columns */
alter table "externallink_externallink" drop column is_deleted;
alter table "externallink_externallink" drop column permalink;
alter table "externallink_externallink" drop column id;
update core_object set permalink='LINK' where type=8;

/* 52. Moving post_status to core_object.status */
update "core_object" e1 set "status"=1 where exists (select post_status from "blog_post" where "blog_post"."post_status"=2 and e1.id="blog_post"."parent_id" limit 1);
update "core_object" e1 set "status"=2 where exists (select post_status from "blog_post" where "blog_post"."post_status"=1 and e1.id="blog_post"."parent_id" limit 1);
update "core_object" e1 set "status"=3 where exists (select post_status from "blog_post" where "blog_post"."post_status"=3 and e1.id="blog_post"."parent_id" limit 1);

/* 53. Removed post_status */
alter table "blog_post" drop column post_status;

/* 54. Create index for link_id */
CREATE INDEX useractivity_useractivity_link_id ON useractivity_useractivity USING btree (link_id);
  
/* 55. Create index for object_id */ 
CREATE INDEX useractivity_useractivity_object_id ON useractivity_useractivity USING btree (object_id);  

/* 56. watching_object column */
alter table useractivity_useractivity add column "watching_object_id" integer NULL;
update useractivity_useractivity set watching_object_id=object_id;
CREATE INDEX useractivity_useractivity_watching_object_id ON useractivity_useractivity USING btree (watching_object_id); 
  
/* 57. Link object ids */
update useractivity_useractivity set link_id=object_id where activity_type=5;

/* 58. Threadedcomment inherits form core_object */
alter table threadedcomments_threadedcomment drop constraint parent_id_refs_id_7ef2a789;
alter table threadedcomments_threadedcomment drop constraint threadedcomments_threadedcomment_pkey;
alter table threadedcomments_threadedcomment add column "parent_object_id" integer NULL;
alter table threadedcomments_threadedcomment add column permalink character varying(128);
update "threadedcomments_threadedcomment" e1 set "permalink" = (select 'comment-' || "threadedcomments_threadedcomment"."id" from "threadedcomments_threadedcomment" where e1.id = id limit 1);
insert into core_object(type, permalink, status, version) (select 9, permalink, 1, 1 from threadedcomments_threadedcomment);
update threadedcomments_threadedcomment e1 set parent_object_id = (select id from core_object where permalink = e1.permalink and type=9 limit 1);
alter table "threadedcomments_threadedcomment" alter column "parent_object_id" SET NOT NULL;
alter table threadedcomments_threadedcomment add constraint "threadedcomments_threadedcomment_pkey" PRIMARY KEY(parent_object_id);
update "threadedcomments_threadedcomment" e1 set "parent_id" = (select "parent_object_id" from "threadedcomments_threadedcomment" where e1.parent_id = id limit 1);
ALTER TABLE "threadedcomments_threadedcomment" ADD CONSTRAINT "parent_id_refs_parent_object_id_7ef2a789" FOREIGN KEY ("parent_id") REFERENCES "threadedcomments_threadedcomment" ("parent_object_id") DEFERRABLE INITIALLY DEFERRED;
update useractivity_useractivity a1 set comment_id=(select parent_object_id from threadedcomments_threadedcomment where a1.comment_id=threadedcomments_threadedcomment.id) where activity_type=3;
update useractivity_useractivity set object_id=comment_id where activity_type=3;

/* 59. unused columns */
alter table "threadedcomments_threadedcomment" drop column permalink;
alter table "threadedcomments_threadedcomment" drop column id;
update core_object set permalink='COMMENT' where type=9;

/* 60. localized blog titles */
ALTER TABLE blog_blog ADD column "LANG" character varying(2) not null DEFAULT 'pl';
INSERT INTO blog_blog(user_id, title, "LANG") SELECT user_id, title, 'en' FROM blog_blog WHERE "LANG"='pl';
alter table blog_post add column "user_id" integer NULL;
update "blog_post" set "user_id" = (select "user_id" from "blog_blog" where "blog_blog"."id"="blog_post"."author_id");
update blog_post set author_id = (select id from blog_blog where blog_blog.user_id=blog_post.user_id and blog_blog."LANG"=blog_post."LANG");
alter table blog_post drop column user_id;

/* 61.Number of comments in core_object */
alter table core_object add column "number_of_comments" integer null;
update core_object set number_of_comments = (select count(*) from threadedcomments_threadedcomment where core_object.id=threadedcomments_threadedcomment.object_id) WHERE core_object.id in (select distinct object_id from threadedcomments_threadedcomment)
/* 62. Constraint for watching http://jira.filmaster.org/browse/FLM-299 */
ALTER TABLE "useractivity_watching" ADD CONSTRAINT "one_watching_per_object" UNIQUE ("object_id" , "user_id");
DELETE FROM useractivity_watching where object_id is null;
ALTER TABLE "useractivity_watching" ALTER object_id SET NOT NULL;
/* 63. Language for bacht notices: http://jira.filmaster.org/browse/FLM-306 */
ALTER TABLE notification_noticequeuebatch ADD "LANG" character varying(2) not null DEFAULT 'pl';

/* 64. Number of attempts in film_to_import */
alter table import_films_filmtoimport add column "attempts" integer not null DEFAULT 0;

/* 65. New fields in core_character for contest */
ALTER TABLE "core_character" ADD "description_lead" varchar(350) NULL;
ALTER TABLE "core_character" ADD "description_full" varchar(1000) NULL;
ALTER TABLE "core_character" ADD "image" character varying(100) NULL;
ALTER TABLE "core_character" ADD "image_thumb" character varying(100) NULL;
CREATE INDEX core_character_character ON core_character USING btree (character); 
ALTER TABLE "core_character" ADD "image_thumb_lost" character varying(100) NULL;

ALTER TABLE "core_profile" ADD COLUMN "registration_source" varchar(255);


/* 66. New fields in externallink */
alter table externallink_externallink add column video_thumb character varying(50);
alter table externallink_externallink add column excerpt character varying(200);

/* 67. Constraint for http://jira.filmaster.org/browse/FLM-385 */
ALTER TABLE "useractivity_useractivity" ADD CONSTRAINT "one_activity_for_object" UNIQUE("object_id");

/* 68. Constraint for shop items (one item of one kind for a film) */
ALTER TABLE "shop_item" ADD CONSTRAINT "one_item_for_film" UNIQUE("id", "film_id");
ALTER TABLE "showtimes_country" ADD COLUMN "code" varchar(2);
ALTER TABLE "core_profile" ADD COLUMN "iphone_token" varchar(128);

/* 69. New field tmdb_import_status in core.models.film */
alter table core_film add column tmdb_import_status integer NOT NULL DEFAULT 0;

/* 70. New field iphone_token in core.models.Profile */
ALTER TABLE "core_profile" ADD COLUMN "iphone_token" varchar(128);
/* 71. new field in showtimes.film */
ALTER TABLE "showtimes_town" ADD COLUMN "has_cinemas" boolean NOT NULL default true;
/* 72. showtimes.models.FilmOnChannel imdb_code */
ALTER TABLE "showtimes_filmonchannel" ADD COLUMN "imdb_code" varchar(128);
/* 73. showtimes.models.Channel last_screening_date */
ALTER TABLE "showtimes_channel" ADD COLUMN "last_screening_date" date;

/* 74. Relation to user in blog_post */
alter table "blog_post" add column "user_id" integer REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "blog_post_user_id" ON "blog_post" ("user_id");
update "blog_post" set "user_id" = (select "user_id" from "blog_blog" where "blog_blog"."id"="blog_post"."author_id");
alter table "blog_post" alter column "user_id" SET NOT NULL;

/* 75. One user per blog */
ALTER TABLE "blog_blog" ADD CONSTRAINT "one_user_per_blog" UNIQUE ("user_id", "LANG");

/* 76. pingback_note table */
CREATE TABLE blog_pingbacknote
(
  id serial NOT NULL,
  note_id integer NOT NULL,
  is_ping boolean NOT NULL,
  created_at timestamp with time zone NOT NULL,
  CONSTRAINT blog_pingbacknote_pkey PRIMARY KEY (id),
  CONSTRAINT blog_pingbacknote_note_id_fkey FOREIGN KEY (note_id)
      REFERENCES blog_post (parent_id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED
)
WITH (OIDS=FALSE);
ALTER TABLE blog_pingbacknote OWNER TO postgres;

-- Index: blog_pingbacknote_note_id

-- DROP INDEX blog_pingbacknote_note_id;

CREATE INDEX blog_pingbacknote_note_id
  ON blog_pingbacknote
  USING btree
  (note_id);

/* 77. Replace one_imdb_code_per_film constraint to accept nulls */
ALTER TABLE core_film DROP CONSTRAINT one_imdb_code_per_film;
CREATE UNIQUE INDEX "one_imdb_code_per_film" on "core_film"("imdb_code") WHERE "imdb_code" IS NOT NULL;
update core_film set imdb_code = NULL where imdb_code like '-%';

/* 78. core_profile metacritic_name field */
ALTER TABLE core_profile add column "metacritic_name" varchar(128);

/* 79. longer URL */
ALTER TABLE externallink_externallink ALTER COLUMN url TYPE VARCHAR(2048);

/* 80. facebook access_token */
ALTER TABLE "facebook_connect_fbassociation" ADD COLUMN "access_token" varchar(128);

/* 81. noticetype */
ALTER TABLE "notification_noticetype" ADD COLUMN "type" integer NOT NULL default 0;
/* 82. Allow longer notecesettings media id (was 1 char) */
alter table "notification_noticesetting" alter medium type varchar(16);
/* 83. twitter access token */
ALTER TABLE "core_profile" ADD COLUMN "twitter_access_token" varchar(128);
/* 84. foursquare access token */
ALTER TABLE "core_profile" ADD COLUMN "foursquare_access_token" varchar(128);

/* 85. Move blog title form blog_blog to core_profile */
ALTER TABLE "core_profile" ADD COLUMN "blog_title" varchar(200);
update "core_profile" set "blog_title" = (select "title" from "blog_blog" where "blog_blog".user_id = "core_profile".user_id and "blog_blog"."LANG" ="core_profile"."LANG" LIMIT 1);
alter table "blog_post" drop column "author_id";

/* 86. Beta code in registration model */
alter table register_registrationmodel add column beta_code character varying(128);
