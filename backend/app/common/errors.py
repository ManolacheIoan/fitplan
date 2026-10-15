class DomainError(Exception):
    """A business-rule failure; routers turn it into an HTTP error with `code` as detail."""

    def __init__(self, code: str, status: int) -> None:
        super().__init__(code)
        self.code = code
        self.status = status
