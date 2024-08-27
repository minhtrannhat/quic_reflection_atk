import asyncio
from aioquic.asyncio.protocol import QuicConnectionProtocol
import uvloop
import ssl
from typing import cast, Optional

from aioquic.asyncio.client import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent, StreamDataReceived
from aioquic.quic.connection import QuicConnection


async def run_client(host: str, port: int, message: str) -> None:
    configuration = QuicConfiguration(
        is_client=True, alpn_protocols=["quic-echo"], verify_mode=ssl.CERT_NONE
    )  # our own custome alpn protocol

    async with connect(
        host,
        port,
        configuration=configuration,
        create_protocol=QuicClientProtocol,
        wait_connected=True,
    ) as client:
        client = cast(QuicClientProtocol, client)

        assert (
            client.quic is not None
        ), "QUIC Client connection is not properly initilized"

        # Open a stream and send data
        stream_id = client.quic.get_next_available_stream_id()
        client.quic.send_stream_data(stream_id, message.encode())

        # Wait for the response
        response = await client.wait_for_response(stream_id)
        print(f"Response from server: {response}")


class QuicClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.quic: Optional[QuicConnection] = None
        self.stream_data = {}

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, StreamDataReceived):
            stream_id = event.stream_id
            data = event.data
            if stream_id in self.stream_data:
                self.stream_data[stream_id] += data
            else:
                self.stream_data[stream_id] = data

    async def wait_for_response(self, stream_id: int) -> str:
        while stream_id not in self.stream_data:
            await asyncio.sleep(0.1)
        return self.stream_data[stream_id].decode()


if __name__ == "__main__":
    host = "localhost"
    port = 8000
    message = "Hello, QUIC server!"

    uvloop.run(run_client(host, port, message))
