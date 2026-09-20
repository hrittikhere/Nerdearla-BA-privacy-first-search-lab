"""Conservative audit of the documented sbx decision/resources rule structure."""

LOCAL_ENDPOINT = "localhost:11435"


def audit_allow_rules(payload):
    resources = []

    def visit(value):
        if isinstance(value, dict):
            fields = {k.lower(): v for k, v in value.items()}
            if fields.get("decision") == "allow":
                targets = fields.get("resources")
                if not isinstance(targets, list) or not all(isinstance(t, str) for t in targets):
                    raise ValueError(
                        "Unrecognized sbx allow-rule shape; cannot certify the allowlist"
                    )
                resources.extend(targets)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    if not resources:
        raise ValueError(
            "No recognizable local allow rule; inspect the sbx JSON/schema before proceeding"
        )
    unexpected = sorted(set(resources) - {LOCAL_ENDPOINT})
    if unexpected:
        raise ValueError(f"External/broad allowances remain: {unexpected}")
    return {"allowed_resources": sorted(set(resources)), "external_allowances": 0}
