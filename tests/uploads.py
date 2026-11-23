import io


class SimpleUploadedFile(io.BytesIO):
    def __init__(
        self,
        name,
        content,
        content_type=None,
    ):
        super().__init__(content)
        self.name = name
        self.size = len(content)
