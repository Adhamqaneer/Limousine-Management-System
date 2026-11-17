"""HTTP streaming and lifetime of a completed temporary attachment archive."""

from urllib.parse import quote
from starlette.responses import StreamingResponse
from limousine.infrastructure.attachment_archive import CHUNK_BYTES


class ArchiveResponse(StreamingResponse):
    def __init__(self, archive, filename):
        self.archive = archive
        archive.seek(0, 2)
        length = archive.tell()
        archive.seek(0)

        def chunks():
            while chunk := archive.read(CHUNK_BYTES):
                yield chunk

        super().__init__(chunks(), media_type='application/zip', headers={
            'Content-Disposition': "attachment; filename*=UTF-8''" + quote(filename, safe=''),
            'Content-Length': str(length),
        })

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            self.archive.close()
