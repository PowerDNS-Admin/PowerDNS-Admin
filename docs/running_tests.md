### Running tests

**NOTE:** Tests will create `__pycache__` folders which will be owned by root, which might be issue during rebuild

 thus (e.g. invalid tar headers message) when such situation occurs, you need to remove those folders as root

1. Build images

  ```
    docker-compose -f docker-compose-test.yml build
  ```

2. Run tests

  ```
    docker-compose -f docker-compose-test.yml up
  ```

3. To teardown the test environment

  ```
    docker-compose -f docker-compose-test.yml down
    docker-compose -f docker-compose-test.yml rm
  ```
