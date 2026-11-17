"""Driver-period input and boundary rules."""
import re
from datetime import date
from limousine.domain.vehicles import DomainError, normalize_vehicle_fields

class DriverValidationError(DomainError):
    """A driver rule failure with a stable field and localized-message key."""

    def __init__(self, field, reason, message):
        super().__init__(message)
        self.field = field
        self.reason = reason

def driver_details(name, phone):
    values = {}
    for field, value in [('driver_name', name), ('driver_phone', phone)]:
        try:
            values.update(normalize_vehicle_fields({field: value}))
        except DomainError as error:
            reason = 'nameRule' if field == 'driver_name' else 'phoneRule'
            raise DriverValidationError(field, reason, str(error)) from error
    if not values['driver_name']:
        raise DriverValidationError('driver_name','nameRule','Enter the driver name.')
    return values

def driver_date(value, *, required=False):
    if value in (None,''):
        if required: raise DriverValidationError('started_on','startRequired','Enter the driver start date.')
        return None
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',value):
        raise DriverValidationError('started_on','dateInvalid','Enter a valid date (YYYY-MM-DD).')
    try:return date.fromisoformat(value)
    except ValueError:raise DriverValidationError('started_on','dateInvalid','Enter a valid date.') from None

def validate_boundary(start, current_start=None, previous_end=None, *, correcting=False):
    if start is None:
        if current_start is not None: raise DriverValidationError('started_on','knownStart','A known start date cannot be cleared.')
        return
    if not correcting and current_start is not None and start < current_start:
        raise DriverValidationError('started_on','overlapStart','The new driver cannot start before the current driver.')
    if previous_end is not None and start < previous_end:
        raise DriverValidationError('started_on','overlapStart','The start date overlaps an earlier driver period.')
