simple_search
=============

`simple_search` is a very simple (and thus probably not very fast) python module
to search for keywords inside the context of functions/methods. The twist here
is that you can search for multiple keywords so your search results will be
functions that contain all the specified keywords. This is of course not your
everyday search but I've found myself wanting this feature in certain occasions,
for example: I want to search functions that perform certain operations that
might span several lines and I kinda know some of the values.

usage
=====

I'm running this on poetry so I guess it should be something like

```bash
$ git clone blahblahblah`
$ cd blahblahblah
$ poetry install
$ poetry run python -m simple_search -h
```

It is noteworthy that the module can be used through a pipe for searching
individual files but it is terribly slow for stuff like piping `find` results.
In that case it is best to use the `--directories` arg.
