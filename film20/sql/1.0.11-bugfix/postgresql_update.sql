/* http://jira.filmaster.org/browse/FLM-637 */
alter table facebook_connect_fbassociation add constraint "one_fb_association" unique ("fb_uid");
