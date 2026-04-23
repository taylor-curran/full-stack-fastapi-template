Feature: Auth API endpoints

  Background:
    * url baseUrl

  Scenario: Admin can get an access token
    Given path "login", "access-token"
    And form field username = adminEmail
    And form field password = adminPassword
    When method post
    Then status 200
    And match response.access_token == '#string'
    And match response.token_type == 'bearer'

  Scenario: Login fails with incorrect password
    Given path "login", "access-token"
    And form field username = adminEmail
    And form field password = "invalid-password"
    When method post
    Then status 400
    And match response.detail == "Incorrect email or password"

  Scenario: Test-token endpoint accepts a valid bearer token
    Given path "login", "access-token"
    And form field username = adminEmail
    And form field password = adminPassword
    When method post
    Then status 200
    * def accessToken = response.access_token

    Given path "login", "test-token"
    And header Authorization = "Bearer " + accessToken
    When method post
    Then status 200
    And match response.email == adminEmail
    And match response.is_superuser == true
