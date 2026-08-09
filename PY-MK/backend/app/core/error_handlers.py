from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message, "type": "app_error"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # exc.errors() puede incluir un "ctx" con la excepción original sin
        # serializar (por ejemplo, el ValueError crudo de un @model_validator
        # que rechaza el payload) -- json.dumps() no sabe convertirla y
        # rompía con un 500 en vez de devolver el 422 esperado.
        details = [
            {k: v for k, v in error.items() if k != "ctx"} for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "message": "Payload validation failed",
                "type": "validation_error",
                "details": details,
            },
        )
