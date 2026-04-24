Feature: Users API endpoints

  Background:
    * url baseUrl
    * def uniqueId = java.util.UUID.randomUUID() + ''
    * def signupEmail = "karate-user-" + uniqueId + "@example.com"
    * def signupPassword = "changethis123"

  Scenario: Superuser can read own profile
    # Only this scenario actually needs the admin token, so do the login
    # here rather than in Background (which would charge the public-signup
    # scenarios for an admin round-trip they never use).
    * def adminAuth = call read('classpath:helpers/login.feature') { username: '#(adminEmail)', password: '#(adminPassword)' }

    Given path "users", "me"
    And header Authorization = adminAuth.authHeader
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
    * call read('classpath:helpers/signup-user.feature') { email: '#(signupEmail)', password: '#(signupPassword)', fullName: 'Karate Signup User' }

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
    # Avoid coupling to the exact UI-facing copy in app/api/routes/users.py.
    And match response.detail == '#string'
    And match response.detail == '#regex (?i).*already exists.*'
