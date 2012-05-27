/*1. Dodanie pola imdb_code */ 
ALTER TABLE core_object ADD imdb_code INT NOT NULL DEFAULT 0;
/*2. Rating połączone z person i film... optymalizacja */
ALTER TABLE core_rating ADD film_id integer NULL REFERENCES "core_film" ("id");
ALTER TABLE core_rating ADD person_id integer NULL REFERENCES "core_person" ("id");
/*3. Dodatkowe pola w profilu */
ALTER TABLE core_profile ADD "description" varchar(255) NULL;
ALTER TABLE core_profile ADD "jabber_id" varchar(50) NULL;
ALTER TABLE core_profile ADD "gg" varchar(50) NULL;
ALTER TABLE core_profile ADD "msn" varchar(50) NULL;
ALTER TABLE core_profile ADD "icq" varchar(50) NULL;
ALTER TABLE core_profile ADD "aol" varchar(50) NULL;
ALTER TABLE core_profile ADD "facebook_name" varchar(50) NULL;
ALTER TABLE core_profile ADD "myspace_name" varchar(50) NULL;
ALTER TABLE core_profile ADD "criticker_name" varchar(50) NULL;
ALTER TABLE core_profile ADD "imdb_name" varchar(50) NULL;
/*4. Data i typ zaproszenia: invitation_date, invitation_type */
ALTER TABLE core_invitation ADD "invitation_date" datetime NOT NULL DEFAULT '2000-01-01';
ALTER TABLE core_invitation ADD "handled_date" datetime NOT NULL DEFAULT '2000-01-01';
ALTER TABLE core_invitation ADD "invitation_type" integer NOT NULL DEFAULT 1;
/*5. Dodanie pól is_deleted oraz is_published w modelu bloga */
ALTER TABLE blog_post ADD is_published BOOL NOT NULL DEFAULT TRUE;
ALTER TABLE blog_post ADD is_deleted BOOL NOT NULL DEFAULT TRUE;
/*6. Friends since */
ALTER TABLE core_friend ADD "friends_since" datetime NOT NULL DEFAULT '2000-01-01';
/*7. Recreate ratings table */
DROP TABLE "core_rating";
CREATE TABLE "core_rating" (
    "id" integer NOT NULL PRIMARY KEY,
    "parent_id" integer NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "film_id" integer NULL,
    "actor_id" integer NULL,
    "director_id" integer NULL,
    "rating" integer NOT NULL,
    "normalized" integer NOT NULL,
    "type" integer NOT NULL
);
/*8. Invitation - read */
ALTER TABLE core_invitation ADD "read" bool NULL;
UPDATE core_invitation SET read = 0;
/*9. Invitation - nulle */
DROP TABLE "core_invitation";
CREATE TABLE "core_invitation" (
    "id" integer NOT NULL PRIMARY KEY,
    "inviting_user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "invited_user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "invitation_comment" varchar(255) NULL,
    "invitation_reply" varchar(255) NULL,
    "invitation_date" datetime NOT NULL,
    "handled_date" datetime NOT NULL,
    "invitation_type" integer NOT NULL,
    "status" integer NOT NULL
, "read" bool NULL);
/*10. Popularity */
ALTER TABLE core_film ADD "popularity" integer NOT NULL DEFAULT 0;
ALTER TABLE core_film ADD "popularity_month" integer NOT NULL DEFAULT 0;
ALTER TABLE core_person ADD "actor_popularity" integer NOT NULL DEFAULT 0;
ALTER TABLE core_person ADD "actor_popularity_month" integer NOT NULL DEFAULT 0;
ALTER TABLE core_person ADD "director_popularity" integer NOT NULL DEFAULT 0;
ALTER TABLE core_person ADD "director_popularity_month" integer NOT NULL DEFAULT 0;
ALTER TABLE core_rating ADD "add_date" datetime NOT NULL DEFAULT '2000-01-01';
ALTER TABLE core_rating ADD "last_mod_date" datetime NOT NULL DEFAULT '2000-01-01';
ALTER TABLE core_rating ADD "guess_rating_alg1" integer NULL;
ALTER TABLE core_rating ADD "guess_rating_alg2" integer NULL;
/*11. Rating -- not null to null */
DROP TABLE "core_rating";
CREATE TABLE "core_rating" (
    "id" integer NOT NULL PRIMARY KEY,
    "parent_id" integer NOT NULL REFERENCES "core_object" ("id"),
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "film_id" integer NULL REFERENCES "core_film" ("id"),
    "actor_id" integer NULL REFERENCES "core_person" ("id"),
    "director_id" integer NULL REFERENCES "core_person" ("id"),
    "rating" integer NULL,
    "normalized" integer NULL,
    "guess_rating_alg1" integer NULL,
    "guess_rating_alg2" integer NULL,
    "type" integer NOT NULL,
    "first_rated" datetime NULL,
    "last_rated" datetime NULL
);
/* Related person/film for blog note*/
CREATE TABLE "blog_post_related_film" (
    "id" integer NOT NULL PRIMARY KEY,
    "post_id" integer NOT NULL REFERENCES "blog_post" ("id"),
    "film_id" integer NOT NULL REFERENCES "core_film" ("id"),
    UNIQUE ("post_id", "film_id")
)
;

CREATE TABLE "blog_post_related_person" (
    "id" integer NOT NULL PRIMARY KEY,
    "post_id" integer NOT NULL REFERENCES "blog_post" ("id"),
    "person_id" integer NOT NULL REFERENCES "core_person" ("id"),
    UNIQUE ("post_id", "person_id")
)
;
/*12. Friends i Invitations w nowej tabeli */
DROP TABLE core_invitation;
DROP TABLE core_friend;

/*13. Tags in core_film */
ALTER TABLE core_film ADD "tag_list" varchar(255) NULL;

/*14. Blog w nowej tabeli*/
DROP TABLE "blog_post";
DROP TABLE "blog_post_related_film";
DROP TABLE "blog_post_related_person";
