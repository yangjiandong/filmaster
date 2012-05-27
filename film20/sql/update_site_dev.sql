update django_site set domain='filmmaster.pl' where name = 'Filmaster.pl';
-- remove some sensitive stuff
delete from userprofile_avatar;
delete from messages_message;
-- and the password shall be dupa.8
update auth_user set password='sha1$9eb3d$245202c8dc8765a60cb3bb32ecd6c9e64bf2a6ed';
