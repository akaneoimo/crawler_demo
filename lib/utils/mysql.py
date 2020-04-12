import pymysql


class DataBase:
    def __init__(self, host, username, password, database):
        self.conn = pymysql.connect(host, username, password, database, charset='utf8', cursorclass=pymysql.cursors.DictCursor)
        self.table_columns = {
            table: [r['Field'] for r in self.execute(f'describe {table}', res=True)] \
            for table in [r[0] for r in self.execute('show tables', res='tuple')]
        }
        
        self._decorate()
    
    def create(self, table, **columns):
        self.execute(f'''
            create table {table} ({','.join([f"{column_name} {column_type}" for column_name, column_type in columns.items()])})
        ''')
    
    def drop(self, table):
        self.execute(f'drop table {table}')
    
    @staticmethod
    def _placeholder_expression(concat_word, constraints, formatter=0):
        assert concat_word in ['and', 'or', ',']
        if constraints:
            if concat_word in ['and', 'or']:
                return f' {concat_word} '.join([f'{key} {"in" if isinstance(value, list) else "="} {f"%({key})s"}' for key, value in constraints.items()])
            else:
                if formatter == 0:
                    return f','.join([key for key, _ in constraints.items()])
                elif formatter == 1:
                    return f','.join([f'%({key})s' for key, _ in constraints.items()])
                elif formatter == 2:
                    return f','.join([f'{key.strip("-")}=%({key})s' for key, _ in constraints.items()])
        return ''

    def select(self, options, *columns, **constraints):
        col_exp = '*' if not columns else ','.join(columns)
        return self.execute((
            f"select {col_exp} from {options['table']} "
            f"{'where ' if constraints else ' '}"
            f"{self._placeholder_expression(options['concat'], constraints)}"
            f"{options['extra']}"
        ), constraints, res=options['res'])

    def insert(self, options, **data):
        lastrowid = self.execute((
            f"insert into {options['table']} "
            f"({self._placeholder_expression(',', data)}) values "
            f"({self._placeholder_expression(',', data, 1)})"
        ), data, commit=options['commit'])
        try:
            return lastrowid
            # primary_key = options['primary_key']
            # return max(self.select(options['table'], primary_key), key=lambda r: r[primary_key])[primary_key]
        except:
            return -1

    def update(self, options, **data):
        data = {f'-{key}': value for key, value in data.items()}
        sql = (
            f"update {options['table']} set {self._placeholder_expression(',', data, 2)} "
            f"{'where ' if options['constraints'] else ' '} "
            f"{self._placeholder_expression(options['concat'], options['constraints'])}"
        )
        data.update(options['constraints'])
        self.execute(sql, data, commit=options['commit'])

    def delete(self, options, **constraints):
        self.execute((
            f"delete from {options['table']} "
            f"{'where ' if constraints else ' '} "
            f"{self._placeholder_expression(options['concat'], constraints)}"
        ), constraints, commit=options['commit'])

    def random(self, table, num, *columns):
        # return self.select(table, *columns, id=[i for i in random.sample([r['id'] for r in self.select(table, 'id')], num)])
        col_exp = ','.join(columns or self.columns.keys())
        return [self.execute(f'''
           select {col_exp} from `{table}` as t1
           join (
               select round (
                   rand() * (
                       (select max(id) from `{table}`) - (select min(id) from `{table}`)
                   ) + (select min(id) from `{table}`)
               ) as id_
           ) as t2
           where t1.id >= t2.id_ order by t1.id limit 1
        ''', res=True) for _ in range(num)]

    def execute(self, sql, data=None, res=False, commit=False):
        self.conn.connect()
        if res == 'tuple':
            cursor = self.conn.cursor(cursor=pymysql.cursors.Cursor)
        elif res == 'dict':
            cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
        else:
            cursor = self.conn.cursor()
        try:
            cursor.execute(sql, data)
            if commit:
                self.commit()
            if res:
                return cursor.fetchall()
        except Exception as e:
            raise e
        finally:
            cursor.close()
        return cursor.lastrowid
    
    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.close()
        except:
            pass

    def __del__(self):
        try:
            self.close()
        except:
            pass

    class Check:
        def __init__(self, func, valid_table_columns):
            self.func = func
            self.valid_table_columns = valid_table_columns
            self.default_options = {
                'select': {
                    'extra': '',
                    'concat': 'and',
                    'res': True,
                },
                'insert': {
                    'res': True,
                    'commit': True,
                    'primary_key': 'id'
                },
                'update': {
                    'concat': 'and',
                    'commit': True,
                    'contraints': {}
                },
                'delete': {
                    'concat': 'and',
                    'commit': True,
                    'contraints': {}
                }
            }
        def __call__(self, options, *columns, **constraints):
            """
            options: {
                'table': table_name,
                'res': False or True or 'tuple' or 'dict', 
                'extra': extra query constraints appended at end, *** ONLY USE `extra` FOR YOURSELF, SUCH AS `asc by id`, NEVER ACCEPT `extra` FROM USER ***,
                'concat': 'and' or 'or',
                'commit': False or True
            }
            *columns: columns to query
            *constraints: string or list(tuple), string for `=` and list for `in`
            """
            if type(options) is str:
                options = {'table': options}
            options_ = self.default_options[self.func.__name__].copy()
            options_.update(options)
            table = options_.get('table')
            # if self.valid_table_columns.get(table) and set(columns) <= set(self.valid_table_columns[table]):
            return self.func(options_, *columns, **constraints)
            # raise ValueError('table or columns are not invalid')
    
    def _decorate(self):
        # use `Check` class to decorate the `Database` instance method and pass the instance as parameter to `Check`
        # if use syntactic sugar, call the decorated function from the `Check` instance will not get the `Database` instance
        # or we can use __get__ to get the `Database` instance
        self.select = self.Check(self.select, self.table_columns)
        self.insert = self.Check(self.insert, self.table_columns)
        self.update = self.Check(self.update, self.table_columns)
        self.delete = self.Check(self.delete, self.table_columns)
