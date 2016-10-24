import argparse
import asyncio
import sys
from asyncio.streams import StreamWriter, FlowControlMixin

async def stream_connect(reader, *writers):
    try:
        while True:
            data = await reader.read(1)
            if data == b'':
                break
            for writer in writers:
                writer.write(data)
    except asyncio.CancelledError:
        pass

async def listen_server(callback, host, port):
    async def cb(reader, writer):
        server.close()
        await callback(reader, writer)
        writer.close()
    server = await asyncio.start_server(cb, host=args.host, port=args.port)
    await server.wait_closed()

async def run_process(command, reader, writer):
    process = await asyncio.create_subprocess_shell(
        command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    tasks = [asyncio.ensure_future(t) for t in (
        stream_connect(reader, process.stdin),
        stream_connect(process.stdout, writer),
        stream_connect(process.stderr, writer),
    )]
    await process.wait()
    for t in tasks:
        t.cancel()
    await asyncio.sleep(0)

async def execute(args, loop):
    async def callback(reader, writer):
        await run_process(args.command, reader, writer)
    await listen_server(callback, host=args.host, port=args.port)

async def listen(args, loop):
    stdio_reader, stdio_writer = await connect_stdio()
    async def callback(reader, writer):
        await stream_connect(reader,stdio_writer)
    server = await asyncio.start_server(callback, host=args.host, port=args.port)
    await server.wait_closed()

async def shell(args, loop):
    async def callback(reader, writer):
        while True:
            writer.write(b'## ')
            command = await reader.readline()
            if command == b'exit\n':
                break
            await run_process(command, reader, writer)
            writer.write(b'\n')
        await writer.drain()
    ##await listen_server(callback, host=args.host, port=args.port)
    server = await asyncio.start_server(callback, host=args.host, port=args.port)
    await server.wait_closed()


async def upload(args, loop):
    reader, writer = await asyncio.open_connection(host=args.host, port=args.port)
    writer.write(args.file.read())
    await writer.drain()

async def connect_stdio(loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    reader_protocol = asyncio.StreamReaderProtocol(reader)
    writer_transport, writer_protocol = await loop.connect_write_pipe(FlowControlMixin, sys.stdout)
    writer = StreamWriter(writer_transport, writer_protocol, None, loop)
    await loop.connect_read_pipe(lambda: reader_protocol, sys.stdin)
    return reader, writer

async def client(args, loop):
    reader, writer = await asyncio.open_connection(host=args.host, port=args.port)
    stdio_reader, stdio_writer = await connect_stdio()
    t = asyncio.ensure_future(stream_connect(stdio_reader,writer))
    try:
        await stream_connect(reader, stdio_writer)
    finally:
        t.cancel()

if __name__ == '__main__':
    async def usage(args, loop):
        print(parser.usage)
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=usage)
    parser.add_argument('host')
    parser.add_argument('port', type=int)
    subparsers = parser.add_subparsers()

    execute_p = subparsers.add_parser('execute')
    execute_p.set_defaults(func=execute)
    execute_p.add_argument('command')

    client_p = subparsers.add_parser('client')
    client_p.set_defaults(func=client)

    listen_p = subparsers.add_parser('listen')
    listen_p.set_defaults(func=listen)

    shell_p = subparsers.add_parser('shell')
    shell_p.set_defaults(func=shell)

    upload_p = subparsers.add_parser('upload')
    upload_p.set_defaults(func=upload)
    upload_p.add_argument('file', type=argparse.FileType('rb'))

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(args.func(args, loop))
    finally:
        loop.close()
