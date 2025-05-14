In this repository, please create an AWS Python 3.13 Lambda that does the following:

* It can receive events from an API Gateway and AWS AppSync.
* It processes CRUD events on a DynamoDB table.
* The dynamodb table name is found by looking it up in an AWS AppConfig configuration. The variable to lookup is 'serviceOrderTableName'.
* In the case where the the request is an addition (a POST request), it should:
    - Validate that the request has a customerId in the URI. It should also have a parameter that contains a locationId.
    - The request should have a json structure that contains the service order fields. It has the following fields:
        - unitId (uuid.uuid4())
        - actionId (uuid.uuid4())
        - serviceDate (ISO 8601)
        - serviceTime (ISO 8601)
        - serviceDuration (int)
        - serviceStatus (str)
        - employeeId (uuid.uuid4())
        - serviceNotes (str)
    - The required fields in that list are unitId and actionId. They must exist or the request will fail. All other fields are optional and should be omitted if not provided.
    - Insert the new item into the DynamoDB table. The PK on the insert should be a uuid, and the SK should be the customerId. It should also add a createdAt timestamp in ISO 8601 format.
    - Return the new item's ID and status code 201.
* In the case where the request is an update (an PUT request), it should:
    - Validate that the request has a valid uuid.
    - The request should have a json structure that contains the service order fields. It has the following fields:
        - unitId (uuid.uuid4())
        - actionId (uuid.uuid4())
        - serviceDate (ISO 8601)
        - serviceTime (ISO 8601)
        - serviceDuration (int)
        - serviceStatus (str)
        - employeeId (uuid.uuid4())
        - serviceNotes (str)
    - The required fields in that list are unitId and actionId. They must exist or the request will fail. All other fields are optional and should be omitted if not provided.
    - Update the existing item in the DynamoDB table. The PK on the update should be a uuid, and the SK should be the customerId. It should also update the updatedAt timestamp in ISO 8601 format.
    - Return the updated item's ID and status code 200.
* In the case where the request is a deletion (a DELETE request), it should:
    - Validate that the request has a uuid in the URI.
    - Update the existing item in the DynamoDB table. The PK on the update should be a uuid, and the SK should be the customerId. It should add a deletedAt timestamp in ISO 8601 format.
    - Return status code 204.
* In the case where the request is a retrieval (a GET request), it should:
    - Validate that the request has a customerId in the URI. It may optionally include a uuid or a locationId in the URI.
    - Retrieve the existing item(s) from the DynamoDB table. If a uuid is provided, retrieve the item with that uuid and customerId. If a locationId is provided, retrieve all items with that locationId and customerId. If neither is provided, retrieve all items with the customerId.
    - Return the retrieved item's ID and status code 200.
* Make sure errors are handled appropriately.
* Make sure that tests are written for all cases.
* Make sure the code is linted and formatted according to ruff and the other rules that have been given.
* All code should comply with mypy and pylint.
* All code should be documented with docstrings.
* Create the required requirements.txt file and install all dependencies.
