from film20.utils import cache

def compute_guess_score_for_all_films(user):
    if not hasattr(user, '_guess_score'):
        key = cache.Key("guess_score", user.id)
        user._guess_score = cache.get(key)
        if user._guess_score is None:
            from film20.core.models import Recommendation
            items = Recommendation.objects.filter(user=user.id)
            items = items.values_list('film_id', 'guess_rating_alg2')
            user._guess_score = dict((r[0], float(r[1])) for r in items)
        cache.set(key, user._guess_score)
    return user._guess_score

def compute_guess_score_for_films(user, film_ids):
    film_ids = set(film_ids)
    scores = compute_guess_score_for_all_films(user)
    return dict(i for i in scores.items() if i[0] in film_ids)

def compute_guess_score(user, film_id):
    scores = compute_guess_score_for_all_films(user)
    return scores.get(film_id)

def _compute_fast_recommendations(user, send_notice):
    from film20.recommendations.bot_helper import compute_fast_recommendations
    compute_fast_recommendations(user.id, send_notice)
    cache.delete(cache.Key("guess_score", user.id))

def compute_user_features(user, save=False, initial=False):
    if initial:
        profile = user.get_profile()
        no_recommendations = (profile.recommendations_status == profile.NO_RECOMMENDATIONS)

        if no_recommendations:
            profile.recommendations_status = profile.FAST_RECOMMENDATIONS_WAITING
            profile.save()

        from film20.core.deferred import defer
        defer(_compute_fast_recommendations, user, no_recommendations)

