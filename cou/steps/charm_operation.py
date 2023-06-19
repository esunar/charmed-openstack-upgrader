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

"""Charm operation utilities."""
import logging
import subprocess
from typing import Any

from zaza.model import (
    CURRENT_MODEL,
    get_application_config,
    set_application_config,
    upgrade_charm,
)


def charm_upgrade(application_name: str) -> None:
    """Upgrade a charm to the latest revision in the current channel."""
    logging.info("Upgrading %s to the latest revision in the current channel", application_name)
    upgrade_charm(application_name)


def charm_channel_refresh(application_name: str, channel: str) -> None:
    """Refresh a charm to track a target channel."""
    logging.info("Refresh %s to the %s channel", application_name, channel)
    upgrade_charm(application_name, channel=channel)


def component_upgrade(**kwargs: Any) -> None:
    """Upgrade app."""
    application_name = kwargs["app"]
    old_origin = kwargs["old_origin"]
    new_origin = kwargs["new_origin"]
    channel = kwargs["channel"]

    juju_run(["juju", "refresh", application_name])
    config = get_application_config(application_name)

    src_option = "openstack-origin"
    try:
        config[src_option]
    except KeyError:
        src_option = "source"

    if config[src_option]["value"] == new_origin:
        logging.info("Already upgraded %s", application_name)
        return

    supported = True
    try:
        config["action-managed-upgrade"]
    except KeyError:
        supported = False

    new_config = {src_option: old_origin}
    if supported:
        new_config["action-managed-upgrade"] = "False"
    set_application_config(application_name, new_config)

    juju_run(["juju", "refresh", application_name, "--channel", channel])

    new_config = {src_option: new_origin}
    set_application_config(application_name, new_config)


def juju_run(command: list[str]) -> None:
    """Run juju command in console."""
    if CURRENT_MODEL:
        command.append("-m")
        command.append(CURRENT_MODEL)
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
