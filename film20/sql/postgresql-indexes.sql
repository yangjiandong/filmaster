-- optimizations for PostgreSQL
CREATE INDEX "core_object_permalink" on "core_object"("permalink");

-- person
CREATE INDEX "core_person_surname" on "core_person"("surname");
CREATE INDEX "core_person_surname_upper" on "core_person" USING btree (upper("surname"));
CREATE INDEX "core_person_surname_upper_vpo" on "core_person" USING btree (upper("surname") varchar_pattern_ops);

CREATE INDEX "core_person_actor_popularity" on "core_person"("actor_popularity");
CREATE INDEX "core_person_actor_popularity_month" on "core_person"("actor_popularity_month");
CREATE INDEX "core_person_director_popularity" on "core_person"("director_popularity");
CREATE INDEX "core_person_director_popularity_month" on "core_person"("director_popularity_month");

-- This does not exist anymore. TODO: apply same inxed on the new schema
--CREATE INDEX "core_film_actors_person_id" on "core_film_actors"("person_id");

-- character
CREATE INDEX "core_character_importance" on "core_character"("importance");

-- film
CREATE INDEX "core_film_popularity" on "core_film"("popularity");
CREATE INDEX "core_film_popularity_month" on "core_film"("popularity_month");

--CREATE INDEX "core_film_title_upper_text" on "core_film" USING btree (upper("title"::text));
--CREATE INDEX "core_film_title_upper" on "core_film" USING btree (upper("title"));
--CREATE INDEX "core_film_title_upper_vpo" on "core_film" USING btree (upper("title") varchar_pattern_ops);

-- rating
CREATE INDEX "core_rating_guess_rating_alg1" on "core_rating"("guess_rating_alg1");
CREATE INDEX "core_rating_last_rated" on "core_rating"("last_rated");
CREATE INDEX "core_rating_rating" on "core_rating"("rating");
CREATE INDEX "core_rating_normalized" on "core_rating"("normalized");
CREATE INDEX "core_rating_number_of_ratings" on "core_rating"("number_of_ratings");

create unique index "one_rating_for_user_parent_type" on "core_rating" (user_id, parent_id, type) where actor_id is null and director_id is null;
create unique index "one_rating_for_user_parent_type_actor" on "core_rating" (user_id, parent_id, type, actor_id) where director_id is null;
create unique index "one_rating_for_user_parent_type_director" on "core_rating" (user_id, parent_id, type, director_id) where actor_id is null;

-- ratingcomparator (dla recom_helper.guess_score)
CREATE INDEX "core_ratingcomparator_score" on "core_ratingcomparator"("score");
CREATE INDEX "core_ratingcomparator_updated_at" on "core_ratingcomparator"("updated_at");
-- NEW
CREATE INDEX "core_ratingcomparator_users_score" on "core_ratingcomparator"("main_user_id", "compared_user_id", "score");
-- only one record for earch pair 
CREATE UNIQUE INDEX "core_ratingcomparator_pair" on "core_ratingcomparator"("main_user_id", "compared_user_id");

-- filmlocalized
CREATE INDEX "core_filmlocalized_title" on "core_filmlocalized"("title");
--CREATE INDEX "core_filmlocalized_title_upper" on "core_filmlocalized" USING btree (upper("title"));
--CREATE INDEX "core_filmlocalized_title_upper_vpo" on "core_filmlocalized" USING btree (upper("title") varchar_pattern_ops);

-- filmranking
CREATE INDEX "core_filmranking_votes" on "core_filmranking"("number_of_votes");
CREATE INDEX "core_filmranking_score" on "core_filmranking"("average_score");

-- basketitem
CREATE INDEX "filmbasket_basketitem_ids" on "filmbasket_basketitem"("film_id", "user_id");
CREATE INDEX "core_rating_ids" on "core_rating"("film_id", "user_id");
CREATE UNIQUE INDEX "core_rating_unique_id_type" on "core_rating"("film_id", "user_id", "type");

-- auth_user...
CREATE UNIQUE INDEX "auth_user_email" on "auth_user"("email") WHERE "email"<>'';

-- one activity for a short review per locale per user per film
CREATE UNIQUE INDEX "one_short_review_per_user_film_lang" ON "useractivity_useractivity"(film_id, user_id, "LANG") WHERE activity_type=2;

