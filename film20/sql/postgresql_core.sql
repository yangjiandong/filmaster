BEGIN;
CREATE TABLE "core_object" (
    "id" serial NOT NULL PRIMARY KEY,
    "type" integer NOT NULL,
    "permalink" varchar(40) NOT NULL,
    "status" integer NOT NULL
)
;
CREATE TABLE "core_objectlocalized" (
    "id" serial NOT NULL PRIMARY KEY,
    "parent_id" integer NOT NULL REFERENCES "core_object" ("id") DEFERRABLE INITIALLY DEFERRED,
    "tag_list" varchar(255) NOT NULL,
    "LANG" varchar(2) NOT NULL
)
;
CREATE TABLE "core_profile" (
    "id" serial NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "openid" varchar(100) NULL,
    "website" varchar(100) NULL,
    "description" varchar(255) NULL,
    "jabber_id" varchar(50) NULL,
    "gg" varchar(50) NULL,
    "msn" varchar(50) NULL,
    "icq" varchar(50) NULL,
    "aol" varchar(50) NULL,
    "facebook_name" varchar(50) NULL,
    "myspace_name" varchar(50) NULL,
    "criticker_name" varchar(50) NULL,
    "imdb_name" varchar(50) NULL,
    "karma" integer NOT NULL
)
;
CREATE TABLE "core_person" (
    "imdb_code" integer NOT NULL,
    "parent_id" integer NOT NULL PRIMARY KEY REFERENCES "core_object" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(30) NOT NULL,
    "surname" varchar(50) NOT NULL,
    "day_of_birth" integer NULL,
    "month_of_birth" integer NULL,
    "year_of_birth" integer NULL,
    "gender" varchar(1) NULL,
    "is_director" boolean NOT NULL,
    "is_actor" boolean NOT NULL,
    "actor_popularity" integer NOT NULL,
    "director_popularity" integer NOT NULL,
    "actor_popularity_month" integer NOT NULL,
    "director_popularity_month" integer NOT NULL,
    "version" integer NOT NULL,
    "status" integer NOT NULL
)
;
CREATE TABLE "core_film" (
    "imdb_code" integer NOT NULL,
    "parent_id" integer NOT NULL PRIMARY KEY REFERENCES "core_object" ("id") DEFERRABLE INITIALLY DEFERRED,
    "title" varchar(60) NOT NULL,
    "release_year" integer NOT NULL,
    "release_date" date NULL,
    "popularity" integer NOT NULL,
    "popularity_month" integer NOT NULL,
    "version" integer NOT NULL,
    "status" integer NOT NULL
)
;
CREATE TABLE "core_rating" (
    "id" serial NOT NULL PRIMARY KEY,
    "parent_id" integer NOT NULL REFERENCES "core_object" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "film_id" integer NULL REFERENCES "core_film" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    "actor_id" integer NULL REFERENCES "core_person" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    "director_id" integer NULL REFERENCES "core_person" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    "rating" integer NULL,
    "normalized" numeric(6, 4) NULL,
    "guess_rating_alg1" numeric(6, 4) NULL,
    "guess_rating_alg2" numeric(6, 4) NULL,
    "type" integer NOT NULL,
    "first_rated" timestamp with time zone NULL,
    "last_rated" timestamp with time zone NULL
)
;
CREATE TABLE "core_shortreview" (
    "id" serial NOT NULL PRIMARY KEY,
    "rating_id" integer NOT NULL REFERENCES "core_rating" ("id") DEFERRABLE INITIALLY DEFERRED,
    "review_text" varchar(255) NOT NULL,
    "LANG" varchar(2) NOT NULL
)
;
CREATE TABLE "core_ratingcomparator" (
    "id" serial NOT NULL PRIMARY KEY,
    "main_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "compared_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "comment" varchar(255) NOT NULL,
    "score" numeric(4, 2) NOT NULL
)
;
CREATE TABLE "core_film_directors" (
    "id" serial NOT NULL PRIMARY KEY,
    "film_id" integer NOT NULL REFERENCES "core_film" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    "person_id" integer NOT NULL REFERENCES "core_person" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("film_id", "person_id")
)
;
CREATE TABLE "core_film_actors" (
    "id" serial NOT NULL PRIMARY KEY,
    "film_id" integer NOT NULL REFERENCES "core_film" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    "person_id" integer NOT NULL REFERENCES "core_person" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("film_id", "person_id")
)
;
CREATE INDEX "core_objectlocalized_parent_id" ON "core_objectlocalized" ("parent_id");
CREATE INDEX "core_rating_parent_id" ON "core_rating" ("parent_id");
CREATE INDEX "core_rating_user_id" ON "core_rating" ("user_id");
CREATE INDEX "core_rating_film_id" ON "core_rating" ("film_id");
CREATE INDEX "core_rating_actor_id" ON "core_rating" ("actor_id");
CREATE INDEX "core_rating_director_id" ON "core_rating" ("director_id");
CREATE INDEX "core_shortreview_rating_id" ON "core_shortreview" ("rating_id");
CREATE INDEX "core_ratingcomparator_main_user_id" ON "core_ratingcomparator" ("main_user_id");
CREATE INDEX "core_ratingcomparator_compared_user_id" ON "core_ratingcomparator" ("compared_user_id");
COMMIT;
