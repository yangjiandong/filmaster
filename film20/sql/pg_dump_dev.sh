cat update_site_dev.sql | psql -U film20 film20dev
pg_dump film20dev -U film20 -cR > film20dev_full.sql
tar cvjf ../static/db/film20dev_full.sql.tar.bz2 film20dev_full.sql
rm film20dev_full.sql
