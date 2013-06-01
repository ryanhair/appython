appython
========

App engine python tools

Setup
---------

* Add the following to app.yaml (appython.folder.path: dot-seperated path in your project to the appython folder)

        - url: /*
          script: <appython.folder.path>.main.app
for example, appython.main.app

* Any handler you create needs to be added to includes.py.  For example, if you had a handler under the path '/handlers/device/address', and the handler is called AddressHandler, you would add 'handlers.device.address.AddressHandler' to the handlers array.  Also note that the file must be in a folder that also has an &#95;&#95;init&#95;&#95;.py

And you're ready to begin!

Create a Model
----------------------

Using the included BaseModel is much the same as using ndb.Model, with a little syntactic sugar on top.  It automatically gives you `to_json` and `from_json` methods (which helps simplify handlers, explained later), and it also adds default "created" and "updated" properties, which are automatically updated for you.

    from appython.base_model import BaseModel
    
    class Address
        street = ndb.StringProperty(required=True)
        apt = ndb.StringProperty()
        city = ndb.StringProperty(required=True)
        state = ndb.StringProperty(required=True)
        zip = ndb.StringProperty(required=True)

Create a Handler
------------------------

Creating a handler is easy.  Below is an example:

    from models.address import Address
    
    @endpoint('/address')
    class AddressHandler:
        @get('/')
        def get_addresses(self):
            return Address.query().fetch()

First, remember that you need to add this handler to includes.py

Note the `endpoint` annotation.  This specifies what path this handler will match to.

Next, the `get` annotation.  You can specify an extra path here if desired, which will be appended to the path specified in `endpoint`.  `@get` is equivalent to `@get('/')`

`self` has a reference to request and response, which are instances of webapp2 Request and Response classes.  Use self.request and self.response as you would normally do with regular AppEngine handlers (minus using self.response.out.write).

Note that you can return anything that is `json.dumps`-able or extends from BaseModel (that's where we use BaseModel's `to_json` internally)

Full example (car.py)
------------------

    from appython.base_model import BaseModel
    from google.appengine.ext import ndb
    
    class Car(BaseModel):
        make = ndb.StringProperty(required=True)
        model = ndb.StringProperty(required=True)
        vin = ndb.StringProperty(required=True)
        color = ndb.StringProperty()
    
    @endpoint('/book')
    class CarHandler:
        @get
        def get_all(self):
            return Car.query().fetch()
        
        @get('/<id>')
        def get_by_id(self, id):
            return Car.get_by_id(id)
        
        @post
        @expects(Car)  #expects will grab request body and create models out of it, passing it as first param after self
        def create(self, cars):
            if isinstance(cars, list):
                for car in cars:
                    car.put()
                return [car.key.id() for car in cars]
            
            cars.put()
            return cars.key.id() 
        
        @put
        @expects(Car, multiple=False)
        def update(self, car):
            car.put()
            return car.key.id()
        
        @delete
        @expects(Car, multiple=False, keys_only=True)
        def delete(self, car_key):
            car_key.delete()
            return {
                'deleted':True
            }

includes.py

    handlers = [
        'car.CarHandler'
    ]

To do:
-----
*Fix BaseModel's to_json to allow passing in a "graph path", or a dict that represents what should be loaded.
For example, if I have the following structure:
                    CarDealershipFranchise
                   /                       \
             CarDealershipList      ExecutiveList
            /                 \
          CarList          EmployeeList

I could call to_json on CarDealershipFranchise with { ExecutiveList: Load.Basic, carDealershipList: { EmployeeList: {  }, carList: Load.Basic } } to get all the way deep