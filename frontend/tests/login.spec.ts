import { expect, type Page, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { randomPassword } from "./utils/random.ts"

test.use({ storageState: { cookies: [], origins: [] } })

const fillForm = async (page: Page, email: string, password: string) => {
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
}

const verifyInput = async (page: Page, testId: string) => {
  const input = page.getByTestId(testId)
  await expect(input).toBeVisible()
  await expect(input).toHaveText("")
  await expect(input).toBeEditable()
}

/**
 * Log in via the public REST API and seed the resulting access token into
 * localStorage so subsequent navigations are authenticated. This avoids
 * re-running the full form-submit path for tests whose actual subject is
 * "what does the app do once a session already exists?".
 */
const seedAuthenticatedSession = async (
  page: Page,
  email: string,
  password: string,
) => {
  const apiUrl = process.env.VITE_API_URL
  if (!apiUrl) {
    throw new Error("VITE_API_URL is not set")
  }

  const response = await page.request.post(
    `${apiUrl}/api/v1/login/access-token`,
    {
      form: { username: email, password },
    },
  )
  expect(response.ok()).toBeTruthy()
  const { access_token } = (await response.json()) as { access_token: string }

  await page.goto("/login")
  await page.evaluate((token) => {
    localStorage.setItem("access_token", token)
  }, access_token)
}

test("Inputs are visible, empty and editable", async ({ page }) => {
  await page.goto("/login")

  await verifyInput(page, "email-input")
  await verifyInput(page, "password-input")
})

test("Log In button is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(page.getByRole("button", { name: "Log In" })).toBeVisible()
})

test("Forgot Password link is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(
    page.getByRole("link", { name: "Forgot your password?" }),
  ).toBeVisible()
})

test("Sign up link navigates to registration page", async ({ page }) => {
  await page.goto("/login")

  await page.getByRole("link", { name: "Sign up" }).click()
  await page.waitForURL("/signup")
  await expect(page).toHaveURL("/signup")
})

// Cover both ways of submitting the login form (button click + Enter key)
// from a single dashboard-success assertion site, so that the success
// expectation only lives in one place.
const submissionMethods: Array<{
  name: string
  submit: (page: Page) => Promise<void>
}> = [
  {
    name: "button click",
    submit: async (page) => {
      await page.getByRole("button", { name: "Log In" }).click()
    },
  },
  {
    name: "Enter key",
    submit: async (page) => {
      await page.getByTestId("password-input").press("Enter")
    },
  },
]

for (const { name, submit } of submissionMethods) {
  test(`Log in with valid email and password (${name})`, async ({ page }) => {
    await page.goto("/login")

    await fillForm(page, firstSuperuser, firstSuperuserPassword)
    await submit(page)

    await page.waitForURL("/")
    await expect(
      page.getByText("Welcome back, nice to see you again!"),
    ).toBeVisible()
  })
}

test("Authenticated users are redirected away from /login", async ({
  page,
}) => {
  // Seed the session via the API instead of going through the form a
  // second time; the behaviour under test is the redirect, not the form.
  await seedAuthenticatedSession(page, firstSuperuser, firstSuperuserPassword)

  await page.goto("/login")
  await page.waitForURL("/")
  await expect(page).toHaveURL("/")
})

test("Log in with invalid email", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, "invalidemail", firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Invalid email address")).toBeVisible()
})

test("Log in with invalid password", async ({ page }) => {
  const password = randomPassword()

  await page.goto("/login")
  await fillForm(page, firstSuperuser, password)
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Incorrect email or password")).toBeVisible()
})

test("Successful log out", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")
})

test("Logged-out user cannot access protected routes", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")

  await page.goto("/settings")
  await page.waitForURL("/login")
})

test("Redirects to /login when token is wrong", async ({ page }) => {
  await page.goto("/settings")
  await page.evaluate(() => {
    localStorage.setItem("access_token", "invalid_token")
  })
  await page.goto("/settings")
  await page.waitForURL("/login")
  await expect(page).toHaveURL("/login")
})
