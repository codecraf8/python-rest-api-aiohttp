# Rest API using asyncio

Asyncio is python library for writing single-threaded concurrent code using coroutines, multiplexing I/O access over sockets and other resources, running network clients and servers, and other related primitives.

This provides concurrency especially for I/O bound tasks over sockets and other resources. Concurrency ensures that user does not have wait for the I/O bound results. 

In this article, we will create a rest API for our application using asyncio. It is a simples application having one table Note with following fields:

* Title
* Description
* Created At
* Created By
* Priority

### Set up aiohttp
Activate a virtual environment in python 3 and install aiohttp

```
pip install aiohttp
```

or clone the github repository and install the requirements
```
pip install -r requirements.txt
```

### Models

We will configure application to use sqlite as our database in models.py

```
# DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
DB_URI = 'sqlite:///stuff.db'

Session = sessionmaker(autocommit=False,
                       autoflush=False,
                       bind=create_engine(DB_URI))
session = scoped_session(Session)
Base = declarative_base()
```

Then we create Note class for note objects in models.py

```
class Note(Base):
    __tablename__ = 'notes'
    id      = Column(Integer, primary_key=True)
    title    = Column(String(50))
    description     = Column(String(50))
    created_at     = Column(String(50))
    created_by     = Column(String(50))
    priority     = Column(Integer)

    def __init__(self, title, description, created_at ,created_by, priority):
        self.title = title
        self.description = description
        self.created_at = created_at
        self.created_by = created_by
        self.priority = priority

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def to_json(self):
        to_serialize = ['id', 'title', 'description', 'created_at', 'created_by', 'priority']
        d = {}
        for attr_name in to_serialize:
            d[attr_name] = getattr(self, attr_name)
        return d
```

### Resources
We define our API endpoints in aiohttp_rest.py file
```
DEFAULT_METHODS = ('GET', 'POST', 'PUT', 'DELETE')


class RestEndpoint:
    def __init__(self):
        self.methods = {}

        for method_name in DEFAULT_METHODS:
            method = getattr(self, method_name.lower(), None)
            if method:
                self.register_method(method_name, method)

    def register_method(self, method_name, method):
        self.methods[method_name.upper()] = method

    async def dispatch(self, request: Request):
        method = self.methods.get(request.method.upper())
        if not method:
            raise HTTPMethodNotAllowed('', DEFAULT_METHODS)

        wanted_args = list(inspect.signature(method).parameters.keys())
        available_args = request.match_info.copy()
        available_args.update({'request': request})

        unsatisfied_args = set(wanted_args) - set(available_args.keys())
        if unsatisfied_args:
            # Expected match info that doesn't exist
            raise HttpBadRequest('')

        return await method(**{arg_name: available_args[arg_name] for arg_name in wanted_args})


class CollectionEndpoint(RestEndpoint):
    def __init__(self, resource):
        super().__init__()
        self.resource = resource

    async def get(self) -> Response:
        data = []

        notes = session.query(Note).all()
        for instance in self.resource.collection.values():
            data.append(self.resource.render(instance))
        data = self.resource.encode(data)
        return Response ( status=200, body=self.resource.encode({
            'notes': [
                {'id': note.id, 'title': note.title, 'description': note.description,
                'created_at': note.created_at, 'created_by': note.created_by, 'priority': note.priority}

                    for note in session.query(Note)

                    ]
            }), content_type='application/json')


    async def post(self, request):
        data = await request.json()
        note=Note(title=data['title'], description=data['description'], created_at=data['created_at'], created_by=data['created_by'], priority=data['priority'])
        session.add(note)
        session.commit()

        return Response(status=201, body=self.resource.encode({
            'notes': [
                {'id': note.id, 'title': note.title, 'description': note.description,
                'created_at': note.created_at, 'created_by': note.created_by, 'priority': note.priority}

                    for note in session.query(Note)

                    ]
            }), content_type='application/json')


class InstanceEndpoint(RestEndpoint):
    def __init__(self, resource):
        super().__init__()
        self.resource = resource

    async def get(self, instance_id):
        instance = session.query(Note).filter(Note.id == instance_id).first()
        if not instance:
            return Response(status=404, body=json.dumps({'not found': 404}), content_type='application/json')
        data = self.resource.render_and_encode(instance)
        return Response(status=200, body=data, content_type='application/json')

    async def put(self, request, instance_id):

        data = await request.json()

        note = session.query(Note).filter(Note.id == instance_id).first()
        note.title = data['title']
        note.description = data['description']
        note.created_at = data['created_at']
        note.created_by = data['created_by']
        note.priority = data['priority']
        session.add(note)
        session.commit()

        return Response(status=201, body=self.resource.render_and_encode(note),
                        content_type='application/json')

    async def delete(self, instance_id):
        note = session.query(Note).filter(Note.id == instance_id).first()
        if not note:
            abort(404, message="Note {} doesn't exist".format(id))
        session.delete(note)
        session.commit()
        return Response(status=204)


class RestResource:
    def __init__(self, notes, factory, collection, properties, id_field):
        self.notes = notes
        self.factory = factory
        self.collection = collection
        self.properties = properties
        self.id_field = id_field

        self.collection_endpoint = CollectionEndpoint(self)
        self.instance_endpoint = InstanceEndpoint(self)

    def register(self, router: UrlDispatcher):
        router.add_route('*', '/{notes}'.format(notes=self.notes), self.collection_endpoint.dispatch)
        router.add_route('*', '/{notes}/{{instance_id}}'.format(notes=self.notes), self.instance_endpoint.dispatch)


    def render(self, instance):
        return OrderedDict((notes, getattr(instance, notes)) for notes in self.properties)

    @staticmethod
    def encode(data):
        return json.dumps(data, indent=4).encode('utf-8')

    def render_and_encode(self, instance):
        return self.encode(self.render(instance))

```

And then we declare our resources in aio-app.py file
```
from aiohttp.web import Application, run_app

from aiohttp_rest import RestResource
from models import Note
from sqlalchemy import engine_from_config


notes = {}
app = Application()
person_resource = RestResource('notes', Note, notes, ('title', 'description', 'created_at', 'created_by', 'priority'), 'title')
person_resource.register(app.router)


if __name__ == '__main__':

    run_app(app)

```

### Running the application
First create the database by:
```
python models.py
```

Run the app by executing following in terminal
```
python aio-app.py
```

Open python shell and execute some requests
```
requests.post('http://localhost:8080/notes',
                 data=json.dumps({ "title": "note two",
                 "created_at": "2017-08-23 00:00", "created_by": "apcelent", "description": "sample notes", "priority": 4
}))

requests.put('http://localhost:8080/notes/1',
                 data=json.dumps({ "title": "note edit",
                 "created_at": "2017-08-23 00:00", "created_by": "apcelent", "description": "sample notes edit", "priority": 4
}))


requests.delete('http://localhost:8080/notes/1')
```

These will create some notes in database using asyncIO REST API. These notes can be viewed at http://127.0.0.1:8080/notes