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

"""Upgrade planning utilities."""

import logging
import sys
from argparse import Namespace
from typing import Any

from termcolor import colored

from cou.steps import UpgradeStep
from cou.steps.backup import backup
from cou.steps.charm_operation import component_upgrade
from cou.zaza_utils.model import block_until_all_units_idle

CLOUD_FOCAL_VICTORIA = "cloud:focal-victoria"

VICTORIA_STABLE = "victoria/stable"

AVAILABLE_OPTIONS = "cas"


def generate_plan(args: Namespace) -> UpgradeStep:
    """Generate plan for upgrade."""
    logging.info(args)  # for placeholder
    plan = UpgradeStep(description="Top level plan", parallel=False, function=None)
    plan.add_step(
        UpgradeStep(description="backup mysql databases", parallel=False, function=backup)
    )
    keystone = plan.add_step(
        UpgradeStep(description="Upgrade keystone", parallel=False, function=None)
    )

    keystone.add_step(
        UpgradeStep(
            description="Upgrade without action-managed-upgrade keystone",
            parallel=False,
            function=component_upgrade,
            app="keystone",
            old_origin="distro",
            new_origin=CLOUD_FOCAL_VICTORIA,
            channel=VICTORIA_STABLE,
        )
    )
    keystone.add_step(
        UpgradeStep(
            description="wait for upgrade",
            parallel=False,
            confirmation=False,
            function=block_until_all_units_idle,
        )
    )

    control_plane = plan.add_step(
        UpgradeStep(description="Upgrade Control Plane", parallel=False, function=None)
    )
    control_plane.add_step(
        UpgradeStep(
            description="Upgrade without action-managed-upgrade cinder",
            parallel=False,
            function=component_upgrade,
            app="cinder",
            old_origin="distro",
            new_origin=CLOUD_FOCAL_VICTORIA,
            channel=VICTORIA_STABLE,
        )
    )
    control_plane.add_step(
        UpgradeStep(
            description="Upgrade without action-managed-upgrade glance",
            parallel=False,
            function=component_upgrade,
            app="glance",
            old_origin="distro",
            new_origin=CLOUD_FOCAL_VICTORIA,
            channel=VICTORIA_STABLE,
        )
    )
    control_plane.add_step(
        UpgradeStep(
            description="Upgrade without action-managed-upgrade placement",
            parallel=False,
            function=component_upgrade,
            app="placement",
            old_origin="distro",
            new_origin=CLOUD_FOCAL_VICTORIA,
            channel=VICTORIA_STABLE,
        )
    )
    control_plane.add_step(
        UpgradeStep(
            description="Upgrade without action-managed-upgrade nova-cloud-controller",
            parallel=False,
            function=component_upgrade,
            app="nova-cloud-controller",
            old_origin="distro",
            new_origin=CLOUD_FOCAL_VICTORIA,
            channel=VICTORIA_STABLE,
        )
    )
    control_plane.add_step(
        UpgradeStep(
            description="Upgrade without action-managed-upgrade neutron-api",
            parallel=False,
            function=component_upgrade,
            app="neutron-api",
            old_origin="distro",
            new_origin=CLOUD_FOCAL_VICTORIA,
            channel=VICTORIA_STABLE,
        )
    )
    control_plane.add_step(
        UpgradeStep(
            description="Upgrade without action-managed-upgrade neutron-gateway",
            parallel=False,
            function=component_upgrade,
            app="neutron-gateway",
            old_origin="distro",
            new_origin=CLOUD_FOCAL_VICTORIA,
            channel=VICTORIA_STABLE,
        )
    )
    control_plane.add_step(
        UpgradeStep(
            description="wait for upgrade",
            parallel=False,
            confirmation=False,
            function=block_until_all_units_idle,
        )
    )
    return plan


def prompt(parameter: str) -> str:
    """Generate eye-catching prompt."""

    def bold(text: str) -> str:
        return colored(text, "red", attrs=["bold"])

    def normal(text: str) -> str:
        return colored(text, "red")

    return (
        normal(parameter + " (")
        + bold("c")
        + normal(")ontinue/(")
        + bold("a")
        + normal(")bort/(")
        + bold("s")
        + normal(")kip:")
    )


def apply_plan(upgrade_plan: Any) -> None:
    """Apply the plan for upgrade."""
    result = "X"
    while result.casefold() not in AVAILABLE_OPTIONS:
        result = "c"
        if upgrade_plan.confirmation:
            result = input(prompt(upgrade_plan.description)).casefold()
        else:
            print(prompt(upgrade_plan.description) + "c")

        match result:
            case "c":
                upgrade_plan.run()
                for sub_step in upgrade_plan.sub_steps:
                    apply_plan(sub_step)
            case "a":
                logging.info("Aborting plan")
                sys.exit(1)
            case "s":
                logging.info("Skipped")
            case _:
                logging.info("No valid input provided!")


def dump_plan(upgrade_plan: UpgradeStep, ident: int = 0) -> None:
    """Dump the plan for upgrade."""
    tab = "\t"
    logging.info(f"{tab * ident}{upgrade_plan.description}")  # pylint: disable=W1203
    for sub_step in upgrade_plan.sub_steps:
        dump_plan(sub_step, ident + 1)
