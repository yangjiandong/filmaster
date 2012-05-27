#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
import datetime
from django.conf import settings
from django.utils.functional import SimpleLazyObject
import cPickle as pickle

def _create_redis_connection():
    import redis
    return redis.Redis(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB)

redis = SimpleLazyObject(_create_redis_connection)

def _rating_key(film_id=None, actor_id=None, director_id=None, type=1):
    key = ('type', str(type))
    if film_id:
        key += ('film', str(film_id))
    if actor_id:
        key += ('actor', str(actor_id))
    if director_id:
        key += ('director', str(director_id))

    return ':'.join(key)

def rate(user_id, value, film_id=None, actor_id=None, director_id=None, type=1, overwrite=True, check_if_exists=False):
    user_key = "user:%s:ratings" % user_id

    key = _rating_key(film_id, actor_id, director_id, type)

    assert user_id

    if not overwrite or check_if_exists:
        exists = redis.get("user:%s:rating:%s" % (user_id, key)) is not None
        if not overwrite and exists:
            return exists
    else:
        exists = None

    with redis.pipeline() as pipe:
        if value:
            if type == 1 and film_id:
                pipe.hset(user_key, film_id, value)
                pipe.sadd("users", user_id)
            pipe.hset("ratings:%s" % key, user_id, value)
            pipe.set("user:%s:rating:%s" % (user_id, key), value)
        else:
            if type == 1:
                pipe.hdel(user_key, film_id)
            pipe.hdel("ratings" + key, user_id)
            pipe.delete("user:%s:rating:%s" % (user_id, key))
        pipe.execute()
    return exists


def get_rating(user_id, film_id=None, actor_id=None, director_id=None, type=1):
    key = _rating_key(film_id, actor_id, director_id, type)
    value = redis.get("user:%s:rating:%s" % (user_id, key))
    if value is not None:
        value = int(value)
    return value

def get_user_ids(min_ratings=1):
    ids = set()
    user_ids = redis.smembers('users')
    for user_id in user_ids:
        if redis.hlen('user:%s:ratings' % user_id) >= min_ratings:
            ids.add(int(user_id))
    return ids

def get_user_ratings(user_id):
    if not user_id:
        return dict()
    user_key = "user:%s:ratings" % user_id
    return dict((int(id), int(r)) for (id, r) in redis.hgetall(user_key).items())

def get_rated_films(user_id):
    if not user_id:
        return set()
    user_key = "user:%s:ratings" % user_id
    return set(int(id) for id in redis.hkeys(user_key))

def get_film_ratings(film_id):
    return get_ratings(film_id=film_id, type=1)

def get_ratings(film_id=None, actor_id=None, director_id=None, type=1):
    key = "ratings:%s" % _rating_key(film_id, actor_id, director_id, type)
    return dict((int(id), int(r)) for (id, r) in redis.hgetall(key).items())

SEEN_EXPIRES_IN_DAYS = 30

def mark_films_as_seen(user, film_ids):
    user_id = str(user.id or user.username)
    key = 'user:%s:seen:%s' % (user_id, datetime.date.today())
    redis.sadd(key, *film_ids)
    redis.expire(key, SEEN_EXPIRES_IN_DAYS * 24 * 3600)

def get_seen_films(user):
    user_id = str(user.id or user.username)
    key_prefix = "user:%s:seen" % user_id
    keys = ["%s:%s" % (key_prefix, (datetime.date.today() - datetime.timedelta(days=i))) for i in range(SEEN_EXPIRES_IN_DAYS)]
    return set(int(id) for id in redis.sunion(keys))

def get_ids_with_features(key_prefix):
    return redis.smembers("%s:ids" % key_prefix)

def reset_ids_with_features(key_prefix):
    return redis.delete("%s:ids" % key_prefix)

def add_to_set(key_prefix, id, data_set):
    key = "%s:%s" % (key_prefix, id)
    redis.sadd(key, *data_set) 

def add_to_dict(key_prefix, id, data_dict):
    if data_dict:
        key = "%s:%s" % (key_prefix, id)
        redis.hmset(key, data_dict)

def get_string_set(key_prefix, id):
    key = "%s:%s" % (key_prefix, id)
    return redis.smembers(key)

def get_int_set(key_prefix, id):
    key = "%s:%s" % (key_prefix, id)
    return set([int(el) for el in redis.smembers(key)])

def get_int_dict(key_prefix, id): 
    return get_dict(key_prefix, id)

def get_dict(key_prefix, id, key_type=int, val_type=int):
    key = "%s:%s" % (key_prefix, id)
    return dict([(key_type(a), val_type(b)) for (a, b) in redis.hgetall(key).items()])

def reset_features(key_prefix, id, type=None):
    # TODO - type support
    key = "%s:%s" % (key_prefix, id)
    redis.delete(key)

def set_features(key_prefix, id, features):
    # TODO - type support
    key = "%s:%s" % (key_prefix, id)
    redis.set(key, pickle.dumps(features))
    redis.sadd("%s:ids" % key_prefix, id)

def get_features(key_prefix, id, type=None):
    # TODO - type support
    # assert key_prefix.startswith('cache_user')
    key = "%s:%s" % (key_prefix, id)
    features = redis.get(key)
    if not features:
        return dict()
    return pickle.loads(features)

def get_many_features(key_prefix, ids, type=None):
    keys = ["%s:%s" % (key_prefix, id) for id in ids]
    features = redis.mget(*keys)
    return dict( (k, pickle.loads(v)) for (k, v) in zip(ids, features) if v )

