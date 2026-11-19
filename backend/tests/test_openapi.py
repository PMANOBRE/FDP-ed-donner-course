def test_every_operation_follows_the_api_rules(api):
    schema = api.get("/openapi.json").json()
    operations = [op for path in schema["paths"].values() for op in path.values()]
    assert operations
    for op in operations:
        assert op["operationId"]
        assert op["description"]
        assert "\n" not in op["description"].strip()
        for parameter in op.get("parameters", []):
            assert parameter["required"], (op["operationId"], parameter["name"])
        body = op.get("requestBody")
        if body:
            assert body["required"], op["operationId"]
            ref = body["content"]["application/json"]["schema"]["$ref"]
            model = schema["components"]["schemas"][ref.split("/")[-1]]
            assert set(model.get("required", [])) == set(model["properties"]), ref


def test_operation_ids_are_the_function_names(api):
    schema = api.get("/openapi.json").json()
    ids = [
        op["operationId"] for path in schema["paths"].values() for op in path.values()
    ]
    assert len(ids) == len(set(ids))
    assert {
        "health",
        "list_claims",
        "get_claim",
        "get_policy",
        "get_claim_history",
    } <= set(ids)
