import sqlite3

def make_dicts(cursor, row):
  return dict((cursor.description[idx][0], value)
              for idx, value in enumerate(row))

class RealbotStorage:
  def __init__(self, filename):
    self.db = sqlite3.connect(filename)
    self.db.row_factory = make_dicts

  def import_schema(self, schema_filename):
    with open(schema_filename) as f:
      cur = self.db.cursor()
      cur.executescript(f.read())
      self.db.commit()

  def query(self, sql, args=(), one_row=False):
    cur = self.db.cursor()
    cur.execute(sql, args)
    self.db.commit()
    result = cur.fetchall()
    cur.close()
    return (result[0] if result else None) if one_row else result

  def close(self):
    self.db.close()
