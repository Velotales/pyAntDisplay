#!/usr/bin/env python3
"""
PyANTDisplay - ANT Backend Abstraction

Copyright (c) 2025 Velotales

MIT License

Provides a thin abstraction over ANT libraries to allow switching
between backends (e.g., openant, python-ant) without changing
application code.
"""

from typing import Optional

from colorama import Fore, Style


class ChannelType:
    BIDIRECTIONAL_RECEIVE = 0


class _OpenAntChannelWrapper:
    def __init__(self, channel):
        self._ch = channel
        # Lazy import for message IDs
        try:
            from openant.easy.node import Message as _Msg  # type: ignore

            self._Message = _Msg
        except Exception:
            self._Message = None

    # Event handlers
    @property
    def on_broadcast_data(self):
        return getattr(self._ch, "on_broadcast_data", None)

    @on_broadcast_data.setter
    def on_broadcast_data(self, cb):
        self._ch.on_broadcast_data = cb

    @property
    def on_burst_data(self):
        return getattr(self._ch, "on_burst_data", None)

    @on_burst_data.setter
    def on_burst_data(self, cb):
        self._ch.on_burst_data = cb

    # Channel controls
    def set_period(self, period: int):
        self._ch.set_period(period)

    def set_search_timeout(self, timeout: int):
        self._ch.set_search_timeout(timeout)

    def set_rf_freq(self, freq: int):
        self._ch.set_rf_freq(freq)

    def set_id(self, device_number: int, device_type: int, transmission_type: int):
        self._ch.set_id(device_number, device_type, transmission_type)

    def open(self):
        self._ch.open()

    def close(self):
        self._ch.close()

    def enable_extended_messages(self, enabled: bool):
        # Expose openant's extended message toggle when available
        if hasattr(self._ch, "enable_extended_messages"):
            self._ch.enable_extended_messages(enabled)

    def request_channel_id(self):
        """Return (device_number, device_type, transmission_type) if supported."""
        if self._Message is None or not hasattr(self._ch, "request_message"):
            return None
        try:
            res = self._ch.request_message(self._Message.ID.RESPONSE_CHANNEL_ID)
            _, _, id_data = res
            dev_num = id_data[0] | (id_data[1] << 8)
            dev_type = id_data[2]
            trans_type = id_data[3]
            return (dev_num, dev_type, trans_type)
        except Exception:
            return None


class _OpenAntNodeWrapper:
    def __init__(self, node, channel_type_cls):
        self._node = node
        self._ChannelTypeCls = channel_type_cls
        # Import here to avoid top-level dependency issues
        from openant.easy.channel import Channel as OpenAntChannel

        self._OpenAntChannel = OpenAntChannel

    def start(self):
        self._node.start()

    def stop(self):
        self._node.stop()

    def new_network(self, key):
        # openant.easy.Node typically uses set_network_key instead of new_network
        try:
            return self._node.new_network(key=key)
        except Exception:
            # Fallback: set network key on network 0
            self._node.set_network_key(0, key)
            return 0

    def set_network_key(self, network_number: int, key):
        self._node.set_network_key(network_number, key)

    def new_channel(self, ch_type: int):
        # Map our ChannelType to openant channel type
        if ch_type == self._ChannelTypeCls.BIDIRECTIONAL_RECEIVE:
            ch = self._node.new_channel(self._OpenAntChannel.Type.BIDIRECTIONAL_RECEIVE)
        else:
            ch = self._node.new_channel(ch_type)
        return _OpenAntChannelWrapper(ch)


class AntBackend:
    def __init__(self, preferred: Optional[str] = None, debug: bool = False):
        self.preferred = (preferred or "openant").lower()
        self.debug = debug
        self.name = None
        self._channel_type_cls = ChannelType
        self._node_wrapper_cls = None

        # Try to select backend
        self._select_backend()

    def _select_backend(self):
        # Attempt python-ant first if preferred
        if self.preferred == "python-ant":
            try:
                # Placeholder: python-ant import (adjust if library name differs)
                import python_ant  # type: ignore # noqa: F401

                if self.debug:
                    print(f"{Fore.BLUE}[DEBUG] Selected backend: python-ant{Style.RESET_ALL}")
                # Not implemented: provide wrappers when library is available
                self.name = "python-ant"
                # For now, raise to fallback unless implemented
                raise ImportError("python-ant backend not implemented in this environment")
            except Exception as e:
                if self.debug:
                    print(
                        f"{Fore.YELLOW}[DEBUG] python-ant unavailable ({e}); falling back to openant{Style.RESET_ALL}"
                    )

        # Fallback to openant
        try:
            from openant.easy.node import Node as OpenAntNode

            def _create_node():
                return _OpenAntNodeWrapper(OpenAntNode(), self._channel_type_cls)

            self._create_node = _create_node
            self.name = "openant"
            if self.debug:
                print(f"{Fore.BLUE}[DEBUG] Selected backend: openant{Style.RESET_ALL}")
        except Exception as e:
            self._create_node = None
            self.name = None
            raise RuntimeError(f"No ANT backend available: {e}")

    def create_node(self):
        if not hasattr(self, "_create_node") or self._create_node is None:
            raise RuntimeError("ANT backend not initialized")
        return self._create_node()

    @property
    def channel_type(self):
        return self._channel_type_cls
