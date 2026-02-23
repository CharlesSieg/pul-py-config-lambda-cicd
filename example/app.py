import json


def handler(event, context):
    """Simple Lambda handler for demonstration."""
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Hello from containerized Lambda!",
            "version": "1.0.0",
        }),
    }
