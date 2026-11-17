"""Driver-period input and boundary rules."""
import re
from datetime import date
from limousine.domain.vehicles import DomainError, normalize_vehicle_fields

def driver_details(name, phone):
    values = normalize_vehicle_fields({'driver_name':name,'driver_phone':phone})
    if not values['driver_name']:
        raise DomainError('Enter the driver name.')
    return values

def driver_date(value, *, required=False):
    if value in (None,''):
        if required: raise DomainError('Enter the driver start date.')
        return None
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',value):
        raise DomainError('Enter a valid date (YYYY-MM-DD).')
    try:return date.fromisoformat(value)
    except ValueError:raise DomainError('Enter a valid date.') from None

def validate_boundary(start, current_start=None, previous_end=None, *, correcting=False):
    if start is None:
        if current_start is not None: raise DomainError('A known start date cannot be cleared.')
        return
    if not correcting and current_start is not None and start < current_start:
        raise DomainError('The new driver cannot start before the current driver.')
    if previous_end is not None and start < previous_end:
        raise DomainError('The start date overlaps an earlier driver period.')
