-- set rating for short reviews with no rating (in case review is posted before rating) - to be run in cron daily
update core_shortreview r set rating_id = (select id from core_rating where user_id=r.user_id and type=1 and parent_id=r.object_id) where rating_id is null;

-- set profiles to primary if there is only one profile object for the user (this works around a bug to be fixed in which for some cases the new profile created is not set as primary)
--update core_profile p1 set is_primary=true WHERE "LANG"='pl' AND NOT EXISTS(select * from core_profile p2 where "LANG"='en' and p1.user_id=p2.user_id) and is_primary=false;
--update core_profile p1 set is_primary=true WHERE "LANG"='en' AND NOT EXISTS(select * from core_profile p2 where "LANG"='pl' and p1.user_id=p2.user_id) and is_primary=false;

-- create localized profiles for users with only one profile (english or polish)
--INSERT INTO core_profile(user_id,date,country,latitude,longitude,location,gender,website,description,jabber_id,gg,msn,icq,aol,facebook_name,myspace_name,criticker_name,imdb_name,openid,karma,"LANG") SELECT user_id,now(),country,latitude,longitude,location,gender,website,description,jabber_id,gg,msn,icq,aol,facebook_name,myspace_name,criticker_name,imdb_name,openid,karma,'en' FROM core_profile p1 WHERE "LANG"='pl' AND NOT EXISTS(select * from core_profile p2 where "LANG"='en' and p1.user_id=p2.user_id);
--INSERT INTO core_profile(user_id,date,country,latitude,longitude,location,gender,website,description,jabber_id,gg,msn,icq,aol,facebook_name,myspace_name,criticker_name,imdb_name,openid,karma,"LANG") SELECT user_id,now(),country,latitude,longitude,location,gender,website,description,jabber_id,gg,msn,icq,aol,facebook_name,myspace_name,criticker_name,imdb_name,openid,karma,'pl' FROM core_profile p1 WHERE "LANG"='en' AND NOT EXISTS(select * from core_profile p2 where "LANG"='pl' and p1.user_id=p2.user_id);

-- update existing profiles to set the first one as primary in case none is primary
--update core_profile p1 set is_primary=true WHERE NOT EXISTS(select * from core_profile p2 where p1.user_id=p2.user_id and is_primary = true) and is_primary=false AND p1.id<(SELECT min(p2.id) from core_profile p2 where p1.user_id=p2.user_id and p2."LANG"<>p1."LANG");

-- set link descriptions for fetched synopses 
update core_filmlocalized set fetched_description_url_text = 'Fdb' where fetched_description_type<>1 and fetched_description_url like 'http://fdb.pl%' and fetched_description_type<>1;
update core_filmlocalized set fetched_description_url_text = 'Filmweb' where fetched_description_type<>1 and fetched_description_url like 'http://www.filmweb.pl%' and fetched_description_type<>1;

-- recreating indexes after generating recommendations: this is done in the recommendation script now
--CREATE INDEX core_recommendation_film_id ON core_recommendation (film_id);
--CREATE INDEX core_recommendation_user_id ON core_recommendation (user_id);
--CREATE INDEX core_recommendation_user_and_film ON core_recommendation (user_id, film_id);

-- remove facebook emails that are not emails
--update auth_user set email = '' WHERE email !~ '[^0-9]' and email<>''; 
