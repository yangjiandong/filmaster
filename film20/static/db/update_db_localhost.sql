update django_site set domain='localhost' where name = 'Filmaster.pl';
update django_site set domain='localhost' where name = 'Filmaster.com';
-- delete private messages
delete from messages_message;
update auth_user set email = '', password = 'sha1$9eb3d$245202c8dc8765a60cb3bb32ecd6c9e64bf2a6ed'; -- dupa.8
-- notifications and other data
delete from emailconfirmation_emailconfirmation;
delete from emailconfirmation_emailaddress;
delete from notification_notice;

delete from core_filmlog ;
delete from core_personlog;
delete from core_personlog_old;
