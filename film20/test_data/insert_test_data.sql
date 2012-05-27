INSERT INTO core_object(id, type, permalink, status) VALUES(1,1,'przypadek', 1);
INSERT INTO core_object(id, type, permalink, status) VALUES(2,2,'krzysztof-kieslowski', 1);
INSERT INTO core_object(id, type, permalink, status) VALUES(3,2,'boguslaw-linda', 1);
INSERT INTO core_object(id, type, permalink, status) VALUES(4,1,'psy', 1);
INSERT INTO core_object(id, type, permalink, status) VALUES(5,2,'wladyslaw-pasikowski', 1);

INSERT INTO core_person(id, parent_id, name, surname, is_director, is_actor, version, status) 
VALUES(1,2,'Krzysztof', 'Kieślowski', 1, 0, 1, 1);
INSERT INTO core_person(id, parent_id, name, surname, is_director, is_actor, version, status) 
VALUES(2,3,'Bogusław', 'Linda', 1, 1, 1, 1);
INSERT INTO core_person(id, parent_id, name, surname, is_director, is_actor, version, status) 
VALUES(3,5,'Władysław', 'Pasikowski', 1, 0, 1, 1);

INSERT INTO core_film(id, parent_id, title, release_year, version, status)
VALUES(1, 1, 'Przypadek', 1989, 1,1);
INSERT INTO core_film(id, parent_id, title, release_year, version, status)
VALUES(2, 4, 'Psy', 1993, 1,1);

INSERT INTO core_film_directors(id, film_id, person_id) VALUES(1, 1, 1);
INSERT INTO core_film_directors(id, film_id, person_id) VALUES(2, 2, 3);

INSERT INTO core_film_actors(id, film_id, person_id) VALUES(1, 1, 2);
INSERT INTO core_film_actors(id, film_id, person_id) VALUES(2, 2, 2);
