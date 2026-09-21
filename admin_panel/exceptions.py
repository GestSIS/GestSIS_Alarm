from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    """
    Post-processes DRF's default exception response to match the GestSIS API
    error contract: {"message": str, "errors"?: {field: [str, ...]}}.

    - A plain "detail" (permission/auth/not-found errors, or a
      ValidationError raised with a single message) becomes
      {"message": <detail>}.
    - Field-level validation errors (a dict or list, e.g. from
      serializer.is_valid(raise_exception=True)) become
      {"message": "Validation échouée", "errors": <original dict/list>}.
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        return response

    data = response.data

    if isinstance(data, dict) and set(data.keys()) == {"detail"}:
        response.data = {"message": str(data["detail"])}
    else:
        if isinstance(data, list):
            data = {"non_field_errors": data}
        response.data = {
            "message": "Validation échouée",
            "errors": data,
        }

    return response
