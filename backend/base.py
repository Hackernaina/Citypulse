from itertools import count

class FindingFactory:
    _counter = count(1)

    @classmethod
    def make(cls, **kwargs):
        from app.models.finding import Finding
        return Finding(id=f"F-{next(cls._counter):03d}", **kwargs)
