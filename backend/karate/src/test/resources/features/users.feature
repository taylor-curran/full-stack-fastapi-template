Feature: Users API endpoints

  Background:
    * url baseUrl
    * def uniqueId = java.util.UUID.randomUUID() + ''
    * def signupEmail = "karate-user-" + uniqueId + "@example.com"
    * def signupPassword = "changethis123"
    * def adminLoginData = { username: '#(adminEmail)', password: '#(adminPassword)' }
    Given path "login", "access-token"
    And form fields adminLoginData
    When method post
    Then status 200
    * def accessToken = response.access_token
    * def authHeader = "Bearer " + accessToken

  Scenario: Superuser can read own profile
    Given path "users", "me"
    And header Authorization = authHeader
    When method get
    Then status 200
    And match response.email == adminEmail
    And match response.is_superuser == true

  Scenario: Public signup creates a user
    Given path "users", "signup"
    And request
      """
      {
        "email": "#(signupEmail)",
        "password": "#(signupPassword)",
        "full_name": "Karate Signup User"
      }
      """
    When method post
    Then status 200
    And match response.email == signupEmail
    And match response.full_name == "Karate Signup User"
    And match response.id == '#uuid'

  Scenario: Duplicate signup email is rejected
    Given path "users", "signup"
    And request
      """
      {
        "email": "#(signupEmail)",
        "password": "#(signupPassword)",
        "full_name": "Karate Signup User"
      }
      """
    When method post
    Then status 200

    Given path "users", "signup"
    And request
      """
      {
        "email": "#(signupEmail)",
        "password": "#(signupPassword)",
        "full_name": "Karate Signup User"
      }
      """
    When method post
    Then status 400
    And match response.detail == "The user with this email already exists in the system"
