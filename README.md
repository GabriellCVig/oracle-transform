# oracle-transform
Docker oracle integration courtesy of [egojason/docker-python-oracle](https://github.com/egojason/docker-python-oracle)
  
This docker image serves as a microservice to be used in an HTTP transform by executing queries to a database for entities.

## How to use:
### Setup environment
#### Dev phase
1. Create testing environment
    * Recommended using PyCharm with Docker integration to easily set environment variables for the container during the testing phase.
    * Otherwise set the env variables in your terminal environment and run something like 
        * ```docker build -t <your-docker-user>/httpOracle . && docker run --env db_host=$DB_HOST --env db_port=$DB_PORT --env db_database=$DB_DATABASE --env db_username=$DB_USERNAME --env db_password=$DB_PSW --env handler=$DB_HANDLER --env query=$DB_QUERY --env LOG_LEVEL=$DB_LOG_LEVEL --name httpOracle -t -i -p 5000:5000 --rm <your-dockeruser>/httpOracle```
            * Where each $DB_% is an environment variable which is available in the terminal

* !!!Setup your query to use '{key}' to grab values from the entity!
    * Like this ```SELECT * FROM A WHERE a.ID = '{_id}'```
        * This query will use the current entity's _id and pass it into the query.  
 
2. Create your own handler in handlers.python
    * You probably need your own handler to get the values you want back from the query.
        * Look at do_meterpoint_query handler for inspiration.
    * Each handler needs the parameters: ```dbconnection, variables, logger, entity```
        * _Variables_ to get the query.
        * _dbconnection_ to run the query against.
        * _logger_ to log the errors which might be generated
        * _entity_ which is the input entity to the HTTP transform and ends up as the output of the HTTP tansform
            * I recommend only appending keys here and not removing values! You can choose which fields you want to keep in a second DTL transform.
    * Set your handler name as the environment variable 'handler' and pass it into the program.
3. Use ```curl 0.0.0.0:5000/transform -X POST -d '{"_id":"mock-data"}'``` and look at the result
    * If something goes wrong use ```docker logs httpOracle```

#### Sesam Testing Phase
1. Run the microservice inside Sesam.
 System config:
```
{
  "_id": "http-oracle-transform",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "LOG_LEVEL": "WARNING",
      "database": "$ENV(HTTP_ORACLE_DATABASE)",
      "handler": "<your-own-handler>",
      "host": "$ENV(HTTP_ORACLE_HOST)",
      "password": "$SECRET(HTTP_ORACLE_PASSWORD)",
      "port": 1521,
      "query": "SELECT * FROM a WHERE a.ID = '{_id}' AND a.phone_no = '{phone_no}",
      "username": "$ENV(HTTP_ORACLE_USERNAME)"
    },
    "image": "<your-usr>/http-oracle-transform",
    "port": 5000
  },
  "verify_ssl": true
}
```
Pipe example config
```{
  "_id": "testing-http-transform",
  "type": "pipe",
  "source": {
    "type": "embedded",
    "entities":[{"_id":"mock-data"}]
  },
  "transform": [{
    "type": "http",
    "system": "http-oracle-transform",
    "batch_size": 100,
    "url": "/transform"
  }, {
    "type": "dtl",
    "rules": {
      "default": [
        ["copy", "*"]
      ]
    }
  }]
}
```
