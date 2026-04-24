@ignore
Feature: Helper - sign up a public user

  # Inputs:
  #   email    (required) - email address for the new user
  #   password (required) - plaintext password for the new user
  #   fullName (optional) - defaults to "Karate Helper User"
  #
  # Output:
  #   response - the created user record from POST /users/signup

  Background:
    * url baseUrl
    * def fullName = (typeof fullName == 'undefined' || fullName == null) ? 'Karate Helper User' : fullName

  Scenario: Sign up a public user
    Given path "users", "signup"
    And request
      """
      {
        "email": "#(email)",
        "password": "#(password)",
        "full_name": "#(fullName)"
      }
      """
    When method post
    Then status 200
