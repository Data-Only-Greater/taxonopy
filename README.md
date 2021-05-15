## Taxonopy

Record update process:

```
db = DataBase(db_path)
doc = db.search(make_query("Title", "Bob"))[0]
record = SCHTree.from_dict(dict(doc))
builder = RecordBuilder(schema)
updated = builder.build(record)
db.replace(doc.doc_id, updated)
```
