Feature: Auth API endpoints

  Background:
    * url baseUrl
    * def userId = java.util.UUID.randomUUID() + ''
    * def loginEmail = 'karate-auth-' + userId + '@example.com'
    * def loginPassword = 'changethis123'

  Scenario: User can get an access token
    Given path "users", "signup"
    And request
      """
      {
        "email": "#(loginEmail)",
        "password": "#(loginPassword)",
        "full_name": "Karate Auth User"
      }
      """
    When method post
    Then status 200

    Given path "login", "access-token"
    And form field username = loginEmail
    And form field password = loginPassword
    When method post
    Then status 200
    And match response.access_token == '#string'
    And match response.token_type == 'bearer'

  Scenario: Login fails with incorrect password
    Given path "users", "signup"
    And request
      """
      {
        "email": "#(loginEmail)",
        "password": "#(loginPassword)",
        "full_name": "Karate Auth User"
      }
      """
    When method post
    Then status 200

    Given path "login", "access-token"
    And form field username = loginEmail
    And form field password = "invalid-password"
    When method post
    Then status 400
    And match response.detail == "Incorrect email or password"

  Scenario: Test-token endpoint accepts a valid bearer token
    Given path "users", "signup"
    And request
      """
      {
        "email": "#(loginEmail)",
        "password": "#(loginPassword)",
        "full_name": "Karate Auth User"
      }
      """
    When method post
    Then status 200

    Given path "login", "access-token"
    And form field username = loginEmail
    And form field password = loginPassword
    When method post
    Then status 200
    * def accessToken = response.access_token

    Given path "login", "test-token"
    And header Authorization = "Bearer " + accessToken
    When method post
    Then status 200
    And match response.email == loginEmail
