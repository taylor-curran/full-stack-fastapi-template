Feature: Auth API endpoints

  Background:
    * url baseUrl
    * def userId = java.util.UUID.randomUUID() + ''
    * def loginEmail = 'karate-auth-' + userId + '@example.com'
    * def loginPassword = 'changethis123'
    # callonce ensures the user is created exactly once per scenario regardless
    # of how many times the helper is referenced.
    * callonce read('classpath:helpers/signup-user.feature') { email: '#(loginEmail)', password: '#(loginPassword)', fullName: 'Karate Auth User' }

  Scenario: User can get an access token
    Given path "login", "access-token"
    And form field username = loginEmail
    And form field password = loginPassword
    When method post
    Then status 200
    And match response.access_token == '#string'
    And match response.token_type == 'bearer'

  Scenario: Login fails with incorrect password
    Given path "login", "access-token"
    And form field username = loginEmail
    And form field password = "invalid-password"
    When method post
    Then status 400
    # Avoid coupling to the exact UI-facing copy in app/api/routes/login.py.
    # Assert on shape + a stable token instead.
    And match response.detail == '#string'
    And match response.detail contains 'password'

  Scenario: Test-token endpoint accepts a valid bearer token
    * def auth = call read('classpath:helpers/login.feature') { username: '#(loginEmail)', password: '#(loginPassword)' }

    Given path "login", "test-token"
    And header Authorization = auth.authHeader
    When method post
    Then status 200
    And match response.email == loginEmail
