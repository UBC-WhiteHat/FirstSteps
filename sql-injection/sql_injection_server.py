import asyncio
from tornado import web
from tornado.platform.asyncio import AsyncIOMainLoop

import asyncpg

class TestHandler(web.RequestHandler):
    def get(self):
        self.write('''
        <form action="" method="POST">
            <label for="name">Name: </label>
            <input name="name" id="name" type="text"/>
            <input type="submit" value="Send"/>
        </form>
        ''')
    async def post(self):
        name = self.get_argument('name')
        con = await asyncpg.connect(
            host='postgres',
            user='postgres',
            password='passwd')
        try:
            #insert_result = await con.execute('''
            #    INSERT INTO names (name) VALUES ('{name}');
            #'''.format(name=name))
            insert_result = await con.execute('''
                INSERT INTO names (name) VALUES ($1);
            ''', name)
            rows = await con.fetch('''
                SELECT * from names;
            ''')
            self.write('''
                {insert_result} <br />
                {rows} <br />
            '''.format(
                insert_result=insert_result,
                rows=[dict(row) for row in rows]))
        finally:
            await con.close()

def main():
    AsyncIOMainLoop().install()

    app = web.Application([
        (r"/", TestHandler),
    ])
    app.listen(8888)
    print("Running...")

    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    main()
