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

  Scenario: Listing items supports q search combined with sort order
    # Seed two items with a known unique substring so we can search for them
    # deterministically without depending on other pre-existing data.
    * def tag = "karate-search-" + java.util.UUID.randomUUID()
    * def titleA = "Alpha " + tag
    * def titleB = "Bravo " + tag

    Given path "items"
    And header Authorization = adminAuth.authHeader
    And request { title: '#(titleA)', description: 'search seed A' }
    When method post
    Then status 200

    Given path "items"
    And header Authorization = adminAuth.authHeader
    And request { title: '#(titleB)', description: 'search seed B' }
    When method post
    Then status 200

    # Ask for those two items specifically, sorted by title ascending.
    Given path "items"
    And header Authorization = adminAuth.authHeader
    And param q = tag
    And param sort = "title_asc"
    When method get
    Then status 200
    And match response.count == 2
    And match response.data[0].title == titleA
    And match response.data[1].title == titleB

    # Flip to title_desc and confirm the order swaps.
    Given path "items"
    And header Authorization = adminAuth.authHeader
    And param q = tag
    And param sort = "title_desc"
    When method get
    Then status 200
    And match response.data[0].title == titleB
    And match response.data[1].title == titleA

  Scenario: Invalid sort value returns 422
    Given path "items"
    And header Authorization = adminAuth.authHeader
    And param sort = "not_a_real_sort"
    When method get
    Then status 422

  Scenario: status=mine filter returns only the caller's items
    # Seed an item as the admin (our "mine" caller) with a unique tag.
    * def mineTag = "karate-mine-" + java.util.UUID.randomUUID()
    * def mineTitle = "Mine item " + mineTag

    Given path "items"
    And header Authorization = adminAuth.authHeader
    And request { title: '#(mineTitle)', description: 'owned by admin' }
    When method post
    Then status 200

    # Seed an item as a different freshly-created user so it should be
    # excluded by status=mine when queried as admin.
    * def otherEmail = 'karate-items-other-' + java.util.UUID.randomUUID() + '@example.com'
    * def otherPassword = 'otherpass1234'
    * call read('classpath:helpers/signup-user.feature') { email: '#(otherEmail)', password: '#(otherPassword)', fullName: 'Other Owner' }
    * def otherAuth = call read('classpath:helpers/login.feature') { username: '#(otherEmail)', password: '#(otherPassword)' }
    * def otherTitle = "Other item " + mineTag

    Given path "items"
    And header Authorization = otherAuth.authHeader
    And request { title: '#(otherTitle)', description: 'owned by other' }
    When method post
    Then status 200

    # As admin, status=mine narrowed by q should only return admin's seeded item.
    Given path "items"
    And header Authorization = adminAuth.authHeader
    And param q = mineTag
    And param status = "mine"
    When method get
    Then status 200
    And match response.count == 1
    And match response.data[0].title == mineTitle

    # And status=others should only surface the other user's item.
    Given path "items"
    And header Authorization = adminAuth.authHeader
    And param q = mineTag
    And param status = "others"
    When method get
    Then status 200
    And match response.count == 1
    And match response.data[0].title == otherTitle
