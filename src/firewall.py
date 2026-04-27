"""Windows Firewall management for LoL chat blocking.

This module provides a high-level interface to create and remove Windows
Firewall outbound rules that block TCP connections to Riot's chat servers.
Requires administrator privileges to execute.
"""

from __future__ import annotations

import logging
import socket
import subprocess
from dataclasses import dataclass
from typing import Self

__all__ = ["FirewallManager", "FirewallError"]

logger = logging.getLogger(__name__)

_RULE_PREFIX = "LoLChatOff"
_RULE_NAME_IPV4 = f"{_RULE_PREFIX}_IPv4"
_RULE_NAME_IPV6 = f"{_RULE_PREFIX}_IPv6"


class FirewallError(Exception):
    """Raised when a firewall operation fails."""


@dataclass(frozen=True, slots=True)
class ResolvedAddresses:
    """Resolved IP addresses for a chat server."""

    ipv4: str
    ipv6: str | None = None

    @classmethod
    def from_hostname(cls, hostname: str) -> Self:
        """Resolve a hostname to its IPv4 and IPv6 addresses.

        Raises:
            FirewallError: If the hostname cannot be resolved to an IPv4 address.
        """
        try:
            info = socket.getaddrinfo(hostname, None, socket.AF_INET)
            ipv4 = str(info[0][4][0])
        except (socket.gaierror, IndexError) as exc:
            raise FirewallError(
                f"Failed to resolve IPv4 for {hostname!r}"
            ) from exc

        ipv6: str | None = None
        try:
            info6 = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            ipv6 = str(info6[0][4][0])
        except (socket.gaierror, IndexError):
            logger.debug("IPv6 resolution failed for %s, skipping", hostname)

        return cls(ipv4=ipv4, ipv6=ipv6)


class FirewallManager:
    """Manages Windows Firewall rules for blocking LoL chat traffic.

    Usage::

        fw = FirewallManager()
        if not fw.is_blocked:
            fw.block("br.chat.si.riotgames.com")
        else:
            fw.unblock()
    """

    @property
    def is_blocked(self) -> bool:
        """Whether the chat-blocking firewall rules are currently active."""
        result = self._exec(
            "show", "rule", f"name={_RULE_NAME_IPV4}"
        )
        return _RULE_NAME_IPV4 in result.stdout

    def block(self, hostname: str) -> None:
        """Add firewall rules to block outbound traffic to the chat server.

        Args:
            hostname: The chat server FQDN to resolve and block.

        Raises:
            FirewallError: If DNS resolution or rule creation fails.
        """
        if self.is_blocked:
            logger.info("Rules already active, unblocking first")
            self.unblock()

        addresses = ResolvedAddresses.from_hostname(hostname)
        logger.info("Blocking %s (IPv4=%s, IPv6=%s)", hostname, addresses.ipv4, addresses.ipv6)

        self._add_rule(_RULE_NAME_IPV4, addresses.ipv4)

        if addresses.ipv6:
            self._add_rule(_RULE_NAME_IPV6, addresses.ipv6)

    def unblock(self) -> None:
        """Remove all chat-blocking firewall rules.

        Raises:
            FirewallError: If no rules existed to remove.
        """
        ipv4_removed = self._delete_rule(_RULE_NAME_IPV4)
        ipv6_removed = self._delete_rule(_RULE_NAME_IPV6)

        if not ipv4_removed and not ipv6_removed:
            raise FirewallError("No active rules to remove")

        logger.info("Chat blocking rules removed")

    def _add_rule(self, name: str, remote_ip: str) -> None:
        result = self._exec(
            "add", "rule",
            f"name={name}", "dir=out", "action=block",
            "protocol=TCP", f"remoteip={remote_ip}",
        )
        if result.returncode != 0:
            raise FirewallError(
                f"Failed to add rule {name!r}: {result.stderr.strip()}"
            )

    def _delete_rule(self, name: str) -> bool:
        result = self._exec("delete", "rule", f"name={name}")
        return result.returncode == 0

    @staticmethod
    def _exec(*args: str) -> subprocess.CompletedProcess[str]:
        """Execute a netsh advfirewall firewall command."""
        cmd = ["netsh", "advfirewall", "firewall", *args]
        logger.debug("Executing: %s", " ".join(cmd))
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
