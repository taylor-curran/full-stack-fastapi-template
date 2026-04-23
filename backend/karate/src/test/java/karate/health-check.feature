Feature: Backend health check

  Scenario: Health endpoint returns true
    * def apiBaseUrl = karate.properties['apiBaseUrl'] ? karate.properties['apiBaseUrl'] : 'http://localhost:8000'
    Given url apiBaseUrl
    And path 'api', 'v1', 'utils', 'health-check'
    When method get
    Then status 200
    And match response == true
