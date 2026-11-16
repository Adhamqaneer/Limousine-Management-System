from unittest import TestCase
from unittest.mock import MagicMock
import psycopg
from limousine.infrastructure.file_cleanup import FileCleanup


class FileCleanupTests(TestCase):
    def test_pending_entry_is_retained_when_disk_or_database_fails(self):
        database, store = MagicMock(), MagicMock()
        connection = database.connect.return_value.__enter__.return_value
        connection.execute.return_value.fetchone.side_effect = [{"storage_key": "key"}, {"used": False}]
        store.delete.side_effect = PermissionError()
        with self.assertLogs("limousine.infrastructure.file_cleanup", level="WARNING"):
            self.assertFalse(FileCleanup(database, store).process("key"))
        self.assertFalse(any("DELETE FROM hspace_file_cleanup" in call.args[0] for call in connection.execute.call_args_list))
        database.connect.side_effect = psycopg.OperationalError("private")
        with self.assertLogs("limousine.infrastructure.file_cleanup", level="WARNING") as captured:
            self.assertFalse(FileCleanup(database, store).process("key"))
        self.assertNotIn("private", " ".join(captured.output))

    def test_referenced_file_is_never_unlinked(self):
        database, store = MagicMock(), MagicMock()
        connection = database.connect.return_value.__enter__.return_value
        connection.execute.return_value.fetchone.side_effect = [{"storage_key": "key"}, {"used": True}]
        self.assertTrue(FileCleanup(database, store).process("key"))
        store.delete.assert_not_called()
