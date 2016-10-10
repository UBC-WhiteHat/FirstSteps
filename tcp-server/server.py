import argparse
import asyncio

async def stream_connect(reader, *writers):
    try:
        while True:
            data = await reader.readline()
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
    async def callback(reader, writer):
        while not reader.at_eof():
            data = await reader.read()
            if data == b'':
                reader.feed_eof()
            print(data)
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
    await listen_server(callback, host=args.host, port=args.port)

async def upload(args, loop):
    reader, writer = await asyncio.open_connection(host=args.host, port=args.port)
    writer.write(args.file.read())
    await writer.drain()

async def usage(args, loop):
    print("Please specify a command.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=usage)
    parser.add_argument('host')
    parser.add_argument('port', type=int)
    subparsers = parser.add_subparsers()

    execute_p = subparsers.add_parser('execute')
    execute_p.set_defaults(func=execute)
    execute_p.add_argument('command')

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
