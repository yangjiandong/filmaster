alter table core_localizedprofile drop constraint "core_localizedprofile_user_id_key";
alter table core_localizedprofile drop constraint "core_localizedprofile_user_id_key1";
ALTER TABLE "core_localizedprofile" ADD CONSTRAINT "core_localizedprofile_user_lang_unique" UNIQUE ("user_id" , "LANG");
