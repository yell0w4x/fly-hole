# import time
# import os
# from os.path import join, exists
from subprocess import check_call
import subprocess
from dns_server_mock import server_run

import pytest
import requests
from requests import codes
import signal
import time
from base64 import b64encode
from multiprocessing import Process


SUT_LOG_FN = '/test/sut/sut.log'


def run_relay(is_python_sut, is_debug_sut):
    if is_python_sut:
        return subprocess.Popen(['bash', '-c', f'exec python -u /test/sut/doh_relay.py >> {SUT_LOG_FN} 2>&1'])

    if is_debug_sut:
        return subprocess.Popen(['bash', '-c', f'RUST_BACKTRACE=full exec /test/sut/target/debug/relay >> {SUT_LOG_FN} 2>&1'])

    return subprocess.Popen(['bash', '-c', f'RUST_BACKTRACE=full exec /test/sut/target/release/relay >> {SUT_LOG_FN} 2>&1'])


@pytest.fixture(scope='function', autouse=True)
def print_test_name(request):
    test_name = request.node.name

    with open(SUT_LOG_FN, 'a') as f:
        f.write(f'{test_name:=^120}\n')


@pytest.fixture
def dns_server_mock(populate_error):
    proc = Process(target=server_run, args=(populate_error,))
    proc.start()
    yield proc
    proc.terminate()
    proc.join()


@pytest.fixture
def sut(is_python_sut, is_debug_sut):
    p = run_relay(is_python_sut, is_debug_sut)
    yield p
    p.terminate()
    p.wait(timeout=5)


@pytest.fixture
def wait_for_sut_up(sut):
    check_call(['/test/wait-for-it.sh', '--host=127.0.0.1', '--port=8000', '--timeout=10'])


DATA = b'UDP request goes here'
REVERSED_DATA = bytes(reversed(DATA))


@pytest.mark.parametrize('populate_error', [False])
def test_relay_dns_packets_via_get(dns_server_mock, wait_for_sut_up, sut):
    b64_data = b64encode(DATA).replace(b'==', b'')
    resp = requests.get(f'http://127.0.0.1:8000/?dns={b64_data.decode("utf-8")}', timeout=2)
    resp.raise_for_status()
    assert resp.content == REVERSED_DATA


@pytest.mark.parametrize('populate_error', [False])
def test_relay_dns_packets_via_post(dns_server_mock, wait_for_sut_up, sut):
    resp = requests.post(f'http://127.0.0.1:8000/', data=DATA, timeout=2)
    resp.raise_for_status()
    assert resp.content == REVERSED_DATA


@pytest.mark.parametrize('populate_error', [True])
def test_relay_must_return_bad_gateway_if_upstream_is_broken_get(dns_server_mock, wait_for_sut_up, sut):
    b64_data = b64encode(DATA).replace(b'==', b'')
    resp = requests.get(f'http://127.0.0.1:8000/?dns={b64_data.decode("utf-8")}', timeout=6)
    assert resp.status_code == codes.bad_gateway


@pytest.mark.parametrize('populate_error', [True])
def test_relay_must_return_bad_gateway_if_upstream_is_broken_post(dns_server_mock, wait_for_sut_up, sut):
    resp = requests.post(f'http://127.0.0.1:8000/', data=DATA, timeout=6)
    assert resp.status_code == requests.codes.bad_gateway


@pytest.mark.parametrize('populate_error', [False])
@pytest.mark.parametrize('url', ['http://127.0.0.1:8000/?dns=', 
                                 'http://127.0.0.1:8000/',
                                 'http://127.0.0.1:8000/?dns=corrupted-data'])
def test_relay_must_return_bad_request_if_invalid_parameter_given_get(dns_server_mock, wait_for_sut_up, sut, url):
    resp = requests.get(url, timeout=2)
    assert resp.status_code == codes.bad_request


@pytest.mark.parametrize('populate_error', [False])
@pytest.mark.parametrize('data', [None, bytes()])
def test_relay_must_return_bad_request_if_invalid_parameter_given_post(dns_server_mock, wait_for_sut_up, sut, data):
    resp = requests.post('http://127.0.0.1:8000/', data=data, timeout=2)
    assert resp.status_code == codes.bad_request


@pytest.mark.parametrize('populate_error', [False])
@pytest.mark.parametrize('method', ['GET', 'POST'])
def test_relay_must_return_not_found_if_unknown_url_requested(dns_server_mock, wait_for_sut_up, sut, method):
    resp = requests.request(method, 'http://127.0.0.1:8000/asdf', timeout=2)
    assert resp.status_code == codes.not_found


@pytest.mark.parametrize('populate_error', [False])
@pytest.mark.parametrize('method, expected_status_codes', 
                         [('HEAD', [codes.method_not_allowed]), 
                          ('PUT', [codes.method_not_allowed]), 
                          ('DELETE', [codes.method_not_allowed]), 
                          # aiohttp somehow yields 404 for CONNECT and doesn't allow override                          
                          ('CONNECT', [codes.method_not_allowed, codes.not_found]), 
                          ('OPTIONS', [codes.method_not_allowed]), 
                          ('TRACE', [codes.method_not_allowed]), 
                          ('PATCH', [codes.method_not_allowed]), 
                          ('OUT-OF-RFC', [codes.method_not_allowed, codes.bad_request])])
def test_relay_must_allow_only_get_and_post_methods(dns_server_mock, wait_for_sut_up, sut, method, expected_status_codes):
    resp = requests.request(method, 'http://127.0.0.1:8000/', timeout=2)
    assert resp.status_code in expected_status_codes
