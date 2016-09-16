from tornado import ioloop, web

class TestHandler(web.RequestHandler):
    def get(self):
        self.write('<h1>Test</h1>')

def main():
    app = web.Application([
        (r"/", TestHandler),
    ])
    app.listen(8888)
    print("Running...")
    ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()
