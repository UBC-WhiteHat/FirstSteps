import argparse
import asyncio
import subprocess

async def execute(args, loop):
    pass

async def listen(args, loop):
    async def callback(reader, writer):
        print('Connected')
        while not reader.at_eof():
            data = await reader.read()
            if len(data) == 0:
                reader.feed_eof()
            print(data)
    server = await asyncio.start_server(callback, host=args.host, port=args.port)
    await server.wait_closed()

async def shell(args, loop):
    print('shell', args)

async def upload(args, loop):
    reader, writer = await asyncio.open_connection(host=args.host, port=args.port)
    writer.write(args.file.read())
    await writer.drain()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
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

    loop.run_until_complete(args.func(args, loop))
