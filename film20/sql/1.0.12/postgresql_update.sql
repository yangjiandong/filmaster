alter table "useractivity_useractivity" add column "rating" integer;
update useractivity_useractivity ua set rating=(select r.rating from core_shortreview "s" left join core_rating r on (s.rating_id=r.id) where s.parent_id=ua.short_review_id) where activity_type=2;
update useractivity_useractivity ua set rating=(select r.rating from blog_post post join blog_post_related_film rf on post.parent_id=rf.post_id join core_film f on rf.film_id=f.parent_id join core_rating r on f.parent_id=r.film_id and r.type=1 and r.user_id = post.user_id where rf.post_id=ua.post_id order by rf.id limit 1) where activity_type=1;
alter table "core_usermeta" add column "recommendations_notice_sent" integer NOT NULL default 1;
create unique index "one_recommendation_per_film" on "core_recommendation"("film_id", "user_id", "guess_rating_alg2") where "film_id" is not null and "guess_rating_alg2" is not null;
