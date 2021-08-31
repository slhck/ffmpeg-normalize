# Developer Guide

## Tests

Tests are located in `test/test.py`. To run them:

- Install `requirements.txt` and `requirements.dev.txt`
- Run `pytest test/test.py`

## Making Releases

Install the Python packages:

```
pip3 install wheel twine pystache pypandoc gitchangelog
```

Release with:

```
./release.sh
```
