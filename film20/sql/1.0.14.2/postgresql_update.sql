--- FLM-847
ALTER TABLE "massemail_massemail" ADD COLUMN "is_processed" boolean;
UPDATE "massemail_massemail" SET "is_processed" = true;
ALTER TABLE "massemail_massemail" ALTER COLUMN "is_processed" SET NOT NULL;

--- FLM-818
ALTER TABLE "add_films_addedfilm" ADD COLUMN "localized_title" varchar(128);
ALTER TABLE "add_films_addedfilm" DROP COLUMN "director_id";

CREATE TABLE "add_films_addedfilm_directors" (
    "id" serial NOT NULL PRIMARY KEY,
    "addedfilm_id" integer NOT NULL REFERENCES "add_films_addedfilm" ("id") DEFERRABLE INITIALLY DEFERRED,
    "person_id" integer NOT NULL REFERENCES "core_person" ("parent_id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("addedfilm_id", "person_id")
);
