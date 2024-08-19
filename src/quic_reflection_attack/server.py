import asyncio
from typing import Optional
import uvloop

from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import QuicEvent, StreamDataReceived
from aioquic.asyncio import serve  # type: ignore


class QuicServerProtocol:
    def __init__(self):
        self.quic: Optional[QuicConnection] = None

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, StreamDataReceived):
            print(f"Received data on stream {event.stream_id}: {event.data.decode()}")

            assert self.quic is not None, "QUIC Connection is not initialized"

            # Echo the received data back to the client
            self.quic.send_stream_data(event.stream_id, event.data)


async def main():
    configuration = QuicConfiguration(
        is_client=False,
        alpn_protocols=["quic-echo"],  # our own custome ALPN protocol
    )

    # Load your SSL certificate and private key
    configuration.load_cert_chain("server.crt", "server.key")  # type: ignore

    await serve(
        "localhost",
        8000,
        configuration=configuration,
        create_protocol=QuicServerProtocol,
    )

    await asyncio.Future()  # Run forever


if __name__ == "__main__":
    uvloop.run(main())
