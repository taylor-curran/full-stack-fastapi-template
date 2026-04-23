Feature: Items API endpoints

  Background:
    * url baseUrl

  Scenario: Superuser can create a new item
    * def itemTitle = "Karate Item " + java.util.UUID.randomUUID()
    * def itemDescription = "Created from Karate"

    Given path "login", "access-token"
    And form field username = adminEmail
    And form field password = adminPassword
    When method post
    Then status 200
    * def accessToken = response.access_token

    Given path "items"
    And header Authorization = "Bearer " + accessToken
    And request
      """
      {
        "title": "#(itemTitle)",
        "description": "#(itemDescription)"
      }
      """
    When method post
    Then status 200
    And match response.id == '#string'
    And match response.title == itemTitle
    And match response.description == itemDescription

  Scenario: Superuser can update an existing item
    * def originalTitle = "Karate Item " + java.util.UUID.randomUUID()
    * def updatedTitle = "Karate Item Updated " + java.util.UUID.randomUUID()
    * def updatedDescription = "Updated from Karate"

    Given path "login", "access-token"
    And form field username = adminEmail
    And form field password = adminPassword
    When method post
    Then status 200
    * def accessToken = response.access_token

    Given path "items"
    And header Authorization = "Bearer " + accessToken
    And request
      """
      {
        "title": "#(originalTitle)",
        "description": "Original Description"
      }
      """
    When method post
    Then status 200
    * def itemId = response.id

    Given path "items", itemId
    And header Authorization = "Bearer " + accessToken
    And request
      """
      {
        "title": "#(updatedTitle)",
        "description": "#(updatedDescription)"
      }
      """
    When method put
    Then status 200
    And match response.id == itemId
    And match response.title == updatedTitle
    And match response.description == updatedDescription

  Scenario: Superuser can delete an item and it is no longer found
    * def itemTitle = "Karate Item " + java.util.UUID.randomUUID()

    Given path "login", "access-token"
    And form field username = adminEmail
    And form field password = adminPassword
    When method post
    Then status 200
    * def accessToken = response.access_token

    Given path "items"
    And header Authorization = "Bearer " + accessToken
    And request
      """
      {
        "title": "#(itemTitle)",
        "description": "To be deleted"
      }
      """
    When method post
    Then status 200
    * def itemId = response.id

    Given path "items", itemId
    And header Authorization = "Bearer " + accessToken
    When method delete
    Then status 200
    And match response.message == "Item deleted successfully"

    Given path "items", itemId
    And header Authorization = "Bearer " + accessToken
    When method get
    Then status 404
    And match response.detail == "Item not found"
