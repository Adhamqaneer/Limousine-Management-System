"""Driver assignment/correction use cases and persistence contract."""
from typing import Protocol
from datetime import date
from limousine.domain.recycling import require_actor
from limousine.domain.drivers import driver_details, driver_date
from limousine.domain.vehicles import DomainError

class DriverRepository(Protocol):
    def change_driver(self, vehicle_id, details, started_on, actor, *, correcting=False): ...
    def history(self, vehicle_id=None, query='', on_date=None): ...
    def corrections(self, vehicle_id): ...

class DriverService:
    def __init__(self, repository:DriverRepository, today=date.today): self.repository,self.today=repository,today

    def _start(self, value, *, required=False):
        start=driver_date(value,required=required)
        if start is not None and start>self.today():raise DomainError('A driver start date cannot be in the future.')
        return start

    def assign(self, vehicle_id, name, phone, started_on, actor):
        require_actor(actor)
        return self.repository.change_driver(vehicle_id,driver_details(name,phone),self._start(started_on,required=True),actor)

    def correct(self, vehicle_id, name, phone, started_on, actor):
        require_actor(actor)
        return self.repository.change_driver(vehicle_id,driver_details(name,phone),self._start(started_on),actor,correcting=True)

    def history(self, vehicle_id=None, query='', on_date=None):
        if not isinstance(query,str) or len(query)>200: raise DomainError('Driver search is too long.')
        return self.repository.history(vehicle_id,query.strip(),driver_date(on_date))

    def corrections(self, vehicle_id): return self.repository.corrections(vehicle_id)
