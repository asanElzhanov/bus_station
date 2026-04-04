from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи'

    def ready(self):
        from django.template.context import BaseContext

        def _base_context_copy(self):
            duplicate = self.__class__.__new__(self.__class__)
            duplicate.__dict__ = self.__dict__.copy()
            duplicate.dicts = self.dicts[:]
            return duplicate

        BaseContext.__copy__ = _base_context_copy
