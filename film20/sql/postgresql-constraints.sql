-- constraints

-- one language version per object
ALTER TABLE "core_objectlocalized" ADD CONSTRAINT "one_language_version_for_parent" UNIQUE ("parent_id" , "LANG");

-- one rating per user per film per type
ALTER TABLE "core_rating" ADD CONSTRAINT "one_rating_per_film" UNIQUE ("parent_id" , "user_id", "type");

-- one review per rating
ALTER TABLE "core_shortreview" ADD CONSTRAINT "one_review_per_rating" UNIQUE ("rating_id" , "LANG");
ALTER TABLE "core_shortreview" ADD CONSTRAINT "one_review_per_user_object" UNIQUE ("object_id" , "user_id", "LANG");

-- one character per film/person/lang
ALTER TABLE "core_character" ADD CONSTRAINT "one_character_per_film_per_lang" UNIQUE ("film_id", "person_id" , "character", "importance", "LANG");

-- only one localized profile per user (one in each language)
ALTER TABLE "core_profile" ADD CONSTRAINT "one_profile_per_user_per_lang" UNIQUE ("user_id" , "LANG");

ALTER TABLE "core_film" ADD CONSTRAINT "one_imdb_code_per_film" UNIQUE ("imdb_code");

