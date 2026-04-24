import { expect, type Page, test } from "@playwright/test"
import { createUser } from "./utils/privateApi"
import {
  randomEmail,
  randomItemDescription,
  randomItemTitle,
  randomPassword,
} from "./utils/random"
import { logInUser } from "./utils/user"

// Open the actions menu for the row whose visible text contains `title`.
// Uses an accessible name rather than a positional `.last()` selector so
// the test isn't silently broken by a future status icon rendered as a
// button in the same row.
const openRowActions = async (page: Page, title: string) => {
  const row = page.getByRole("row").filter({ hasText: title })
  await row.getByRole("button", { name: "Item actions" }).click()
  return row
}

const createItemViaForm = async (
  page: Page,
  { title, description }: { title: string; description?: string },
) => {
  await page.getByRole("button", { name: "Add Item" }).click()
  await page.getByLabel("Title").fill(title)
  if (description !== undefined) {
    await page.getByLabel("Description").fill(description)
  }
  await page.getByRole("button", { name: "Save" }).click()
  await expect(page.getByText("Item created successfully")).toBeVisible()
}

test("Items page is accessible and shows correct title", async ({ page }) => {
  await page.goto("/items")
  await expect(page.getByRole("heading", { name: "Items" })).toBeVisible()
  await expect(page.getByText("Create and manage your items")).toBeVisible()
})

test("Add Item button is visible", async ({ page }) => {
  await page.goto("/items")
  await expect(page.getByRole("button", { name: "Add Item" })).toBeVisible()
})

test.describe("Items management", () => {
  test.use({ storageState: { cookies: [], origins: [] } })
  let email: string
  const password = randomPassword()

  test.beforeAll(async () => {
    email = randomEmail()
    await createUser({ email, password })
  })

  test.beforeEach(async ({ page }) => {
    await logInUser(page, email, password)
    await page.goto("/items")
  })

  test("Create a new item successfully (and persists across reload)", async ({
    page,
  }) => {
    const title = randomItemTitle()
    const description = randomItemDescription()

    await createItemViaForm(page, { title, description })
    await expect(page.getByText(title)).toBeVisible()

    // Reload-persistence is the same flow with one extra assertion site,
    // so cover it here rather than duplicating the whole create path in a
    // separate test.
    await page.reload()
    const row = page.getByRole("row").filter({ hasText: title })
    await expect(row).toBeVisible()
    await expect(row.getByText(description)).toBeVisible()
  })

  test("Create item with only required fields", async ({ page }) => {
    const title = randomItemTitle()

    await createItemViaForm(page, { title })
    await expect(page.getByText(title)).toBeVisible()
  })

  test("Cancel item creation", async ({ page }) => {
    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill("Test Item")
    await page.getByRole("button", { name: "Cancel" }).click()

    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("Title is required", async ({ page }) => {
    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill("")
    await page.getByLabel("Title").blur()

    await expect(page.getByText("Title is required")).toBeVisible()
  })

  test.describe("Edit and Delete", () => {
    let itemTitle: string

    test.beforeEach(async ({ page }) => {
      itemTitle = randomItemTitle()
      await createItemViaForm(page, { title: itemTitle })
      await expect(page.getByRole("dialog")).not.toBeVisible()
    })

    test("Edit an item successfully (and persists across reload)", async ({
      page,
    }) => {
      await openRowActions(page, itemTitle)
      await page.getByRole("menuitem", { name: "Edit Item" }).click()

      const updatedTitle = randomItemTitle()
      await page.getByLabel("Title").fill(updatedTitle)
      await page.getByRole("button", { name: "Save" }).click()

      await expect(page.getByText("Item updated successfully")).toBeVisible()
      await expect(page.getByText(updatedTitle)).toBeVisible()

      await page.reload()
      await expect(
        page.getByRole("row").filter({ hasText: updatedTitle }),
      ).toBeVisible()
    })

    test("Delete an item successfully (and stays removed across reload)", async ({
      page,
    }) => {
      await openRowActions(page, itemTitle)
      await page.getByRole("menuitem", { name: "Delete Item" }).click()
      await page.getByRole("button", { name: "Delete" }).click()

      await expect(
        page.getByText("The item was deleted successfully"),
      ).toBeVisible()

      // Scope the absence assertion to the table — `toHaveCount(0)` won't
      // be fooled by a stale toast/snackbar that still echoes the title
      // text elsewhere on the page.
      await expect(
        page.getByRole("row").filter({ hasText: itemTitle }),
      ).toHaveCount(0)

      await page.reload()
      await expect(
        page.getByRole("row").filter({ hasText: itemTitle }),
      ).toHaveCount(0)
    })
  })
})

test.describe("Items empty state", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Shows empty state message when no items exist", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/items")

    await expect(page.getByText("You don't have any items yet")).toBeVisible()
    await expect(page.getByText("Add a new item to get started")).toBeVisible()
  })
})
