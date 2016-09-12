import asyncio

@asyncio.coroutine
def handle_echo(reader, writer):
    text = None
    while text != 'end':
        data = yield from reader.readline()
        text = data.decode().strip()
        print('Received: {}'.format(text))
        writer.write(data)
    print('Closing...')
    yield from writer.drain()
    writer.close()

loop = asyncio.get_event_loop()
server = loop.run_until_complete(
    asyncio.start_server(handle_echo, '127.0.0.1', 8888, loop=loop))

print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
