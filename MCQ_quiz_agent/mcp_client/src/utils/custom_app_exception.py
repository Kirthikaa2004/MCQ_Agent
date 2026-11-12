from fastapi.responses import JSONResponse


class CustomAppException(Exception):
    def __init__(self, message: str | dict, status_code: int = 500, err_code: str = "INTERNAL_SERVER_ERROR"):
        self.message = message
        self.status_code = status_code
        self.err_code = err_code
        super().__init__(self.message)

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status_code,
            content={
                "message": self.message,
                "status_code": self.status_code,
                "err_code": self.err_code,
            },
        )
