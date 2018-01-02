1. activate environment(python > 3.5)
2. Install requirements
3. Create database python models.py
4. Run the app python aio-app.py

run in the shell

requests.post('http://localhost:8080/notes',
                 data=json.dumps({ "title": "note two",
                 "created_at": "2017-08-23 00:00", "created_by": "apcelent", "description": "sample notes", "priority": 4
}))

requests.put('http://localhost:8080/notes/1',
                 data=json.dumps({ "title": "note edit",
                 "created_at": "2017-08-23 00:00", "created_by": "apcelent", "description": "sample notes edit", "priority": 4
}))


requests.delete('http://localhost:8080/notes/1')
