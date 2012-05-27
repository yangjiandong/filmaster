pg_dump film20 -U film20 -cR > film20_full.sql
tar cvjf ../static/db/film20_full.sql.tar.bz2 film20_full.sql
rm film20_full.sql
