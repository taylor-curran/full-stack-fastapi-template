@ignore
Feature: Helper - obtain an access token via /login/access-token

  # Inputs:
  #   username (required) - the email/username to authenticate as
  #   password (required) - the plaintext password
  #
  # Outputs:
  #   accessToken - bearer token string
  #   authHeader  - "Bearer <accessToken>", ready to assign to Authorization

  Background:
    * url baseUrl

  Scenario: Obtain an access token
    Given path "login", "access-token"
    And form field username = username
    And form field password = password
    When method post
    Then status 200
    * def accessToken = response.access_token
    * def authHeader = "Bearer " + accessToken
