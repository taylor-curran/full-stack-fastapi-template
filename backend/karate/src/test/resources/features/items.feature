Feature: Items API endpoints

  Background:
    * url baseUrl
    * def adminAuth = callonce read('classpath:helpers/login.feature') { username: '#(adminEmail)', password: '#(adminPassword)' }

  Scenario: Superuser can create a new item
    * def itemTitle = "Karate Item " + java.util.UUID.randomUUID()
    * def itemDescription = "Created from Karate"

    Given path "items"
    And header Authorization = adminAuth.authHeader
    And request
      """
      {
        "title": "#(itemTitle)",
        "description": "#(itemDescription)"
      }
      """
    When method post
    Then status 200
    And match response.id == '#uuid'
    And match response.title == itemTitle
    And match response.description == itemDescription

  Scenario: Superuser can update an existing item
    * def originalTitle = "Karate Item " + java.util.UUID.randomUUID()
    * def updatedTitle = "Karate Item Updated " + java.util.UUID.randomUUID()
    * def updatedDescription = "Updated from Karate"

    Given path "items"
    And header Authorization = adminAuth.authHeader
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
    And header Authorization = adminAuth.authHeader
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

    Given path "items"
    And header Authorization = adminAuth.authHeader
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
    And header Authorization = adminAuth.authHeader
    When method delete
    Then status 200
    And match response.message == "Item deleted successfully"

    Given path "items", itemId
    And header Authorization = adminAuth.authHeader
    When method get
    Then status 404
    # Loose match so that re-wording the API copy in items.py doesn't
    # silently break this assertion.
    And match response.detail == '#string'
    And match response.detail == '#regex (?i).*not found.*'

  Scenario: Non-superuser cannot read another user's item (403)
    # Owner: a fresh non-superuser, created via public signup.
    * def ownerEmail = 'karate-item-owner-' + java.util.UUID.randomUUID() + '@example.com'
    * def ownerPassword = 'ownerpass1234'
    * call read('classpath:helpers/signup-user.feature') { email: '#(ownerEmail)', password: '#(ownerPassword)', fullName: 'Item Owner' }
    * def ownerAuth = call read('classpath:helpers/login.feature') { username: '#(ownerEmail)', password: '#(ownerPassword)' }

    # Intruder: a different non-superuser.
    * def intruderEmail = 'karate-item-intruder-' + java.util.UUID.randomUUID() + '@example.com'
    * def intruderPassword = 'intruderpass1234'
    * call read('classpath:helpers/signup-user.feature') { email: '#(intruderEmail)', password: '#(intruderPassword)', fullName: 'Item Intruder' }
    * def intruderAuth = call read('classpath:helpers/login.feature') { username: '#(intruderEmail)', password: '#(intruderPassword)' }

    # Owner creates an item.
    Given path "items"
    And header Authorization = ownerAuth.authHeader
    And request { title: 'Owned by owner', description: 'cross-user test' }
    When method post
    Then status 200
    * def itemId = response.id

    # Intruder cannot read the owner's item.
    Given path "items", itemId
    And header Authorization = intruderAuth.authHeader
    When method get
    Then status 403
    And match response.detail == '#string'

    # Intruder cannot update or delete it either.
    Given path "items", itemId
    And header Authorization = intruderAuth.authHeader
    And request { title: 'attempted update' }
    When method put
    Then status 403

    Given path "items", itemId
    And header Authorization = intruderAuth.authHeader
    When method delete
    Then status 403
