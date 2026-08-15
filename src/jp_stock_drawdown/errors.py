class JpStockDrawdownError(Exception):
    exit_code = 1


class UsageError(JpStockDrawdownError):
    exit_code = 2


class DataFetchError(JpStockDrawdownError):
    exit_code = 3

    def __init__(self, message: str, *, rate_limited: bool = False) -> None:
        super().__init__(message)
        self.rate_limited = rate_limited


class NoDataError(JpStockDrawdownError):
    exit_code = 4
