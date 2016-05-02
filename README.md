# memoizewrapper

A python module provides decorators to store wrapped function's return values into memory. They are used on relatively expensive functions, which allows a certain delay. For example, they can be used when load meta data from database, which is assumed won't change frequently.

## Features

- Expiring Memoize decorator which allows user to set a time-to-live on cache. (Of course, 0 means forever)
- LRU Memoize decorator which provides a cache storage with a given capacity.
- Flush the cache explicitly
- Key template - user can customize how their key look like.
- Skip cache - user can control what return values they want to cache.
- Deep copy - if the stored value is deep copied.

## Usage

### Expiring cache decorator

```python
import memoizewrapper

# cache will be expired in 10 seconds
# the stored/returned value will be deep-copied. Feel free to change them
# cache is based on parameter `param1`
@memoizewrapper.expiring_memoize(('param1',), 10, deepcopy=True)
def my_func(param1):
    return param1

# flush the cache
my_func.flush()
```

### Lru cache decorator

```python
import memoizewrapper

# it mantains the cache by LRU algorithm, and the capacity is 3
# the stored/returned value is not deep-copied. It is better if the return values are immutable,
# (or, you remember not to modify them)
# cache is based on parameter `param1` and `param2`. Even if the returned values depend on
# `param3`, `param3` wont be a part of the key, see example below
@memoizewrapper.lru_memoize(('param1', 'param2', 'param3'), 3)
def my_func(param1, param2, param3):
    return ', '.join(param1, param2, param3)

my_func('Good', 'morning', 'Beijing')  # 'Good morning Beijing'
my_func('Good', 'morning', 'Shanghai')  # 'Good morning Beijing'
```

### skip cache

```python
import memoizewrapper

# Sometimes, you don't want to cache the return value. Let say we are querying a card database,
# we don't want to cache a card if it does not exist.
@memoizewrapper.lru_memoize(('card_id',), 1000, escape_cache_if=lambda x: x is None)
def query_card_name(card_id, db_connection):
    cursor = db_connection.cursor()
    cursor.execute('''SELECT `card_name` FROM `card` WHERE `card_id`=%(card_id)s''',
                   {'card_id': card_id})
    row = cursor.fetchone()
    return row['card_name'] if row else None
```

### customize key generator and storage

`memoizewrapper` can be extended to provide more features. Samples are provided below.

#### file cache

UNDER CONSTRUCTION

#### actively clean expired cache

UNDER CONSTRUCTION