import pytest
from pytest_socket import enable_socket, socket_allow_hosts


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup():
    """Ensure the bluetooth integration we depend on can load.

    https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/issues/154#issuecomment-2065081783

    """
    enable_socket()
    socket_allow_hosts(
        # Allow "None" to allow the bluetooth integration to load.
        ["None"],
        allow_unix_socket=True,
    )
