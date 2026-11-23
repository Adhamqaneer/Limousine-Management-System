"""Driver assignment/correction use cases and persistence contract."""

from datetime import date, timedelta
from typing import Protocol

from limousine.domain.drivers import DriverValidationError, driver_date, driver_details
from limousine.domain.recycling import require_actor
from limousine.domain.vehicles import DomainError


class DriverRepository(Protocol):
    def change_driver(
        self,
        vehicle_id,
        details,
        started_on,
        actor,
        *,
        correcting=False,
    ): ...
    def history(
        self,
        vehicle_id=None,
        query="",
        on_date=None,
    ): ...
    def corrections(
        self,
        vehicle_id,
    ): ...
    def end_driver(
        self,
        vehicle_id,
        assignment_id,
        ended_on,
        actor,
    ): ...


class DriverService:
    def __init__(
        self,
        repository: DriverRepository,
        today=date.today,
    ):
        self.repository, self.today = repository, today

    def _start(
        self,
        value,
        *,
        required=False,
    ):
        start = driver_date(
            value,
            required=required,
        )
        if (
            start is not None
            and start > self.today()
        ):
            raise DriverValidationError(
                "started_on",
                "futureStart",
                "A driver start date cannot be in the future.",
            )
        return start

    def assign(
        self,
        vehicle_id,
        name,
        phone,
        started_on,
        actor,
    ):
        require_actor(actor)
        return self.repository.change_driver(
            vehicle_id,
            driver_details(
                name,
                phone,
            ),
            self._start(
                started_on,
                required=True,
            ),
            actor,
        )

    def correct(
        self,
        vehicle_id,
        name,
        phone,
        started_on,
        actor,
    ):
        require_actor(actor)
        return self.repository.change_driver(
            vehicle_id,
            driver_details(
                name,
                phone,
            ),
            self._start(started_on),
            actor,
            correcting=True,
        )

    def end(
        self,
        vehicle_id,
        assignment_id,
        last_worked_on,
        actor,
    ):
        require_actor(actor)
        try:
            last_day = driver_date(
                last_worked_on,
                required=True,
            )
        except DriverValidationError as error:
            raise DriverValidationError(
                "last_worked_on",
                "endRequired",
                "Enter the last working date.",
            ) from error
        if last_day > self.today():
            raise DriverValidationError(
                "last_worked_on",
                "futureEnd",
                "The last working date cannot be in the future.",
            )
        if last_day == date.max:
            raise DriverValidationError(
                "last_worked_on",
                "dateInvalid",
                "Enter a valid last working date.",
            )
        return self.repository.end_driver(
            vehicle_id,
            assignment_id,
            last_day + timedelta(days=1),
            actor,
        )

    def history(
        self,
        vehicle_id=None,
        query="",
        on_date=None,
    ):
        if (
            not isinstance(
                query,
                str,
            )
            or len(query) > 200
        ):
            raise DomainError("Driver search is too long.")
        return self.repository.history(
            vehicle_id,
            query.strip(),
            driver_date(on_date),
        )

    def corrections(
        self,
        vehicle_id,
    ):
        return self.repository.corrections(vehicle_id)
