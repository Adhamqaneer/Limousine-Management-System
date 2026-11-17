"""Compatibility entry point for retained deletion/recovery verification.

Uses the intended local database, pre-upgrade backup and rollback-only fixtures.
"""
from verify_recycling import main

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Recovery verification failed ({type(error).__name__}); private details suppressed.')
        raise SystemExit(1)
