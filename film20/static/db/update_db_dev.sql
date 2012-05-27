update django_site set domain='filmmaster.pl' where name = 'Filmaster.pl';
update django_site set domain='dev.filmaster.com' where name = 'Filmaster.com';
-- delete private messages
delete from messages_message;
update auth_user set email = '', password = 'sha1$9eb3d$245202c8dc8765a60cb3bb32ecd6c9e64bf2a6ed'; -- dupa.8
-- notifications and other data
delete from emailconfirmation_emailconfirmation;
delete from emailconfirmation_emailaddress;
delete from notification_notice;

-- delete records
delete from core_filmlog ;
delete from core_personlog;
delete from core_personlog_old;
delete from django_digg_vote;

delete from useractivity_useractivity where id>300;
delete from useractivity_useractivity where short_review_id in (select parent_id from core_shortreview where parent_id>217491);
delete from core_shortreview where parent_id>217491;
delete from blog_post_related_person where post_id in (select parent_id from blog_post where parent_id>203086);
delete from blog_post_related_film where post_id in (select parent_id from blog_post where parent_id>203086);
delete from blog_post where parent_id>203086;
delete from core_rating where id>10000;


-- dump
pg_dump film20 -U film20 -cR > film20_full.sql
tar cvjf film20_full.sql.tar.bz2 film20_full.sql
