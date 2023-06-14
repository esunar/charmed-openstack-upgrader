# Copyright 2023 Canonical Limited.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import OrderedDict, defaultdict

import mock
import pytest

from cou.steps import analyze


@pytest.fixture
def status():
    mock_keystone_ch = mock.MagicMock()
    mock_keystone_ch.base = {"channel": "ussuri/stable"}
    mock_keystone_ch.charm = "ch:amd64/focal/keystone-638"
    mock_keystone_ch.units = OrderedDict(
        [("keystone/0", {}), ("keystone/1", {}), ("keystone/2", {})]
    )

    mock_cinder_ch = mock.MagicMock()
    mock_cinder_ch.base = {"channel": "ussuri/stable"}
    mock_cinder_ch.charm = "ch:amd64/focal/cinder-633"
    mock_cinder_ch.units = OrderedDict([("cinder/0", {}), ("cinder/1", {}), ("cinder/2", {})])

    mock_keystone_cs = mock.MagicMock()
    mock_keystone_cs.base = {"channel": "ussuri/stable"}
    mock_keystone_cs.charm = "cs:amd64/focal/keystone-638"
    mock_keystone_cs.units = OrderedDict(
        [("keystone/0", {}), ("keystone/1", {}), ("keystone/2", {})]
    )

    mock_keystone_wrong_channel = mock.MagicMock()
    mock_keystone_wrong_channel.base = {"channel": "latest/stable"}
    mock_keystone_wrong_channel.charm = "ch:amd64/focal/keystone-638"
    mock_keystone_wrong_channel.units = OrderedDict(
        [("keystone/0", {}), ("keystone/1", {}), ("keystone/2", {})]
    )

    mock_keystone_wallaby = mock.MagicMock()
    mock_keystone_wallaby.base = {"channel": "wallaby/stable"}
    mock_keystone_wallaby.charm = "ch:amd64/focal/keystone-638"
    mock_keystone_wallaby.units = OrderedDict(
        [("keystone/0", {}), ("keystone/1", {}), ("keystone/2", {})]
    )

    status = {
        "keystone_ch": mock_keystone_ch,
        "cinder_ch": mock_cinder_ch,
        "keystone_cs": mock_keystone_cs,
        "keystone_wrong_channel": mock_keystone_wrong_channel,
        "keystone_wallaby": mock_keystone_wallaby,
    }
    return status


@pytest.fixture
def full_status(status):
    mock_full_status = mock.MagicMock()
    mock_full_status.model.name = "my_model"
    mock_full_status.applications = OrderedDict(
        [("keystone", status["keystone_ch"]), ("cinder", status["cinder_ch"])]
    )
    return mock_full_status


@pytest.fixture
def units():
    units_ussuri = defaultdict(dict)
    units_wallaby = defaultdict(dict)
    for unit in ["keystone/0", "keystone/1", "keystone/2"]:
        units_ussuri[unit]["os_version"] = "ussuri"
        units_ussuri[unit]["pkg_version"] = "2:17.0.1-0ubuntu1"
        units_wallaby[unit]["os_version"] = "wallaby"
        units_wallaby[unit]["pkg_version"] = "2:18.1.0-0ubuntu1~cloud0"
    return {"units_ussuri": units_ussuri, "units_wallaby": units_wallaby}


@pytest.fixture
def apps(mocker, status, config):
    keystone_status = status["keystone_ch"]
    cinder_status = status["cinder_ch"]
    app_config = config["keystone"]
    mocker.patch.object(
        analyze,
        "get_pkg_version",
        side_effect=[
            "2:17.0.1-0ubuntu1~cloud0",
            "2:17.0.1-0ubuntu1~cloud0",
            "2:17.0.1-0ubuntu1~cloud0",
            "2:16.4.2-0ubuntu2.2~cloud0",
            "2:16.4.2-0ubuntu2.2~cloud0",
            "2:16.4.2-0ubuntu2.2~cloud0",
        ],
    )
    mocker.patch.object(analyze, "get_openstack_release", return_value=None)
    app_keystone = analyze.Application("keystone", keystone_status, app_config, "my_model")
    app_cinder = analyze.Application("cinder", cinder_status, app_config, "my_model")

    return [app_keystone, app_cinder]


@pytest.fixture
def config():
    return {
        "keystone": {
            "openstack-origin": {"value": "distro"},
        },
        "keystone_wallaby": {"openstack-origin": {"value": "cloud:focal-wallaby"}},
    }