import json
from types import SimpleNamespace
import pytest
from infrastructure import handler as api

@pytest.mark.parametrize("path,method,query,status",[("/bad","GET","",404),("/api/network","POST","",405),("/api/network","GET","x=1",422)])
def test_invalid_requests_do_not_read_s3(monkeypatch,path,method,query,status):
    def unexpected(key): raise AssertionError("S3 must not be read")
    monkeypatch.setattr(api,"load_json",unexpected)
    response=api.handler({"rawPath":path,"rawQueryString":query,"requestContext":{"http":{"method":method}}},SimpleNamespace(aws_request_id="test"))
    assert response["statusCode"]==status

def test_s3_failure_is_sanitized(monkeypatch):
    def unavailable(key): raise RuntimeError("sensitive internal detail")
    monkeypatch.setattr(api,"load_json",unavailable)
    response=api.handler({"rawPath":"/api/network","requestContext":{"http":{"method":"GET"}}},SimpleNamespace(aws_request_id="test"))
    assert response["statusCode"]==503
    assert "sensitive" not in response["body"]
    assert json.loads(response["body"])["request_id"]=="test"
