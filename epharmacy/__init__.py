# epharmacy/__init__.py
# Python 3.15 compatibility patch for django.template.context.BaseContext.__copy__
try:
    import django.template.context as _c
    def _safe_context_copy(self):
        obj = self.__class__.__new__(self.__class__)
        obj.dicts = self.dicts[:]
        return obj
    _c.BaseContext.__copy__ = _safe_context_copy
except Exception:
    pass

