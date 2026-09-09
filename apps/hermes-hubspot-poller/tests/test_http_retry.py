"""Tests for the network-error retry wrapper added 2026-09-09 after the founder's poller lost
whole ticks to transient WinError 10053 / getaddrinfo failed / SSL EOF errors with zero retries."""

from __future__ import annotations

import httpx
import pytest

from http_retry import request_with_retry


def test_succeeds_on_first_attempt_without_retry():
    calls = []

    def send():
        calls.append(1)
        return httpx.Response(200, json={"ok": True})

    response = request_with_retry(send)

    assert response.status_code == 200
    assert len(calls) == 1


def test_retries_on_transport_error_then_succeeds(monkeypatch):
    monkeypatch.setattr("http_retry.time.sleep", lambda _seconds: None)
    calls = []

    def send():
        calls.append(1)
        if len(calls) < 3:
            raise httpx.ConnectError("getaddrinfo failed")
        return httpx.Response(200, json={"ok": True})

    response = request_with_retry(send)

    assert response.status_code == 200
    assert len(calls) == 3


def test_raises_last_error_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr("http_retry.time.sleep", lambda _seconds: None)
    calls = []

    def send():
        calls.append(1)
        raise httpx.ConnectError("getaddrinfo failed")

    with pytest.raises(httpx.ConnectError):
        request_with_retry(send)

    assert len(calls) == 3


def test_does_not_retry_non_transport_exceptions():
    calls = []

    def send():
        calls.append(1)
        raise ValueError("not a network error")

    with pytest.raises(ValueError):
        request_with_retry(send)

    assert len(calls) == 1
