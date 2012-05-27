class Router(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'geo':
            return 'geo'
    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)
    
    def allow_syncdb(self, db, model):
        geo_model = model._meta.app_label == 'geo'
        geo_db = db == 'geo'
        return geo_model and geo_db or not geo_model and not geo_db

