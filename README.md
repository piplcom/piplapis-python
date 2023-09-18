piplapis Python Library
===========================

This is a Python client library for easily integrating Pipl's APIs into your application.

* Full details about Pipl's APIs - [https://pipl.com/api](https://pipl.com/api)  
* This library is available in other languages - [https://docs.pipl.com/docs/code-libraries](https://docs.pipl.com/docs/code-libraries)

Library Requirements
--------------------

* From python SDK version 5.3.0 and above, Python 3.8 and above is supported 

Installation
------------

    pip install piplapis-python
    
Hello World
------------
```
from piplapis.search import SearchAPIRequest
request = SearchAPIRequest(
    api_key='YOURKEY',
    email=u'clark.kent@example.com',
    first_name=u'Clark', 
    last_name=u'Kent'
)
response = request.send()
```

Getting Started & Code Snippets
-------------------------------

**Pipl's Search API**
* API Portal - [https://pipl.com/api/](https://pipl.com/api/)
* Code snippets - [https://docs.pipl.com/docs/code-snippets](https://docs.pipl.com/docs/code-snippets)  
* Full reference - [https://docs.pipl.com/reference/](https://docs.pipl.com/reference/)
