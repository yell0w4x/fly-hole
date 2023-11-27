import pytest


def pytest_addoption(parser):
    parser.addoption('--python', action='store_true', help='Run python SUT)')
    parser.addoption('--rust', action='store_true', help='Run rust SUT)')
    parser.addoption('--debug-sut', action='store_true', help='Build and run debug version of rust based SUT)')


def get_option(request, name):
    option = request.config.getoption(name)
    print(name, option)
    return option


@pytest.fixture(scope='session')
def is_python_sut(request):
    return get_option(request, '--python')


@pytest.fixture(scope='session')
def is_rust_sut(request):
    return get_option(request, '--rust')


@pytest.fixture(scope='session')
def is_debug_sut(request):
    return get_option(request, '--debug-sut')
